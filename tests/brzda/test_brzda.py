"""Regresní test brzdy tools/slusne.py s lokálními servery na 127.0.0.2 a 127.0.0.3 (localhost brzda nebrzdí).

Z kořene repozitáře, přes obal (test sám spouští curl), testovaná brzda je argument:
  python3 -I skills/rodokmen/tools/slusne.py tests/brzda/test_brzda.py skills/rodokmen/tools/slusne.py
  (Windows: python -I -X utf8 …; pusť z Git Bashe i z PowerShellu – bash z PowerShellu je Git\\bin\\bash.exe,
  který si přestaví PATH)
  ROZSIRENI=0 … – jen základní testy (bez heredocu, prodlužování stopky, podprocesů a opakovaného souběhu vláken)
Komunikuje jen s lokálními servery; stav brzdy má každý test ve vlastní dočasné složce (SLUSNE_STAV).
Ověřeno na Windows 11 (Python 3.13, Git Bash, PowerShell 7) 2. 11. 2026; na macOS/Linuxu nezkoušeno
(127.0.0.2 na macOS potřebuje alias na lo0).
"""
import os, subprocess, sys, tempfile, threading, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

SL = os.path.abspath(sys.argv[1])
TOOLS = os.path.dirname(SL)
PY = [sys.executable, "-I", "-X", "utf8"]
KOD = 3
LOG = []
BLOKOVANA_STRANKA = "<html><body>Váš přístup byl zablokován.</body></html>".encode("utf-8")


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        LOG.append((time.time(), self.server.server_address[0], self.path))
        p = self.path.split("?")[0]
        kod = {"/limit": 429, "/busy": 503, "/forbidden": 403, "/t/zakazana.jpg": 403}.get(p, 200)
        telo = BLOKOVANA_STRANKA if p == "/blocked" else b"ok"
        self.send_response(kod)
        self.send_header("Content-Type", "text/html; charset=utf-8" if p == "/blocked" else "text/plain")
        self.send_header("Content-Length", str(len(telo)))
        self.end_headers()
        self.wfile.write(telo)

    def log_message(self, *a):
        pass


