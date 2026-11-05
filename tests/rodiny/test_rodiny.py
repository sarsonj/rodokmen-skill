"""Test nástroje tools/rodiny.py (rekonstrukce rodin, kandidáti, průnik).

Z kořene repozitáře, testovaný nástroj je argument:
  python3 -I tests/rodiny/test_rodiny.py skills/rodokmen/tools/rodiny.py
  (Windows: python -I -X utf8 …)
Postaví dočasný projekt s vymyšlenou rodinou (data/osoby.py), založí případ se dvěma kandidáty stejného jména
a ověří přehled, průnik (vlastní vs. společné shody, dům, rodokmen jen pro současníky) a rodiny (mezery, opakované
jméno, stálý kmotr). Nic nestahuje, jen standardní knihovna.
"""
import json, os, shutil, subprocess, sys, tempfile

NASTROJ = os.path.abspath(sys.argv[1])
PY = [sys.executable, "-I", "-X", "utf8"]
VYSLEDKY = []


def zapis(cesta, text):
    os.makedirs(os.path.dirname(cesta), exist_ok=True)
    with open(cesta, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def spust(tmp, *args, ok=True):
    r = subprocess.run(PY + [os.path.join(tmp, "tools", "rodiny.py"), *args], cwd=tmp, capture_output=True,
                       text=True, encoding="utf-8")
    if ok and r.returncode:
        raise AssertionError(f"rodiny.py {' '.join(args)} skončil kódem {r.returncode}:\n{r.stdout}{r.stderr}")
    return r.stdout + r.stderr


def over(nazev, podminka, vystup=""):
    VYSLEDKY.append((nazev, bool(podminka)))
    print(("OK    " if podminka else "CHYBA ") + nazev)
    if not podminka and vystup:
        print("      " + vystup.replace("\n", "\n      "))


def main():
    tmp = tempfile.mkdtemp(prefix="rodiny_")
    try:
        os.makedirs(os.path.join(tmp, "tools"))
        shutil.copy(NASTROJ, os.path.join(tmp, "tools", "rodiny.py"))
        zapis(os.path.join(tmp, "data", "osoby.py"),
              'P = {16: dict(n="Josef Novák", y="1760–1830", f=["* 1760 Lhota č. 5"]),\n'
              '     32: dict(n="Matěj Novák", y="", f=[]),\n'
              '     2: dict(n="Matěj Novák", y="* 1950", f=["* 1950 Praha"])}\n'
              'SIDE = [dict(k=16, n="Jan Novák (* 1788)", t="Syn Josefa.", r=[])]\n')
        spust(tmp, "novy", "matej_32", "Kdo byl Matěj Novák, otec Josefa?", "--osoba", "32")
        spust(tmp, "kandidat", "matej_32", "A", "Matěj, syn Jana")
        spust(tmp, "kandidat", "matej_32", "B", "Matěj, syn Pavla")
        vstup = [
            {"patri": "kotva", "druh": "N", "datum": "3. 3. 1760", "obec": "Lhota", "dum": "5", "zdroj": "x sn. 1",
             "osoby": [{"jmeno": "Josef Novák", "role": "dite"}, {"jmeno": "Matěj Novák", "role": "otec"},
                       {"jmeno": "Anna", "role": "matka"}, {"jmeno": "Jiří Krejčí", "role": "kmotr"}]},
            {"patri": "A", "druh": "O", "datum": "1. 2. 1755", "obec": "Lhota", "zdroj": "x sn. 2",
             "osoby": [{"jmeno": "Mathias Nowak", "role": "zenich"}, {"jmeno": "Jan Novák", "role": "otec_zenicha"},
                       {"jmeno": "Georgius Krejčí", "role": "svedek"}]},
            {"patri": "B", "druh": "O", "datum": "5. 5. 1756", "obec": "Lhota", "zdroj": "x sn. 3",
             "osoby": [{"jmeno": "Matěj Novák", "role": "zenich"}, {"jmeno": "Pavel Novák", "role": "otec_zenicha"},
                       {"jmeno": "Petr Dvořák", "role": "svedek"}]},
            {"patri": "B", "druh": "N", "datum": "7. 7. 1758", "obec": "Lhota", "dum": "5", "zdroj": "x sn. 4",
             "osoby": [{"jmeno": "Anna Nováková", "role": "dite"}, {"jmeno": "Matěj Novák", "role": "otec"},
                       {"jmeno": "Anna", "role": "matka"}, {"jmeno": "Petr Dvořák", "role": "kmotr"}]},
            {"patri": "B", "druh": "N", "datum": "1. 1. 1763", "obec": "Lhota", "zdroj": "x sn. 5",
             "osoby": [{"jmeno": "Anna Nováková", "role": "dite"}, {"jmeno": "Matěj Novák", "role": "otec"},
                       {"jmeno": "Anna", "role": "matka"}, {"jmeno": "Petr Dvořák", "role": "kmotr"}]},
        ]
        zapis(os.path.join(tmp, "pracovni", "vstup.json"), json.dumps(vstup, ensure_ascii=False))
        out = spust(tmp, "zapis", "matej_32", "pracovni/vstup.json")
        over("zápis pěti záznamů", out.count("zapsáno") == 5, out)

        out = spust(tmp, "zapis", "matej_32", "pracovni/vstup.json")
        over("varování při opakovaném zápisu stejného zdroje", "nezapisuješ ho podruhé" in out, out)
        d = json.load(open(os.path.join(tmp, "data", "rodiny", "matej_32.json"), encoding="utf-8"))
        d["zapisy"] = d["zapisy"][:5]
        zapis(os.path.join(tmp, "data", "rodiny", "matej_32.json"), json.dumps(d, ensure_ascii=False))

        spatny = [{"patri": "Z", "druh": "N", "osoby": [{"jmeno": "X Y", "role": "dite"}]}]
        zapis(os.path.join(tmp, "pracovni", "spatny.json"), json.dumps(spatny))
        out = spust(tmp, "zapis", "matej_32", "pracovni/spatny.json", ok=False)
        over("neznámý kandidát v \"patri\" je chyba", "kandidát neexistuje" in out, out)

        spust(tmp, "ukol", "matej_32", "vse", "1", "křty Matějů")
        spust(tmp, "ukol", "matej_32", "A", "2", "děti A")
        out = spust(tmp, "prehled", "matej_32")
        over("přehled: na řadě je nejnižší vrstva", "NA ŘADĚ – vrstva 1" in out and "u1" in out
             and "čekají i vrstvy 2" in out, out)

        out = spust(tmp, "prunik", "matej_32")
        over("průnik: Matěj Novák je společný oběma (nerozlišuje)", "NEROZLIŠUJE" in out and "matej novak" in out, out)
        over("průnik: latinské Georgius Krejčí u A = kmotr Jiří Krejčí z kotvy",
             "OSOBA    Georgius Krejčí" in out, out)
        over("průnik: dům č. 5 u B", "DŮM      č. 5" in out, out)
        over("průnik: Jan Novák (1755) ~ Jan Novák * 1788 z rodokmenu (současník)",
             "RODOKMEN Jan Novák" in out and "Jan Novák (* 1788)" in out, out)
        over("průnik: Matěj Novák * 1950 se jako současník nehlásí", "* 1950" not in out, out)

        blizko = [{"patri": "B", "druh": "N", "datum": "20. 10. 1758", "obec": "Lhota", "zdroj": "x sn. 6",
                   "osoby": [{"jmeno": "Petr Novák", "role": "dite"}, {"jmeno": "Matěj Novák", "role": "otec"},
                             {"jmeno": "Anna", "role": "matka"}, {"jmeno": "Jiří Krejčí", "role": "kmotr"},
                             {"jmeno": "Petr Dvořák", "role": "svedek"}]}]
        zapis(os.path.join(tmp, "pracovni", "blizko.json"), json.dumps(blizko, ensure_ascii=False))
        spust(tmp, "zapis", "matej_32", "pracovni/blizko.json")
        out = spust(tmp, "rodiny", "matej_32")
        over("rodiny: dva porody 3 měsíce po sobě → dva páry nebo chybné datum", "jedna matka nestihne" in out, out)
        over("rodiny: svědek se počítá do stálých kmotrů (Petr Dvořák 3×)", "stálí kmotři: petr dvorak" in out, out)
        over("rodiny: opakované jméno Anna", "jméno už má dítě" in out, out)
        over("rodiny: mezera 5 let", "mezera 5 let" in out, out)
        over("rodiny: stálý kmotr Petr Dvořák", "stálí kmotři: petr dvorak" in out, out)
        over("rodiny: stejnojmenný pár u kotvy i kandidáta B", "má děti u:" in out, out)

        out = spust(tmp, "stav", "matej_32", "A", "potvrzen", "kmotr Krejčí")
        spust(tmp, "stav", "matej_32", "B", "potvrzen", "omylem")
        out = spust(tmp, "stav", "matej_32", "B", "potvrzen", "omylem")
        over("varování, když jsou potvrzení dva kandidáti", "potvrzený má být jen jeden" in out, out)

        out = spust(tmp, "seznam")
        over("seznam případů", "matej_32" in out, out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    chyb = sum(1 for _, ok in VYSLEDKY if not ok)
    print(f"\n{len(VYSLEDKY) - chyb}/{len(VYSLEDKY)} v pořádku")
    sys.exit(1 if chyb else 0)


if __name__ == "__main__":
    main()
