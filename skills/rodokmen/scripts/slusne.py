#!/usr/bin/env python3
"""Slušný přístup k archivům: společný limit rychlosti dotazů pro nástroje skillu rodokmen.

Použití (z kořene projektu; na Windows `python -I -X utf8` místo `python3 -I`):
  python3 -I scripts/slusne.py tools/<nástroj>.py …       nástroj nebo vlastní skript v Pythonu
  python3 -I scripts/slusne.py - <<'EOF' … EOF            kód v Pythonu ze standardního vstupu (heredoc)
  python3 -I scripts/slusne.py -c "kód" …
  python3 -I scripts/slusne.py curl …                     curl se stejným limitem (místo curl, wget, Invoke-WebRequest)
  python3 -I scripts/slusne.py bash tools/<skript>.sh …   shellový skript – jeho curl jde přes limit
  python3 -I scripts/slusne.py --stav                     které weby jsou právě zablokované

Pravidla (pro každý web zvlášť a společně pro všechny procesy na počítači):
- dotazy (hledání, API, stránky): nejvýš 1 za 2 s; dlaždice a obrázky (podle adresy): nejvýš 10 za s.
  Omezuje se frekvence, ne souběh – bany způsobují série rychlých dotazů, ne několik souběžných stahování.
- Po HTTP 429 nebo 503 (a po 403 na dotaz) je web 30 minut zablokovaný pro všechny procesy. Nástroj hned
  skončí s kódem 75 a nic dalšího nezkouší.
Jak: před spuštěním upraví http.client (putrequest, getresponse), takže pokryje urllib i requests bez úprav
v tools/. Python a curl spouštěné z nástroje jdou taky přes wrapper, bash dostane curl přes BASH_ENV a PATH.
Stav je v ~/.cache/rodokmen/slusne.json se zámkem slusne.lock (jinou složku určí proměnná SLUSNE_STAV).
"""
import hashlib, http.client, json, os, re, runpy, shutil, subprocess, sys, tempfile, threading, time, urllib.parse

if os.name == "nt":
    import msvcrt
else:
    import fcntl

DOTAZ, OBRAZEK = "dotaz", "obrazek"
ROZESTUP = {DOTAZ: 2.0, OBRAZEK: 0.1}   # s mezi dvěma požadavky na jeden web
BLOK_S = 30 * 60
KOD_BLOK = 75
SLUSNE = os.path.abspath(__file__)
STAV_DIR = os.environ.get("SLUSNE_STAV") or os.path.join(os.path.expanduser("~"), ".cache", "rodokmen")
STAV = os.path.join(STAV_DIR, "slusne.json")
# Dlaždice a obrázky podle adresy: přípona, Zoomify/DeepZoom/IIIF, obrázkové servery archivů (Třeboň isrv, Porta fontium iipsrv).
OBR = re.compile(r"\.(jpe?g|png|gif|webp|tiff?|jp2|bmp|dzi|pdf)(?=$|[?&#/])|/TileGroup\d+/|_files/\d+/|iipsrv|isrv\d*\.cgi"
                 r"|[?&]IIIF=|/iiif/|/deepzoom|/tiles?/|\$dist", re.I)
# Volby curl, které berou hodnotu (aby se hodnota nepočítala jako adresa).
CURL_KRATKE = set("AbcCdDeEFHKmoPQrtTuUwxXyYz")
CURL_DLOUHE = {"--output", "--dump-header", "--cookie", "--cookie-jar", "--continue-at", "--data", "--data-ascii",
               "--data-binary", "--data-raw", "--data-urlencode", "--referer", "--cert", "--form", "--form-string",
               "--header", "--config", "--max-time", "--range", "--upload-file", "--user", "--proxy-user", "--write-out",
               "--proxy", "--request", "--user-agent", "--connect-timeout", "--retry", "--retry-delay", "--retry-max-time",
               "--limit-rate", "--resolve", "--connect-to", "--cacert", "--capath", "--key", "--interface", "--max-filesize",
               "--output-dir", "--proxy-header", "--json", "--url-query", "--variable", "--speed-limit", "--speed-time",
               "--time-cond", "--quote", "--ftp-port", "--telnet-option"}


