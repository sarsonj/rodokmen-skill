"""Test obsahových kontrol v tools/kontrola_dat.py a nástroje tools/denik.py na vymyšlených datech.

Z kořene repozitáře:  python -I -X utf8 tests/kontrola_dat/test_kontrola_dat.py
(testuje skills/rodokmen/tools/kontrola_dat.py a denik.py)
Nic nestahuje a nemění data projektu (deník se zkouší na dočasné kopii).
"""
import importlib.util, os, shutil, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "skills", "rodokmen", "tools")
sys.path.insert(0, TOOLS)


def modul(jmeno):
    spec = importlib.util.spec_from_file_location(jmeno, os.path.join(TOOLS, jmeno + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


kd = modul("kontrola_dat")
VYSLEDKY = []


def ma(warn, text, ocekavam=True):
    nasel = any(text in w for w in warn)
    VYSLEDKY.append((nasel == ocekavam, f"{'má' if ocekavam else 'nemá'} hlásit: {text}"))


P = {
    4: dict(n="Jan Novák", y="1840–1900", st="doc", f=["* 3. 3. 1841", "† 1. 1. 1905", "× 1. 2. 1865 Marie (jako vdovec)"],
            r=["o_1865"], note="V matrice neověřeno."),
    5: dict(n="Marie Malá", y="1845–1930", st="doc", f=["* 1845 (strom MH)", "† 1930 (strom Hachová)"], r=["n_1845"]),
    6: dict(n="Petr Kos", y="", st="doc", f=["* asi 1799 (24 let při sňatku)"], r=["n_1845"]),
    7: dict(n="Anna Kosová", y="1850–1930 (?)", st="doc", f=["† 1930 (strom Hachová)"], r=["n_1845"]),
    2: dict(n="Josef Novák", y="1866–1940", st="doc", f=["* 1866", "× 1890 Anna Bílá (vdova)"], r=["o_1890"]),
}
ZAZ = [dict(klic="o_1865", druh="O", datum="1. 2. 1865", nazev="Sňatek", shrnuti="…"),
       dict(klic="o_1890", druh="O", datum="1890", nazev="Sňatek", shrnuti="…"),
       dict(klic="n_1845", druh="N", datum="1845", nazev="Křest Marie (kandidát)", shrnuti="…")]
PREP = {"o_1865": {"orig": "[Bräutigam] Jan Novák, kat., 24 Jahre, ledig\n[Braut] Marie, ledig", "cz": "…"},
        "o_1890": {"orig": "[Bräutigam] Josef Novák, ledig\n[Braut] Anna, Witwe", "cz": "…"}}

w = kd.kontroly(P, [], ZAZ, PREP)
ma(w, "osoba 4 (Jan Novák): y má úmrtí 1900, fakta 1905")
ma(w, "osoba 4 (Jan Novák): y má narození 1840", ocekavam=False)          # rozdíl 1 rok se toleruje
ma(w, "osoba 4 (Jan Novák): poznámka říká „V matrice neověřeno“")
ma(w, "osoba 4 (Jan Novák): u sňatku o_1865 má fakta „vdovec/vdova“, přepis „ledig“")
ma(w, "osoba 5 (Marie Malá): rok 1845 v y je jen z cizího stromu")
ma(w, "osoba 5 (Marie Malá): cituje zápis n_1845, který je podle názvu/shrnutí jen kandidát")
ma(w, "osoba 6 (Petr Kos): fakta mají narození 1799, ale y je prázdné")
ma(w, "osoba 7 (Anna Kosová): rok 1930", ocekavam=False)                   # „(?)“ = nejistota přiznaná
ma(w, "osoba 2 (Josef Novák): u sňatku", ocekavam=False)                   # „vdova“ patří nevěstě, ne jemu

# denik.py na dočasné kopii deníku
denik = modul("denik")
tmp = tempfile.mkdtemp()
try:
    log = os.path.join(tmp, "research_log.md")
    with open(log, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Deník\n\n| # | datum | zdroj | rozsah | hledáno | výsledek | citace |\n|---|---|---|---|---|---|---|\n"
                "| 500 | 2026-11-11 | a | b | c | d | e |\n\n")
    denik.LOG = log
    denik.text_main = lambda: ""
    n = denik.pridej(dict(zdroj="ARON | kniha", rozsah="sn. 1", hledano="x", vysledek="řádek\ndruhý"))
    text = open(log, encoding="utf-8").read()
    VYSLEDKY.append((n == 501, "denik: další číslo 501"))
    VYSLEDKY.append(("\n\n| 501" not in text, "denik: prázdný řádek před novým řádkem smazán"))
    VYSLEDKY.append(("ARON \\| kniha" in text and "řádek druhý" in text, "denik: svislá čára escapována, konec řádku nahrazen"))
    e, _ = denik.kontrola(text, od=500)
    VYSLEDKY.append((not e, f"denik: kontrola čistá ({e})"))
    e, _ = denik.kontrola(text.replace("| 501 |", "\n| 501 |").replace("| e |", "| e | f |"), od=500)
    VYSLEDKY.append((any("prázdný řádek" in x for x in e) and any("sloupců" in x for x in e), "denik: hlásí prázdný řádek a sloupce"))
finally:
    shutil.rmtree(tmp)

spatne = [t for ok, t in VYSLEDKY if not ok]
for ok, t in VYSLEDKY:
    print(("OK   " if ok else "CHYBA"), t)
print(f"{len(VYSLEDKY) - len(spatne)}/{len(VYSLEDKY)} v pořádku")
if spatne:
    print("\nVšechna upozornění:\n" + "\n".join(w))
sys.exit(1 if spatne else 0)
