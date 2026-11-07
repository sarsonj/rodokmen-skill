"""Testy tools/smoke_test.py (vyhodnocení výsledku nástroje, přeskočení chybějících nástrojů, kontrola voleb).

Z kořene repozitáře:
  python3 -I tests/smoke/test_smoke_test.py
  (Windows: python -I -X utf8 tests/smoke/test_smoke_test.py)
Nic nestahuje a žádný nástroj nespouští (kromě volby --seznam).
"""
import importlib.util, os, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "skills", "rodokmen", "tools")
os.environ["SLUSNE_STAV"] = tempfile.mkdtemp(prefix="smoke_slusne_")
spec = importlib.util.spec_from_file_location("smoke_test", os.path.join(TOOLS, "smoke_test.py"))
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)

vysledky = []


def ok(nazev, podminka, detail=""):
    vysledky.append(bool(podminka))
    print(("OK   " if podminka else "CHYBA"), nazev, "" if podminka else detail)


v = smoke.vyhodnot
ok("kód 0 a očekávaný text = OK", v(0, "count 5\n", "", "count", False)[0] == "OK")
ok("kód 0, ale očekávaný text chybí = CHYBA (portál se změnil)", v(0, "nic\n", "", "count", False)[0] == "CHYBA")
ok("chyba nástroje bez náznaku sítě = CHYBA", v(1, "", "KeyError: 'x'", "count", False)[0] == "CHYBA")
ok("chyba sítě = NEDOSTUPNÉ", v(1, "", "urllib.error.URLError: <urlopen error [Errno 104] Connection reset by peer>", "x", False)[0] == "NEDOSTUPNÉ")
ok("HTTP 503 = NEDOSTUPNÉ", v(1, "", "HTTP Error 503: Service Unavailable", "x", False)[0] == "NEDOSTUPNÉ")
ok("volitelný nástroj: libovolná chyba = NEDOSTUPNÉ", v(1, "", "KeyError: 'x'", "x", True)[0] == "NEDOSTUPNÉ")
ok("kód 3 (brzda web zastavila) = ZASTAVENO, ne CHYBA", v(3, "", "slusne: aron je zastavený", "x", False)[0] == "ZASTAVENO")
ok("kód 4 (čeká na souhlas uživatele) = PŘESKOČENO, ne CHYBA", v(4, "", "souhlas musí potvrdit uživatel", "x", False)[0] == "PŘESKOČENO")
ok("prázdný výstup nespadne", v(1, "", "", "x", False)[0] == "CHYBA")

stav, popis = smoke.spust(["neexistuje_nastroj.py", "x"], "x", False)
ok("chybějící nástroj se přeskočí", stav == "PŘESKOČENO" and "není" in popis, (stav, popis))

nazvy = [t[0] for t in smoke.TESTY]
ok("názvy testů jsou jedinečné", len(nazvy) == len(set(nazvy)), nazvy)
ok("každý test má nástroj, očekávaný text a příznak volitelnosti", all(len(t) == 4 and isinstance(t[3], bool) for t in smoke.TESTY))

r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(TOOLS, "smoke_test.py"), "nenizadny"], capture_output=True, text=True,
                   env={**os.environ}, timeout=60)
ok("neznámý nástroj v parametrech skončí hláškou", r.returncode != 0 and "Neznámé nástroje" in r.stderr, (r.returncode, r.stderr))
r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(TOOLS, "smoke_test.py"), "--seznam"], capture_output=True, text=True,
                   env={**os.environ}, timeout=60)
ok("--seznam vypíše všechny testy bez spouštění", r.returncode == 0 and len(r.stdout.strip().splitlines()) == len(smoke.TESTY), r.stdout)

print(f"\n{sum(vysledky)} z {len(vysledky)} v pořádku")
sys.exit(0 if all(vysledky) else 1)
