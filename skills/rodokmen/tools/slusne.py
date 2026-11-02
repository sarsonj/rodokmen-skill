#!/usr/bin/env python3
"""Brzda proti zablokování archivem: společný limit dotazů pro všechny procesy na jednom počítači.

Archivy blokují IP adresu po sérii rychlých dotazů (MZA, ZA Opava…). Nástroje v tools/ si brzdu načítají samy
(`import slusne`). Vlastní skripty, curl a shellové skripty spouštěj přes obal:

  python3 -I tools/slusne.py pracovni/muj_skript.py [argumenty]   -> Python skript (urllib, requests…)
  python3 -I tools/slusne.py - <<'EOF' … EOF                       -> kód v Pythonu ze vstupu (heredoc), i -c "kód"
  python3 -I tools/slusne.py curl [argumenty curl]                 -> curl se stejným limitem
  python3 -I tools/slusne.py bash pracovni/skript.sh [argumenty]   -> shellový skript; curl uvnitř jde přes brzdu
  python3 -I tools/slusne.py stav                                  -> limity a zastavené weby
  python3 -I tools/slusne.py odblokuj [web]                        -> zrušit stopku (jen když víš, proč nastala)

Pravidla (pro každý web zvlášť, společně pro všechny procesy i projekty na počítači – mají jednu IP adresu):
  - dotazy (stránky, hledání, API) nejvýš 1 za 2 s (ZA Opava 1 za 4 s), obrázky a dlaždice nejvýš 10 za s;
    omezuje se frekvence, ne souběh (vlákna stahování dlaždic nevadí),
  - po odpovědi 429/503 (u dotazu i 403), po stránce „zablokováno“ nebo po 3 nepovedených spojeních za sebou
    se web zastaví pro všechny procesy a nástroj hned skončí (kód 3). Nic se neopakuje, nic se neobchází.
    Stopka trvá 30 minut, při druhém odmítnutí webu během 24 h 2 hodiny, při třetím a dalším 8 hodin.
  - curl, python a bash spuštěné z Pythonu (subprocess) jdou taky přes brzdu.
localhost, vlastní web (Netlify), GitHub a npm se nebrzdí. V prohlížeči (Claude in Chrome) brzda neplatí –
tam nejvýš 1 dotaz za 2 s a žádné smyčky fetch / Promise.all.
Stav je v ~/.cache/rodokmen_slusne/ (Windows %LOCALAPPDATA%\\rodokmen_slusne), jen malé soubory JSON.
"""
import http.client, io, json, os, re, shutil, socket, subprocess, sys, tempfile, threading, time
from urllib.parse import urlsplit

DOTAZ, OBRAZEK = 2.0, 0.1            # výchozí rozestup v sekundách
LIMITY = {                           # konec názvu webu: (dotaz, obrázek)
    "archives.cz": (4.0, 0.1),       # ZA Opava (digi.archives.cz, images.archives.cz) – blokuje na 30 min
    "nominatim.openstreetmap.org": (1.1, 1.1),   # pravidla Nominatimu: nejvýš 1 dotaz za s
}
VOLNE = ("localhost", "127.0.0.1", "::1", "0.0.0.0", "netlify.app", "netlify.com", "github.com",
         "githubusercontent.com", "npmjs.org", "pypi.org", "pythonhosted.org")
STOPKY = (30 * 60, 2 * 3600, 8 * 3600)   # stopka po 1., 2. a 3. (i každém dalším) odmítnutí webu během OKNO
OKNO = 24 * 3600
BAN_TEXT = {"archives.cz": re.compile(rb"zablokov[a\xc3\xa1]n|byl[a ]+zablokov|blocked", re.I)}
OBRAZEK_RE = re.compile(r"\.(jpe?g|png|gif|webp|tiff?|jp2|bmp)(\?|$)|_files/|/tilegroup|/ximage/|zoomify|iipsrv|"
                        r"isrv8\.cgi|/iiif/|/tile|/image/|/thumb|//img\.", re.I)
STAV = os.environ.get("SLUSNE_STAV") or os.path.join(
    os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".cache"), "rodokmen_slusne")
KOD = 3
_slozka_ = []
_slozka_zamek = threading.Lock()


def _slozka():
    """Složka stavu. Když do ní nejde psát (sandbox Claude Code), zkusí dočasnou složku systému; když ani to,
    platí brzda jen uvnitř tohoto procesu (None)."""
    with _slozka_zamek:   # první dotaz z víc vláken najednou: zkouška jen jednou (na Windows by si soubory překážely)
        return _slozka_bez_zamku()


