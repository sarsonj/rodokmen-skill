"""Test kontroly rodiny jako grafu v tools/graf.py (a jejího upozornění v tools/kontrola.py).

Z kořene repozitáře, testovaný nástroj je argument:
  python3 -I tests/graf/test_graf.py skills/rodokmen/tools/graf.py
  (Windows: python -I -X utf8 …)
Vymyšlená rodina v dočasné složce, nic nestahuje, jen standardní knihovna.
"""
import importlib.util, os, shutil, subprocess, sys, tempfile

GRAF = os.path.abspath(sys.argv[1])
TOOLS = os.path.dirname(GRAF)
PY = [sys.executable, "-I", "-X", "utf8"]
VYSLEDKY = []

sys.path.insert(0, TOOLS)
spec = importlib.util.spec_from_file_location("graf", GRAF)
graf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graf)

# Pavel (* 1900) ← Josef (* 1870) + Anna (* 1872); Josef ← Jan (* 1840) + Marie (* 1842); Anna ← Karel (* 1845)
# + Rozálie (* 1846). Jan a Karel jsou bratři (Matěj * 1810 a Kateřina * 1815), takže Matěj je předkem dvakrát.
# Otec Matěj se ženil podruhé s Evou (* 1838) a strom vede Jana i u ní (cizí strom často dělá tuhle chybu).
GED = """0 HEAD
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Pavel /Novák/
1 SEX M
1 BIRT
2 DATE 1900
1 FAMC @F1@
0 @I2@ INDI
1 NAME Josef /Novák/
1 SEX M
1 BIRT
2 DATE 1870
1 FAMC @F2@
0 @I3@ INDI
1 NAME Anna /Nováková/
1 SEX F
1 BIRT
2 DATE 1872
1 FAMC @F3@
0 @I4@ INDI
1 NAME Jan /Novák/
1 SEX M
1 BIRT
2 DATE 1840
1 FAMC @F5@
1 FAMC @F4@
0 @I5@ INDI
1 NAME Marie /Malá/
1 SEX F
1 BIRT
2 DATE 1842
0 @I6@ INDI
1 NAME Karel /Novák/
1 SEX M
1 BIRT
2 DATE 1845
1 FAMC @F4@
0 @I7@ INDI
1 NAME Rozálie /Dlouhá/
1 SEX F
1 BIRT
2 DATE 1846
0 @I8@ INDI
1 NAME Matěj /Novák/
1 SEX M
1 BIRT
2 DATE 1810
0 @I9@ INDI
1 NAME Kateřina /Hrdličková/
1 SEX F
1 BIRT
2 DATE 1815
1 DEAT
2 DATE 1860
0 @I10@ INDI
1 NAME Eva /Bílá/
1 SEX F
1 BIRT
2 DATE 1838
0 @I11@ INDI
1 NAME Johann /Nowak/
1 SEX M
1 BIRT
2 DATE 1841
0 @F1@ FAM
1 HUSB @I2@
1 WIFE @I3@
1 CHIL @I1@
0 @F2@ FAM
1 HUSB @I4@
1 WIFE @I5@
1 CHIL @I2@
0 @F3@ FAM
1 HUSB @I6@
1 WIFE @I7@
1 CHIL @I3@
0 @F4@ FAM
1 HUSB @I8@
1 WIFE @I9@
1 CHIL @I4@
1 CHIL @I6@
0 @F5@ FAM
1 HUSB @I8@
1 WIFE @I10@
1 CHIL @I4@
0 TRLR
"""