def server(adr):
    s = ThreadingHTTPServer((adr, 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s.server_address[1]


PA, PB = server("127.0.0.2"), server("127.0.0.3")
A, B = f"http://127.0.0.2:{PA}", f"http://127.0.0.3:{PB}"
tmp = tempfile.mkdtemp(prefix="slusne060_")


def soubor(jmeno, text):
    p = os.path.join(tmp, jmeno)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return p


KLIENT = soubor("klient.py",
                "import sys, urllib.request, urllib.error\n"
                "for u in sys.argv[1:]:\n"
                "    try:\n        r = urllib.request.urlopen(u, timeout=10); st = r.status; r.read()\n"
                "    except urllib.error.HTTPError as e:\n        st = e.code\n"
                "    except urllib.error.URLError as e:\n        st = 'spojení selhalo'\n"
                "    print(u.split('/', 3)[-1], st, flush=True)\n")
# jako nástroj ve tools/: brzdu si načte sám (řádek z 0.6.0), spouští se bez obalu
NASTROJ = soubor("nastroj.py",
                 f"import os as _os, sys as _sys; _sys.path.insert(0, {TOOLS!r}); import slusne\n"
                 "import sys, urllib.request\nfor u in sys.argv[1:]:\n    urllib.request.urlopen(u, timeout=10).read()\n")
VLAKNA = soubor("vlakna.py",
                "import sys, urllib.request, concurrent.futures as cf\n"
                "with cf.ThreadPoolExecutor(8) as ex:\n"
                "    list(ex.map(lambda u: urllib.request.urlopen(u, timeout=10).read(), sys.argv[1:]))\n")
OPAVA = soubor("opava.py",   # digi.archives.cz přesměrovaný na lokální server (jen v tomto procesu)
               "import socket, sys, urllib.request\n_g = socket.getaddrinfo\n"
               "socket.getaddrinfo = lambda h, *a, **k: _g('127.0.0.2' if h.endswith('archives.cz') else h, *a, **k)\n"
               "for u in sys.argv[1:]:\n    print(urllib.request.urlopen(u, timeout=10).status, flush=True)\n")
vysledky = []


def stav(jmeno):
    return {**os.environ, "SLUSNE_STAV": os.path.join(tmp, jmeno)}


def spust(args, env, **kw):
    return subprocess.run(PY + [SL] + args, env=env, capture_output=True, text=True, encoding="utf-8", **kw)


def zaznamy(od, cesta=None):
    return [(t, h, p) for t, h, p in LOG if t >= od and (cesta is None or p.startswith(cesta))]


def rozestupy(z):
    return [round(b[0] - a[0], 2) for a, b in zip(z, z[1:])]


def nejvic_za_sekundu(z):
    """Nejvíc požadavků v libovolném okně 1 s (při 10 za s a kolísání plánovače čekáme 10–11)."""
    t = [x[0] for x in z]
    return max(sum(1 for y in t if x <= y < x + 1.0) for x in t) if t else 0


def check(nazev, ok, detail, info=False):
    if not info:
        vysledky.append(ok)
    znacka = ("OK " if ok else "CHYBA") if not info else ("ano" if ok else "NE ")
    print(f"[{znacka}] {nazev}: {detail}", flush=True)


def posledni(text):
    radky = [r for r in text.strip().splitlines() if r.strip()]
    return radky[-1][:110] if radky else ""


# 1) dotazy na stejný web
e = stav("s1"); t0 = time.time()
r = spust([KLIENT, A + "/api?q=1", A + "/api?q=2", A + "/api?q=3"], e)
z = rozestupy(zaznamy(t0, "/api"))
check("dotazy na stejný web", r.returncode == 0 and len(z) == 2 and all(1.9 <= x <= 2.4 for x in z), f"rozestupy {z} s")

# 2) dlaždice
t0 = time.time()
r = spust([KLIENT] + [A + f"/t/{i}_0.jpg" for i in range(10)], e)
z = zaznamy(t0, "/t/")
celkem = round(z[-1][0] - z[0][0], 2) if z else -1
check("10 dlaždic", r.returncode == 0 and len(z) == 10 and 0.8 <= celkem <= 1.6, f"9 rozestupů za {celkem} s")

# 3) zámek msvcrt: dva procesy a pak zátěž (6 procesů × 20 dlaždic + 4 procesy × 2 dotazy, 8 vláken v jednom procesu)
e = stav("s3"); t0 = time.time()
p = [subprocess.Popen(PY + [SL, KLIENT, A + f"/api?p={i}a", A + f"/api?p={i}b"], env=e, stdout=subprocess.DEVNULL)
     for i in (1, 2)]
[x.wait() for x in p]
z = rozestupy(zaznamy(t0, "/api"))
check("dva procesy současně (zámek msvcrt)", len(z) == 3 and all(x >= 1.9 for x in z), f"rozestupy všech 4 dotazů {z} s")

e = stav("s3b"); t0 = time.time()
procs = [subprocess.Popen(PY + [SL, KLIENT] + [A + f"/t/{i}_{j}.jpg" for j in range(20)], env=e,
                          stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding="utf-8") for i in range(6)]
procs += [subprocess.Popen(PY + [SL, KLIENT, A + f"/api?z={i}a", A + f"/api?z={i}b"], env=e,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding="utf-8") for i in range(4)]
chyby = [(pr.wait(), pr.stderr.read()) for pr in procs]
spatne = [(k, err.strip().splitlines()[-1][:120]) for k, err in chyby if k != 0 or "Error" in err]
dl, dt = zaznamy(t0, "/t/"), zaznamy(t0, "/api?z=")
rd, rq = rozestupy(dl), rozestupy(dt)
check("zátěž: 10 procesů najednou (120 dlaždic + 8 dotazů)",
      not spatne and len(dl) == 120 and len(dt) == 8 and nejvic_za_sekundu(dl) <= 12 and min(rq) >= 1.9,
      f"{len(dl)} dlaždic za {round(dl[-1][0] - dl[0][0], 1)} s, nejvíc {nejvic_za_sekundu(dl)} v jedné sekundě "
      f"(rozestup {min(rd)}–{max(rd)} s), dotazy nejméně {min(rq)} s od sebe; chyby procesů: {spatne or 'žádné'}")
e = stav("s3c"); t0 = time.time()
r = spust([VLAKNA] + [A + f"/t/v{i}.jpg" for i in range(40)], e)
dl = zaznamy(t0, "/t/v")
check("8 vláken v jednom procesu, první dotaz z vláken (nová složka stavu)",
      r.returncode == 0 and len(dl) == 40 and nejvic_za_sekundu(dl) <= 12 and "nejde zapisovat" not in r.stderr,
      f"40 dlaždic za {round(dl[-1][0] - dl[0][0], 1)} s, nejvíc {nejvic_za_sekundu(dl)} za s; {posledni(r.stderr) or 'bez hlášek'}")

# 4) 429: konec, blok pro jiné procesy i curl; jiný web ne; stav a odblokuj
e = stav("s4"); t0 = time.time()
r = spust([KLIENT, A + "/limit", A + "/api?po=limitu"], e)
check("HTTP 429 ukončí nástroj", r.returncode == KOD and not zaznamy(t0, "/api"),
      f"kód {r.returncode}; {posledni(r.stderr.splitlines()[0] if r.stderr else '')}")
t1 = time.time()
r2 = spust([KLIENT, A + "/api?jiny=proces"], e)
r3 = spust(["curl", "-s", A + "/api?curl=1"], e)
r3b = subprocess.run(PY + [NASTROJ, A + "/api?nastroj=1"], env=e, capture_output=True, text=True, encoding="utf-8")
check("blok platí pro jiný proces, curl i nástroj s import slusne",
      (r2.returncode, r3.returncode, r3b.returncode) == (KOD, KOD, KOD) and not zaznamy(t1),
      f"kódy {r2.returncode}/{r3.returncode}/{r3b.returncode}, na server nedošlo nic")
r4 = spust([KLIENT, B + "/api?jiny=web"], e)
check("jiný web (127.0.0.3) zastavený není", r4.returncode == 0 and "200" in r4.stdout, r4.stdout.strip())
r5 = spust(["stav"], e)
check("slusne.py stav", "ZASTAVENO 127.0.0.2" in r5.stdout, [x for x in r5.stdout.splitlines() if "ZASTAV" in x][0][:100])
r6 = spust(["odblokuj", "127.0.0.2"], e)
r7 = spust([KLIENT, A + "/api?po=odblokovani"], e)
check("slusne.py odblokuj", r7.returncode == 0, f"{r6.stdout.strip()} → další dotaz kód {r7.returncode}")

# 5) 503 a 403
e = stav("s5")
r = spust([KLIENT, A + "/busy"], e)
check("HTTP 503", r.returncode == KOD, f"kód {r.returncode}")
e = stav("s6")
r = spust([KLIENT, A + "/t/zakazana.jpg", A + "/api?po=403obrazku"], e)
r2 = spust([KLIENT, B + "/forbidden"], e)
check("403 na obrázek nezastaví, na dotaz ano", r.returncode == 0 and r2.returncode == KOD,
      f"obrázek → kód {r.returncode}, dotaz → kód {r2.returncode}")

# 6) nástroj s „import slusne“ bez obalu
e = stav("s6b"); t0 = time.time()
r = subprocess.run([sys.executable, "-I", "-X", "utf8", NASTROJ, A + "/api?n=1", A + "/api?n=2"], env=e,
                   capture_output=True, text=True, encoding="utf-8")
z = rozestupy(zaznamy(t0, "/api?n="))
check("nástroj s import slusne brzdí i bez obalu", r.returncode == 0 and z and z[0] >= 1.9, f"rozestup {z} s")

# 7) bash skript: curl uvnitř (i ve vnořeném bash -c) má jít přes brzdu
e = stav("s7")
sh = soubor("test.sh", 'curl -s "$1/api?sh=1" -o /dev/null\ncurl -s "$1/api?sh=2" -o /dev/null\n'
                       'bash -c "curl -s \\"$1/api?sh=3\\" -o /dev/null"\necho "curl: $(command -v curl)"\n')
t0 = time.time()
r = spust(["bash", sh, A], e)
z = rozestupy(zaznamy(t0, "/api?sh="))
check(f"slusne.py bash: curl ve skriptu i v bash -c (PATH z {os.environ.get('KONTEXT', '?')})",
      r.returncode == 0 and len(z) == 2 and all(x >= 1.9 for x in z), f"rozestupy {z} s, {r.stdout.strip()[-70:]}")
e = stav("s7b")
r = spust(["curl", "-s", "-o", os.devnull, A + "/limit"], e)
check("slusne.py curl a 429", r.returncode == KOD, f"kód {r.returncode}, stderr {r.stderr.strip()[:70]!r}")
e = stav("s7c"); sh2 = soubor("limit.sh", 'curl -s -o /dev/null "$1/limit"\ncurl -s -o /dev/null "$1/api?po=limitu"\n')
t0 = time.time()
r = spust(["bash", sh2, A], e)
check("slusne.py bash: 429 z curl ve skriptu zastaví další dotazy", not zaznamy(t0, "/api?po="),
      f"kód {r.returncode}, druhý curl {'NEodešel' if not zaznamy(t0, '/api?po=') else 'ODEŠEL'}")

# 8) stránka „zablokováno“ s kódem 200 (ZA Opava) a limit 4 s pro archives.cz
e = stav("s8"); t0 = time.time()
r = spust([OPAVA, f"http://digi.archives.cz:{PA}/api?o=1", f"http://digi.archives.cz:{PA}/api?o=2",
           f"http://digi.archives.cz:{PA}/blocked", f"http://digi.archives.cz:{PA}/api?o=po"], e)
z = rozestupy(zaznamy(t0, "/"))
check("archives.cz: limit 4 s a stránka „zablokováno“ (200)", r.returncode == KOD and len(z) == 2 and all(x >= 3.9 for x in z),
      f"kód {r.returncode}, rozestupy {z} s, po stránce „zablokováno“ už nic")

# 9) 3 nepovedená spojení za sebou (zavřený port na 127.0.0.4)
e = stav("s9"); t0 = time.time()
r = spust([KLIENT] + [f"http://127.0.0.4:9/api?c={i}" for i in range(4)], e)
check("3 nepovedená spojení zastaví web", r.returncode == KOD and "3 nepovedená spojení" in r.stderr,
      f"kód {r.returncode} za {round(time.time() - t0, 1)} s")

# 10) složka stavu, kam nejde zapisovat → dočasná složka
e = {**os.environ, "SLUSNE_STAV": os.path.join(KLIENT, "nelze")}
r = spust(["stav"], e)
check("nezapisovatelná složka stavu → dočasná složka", r.returncode == 0 and "rodokmen_slusne" in r.stdout,
      [x for x in r.stdout.splitlines() if x.startswith("Stav")][0][:110])

# 11) podprocesy z Pythonu: 0.6.0 zatím ne (převezme z PR #53), místní úprava ano
ROZ = os.environ.get("ROZSIRENI", "1") != "0"
e = stav("s11"); skr = soubor("podprocesy.py",
    "import subprocess, sys\n"
    f"subprocess.run(['curl', '-s', '-o', {os.devnull!r}, '{A}/api?sub=1'])\n"
    f"subprocess.run(['curl', '-s', '-o', {os.devnull!r}, '{A}/api?sub=2'])\n"
    f"subprocess.run([sys.executable, '-I', {KLIENT!r}, '{A}/api?sub=3'])\n"
    f"subprocess.run(['bash', '-c', 'curl -s -o /dev/null {A}/api?sub=4'])\n")
t0 = time.time()
spust([skr], e)
z = rozestupy(zaznamy(t0, "/api?sub="))
check("podprocesy curl, python a bash z Pythonu brzděné", len(z) == 3 and all(x >= 1.8 for x in z),
      f"rozestupy {z} s (sloty po 2 s, start procesu curl kolísá o ~0,1 s)", info=not ROZ)

if ROZ:
    import json
    # 12) kód ze vstupu a -c
    e = stav("s12"); t0 = time.time()
    r = spust(["-"], e, input=f"import urllib.request\nfor i in range(2): urllib.request.urlopen('{A}/api?stdin=%d' % i).read()\n")
    r2 = spust(["-c", f"import urllib.request; urllib.request.urlopen('{A}/api?c=1').read()"], e)
    z = rozestupy(zaznamy(t0, "/api?"))
    check("slusne.py - (heredoc) a -c", r.returncode == 0 and r2.returncode == 0 and len(z) == 2 and all(x >= 1.9 for x in z),
          f"rozestupy {z} s {posledni(r.stderr + r2.stderr)}")

    # 13) prodlužování stopky: 30 min → 2 h → 8 h (uplynutí stopky nasimulované úpravou souboru stavu)
    e = stav("s13"); delky = []
    soubor_stavu = os.path.join(tmp, "s13", "127.0.0.2.json")
    for i in range(3):
        if i:
            st = json.load(open(soubor_stavu, encoding="utf-8")); st["stop"] = time.time() - 1
            json.dump(st, open(soubor_stavu, "w", encoding="utf-8"))
        t0 = time.time()
        r = spust([KLIENT, A + "/limit"], e)
        st = json.load(open(soubor_stavu, encoding="utf-8"))
        delky.append(round((st["stop"] - t0) / 60))
    r = spust(["stav"], e)
    check("prodlužování stopky 30 min → 2 h → 8 h", delky == [30, 120, 480] and "3. odmítnutí" in r.stdout,
          f"délky {delky} min; {[x for x in r.stdout.splitlines() if 'ZASTAV' in x][0].strip()[:90]}")
    t0 = time.time()
    r = spust([KLIENT, A + "/limit"], e)   # souběžná odpověď během stopky se nepočítá
    st = json.load(open(soubor_stavu, encoding="utf-8"))
    check("dotaz během stopky odmítnutí nepřidá", st.get("poradi") == 3 and len(st.get("odmitnuti", [])) == 3,
          f"pořadí {st.get('poradi')}, odmítnutí {len(st.get('odmitnuti', []))}, kód {r.returncode}")

    # 14) souběh vláken při prvním dotazu – pětkrát s novou složkou stavu
    spatne = 0
    for i in range(5):
        r = spust([VLAKNA] + [A + f"/t/r{i}_{j}.jpg" for j in range(16)], stav(f"s14_{i}"))
        spatne += "nejde zapisovat" in r.stderr or r.returncode != 0
    check("první dotaz z 8 vláken, 5 opakování", spatne == 0, f"selhání: {spatne} z 5")

print(f"\n{sum(vysledky)} z {len(vysledky)} testů prošlo")
sys.exit(0 if all(vysledky) else 1)