def _slozka_bez_zamku():
    if not _slozka_:
        for d in dict.fromkeys([STAV, os.path.join(tempfile.gettempdir(), "rodokmen_slusne")]):
            try:
                os.makedirs(d, exist_ok=True)
                t = os.path.join(d, f".zkouska_{os.getpid()}_{threading.get_ident()}")
                open(t, "w").close()
                os.remove(t)
                _slozka_.append(d)
                break
            except OSError:
                continue
        else:
            _slozka_.append(None)
            print(f"slusne: do {STAV} ani do dočasné složky nejde zapisovat – brzda platí jen pro tento proces, "
                  "ne pro ostatní. Spouštěj proto stahování po jednom.", file=sys.stderr)
    return _slozka_[0]


class Zastaveno(SystemExit):
    """Web je zastavený. Dědí ze SystemExit: smyčky `except Exception` / `except OSError` ji nespolknou."""


def _skupina(host):
    host = (host or "").lower().strip("[]").rstrip(".")
    if not host or any(host == v or host.endswith("." + v) for v in VOLNE):
        return None, None
    for suffix, lim in LIMITY.items():
        if host == suffix or host.endswith("." + suffix):
            return suffix, lim
    return host, (DOTAZ, OBRAZEK)


def je_obrazek(url):
    return bool(OBRAZEK_RE.search(url or ""))