def druh(host, url):
    if host.split(".")[0] in ("img", "images", "iiif", "tiles") or OBR.search(url):
        return OBRAZEK
    return DOTAZ


# ---------- sdílený stav se zámkem (Windows msvcrt, jinde flock) ----------
_vlakna = threading.Lock()


class _Zamek:
    def __enter__(self):
        _vlakna.acquire()
        try:
            os.makedirs(STAV_DIR, exist_ok=True)
            self.f = open(os.path.join(STAV_DIR, "slusne.lock"), "a+b")
            konec = time.time() + 60
            while True:
                try:
                    if os.name == "nt":
                        self.f.seek(0)
                        msvcrt.locking(self.f.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        fcntl.flock(self.f.fileno(), fcntl.LOCK_EX)
                    return self
                except OSError:
                    if time.time() > konec:
                        raise
                    time.sleep(0.01)
        except BaseException:
            _vlakna.release()
            raise

    def __exit__(self, *_):
        try:
            if os.name == "nt":
                self.f.seek(0)
                msvcrt.locking(self.f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(self.f.fileno(), fcntl.LOCK_UN)
            self.f.close()
        finally:
            _vlakna.release()


def _nacti():
    try:
        with open(STAV, encoding="utf-8") as f:
            st = json.load(f)
        return st if isinstance(st, dict) else {}
    except (OSError, ValueError):
        return {}


def _uloz(st):
    ted = time.time()
    st["dalsi"] = {k: t for k, t in st.get("dalsi", {}).items() if t > ted - 60}
    st["bloky"] = {h: b for h, b in st.get("bloky", {}).items() if b.get("do", 0) > ted}
    with open(STAV, "w", encoding="utf-8", newline="\n") as f:
        json.dump(st, f, ensure_ascii=False)


def _hm(t):
    return time.strftime("%H:%M", time.localtime(t))


def _konec(zprava):
    """Ukončí celý proces hned (i z vlákna stahování) – žádné další pokusy."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.flush()
        except Exception:
            pass
    try:
        sys.stderr.write(f"\nslusne.py: {zprava}\n")
        sys.stderr.flush()
    except Exception:
        pass
    os._exit(KOD_BLOK)


def _blok(st, host):
    b = st.get("bloky", {}).get(host)
    if b and b.get("do", 0) > time.time():
        return (f"{host} je zablokovaný do {_hm(b['do'])} ({b.get('duvod', '?')} v {_hm(b.get('kdy', 0))}). "
                "Nic na něj teď neposílej a nezkoušej to znovu – pokračuj jinou prací a řekni to uživateli.")
    return None


def pockej(host, d):
    """Zkontroluje blok webu a rezervuje si další volný čas pro požadavek; do té doby spí."""
    host = host.lower()
    with _Zamek():
        st = _nacti()
        ted = time.time()
        zprava = _blok(st, host)
        if not zprava:
            klic = f"{host} {d}"
            t = max(ted, st.get("dalsi", {}).get(klic, 0))
            st.setdefault("dalsi", {})[klic] = t + ROZESTUP[d]
            _uloz(st)
    if zprava:
        _konec(zprava)
    if t > ted:
        time.sleep(t - ted)
        with _Zamek():   # mezitím mohl jiný proces dostat 429
            zprava = _blok(_nacti(), host)
        if zprava:
            _konec(zprava)


def zablokuj(hosts, duvod):
    ted = time.time()
    with _Zamek():
        st = _nacti()
        for h in hosts:
            st.setdefault("bloky", {})[h.lower()] = {"do": ted + BLOK_S, "kdy": ted, "duvod": duvod}
        _uloz(st)
    _konec(f"{', '.join(hosts)} vrátil {duvod} – server dává najevo, že ho zatěžujeme. Web je zablokovaný pro všechny "
           f"nástroje do {_hm(ted + BLOK_S)} (30 min). Nic dalšího na něj neposílej a nezkoušej to znovu – pokračuj "
           "jinou prací a řekni to uživateli.")


def problem(status, d):
    return status in (429, 503) or (status == 403 and d == DOTAZ)


# ---------- Python: http.client a podprocesy ----------
def _host_spojeni(conn):
    return (getattr(conn, "_tunnel_host", None) or conn.host or "").lower()


def nainstaluj():
    put0, get0 = http.client.HTTPConnection.putrequest, http.client.HTTPConnection.getresponse

    def putrequest(self, method, url, *a, **kw):
        host = _host_spojeni(self)
        if "://" in url:   # absolutní adresa (přes proxy)
            host = (urllib.parse.urlsplit(url).hostname or host).lower()
        self._slusne = (host, druh(host, url))
        pockej(*self._slusne)
        return put0(self, method, url, *a, **kw)

    def getresponse(self, *a, **kw):
        r = get0(self, *a, **kw)
        host, d = getattr(self, "_slusne", (_host_spojeni(self), DOTAZ))
        if problem(r.status, d):
            zablokuj([host], f"HTTP {r.status}")
        return r

    http.client.HTTPConnection.putrequest = putrequest
    http.client.HTTPConnection.getresponse = getresponse


def _jmeno(p):
    n = os.path.basename(str(p)).lower()
    return n[:-4] if n.endswith(".exe") else n


def _prepis(argv):
    """Podproces python … / curl … pustí taky přes wrapper (podprocesy úpravu http.client nedědí)."""
    jm = _jmeno(argv[0])
    if jm == "curl":
        return [sys.executable, "-I", "-X", "utf8", SLUSNE, "curl", *argv[1:]]
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
            return argv[:i] + [SLUSNE] + argv[i:]
    return argv


def _hlidej_podprocesy():
    init0 = subprocess.Popen.__init__

    def init(self, args, *a, **kw):
        if isinstance(args, (list, tuple)) and args and not kw.get("shell"):
            args = _prepis(list(args))
        if kw.get("env") is not None:
            kw["env"] = {**kw["env"], **{k: os.environ[k] for k in ("BASH_ENV", "SLUSNE_SHIM") if k in os.environ}}
        init0(self, args, *a, **kw)

    subprocess.Popen.__init__ = init


# ---------- shell: curl na začátku PATH (BASH_ENV) ----------
def _posix(p):
    p = os.path.abspath(p)
    if os.name == "nt":
        p = p.replace("\\", "/")
        if re.match(r"[A-Za-z]:", p):
            p = "/" + p[0].lower() + p[2:]
    return p


def _priprav_shim():
    d = os.path.join(STAV_DIR, "shim-" + hashlib.sha1(f"{sys.executable}|{SLUSNE}".encode()).hexdigest()[:10])
    q = lambda s: "'" + s.replace("'", "'\\''") + "'"
    soubory = {"curl": f'#!/bin/sh\nexec {q(_posix(sys.executable))} -I -X utf8 {q(_posix(SLUSNE))} curl "$@"\n',
               "env.sh": f'PATH={q(_posix(d))}:"$PATH"; export PATH\n'}
    os.makedirs(d, exist_ok=True)
    for jm, obsah in soubory.items():
        p = os.path.join(d, jm)
        try:
            with open(p, encoding="utf-8") as f:
                if f.read() == obsah:
                    continue
        except OSError:
            pass
        tmp = f"{p}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(obsah)
        os.chmod(tmp, 0o755)
        try:
            os.replace(tmp, p)
        except OSError:   # jiný proces ho právě zapsal
            os.remove(tmp)
    os.environ["SLUSNE_SHIM"] = d
    os.environ["BASH_ENV"] = _posix(os.path.join(d, "env.sh"))   # bash ho načte i po tom, co si PATH přestaví (Git Bash)
    os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")


def _bash():
    b = shutil.which("bash")
    if os.name != "nt":
        return b or "bash"
    if b and "system32" not in b.lower() and "windowsapps" not in b.lower():   # ne WSL
        return b
    kandidati = []
    g = shutil.which("git")   # …\Git\cmd\git.exe nebo …\Git\mingw64\bin\git.exe
    if g:
        d = os.path.dirname(g)
        for _ in range(3):
            d = os.path.dirname(d)
            kandidati.append(os.path.join(d, "bin", "bash.exe"))
    for env in ("ProgramFiles", "ProgramW6432", "LOCALAPPDATA"):
        if os.environ.get(env):
            kandidati.append(os.path.join(os.environ[env], "Git", "bin", "bash.exe"))
            kandidati.append(os.path.join(os.environ[env], "Programs", "Git", "bin", "bash.exe"))
    for k in kandidati:
        if os.path.isfile(k):
            return k
    sys.exit("slusne.py: nenašel jsem Git Bash (bash.exe).")


# ---------- curl ----------
def curl_cile(args):
    """Adresy, na které curl půjde (bez hodnot voleb jako -o soubor nebo -e referer)."""
    cile, i = [], 0
    while i < len(args):
        a = args[i]
        if a == "--url":
            cile += args[i + 1:i + 2]
            i += 1
        elif a.startswith("--"):
            if "=" not in a and a in CURL_DLOUHE:
                i += 1
        elif a.startswith("-") and len(a) > 1:
            for j, ch in enumerate(a[1:]):
                if ch in CURL_KRATKE:
                    if j == len(a) - 2:   # hodnota je další slovo
                        i += 1
                    break
        else:
            cile.append(a)
        i += 1
    return cile


def _najdi_curl():
    moje = os.path.normcase(os.path.abspath(STAV_DIR))
    cesty = [p for p in os.environ.get("PATH", "").split(os.pathsep)
             if p and not os.path.normcase(os.path.abspath(p)).startswith(moje)]
    c = shutil.which("curl", path=os.pathsep.join(cesty))
    if not c:
        sys.exit("slusne.py: curl nenalezen.")
    return c


def _curl(args):
    curl = _najdi_curl()
    cile = []
    for u in curl_cile(args):
        p = urllib.parse.urlsplit(u if "://" in u else "http://" + u)
        if p.hostname:
            cile.append((p.hostname.lower(), druh(p.hostname, p.path + "?" + p.query)))
    for host, d in cile:
        pockej(host, d)
    hlavicky, navic = None, []
    if cile and not any(a in ("-D", "--dump-header") or a.startswith("--dump-header=") for a in args):
        fd, hlavicky = tempfile.mkstemp(prefix="slusne_", suffix=".txt")
        os.close(fd)
        navic = ["-D", hlavicky]
    try:
        rc = subprocess.call([curl, *navic, *args])
        if hlavicky:
            with open(hlavicky, encoding="latin-1") as f:
                kody = [int(k) for k in re.findall(r"^HTTP/\S+\s+(\d{3})", f.read(), re.M)]
            spatne = [k for k in kody if any(problem(k, d) for _, d in cile)]
            if spatne:
                zablokuj(sorted({h for h, _ in cile}), f"HTTP {spatne[0]}")
        return rc
    finally:
        if hlavicky:
            try:
                os.remove(hlavicky)
            except OSError:
                pass


def _stav():
    with _Zamek():
        st = _nacti()
    bloky = {h: b for h, b in st.get("bloky", {}).items() if b.get("do", 0) > time.time()}
    if not bloky:
        print("Žádný web není zablokovaný.")
    for h, b in sorted(bloky.items()):
        print(f"{h}: zablokovaný do {_hm(b['do'])} ({b.get('duvod', '?')} v {_hm(b.get('kdy', 0))})")
    print(f"Stav: {STAV}")


def main():
    a = sys.argv[1:]
    if not a and not sys.stdin.isatty():   # python slusne.py <<EOF … EOF
        a = ["-"]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if a else 2
    if a[0] == "--stav":
        _stav()
        return 0
    if a[0] == "curl":
        return _curl(a[1:])
    if _jmeno(a[0]) in ("bash", "sh"):
        _priprav_shim()
        return subprocess.call([_bash(), *a[1:]])
    nainstaluj()
    _priprav_shim()
    _hlidej_podprocesy()
    if a[0] in ("-c", "-"):
        kod = a[1] if a[0] == "-c" else sys.stdin.read()
        sys.argv = [a[0], *a[2 if a[0] == "-c" else 1:]]
        exec(compile(kod, "<string>" if a[0] == "-c" else "<stdin>", "exec"), {"__name__": "__main__"})
        return 0
    sys.argv = a
    runpy.run_path(a[0], run_name="__main__")
    return 0


if __name__ == "__main__":
    sys.exit(main())
