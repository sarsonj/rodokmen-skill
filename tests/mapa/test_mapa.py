"""Testy výběru obcí na mapu v tools/export_web.py (vlastni_text, zil_v) a kontroly předků bez obce v tools/kontrola.py.

Z kořene repozitáře:
  python3 -I tests/mapa/test_mapa.py
  (Windows: python -I -X utf8 tests/mapa/test_mapa.py)
Případy jsou z praxe: osoba se objevila na mapě v obci, kde nežila (fara, okres, „u Hořic“, rodná obec matky
nebo nevěsty). Nic nestahuje, kontrola běží v dočasném projektu.
"""
import importlib.util, json, os, re, shutil, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "skills", "rodokmen", "tools")
spec = importlib.util.spec_from_file_location("export_web", os.path.join(TOOLS, "export_web.py"))
ew = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ew)

MISTA = {"Střelná": r"Střeln(á|é|ou)\b", "Francova Lhota": r"Francov(a|y|ě) Lhot", "Humpolec": r"Humpol(ec|ce|ci)\b",
         "Hovězí": r"Hovězí\b", "Hořice": r"Hoři(c|ce|cích)\b", "Chlum": r"Chlum(u|ě)?\b", "Prčice": r"Prčic",
         "Bašnice": r"Bašnic", "Strunkovice": r"Strunkovic", "Benešov": r"Benešov"}
vysledky = []


def ok(nazev, podminka, detail=""):
    vysledky.append(bool(podminka))
    print(("OK   " if podminka else "CHYBA"), nazev, "" if podminka else detail)


def obce(fakty, muz=True):
    t = ew.vlastni_text(fakty, muz)
    return sorted(n for n, rx in MISTA.items() if ew.zil_v(t, re.compile(rx)))


PRIPADY = [   # (název, údaje, muž?, obce na mapě)
    ("vlastní obec", ["* 5. 8. 1820 Střelná č. 69"], True, ["Střelná"]),
    ("matka roz. … z", ["syn Jana Lišky a Marianny roz. Šivkové z Francovy Lhoty", "sedlák ve Střelné"], True,
     ["Střelná"]),
    ("matka s nejistým příjmením (?)", ["dcera Václava Pospíšila a Marie Josífkové (?) z Humpolce"], False, []),
    ("matka se dvěma slovy jména", ["syn Jana a Kateřiny Žižkové ze Strunkovic"], True, []),
    ("matka s popisem", ["syn Josefa a Rosiny, dcery sedláka Jana Kubíka z Hovězí", "† 1801 Střelná"], True,
     ["Střelná"]),
    ("přívlastek u …", ["oddán v Chlumu u Hořic"], True, ["Chlum"]),
    ("fara a okres", ["* 1790 Bašnice (fara Prčice, okres Benešov)"], True, ["Bašnice"]),
    ("muž: obec nevěsty ne", ["* 1730 Hořice", "× 1758 Hořice Kateřina z Bašnic"], True, ["Hořice"]),
    ("muž: sňatek uprostřed údaje", ["chalupník v Hořicích; × 1758 Hořice Kateřina z Bašnic"], True, ["Hořice"]),
    ("žena: obec muže zůstává", ["× 1758 Hořice Jan Novák z Bašnic"], False, ["Bašnice", "Hořice"]),
]
for nazev, fakty, muz, cekam in PRIPADY:
    vyslo = obce(fakty, muz)
    ok(nazev, vyslo == cekam, f"čekal jsem {cekam}, vyšlo {vyslo}")

# kontrola.py vypíše všechny předky bez vlastní obce (dřív jen 3) a obec matky se nepočítá
d = tempfile.mkdtemp(prefix="mapa_kontrola_")
try:
    os.makedirs(os.path.join(d, "data"))
    os.makedirs(os.path.join(d, "tools"))
    for n in ("kontrola.py", "export_web.py"):
        shutil.copy(os.path.join(TOOLS, n), os.path.join(d, "tools"))
    P = {1: dict(n="Petr Novák", st="doc", f=["* 1990 Střelná"])}
    P.update({k: dict(n=f"Jan Novák {k}", st="doc", f=[f"* 18{k:02d} (fara Prčice)"]) for k in (2, 4, 8, 16)})
    P[3] = dict(n="Anna Šivková", st="doc", f=["dcera Josefa a Marie roz. Kubíkové z Hovězí"])
    with open(os.path.join(d, "data", "osoby.py"), "w", encoding="utf-8") as f:
        f.write(f"P = {P!r}\n")
    with open(os.path.join(d, "data", "mista.json"), "w", encoding="utf-8") as f:
        json.dump({n: dict(re=rx, lat=50.0, lon=15.0) for n, rx in MISTA.items()}, f, ensure_ascii=False)
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(d, "tools", "kontrola.py")],
                       capture_output=True, text=True, encoding="utf-8")
    radek = next((l for l in r.stdout.splitlines() if "mapa:" in l), "")
    ok("kontrola: počet předků bez obce", "5 doložených předků" in radek, radek or r.stdout + r.stderr)
    ok("kontrola: vypíše všechny, ne jen tři", all(f"Jan Novák {k}" in radek for k in (2, 4, 8, 16)), radek)
    ok("kontrola: obec matky se nepočítá", "Anna Šivková" in radek, radek)
finally:
    shutil.rmtree(d, ignore_errors=True)

print(f"\n{sum(vysledky)}/{len(vysledky)} v pořádku")
sys.exit(0 if all(vysledky) else 1)