class _Zamek:
    """Zámek souboru, společný všem procesům (flock, na Windows msvcrt)."""
    _vlakna = threading.Lock()

    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self._vlakna.acquire()
        self.f = None
        if self.path.startswith("pamet:"):
            return self
        try:
            self.f = open(self.path, "a+b")
        except OSError:
            self._vlakna.release()
            raise
        if os.name == "nt":
            import msvcrt
            while True:
                try:
                    self.f.seek(0)
                    msvcrt.locking(self.f.fileno(), msvcrt.LK_LOCK, 1)
                    break
                except OSError:
                    time.sleep(0.05)
        else:
            import fcntl
            fcntl.flock(self.f.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        try:
            if self.f and os.name == "nt":
                import msvcrt
                self.f.seek(0)
                msvcrt.locking(self.f.fileno(), msvcrt.LK_UNLCK, 1)
            if self.f:
                self.f.close()
        finally:
            self._vlakna.release()


def _cesta(skupina):
    d = _slozka()
    return os.path.join(d, re.sub(r"[^a-z0-9.-]", "_", skupina) + ".json") if d else "pamet:" + skupina


_pamet = {}


def _nacti(path):
    if path.startswith("pamet:"):
        return dict(_pamet.get(path, {}))
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _uloz(path, data):
    if path.startswith("pamet:"):
        _pamet[path] = dict(data)
        return
    tmp = f"{path}.{os.getpid()}.{threading.get_ident()}.tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f)
    os.replace(tmp, path)   # atomicky – souběžné procesy nikdy nenačtou rozepsaný soubor


def _cas(t):
    lt = time.localtime(t)
    return time.strftime("%H:%M", lt) if lt[:3] == time.localtime()[:3] else f"{lt.tm_mday}. {lt.tm_mon}. {lt.tm_hour}:{lt.tm_min:02d}"


def _hlaska(skupina, st):
    do, n = _cas(st["stop"]), st.get("poradi", 1)
    return (f"slusne: {skupina} je zastavený do {do} ({st.get('duvod', '')}"
            f"{f', {n}. odmítnutí za 24 h' if n > 1 else ''}). Archiv dává najevo, že ho zatěžujeme.\n"
            f"Nezkoušej to znovu dřív a nic neobcházej (jiný nástroj, prohlížeč, jiný postup). Do té doby dělej jinou práci.\n"
            f"Uživateli řekni, co se stalo. Stav: python3 -I tools/slusne.py stav")


_ohlaseno = set()


def _ohlas(skupina, st):
    if skupina not in _ohlaseno:   # z vláken stahování jen jednou
        _ohlaseno.add(skupina)
        print(_hlaska(skupina, st), file=sys.stderr)


def pockej(url_nebo_host, obrazek=None):
    """Před dotazem: počká na volný slot (rezervace pod zámkem, čeká se bez zámku). Zastavený web -> Zastaveno."""
    host = urlsplit(url_nebo_host).hostname if "://" in url_nebo_host else url_nebo_host
    skupina, lim = _skupina(host)
    if not skupina:
        return
    if obrazek is None:
        obrazek = je_obrazek(url_nebo_host)
    klic = "dalsi_obrazek" if obrazek else "dalsi_dotaz"
    path = _cesta(skupina)
    with _Zamek(path + ".lock"):
        st = _nacti(path)
        ted = time.time()
        if st.get("stop", 0) > ted:
            _ohlas(skupina, st)
            raise Zastaveno(KOD)
        slot = max(ted, st.get(klic, 0))
        st[klic] = slot + lim[1 if obrazek else 0]
        st.pop("stop", None)
        _uloz(path, st)
    if slot > ted:
        time.sleep(slot - ted)


def zastav(host, duvod):
    skupina, _ = _skupina(host)
    if not skupina:
        return
    path = _cesta(skupina)
    with _Zamek(path + ".lock"):
        st = _nacti(path)
        ted = time.time()
        if st.get("stop", 0) <= ted:   # už zastavený web = odpověď na souběžný dotaz, ne nové odmítnutí
            odm = [t for t in st.get("odmitnuti", []) if t > ted - OKNO] + [ted]
            st.update(stop=ted + STOPKY[min(len(odm), len(STOPKY)) - 1], duvod=duvod,
                      kdy=time.strftime("%Y-%m-%d %H:%M"), odmitnuti=odm, poradi=len(odm))
            _uloz(path, st)
    _ohlas(skupina, st)
    raise Zastaveno(KOD)


_selhani = {}


def _spojeni_selhalo(host, e):
    skupina, _ = _skupina(host)
    if not skupina:
        return
    _selhani[skupina] = _selhani.get(skupina, 0) + 1
    if _selhani[skupina] >= 3:
        zastav(host, f"3 nepovedená spojení za sebou ({type(e).__name__}) – archiv neodpovídá nebo nás zablokoval")


def kontroluj_odpoved(host, status, obrazek, telo=None):
    skupina, _ = _skupina(host)
    if not skupina:
        return
    _selhani.pop(skupina, None)
    if status in (429, 503) or (status == 403 and not obrazek):
        zastav(host, f"HTTP {status}")
    vzor = BAN_TEXT.get(skupina)
    if vzor and telo and vzor.search(telo):
        zastav(host, "stránka hlásí zablokování")


# --- brzda pro http.client: pokryje urllib, requests i vlastní skripty bez úprav --------------------------------
def _host(conn):
    return getattr(conn, "_tunnel_host", None) or conn.host


def _zapni():
    C = http.client.HTTPConnection
    if getattr(C, "_slusne", False):
        return
    put, get, connect = C.putrequest, C.getresponse, C.connect

    def putrequest(self, method, url, *a, **k):
        self._slusne_obr = je_obrazek(url)
        pockej(_host(self), self._slusne_obr)
        return put(self, method, url, *a, **k)

    def connect_(self):
        try:
            return connect(self)
        except (ConnectionRefusedError, ConnectionResetError, TimeoutError, socket.timeout) as e:
            _spojeni_selhalo(_host(self), e)
            raise

    def getresponse(self):
        r = get(self)
        host, obr = _host(self), getattr(self, "_slusne_obr", False)
        telo = None
        skupina, _ = _skupina(host)
        if skupina in BAN_TEXT and r.status == 200 and "html" in (r.getheader("Content-Type") or ""):
            telo = r.read()             # přečíst a vrátit zpět, aby volající dostal celé tělo
            r.fp, r.length, r.chunked, r.will_close = io.BytesIO(telo), len(telo), False, True
        kontroluj_odpoved(host, r.status, obr, telo)
        return r

    C.putrequest, C.getresponse, C.connect, C._slusne = putrequest, getresponse, connect_, True


# --- brzda pro podprocesy: curl, python a bash spuštěné z Pythonu (úpravu http.client nedědí) ---------------------
_primo = threading.local()   # volání skutečného curl a bash z této brzdy se nepřepisuje


def _prepis(argv):
    jm = os.path.basename(str(argv[0])).lower()
    jm = jm[:-4] if jm.endswith(".exe") else jm
    me = [sys.executable, "-I", "-X", "utf8", os.path.abspath(__file__)]
    if jm == "curl":
        return me + ["curl", *argv[1:]]
    if jm in ("bash", "sh") and len(argv) > 1:
        return me + ["bash", *argv[1:]]
    if re.fullmatch(r"python[\d.]*|pythonw[\d.]*|py", jm):
        i = 1
        while i < len(argv):
            a = str(argv[i])
            if a in ("-X", "-W"):
                i += 2
                continue
            if a == "-m":
                return argv
            if a in ("-c", "-") or not a.startswith("-"):
                break
            i += 1
        if i < len(argv) and os.path.basename(str(argv[i])) != "slusne.py":
            return argv[:i] + [os.path.abspath(__file__)] + argv[i:]
    return argv


def _hlidej_podprocesy():
    P = subprocess.Popen
    if getattr(P, "_slusne", False):
        return
    init = P.__init__

    def init_(self, args, *a, **k):
        if isinstance(args, (list, tuple)) and args and not k.get("shell") and not getattr(_primo, "ano", False):
            args = _prepis(list(args))
        init(self, args, *a, **k)

    P.__init__, P._slusne = init_, True


def _bez_prepisu(fce, *a, **k):
    _primo.ano = True
    try:
        return fce(*a, **k)
    finally:
        _primo.ano = False


_zapni()
_hlidej_podprocesy()


# --- obal pro skripty, curl a bash ---------------------------------------------------------------------------------
def _curl_umi_stderr(real):
    try:
        v = _bez_prepisu(subprocess.run, [real, "--version"], capture_output=True, text=True).stdout
        m = re.match(r"curl (\d+)\.(\d+)", v)
        return bool(m) and (int(m.group(1)), int(m.group(2))) >= (7, 63)
    except OSError:
        return False


def _bash_cesta():
    """bash k spuštění skriptu; na Windows ne C:\\Windows\\System32\\bash.exe (to je WSL, jiný systém), ale Git Bash."""
    if os.name != "nt":
        return shutil.which("bash") or "bash"
    for d in os.environ.get("PATH", "").split(os.pathsep):
        b = os.path.join(d, "bash.exe")
        if os.path.isfile(b) and "system32" not in b.lower() and "windowsapps" not in b.lower():
            return b
    git = shutil.which("git")
    if git:
        for b in (os.path.join(os.path.dirname(os.path.dirname(git)), "bin", "bash.exe"),
                  os.path.join(os.path.dirname(git), "bash.exe")):
            if os.path.isfile(b):
                return b
    return "bash"


def _curl(args):
    real = os.environ.get("SLUSNE_CURL") or shutil.which("curl")
    if not real:
        sys.exit("slusne: curl není nainstalovaný")
    urls = [a for a in args if re.match(r"https?://", a)]
    for u in urls:
        pockej(u)
    vlastni_w = any(a in ("-w", "--write-out") or a.startswith("--write-out=") for a in args) or not _curl_umi_stderr(real)
    extra = [] if vlastni_w else ["-w", "%{stderr}\n@@slusne %{http_code} %{url_effective}\n"]
    p = _bez_prepisu(subprocess.run, [real, *args, *extra], stderr=subprocess.PIPE)
    err = p.stderr.decode("utf-8", "replace").replace("\r\n", "\n")   # curl na Windows píše do stderr \r\n
    kody = re.findall(r"^@@slusne (\d+) (\S*)$", err, re.M)
    sys.stderr.write(re.sub(r"\n?@@slusne \d+ \S*\n", "", err))
    for kod, url in kody:
        kontroluj_odpoved(urlsplit(url).hostname, int(kod), je_obrazek(url))
    if p.returncode in (7, 28, 35, 56) and urls:   # nepřipojil se / timeout / spojení přerušeno
        _spojeni_selhalo(urlsplit(urls[0]).hostname, ConnectionError(f"curl kód {p.returncode}"))
    return p.returncode


def _posix(p):
    """Cesta pro Git Bash: C:\\Users\\x → /c/Users/x (mimo Windows beze změny)."""
    if os.name != "nt":
        return p
    p = p.replace("\\", "/")
    return "/" + p[0].lower() + p[2:] if re.match(r"[A-Za-z]:", p) else p


def _bash(args):
    shim = tempfile.mkdtemp(prefix="slusne_")
    try:
        me = os.path.abspath(__file__)
        with open(os.path.join(shim, "curl"), "w", encoding="utf-8", newline="\n") as f:
            py, me_ = sys.executable.replace("\\", "/"), me.replace("\\", "/")   # Git Bash: lomítka místo zpětných
            f.write(f'#!/bin/sh\nexec "{py}" -I -X utf8 "{me_}" curl "$@"\n')
        os.chmod(os.path.join(shim, "curl"), 0o755)
        # Git\bin\bash.exe (z PowerShellu jiný bash není) si PATH přestaví a skutečný curl by byl před náhradním.
        # BASH_ENV načte každý neinteraktivní bash (i vnořený `bash -c`) až potom, takže náhradní curl vrátí dopředu.
        with open(os.path.join(shim, "env.sh"), "w", encoding="utf-8", newline="\n") as f:
            f.write(f'PATH="{_posix(shim)}:$PATH"; export PATH\n')
        env = dict(os.environ, SLUSNE_CURL=os.environ.get("SLUSNE_CURL") or shutil.which("curl") or "",
                   PATH=shim + os.pathsep + os.environ.get("PATH", ""), BASH_ENV=_posix(os.path.join(shim, "env.sh")))
        return _bez_prepisu(subprocess.run, [_bash_cesta(), *args], env=env).returncode
    finally:
        shutil.rmtree(shim, ignore_errors=True)


def _skript(args):
    import runpy
    if args[0] in ("-", "-c"):   # kód ze vstupu (heredoc) nebo z argumentu
        kod = sys.stdin.read() if args[0] == "-" else (args[1] if len(args) > 1 else "")
        sys.argv = [args[0], *args[2 if args[0] == "-c" else 1:]]
        exec(compile(kod, "<stdin>" if args[0] == "-" else "<string>", "exec"), {"__name__": "__main__"})
        return 0
    if args[0] == "-m":
        sys.argv = args[1:]
        runpy.run_module(args[1], run_name="__main__", alter_sys=True)
    else:
        sys.argv = list(args)
        sys.path.insert(0, os.path.dirname(os.path.abspath(args[0])))
        runpy.run_path(args[0], run_name="__main__")
    return 0


def _stav():
    print(f"Limity: dotaz 1 za {DOTAZ:g} s, obrázek 1 za {OBRAZEK:g} s; zvlášť: " +
          ", ".join(f"{k} {v[0]:g}/{v[1]:g} s" for k, v in LIMITY.items()))
    d = _slozka()
    print("Stav:", d or "jen v paměti procesu (do složky nejde zapisovat)")
    nic, ted = True, time.time()
    for f in sorted(os.listdir(d)) if d else []:
        if f.endswith(".json"):
            st = _nacti(os.path.join(d, f))
            odm = [t for t in st.get("odmitnuti", []) if t > ted - OKNO]
            if st.get("stop", 0) > ted:
                nic = False
                print(f"  ZASTAVENO {f[:-5]} do {_cas(st['stop'])} – {st.get('duvod', '')} (od {st.get('kdy', '?')}, "
                      f"{st.get('poradi', 1)}. odmítnutí za 24 h)")
            elif odm:
                dalsi = STOPKY[min(len(odm) + 1, len(STOPKY)) - 1]
                delka = f"{dalsi // 60} min" if dalsi < 3600 else f"{dalsi // 3600} h"
                print(f"  {f[:-5]}: odmítnutí za 24 h {len(odm)} (poslední {_cas(odm[-1])}), další stopka by trvala {delka}")
    if nic:
        print("  žádný web není zastavený")


def _odblokuj(web=None):
    d = _slozka()
    for f in os.listdir(d) if d else []:
        if f.endswith(".json") and (not web or f[:-5] in (web, _skupina(web)[0])):
            path = os.path.join(d, f)
            with _Zamek(path + ".lock"):
                st = _nacti(path)
                if st.pop("stop", None):
                    print("odblokováno:", f[:-5])
                    st["odmitnuti"] = st.get("odmitnuti", [])[:-1]   # byla to naše chyba – do prodlužování se nepočítá
                _uloz(path, st)


def main(argv):
    for s in (sys.stdout, sys.stderr):   # hlášky česky i na Windows bez -X utf8 (např. z curl() v ahmp_search.sh)
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")
    if not argv and not sys.stdin.isatty():   # slusne.py <<'EOF' … EOF
        argv = ["-"]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "--stav":   # tvar ze starší brzdy scripts/slusne.py
        cmd = "stav"
    if cmd == "stav":
        return _stav()
    if cmd == "odblokuj":
        return _odblokuj(rest[0] if rest else None)
    if cmd == "curl":
        return _curl(rest)
    if cmd in ("bash", "sh"):
        return _bash(rest)
    if re.match(r"(python3?|py)(\.exe)?$", os.path.basename(cmd)):   # „slusne.py python3 x.py“ = „slusne.py x.py“
        cmd, rest = rest[0], rest[1:]
        if cmd == "-I" and rest:
            cmd, rest = rest[0], rest[1:]
    return _skript([cmd, *rest])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
