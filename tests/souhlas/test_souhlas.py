"""Testy tools/souhlas.py (souhlas uživatele s podmínkami portálu s citlivými údaji).

Z kořene repozitáře:
  python3 -I tests/souhlas/test_souhlas.py
  (Windows: python -I -X utf8 tests/souhlas/test_souhlas.py)
Nic nestahuje. Stav souhlasu se zapisuje do dočasné složky (SOUHLAS_STAV).
"""
import builtins, contextlib, importlib.util, io, json, os, sys, tempfile, time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "skills", "rodokmen", "tools")
STAV = tempfile.mkdtemp(prefix="souhlas_")
os.environ["SOUHLAS_STAV"] = STAV
spec = importlib.util.spec_from_file_location("souhlas", os.path.join(TOOLS, "souhlas.py"))
souhlas = importlib.util.module_from_spec(spec)
spec.loader.exec_module(souhlas)

vysledky = []


def ok(nazev, podminka, detail=""):
    vysledky.append(bool(podminka))
    print(("OK   " if podminka else "CHYBA"), nazev, "" if podminka else detail)


def kod(fn, *args, vstup=None, terminal=False):
    """Zavolá fn; vrátí (kód ukončení nebo None, stderr, stdout)."""
    puvodni = souhlas._je_terminal, builtins.input
    souhlas._je_terminal = lambda: terminal
    builtins.input = lambda prompt="": vstup
    out, err, k = io.StringIO(), io.StringIO(), None
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                fn(*args)
            except SystemExit as e:
                k = e.code
    finally:
        souhlas._je_terminal, builtins.input = puvodni
    return k, err.getvalue(), out.getvalue()


ZNENI = "Přečetl jsem podmínky."
ARGS = ("test_portal", "Testovací portál", ZNENI, "tools/test.py souhlas")

k, err, _ = kod(souhlas.vyzaduj, "test_portal", "Testovací portál", ZNENI, "tools/test.py souhlas")
ok("bez souhlasu: vyzaduj skončí kódem 4", k == souhlas.KOD, k)
ok("bez souhlasu: hláška říká, že souhlas potvrdí uživatel sám", "uživatel sám" in err and "tools/test.py souhlas" in err, err)

k, err, _ = kod(souhlas.potvrd, *ARGS[:3], "https://example.org", ARGS[3], vstup="ano", terminal=False)
ok("bez terminálu (Claude, skript): souhlas se nezapíše", k == souhlas.KOD and not os.listdir(STAV), (k, os.listdir(STAV)))
ok("bez terminálu: hláška vysvětlí proč", "interaktivním terminálu" in err, err)

k, err, out = kod(souhlas.potvrd, *ARGS[:3], "https://example.org", ARGS[3], vstup="možná", terminal=True)
ok("jiná odpověď než „ano“: souhlas se nezapíše", k == souhlas.KOD and not os.listdir(STAV), (k, os.listdir(STAV)))
ok("znění se uživateli zobrazí", ZNENI in out and "https://example.org" in out, out)

k, err, out = kod(souhlas.potvrd, *ARGS[:3], "https://example.org", ARGS[3], vstup=" Ano ", terminal=True)
ok("odpověď „ano“ v terminálu souhlas zapíše", k is None and os.path.exists(os.path.join(STAV, "test_portal.json")), (k, err))
ok("zapsaný soubor má datum a otisk znění", set(json.load(open(os.path.join(STAV, "test_portal.json")))) >= {"cas", "datum", "otisk", "portal"})
k, _, _ = kod(souhlas.vyzaduj, *ARGS)
ok("po souhlasu vyzaduj projde", k is None, k)

k, _, _ = kod(souhlas.vyzaduj, "test_portal", "Testovací portál", ZNENI + " Nové znění.", "tools/test.py souhlas")
ok("změněné znění podmínek vyžaduje souhlas znovu", k == souhlas.KOD, k)

d = json.load(open(os.path.join(STAV, "test_portal.json")))
d["cas"] = time.time() - 31 * 24 * 3600
json.dump(d, open(os.path.join(STAV, "test_portal.json"), "w"))
k, _, _ = kod(souhlas.vyzaduj, *ARGS)
ok("souhlas starší než 30 dní vyprší", k == souhlas.KOD, k)

open(os.path.join(STAV, "test_portal.json"), "w").write("{rozbitý soubor")
k, _, _ = kod(souhlas.vyzaduj, *ARGS)
ok("poškozený soubor se bere jako chybějící souhlas", k == souhlas.KOD, k)

d["cas"] = time.time() + 10 * 24 * 3600
json.dump(d, open(os.path.join(STAV, "test_portal.json"), "w"))
k, _, _ = kod(souhlas.vyzaduj, *ARGS)
ok("souhlas s časem v budoucnosti neplatí", k == souhlas.KOD, k)

print(f"\n{sum(vysledky)} z {len(vysledky)} v pořádku")
sys.exit(0 if all(vysledky) else 1)