def zapis(cesta, text):
    os.makedirs(os.path.dirname(cesta), exist_ok=True)
    with open(cesta, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def pripad(nazev, podminka, detail=""):
    VYSLEDKY.append((nazev, bool(podminka), detail))


def strom(text=GED):
    tmp = tempfile.mkdtemp(prefix="graf_")
    zapis(os.path.join(tmp, "strom.ged"), text)
    return tmp, os.path.join(tmp, "strom.ged")


def test_strom():
    tmp, ged = strom()
    try:
        t = graf.nacti_strom(ged)
        pripad("bez cyklů", graf.cykly(t) == [])
        vic = {c["osoba"]: c for c in graf.vic_rodin(t)}
        pripad("dítě ve dvou rodinách", list(vic) == ["@I4@"], str(vic))
        pripad("rodina, kterou bere ged_import (první FAMC), je chronologicky nemožná",
               vic.get("@I4@", {}).get("prvni") == "@F5@" and vic.get("@I4@", {}).get("mozne") == ["@F4@"], str(vic))
        chrono = {(d, r, c) for d, _h, r, c in graf.chronologie(t)}
        pripad("matce Evě by při narození Jana byly 2 roky", ("věk matky", "@I10@", "@I4@") in chrono, str(chrono))
        dvoj = {(a, b) for _s, a, b in graf.dvojnici(t)}
        pripad("Johann Nowak (* 1841) je možná dvojník Jana Nováka (* 1840)",
               ("@I4@", "@I11@") in dvoj or ("@I11@", "@I4@") in dvoj, str(dvoj))
        pripad("sourozenci se jako dvojníci nehlásí", not any({"@I4@", "@I6@"} == {a, b} for a, b in dvoj))
        kek = graf.kekule(t, "@I1@")
        pripad("Matěj je předkem dvakrát (8 a 12)", kek.get("@I8@") == {8, 12}, str(kek.get("@I8@")))
        pripad("návrh SAME", graf.navrh_same(kek) == {12: 8, 13: 9}, str(graf.navrh_same(kek)))
        r = subprocess.run(PY + [GRAF, "strom", ged, "Pavel Novák"], capture_output=True, text=True, encoding="utf-8")
        pripad("výpis strom: SAME a dvě rodiny", r.returncode == 0 and "SAME = {12: 8, 13: 9}" in r.stdout
               and "@F5@" in r.stdout, r.stdout + r.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cyklus():
    tmp, ged = strom(GED.replace("0 @F1@ FAM", "0 @F9@ FAM\n1 HUSB @I1@\n1 CHIL @I8@\n0 @F1@ FAM"))
    try:
        c = graf.cykly(graf.nacti_strom(ged))
        pripad("Pavel jako otec Matěje = cyklus", c and {"@I1@", "@I8@"} <= set(c[0]), str(c))
        r = subprocess.run(PY + [GRAF, "strom", ged], capture_output=True, text=True, encoding="utf-8")
        pripad("cyklus = návratový kód 1", r.returncode == 1 and "CHYBA" in r.stdout, r.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


P = {
    1: dict(n="Pavel Novák", y="* 1900", st="fam", f=[]),
    2: dict(n="Josef Novák", y="1870–1930", st="doc", f=["* 3. 4. 1870 Holice čp. 5"]),
    3: dict(n="Anna Nováková", y="1872–1940", st="doc", f=[]),
    4: dict(n="Jan Novák", y="1840–1869", st="doc", f=["† 2. 1. 1869 Holice"]),   # zemřel rok před narozením syna
    5: dict(n="Marie Malá", y="1856–1900", st="doc", f=[]),                         # matkou ve 14 letech
    6: dict(n="Karel Novák", y="1845–1910", st="doc", f=[]),
    7: dict(n="Rozálie Dlouhá", y="asi 1846–1920", st="doc", f=[]),
    8: dict(n="Matěj Novák", y="1810–1880", st="doc", f=[]),
    9: dict(n="Kateřina Hrdličková", y="1815–1860", st="doc", f=[]),
    12: dict(n="Matěj Novák", y="1810–1880", st="mh", f=[]),
    13: dict(n="Kateřina Hrdličková", y="1815–1860", st="mh", f=[]),
}


def test_predci():
    u = graf.predci(P, {})
    t = "\n".join(u)
    pripad("Matěj na 8 a 12 bez SAME", "osoba 12" in t and "jako 8" in t and "SAME = {12: 8}" in t, t)
    pripad("Jan † 1869 a syn * 1870 je v pořádku (otec smí zemřít rok před)", "osoba 4" not in t, t)
    pripad("Marie Malá matkou ve 14 letech hlášena", "osoba 5" in t and "14" in t, t)
    u = graf.predci(P, {12: 8, 13: 9})
    pripad("s SAME implex nehlásí", not any("SAME" in x for x in u), "\n".join(u))
    P2 = {**P, 9: dict(P[9], y="1815–1844")}
    pripad("matka zemřela před narozením syna Karla (* 1845)",
           any("osoba 9" in x and "zemřela" in x for x in graf.predci(P2, {12: 8, 13: 9})), "\n".join(graf.predci(P2, {})))


def test_kontrola():
    tmp = tempfile.mkdtemp(prefix="graf_kontrola_")
    try:
        zapis(os.path.join(tmp, "data", "osoby.py"), f"P = {P!r}\nSAME = {{}}\n")
        for f in ("zaznamy.json", "prepisy.json"):
            zapis(os.path.join(tmp, "data", f), "[]" if f == "zaznamy.json" else "{}")
        os.makedirs(os.path.join(tmp, "tools"))
        for f in ("kontrola.py", "graf.py", "ged_import.py"):
            shutil.copy(os.path.join(TOOLS, f), os.path.join(tmp, "tools", f))
        r = subprocess.run(PY + [os.path.join(tmp, "tools", "kontrola.py")], capture_output=True, text=True,
                           encoding="utf-8")
        pripad("kontrola.py hlásí implex a věk rodiče z graf.py",
               "upozornění: osoba 12" in r.stdout and "osoba 5" in r.stdout, r.stdout + r.stderr)
        os.remove(os.path.join(tmp, "tools", "graf.py"))
        r = subprocess.run(PY + [os.path.join(tmp, "tools", "kontrola.py")], capture_output=True, text=True,
                           encoding="utf-8")
        pripad("kontrola.py funguje i bez graf.py", "Traceback" not in r.stderr, r.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    for t in (test_strom, test_cyklus, test_predci, test_kontrola):
        try:
            t()
        except Exception as e:  # noqa: BLE001 – spadlý případ se vypíše a test neprojde
            import traceback
            pripad(t.__name__, False, traceback.format_exc())
    for nazev, ok, detail in VYSLEDKY:
        print(("OK   " if ok else "CHYBA"), nazev, "" if ok else "\n      " + detail.replace("\n", "\n      "))
    spatne = sum(1 for _n, ok, _d in VYSLEDKY if not ok)
    print(f"{len(VYSLEDKY) - spatne}/{len(VYSLEDKY)} v pořádku")
    sys.exit(1 if spatne else 0)
