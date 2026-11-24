"""Test tools/stejna_osoba.py (zápis SAME – předek v rodokmenu podruhé).

Z kořene repozitáře:
  python3 -I tests/stejna_osoba/test_stejna_osoba.py skills/rodokmen/tools
  (Windows: python -I -X utf8 …)
Každý případ si postaví dočasný projekt s vymyšlenou rodinou, zkopíruje do něj nástroje a pustí je. Nic nestahuje.
"""
import os, shutil, subprocess, sys, tempfile

TOOLS = os.path.abspath(sys.argv[1])
PY = [sys.executable, "-I", "-X", "utf8"]
VYSLEDKY = []

P = """P = {
 1: dict(n='Martin Test', y='* 1990', st='doc', f=[], r=[]),
 2: dict(n='Otec Test', y='1960', st='doc', f=[], r=[]),
 3: dict(n='Matka Test', y='1962', st='doc', f=[], r=[]),
 8: dict(n='Karel Hora', y='1800–1860', st='doc', f=[], r=[]),
 9: dict(n='Marie Kosová', y='1805–1870', st='doc', f=[], r=[]),
 20: dict(n='Karel Hora', y='1801–1861', st='doc', f=['TÁŽ OSOBA jako 8'], r=[]),
 21: dict(n='Marie Kosová', y='1805', st='doc', f=[], r=[]),
 24: dict(n='Jan Lípa', y='1799', st='doc', f=[], r=[]),
 30: dict(n='Karel Hora', y='1800', st='doc', f=[], r=[]),
 60: dict(n='Tomáš Hora', y='1770', st='doc', f=[], r=[]),
}
SIDE = []
LINES = {}
ISSUES = []
HYPOTEZY = []
"""


def projekt(same):
    tmp = tempfile.mkdtemp(prefix="stejna_osoba_")
    os.makedirs(os.path.join(tmp, "tools"))
    os.makedirs(os.path.join(tmp, "data"))
    for n in ("stejna_osoba.py", "zapis.py"):
        shutil.copy(os.path.join(TOOLS, n), os.path.join(tmp, "tools", n))
    with open(os.path.join(tmp, "data", "osoby.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write(P + same)
    return tmp


def spust(tmp, *args):
    r = subprocess.run(PY + [os.path.join("tools", "stejna_osoba.py"), *args], cwd=tmp, capture_output=True, text=True, encoding="utf-8")
    return r, open(os.path.join(tmp, "data", "osoby.py"), encoding="utf-8").read()[len(P):]


def ma(nazev, ok, detail=""):
    VYSLEDKY.append(ok)
    print(("OK  " if ok else "CHYBA ") + nazev + ("" if ok else f"\n    {detail}"))


def pripad(nazev, same, args, ocekavany_konec=None, chyba=False):
    tmp = projekt(same)
    try:
        r, konec = spust(tmp, *args)
        if chyba:
            ma(nazev, r.returncode != 0 and konec == same, r.stdout + r.stderr + repr(konec))
        else:
            ma(nazev, r.returncode == 0 and konec == ocekavany_konec, r.stdout + r.stderr + repr(konec))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


pripad("prázdné SAME", "SAME = {}\n", ["20", "8"], "SAME = {20: 8}\n")
pripad("jeden řádek", "SAME = {20: 8}\n", ["21", "9"], "SAME = {20: 8, 21: 9}\n")
pripad("víc řádků s čárkou a komentářem", "SAME = {\n    20: 8,  # Hora\n}\n", ["21", "9"], "SAME = {\n    20: 8,  # Hora\n    21: 9,\n}\n")
pripad("víc řádků bez čárky", "SAME = {\n    20: 8\n}\n", ["21", "9"], "SAME = {\n    20: 8,\n    21: 9,\n}\n")
pripad("SAME chybí", "", ["20", "8"], "\n# Předek v rodokmenu vícekrát: {alias: hlavní číslo}\nSAME = {20: 8}\n")
pripad("už zapsáno – nic se nezmění", "SAME = {20: 8}\n", ["20", "8"], "SAME = {20: 8}\n")
pripad("jiná jména", "SAME = {}\n", ["24", "8"], chyba=True)
pripad("jiná jména s --vynutit", "SAME = {}\n", ["24", "8", "--vynutit"], "SAME = {24: 8}\n")
pripad("osoba není v P", "SAME = {}\n", ["99", "8"], chyba=True)
pripad("předek a potomek", "SAME = {}\n", ["4", "2"], chyba=True)
pripad("alias už míří jinam", "SAME = {20: 9}\n", ["20", "8", "--vynutit"], chyba=True)
pripad("hlavní osoba je sama alias", "SAME = {20: 8}\n", ["30", "20"], chyba=True)
pripad("alias má vlastní předky", "SAME = {}\n", ["30", "8"], chyba=True)
pripad("dvě přiřazení SAME", "SAME = {}\nSAME = {}\n", ["20", "8"], chyba=True)
pripad("SAME není slovník", "SAME = dict(a=1)\n", ["20", "8"], chyba=True)
sys.exit(0 if all(VYSLEDKY) else 1)
