"""Testy vazby osob na původní strom (fáze 2 exportu GEDCOM): ged_import.py --osoby / --ged-id, zapis.py ged,
kontrola.py.

Z kořene repozitáře:
  python3 -I tests/gedcom/test_ged_vazba.py
  (Windows: python -I -X utf8 tests/gedcom/test_ged_vazba.py)
Založí dočasné projekty přes novy_projekt.py a malý GEDCOM. Nic nestahuje.
"""
import os, shutil, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "skills", "rodokmen", "tools")
vysledky = []

STROM = """0 HEAD
1 CHAR UTF-8
0 @I1@ INDI
1 RIN MH:I1
1 _UID U1
1 NAME Petr /Novák/
1 BIRT
2 DATE 1980
1 FAMC @F1@
0 @I2@ INDI
1 _UID U2
1 NAME Josef Karel /Novák/
1 BIRT
2 DATE 12 MAR 1952
1 FAMS @F1@
1 FAMC @F2@
0 @I3@ INDI
1 _UID U3
1 NAME Eva /Nováková/
1 BIRT
2 DATE 1955
1 FAMS @F1@
0 @I4@ INDI
1 _UID U4
1 NAME František /Novák/
1 BIRT
2 DATE 1925
1 FAMS @F2@
0 @I5@ INDI
1 _UID U5
1 NAME Jana /Králová/
1 BIRT
2 DATE 1925
1 FAMS @F2@
0 @F1@ FAM
1 HUSB @I2@
1 WIFE @I3@
1 CHIL @I1@
0 @F2@ FAM
1 HUSB @I4@
1 WIFE @I5@
1 CHIL @I2@
0 TRLR
"""


def ok(nazev, podminka, detail=""):
    vysledky.append(bool(podminka))
    print(("OK   " if podminka else "CHYBA"), nazev, "" if podminka else detail)


def projekt(ukazka):
    d = os.path.join(tempfile.mkdtemp(prefix="gedvazba_"), "projekt")
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(TOOLS, "novy_projekt.py"), d]
                       + (["--ukazka"] if ukazka else []), capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    open(os.path.join(d, "dokumenty", "strom.ged"), "w", encoding="utf-8").write(STROM)
    return d


def spust(d, nastroj, *args):
    return subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(d, "tools", nastroj), *args],
                          capture_output=True, text=True, encoding="utf-8", cwd=d)


def osoby(d):
    ns = {}
    exec(open(os.path.join(d, "data", "osoby.py"), encoding="utf-8").read(), ns)
    return ns


def test_kostra():
    d = projekt(False)
    r = spust(d, "ged_import.py", "dokumenty/strom.ged", "Petr Novák", "--osoby")
    ns = {}
    try:
        exec(r.stdout, ns)
    except Exception as e:  # noqa: BLE001
        ns = {"P": {}, "chyba": e}
    P = ns.get("P", {})
    ok("--osoby: kostra je platný Python", P, r.stdout + r.stderr)
    ok("--osoby: ged a uid u každé osoby", P and all(P[k].get("ged") == f"@I{i}@" and P[k].get("uid") == f"U{i}"
                                                     for k, i in ((1, 1), (2, 2), (3, 3), (4, 4), (5, 5))), P)
    shutil.rmtree(os.path.dirname(d), ignore_errors=True)


def test_ged_id_ukazka():
    """Ukázka: osoby jako {…} s apostrofy. 1–3 sedí (Josef má ve stromu druhé jméno, Eva příjmení po sňatku),
    4 má jiný rok narození, 5 jiné jméno."""
    d = projekt(True)
    pred = osoby(d)["P"]
    r = spust(d, "ged_import.py", "dokumenty/strom.ged", "Petr Novák", "--ged-id")
    out = r.stdout
    ok("--ged-id: shody 1–3", r.returncode == 0 and "Shoda (3)" in out, out + r.stderr)
    nesedi = out.split("NESEDÍ", 1)[1] if "NESEDÍ" in out else ""
    ok("--ged-id: 4 (rok) a 5 (jméno) nesedí", "František" in nesedi and "Marie Králová" in nesedi, out)
    ok("--ged-id: nově zjištění předci vypsáni", "Nejsou ve stromu" in out and " 8" in out.split("Nejsou ve stromu")[1], out)
    ok("--ged-id bez --zapsat nic nemění", osoby(d)["P"] == pred)

    r = spust(d, "ged_import.py", "dokumenty/strom.ged", "Petr Novák", "--ged-id", "--zapsat")
    po = osoby(d)
    P = po["P"]
    ok("--zapsat: shody zapsány (ged + uid)", all(P[k].get("ged") == f"@I{k}@" and P[k].get("uid") == f"U{k}"
                                                  for k in (1, 2, 3)), {k: P[k] for k in (1, 2, 3)})
    ok("--zapsat: neshody nezapsány", "ged" not in P[4] and "ged" not in P[5])
    ok("--zapsat: jinak beze změny", all({x: y for x, y in P[k].items() if x not in ("ged", "uid")} == pred[k] for k in pred)
       and set(P) == set(pred))
    zdroj = open(os.path.join(d, "data", "osoby.py"), encoding="utf-8").read()
    ok("--zapsat: styl souboru zachován (apostrofy)", "'ged': '@I1@'" in zdroj, zdroj[:400])
    r = spust(d, "ged_import.py", "dokumenty/strom.ged", "Petr Novák", "--ged-id")
    ok("--ged-id podruhé: už mají správné ged", "Už mají správné ged: 3" in r.stdout and "Shoda (0)" in r.stdout, r.stdout)

    r = spust(d, "zapis.py", "ged", "4", "@I4@", "U4")
    ok("zapis.py ged: ruční vazba", r.returncode == 0 and osoby(d)["P"][4].get("ged") == "@I4@", r.stdout + r.stderr)
    r = spust(d, "zapis.py", "ged", "4", "I4")
    ok("zapis.py ged: špatný tvar ID odmítnut", r.returncode != 0 and osoby(d)["P"][4].get("ged") == "@I4@", r.stderr)
    r = spust(d, "zapis.py", "ged", "4", "@I4@", "U4")
    ok("zapis.py ged: stejná hodnota nic nezmění", r.returncode == 0 and "už má" in r.stdout, r.stdout)

    r = spust(d, "kontrola.py")
    ok("kontrola: osoby bez vazby jako informace", "informace:" in r.stdout and "bez vazby na původní strom" in r.stdout,
       r.stdout)
    spust(d, "zapis.py", "ged", "5", "@I4@")
    r = spust(d, "kontrola.py")
    ok("kontrola: stejné ged u dvou osob", "stejné ged @I4@" in r.stdout, r.stdout)
    shutil.rmtree(os.path.dirname(d), ignore_errors=True)


def test_ged_id_dict():
    """Osoby jako dict(…) (kostra z importu, vlastní projekty): pole přibude na konec dict(…)."""
    d = projekt(False)
    path = os.path.join(d, "data", "osoby.py")
    text = open(path, encoding="utf-8").read().replace(
        "P = {\n}", 'P = {\n 1: dict(n="Petr Novák", y="* 1980", st="fam", f=["* 1980"], r=[]),\n'
                    ' 2: dict(n="Josef Novák", y="* 1952", st="fam", f=["* 12. 3. 1952 Holice"], r=[]),\n}')
    open(path, "w", encoding="utf-8").write(text)
    r = spust(d, "ged_import.py", "dokumenty/strom.ged", "Petr Novák", "--ged-id", "--zapsat")
    P = osoby(d)["P"]
    zdroj = open(path, encoding="utf-8").read()
    ok("dict(…): ged a uid zapsány", P[1].get("ged") == "@I1@" and P[2].get("uid") == "U2", r.stdout + r.stderr)
    ok("dict(…): zapsáno jako klíčové argumenty", 'r=[], ged="@I1@", uid="U1")' in zdroj, zdroj)
    r = spust(d, "kontrola.py")
    ok("kontrola: všichni mají vazbu – bez informace", "bez vazby" not in r.stdout, r.stdout)
    shutil.rmtree(os.path.dirname(d), ignore_errors=True)


def indi(ged_text):
    import re
    return {m: b for m, b in ((re.match(r"0 (@I\d+@)", b)[1], b) for b in re.split(r"(?m)^(?=0 )", ged_text)
                              if re.match(r"0 @I\d+@ INDI", b))}


def test_rozdil():
    """Rozdílový export proti stromu: ukázka, vazba 1–3 zapsaná (4 a 5 nesedí → nové na obsazeném místě)."""
    d = projekt(True)
    r = spust(d, "ged_export.py", "--rozdil", "dokumenty/strom.ged", "--bez-obrazku")
    ok("--rozdil bez vazby ged odmítnut s radou", r.returncode != 0 and "--ged-id" in r.stderr, r.stderr)
    r = spust(d, "ged_export.py", "--se-zmenenymi", "--bez-obrazku")
    ok("--se-zmenenymi bez --rozdil odmítnuto", r.returncode != 0, r.stderr)
    spust(d, "ged_import.py", "dokumenty/strom.ged", "Petr Novák", "--ged-id", "--zapsat")
    P = osoby(d)["P"]

    r = spust(d, "ged_export.py", "--rozdil", "dokumenty/strom.ged", "--bez-obrazku")
    prac = os.path.join(d, "pracovni")
    ok("--rozdil: výstup pracovni/rozdil.ged a přehled rozdil_zmeny.md", r.returncode == 0
       and os.path.isfile(os.path.join(prac, "rozdil.ged")) and os.path.isfile(os.path.join(prac, "rozdil_zmeny.md")),
       r.stdout + r.stderr)
    ged = open(os.path.join(prac, "rozdil.ged"), encoding="utf-8").read()
    prehled = open(os.path.join(prac, "rozdil_zmeny.md"), encoding="utf-8").read()
    osoby_v = indi(ged)
    nove = {f"@I{k}@" for k, p in P.items() if not p.get("ged") and not p.get("n", "").startswith(("otec neuveden", "matka neuvedena"))}
    ok("--rozdil: osoba 1 (ve stromu, bez nových rodičů) v souboru není", "@I1@" not in osoby_v, sorted(osoby_v)[:10])
    ok("--rozdil: kotvy 2 a 3 (k nim se připojují noví rodiče) v souboru jsou", {"@I2@", "@I3@"} <= set(osoby_v))
    ok("--rozdil: všechny nové osoby v souboru", nove <= set(osoby_v), nove - set(osoby_v))
    ok("--rozdil: kotva i u chráněné osoby se jménem a daty ze stromu (vrací jen to, co strom má)",
       "1 NAME Josef Karel /Novák/" in osoby_v["@I2@"] and "2 DATE 12 MAR 1952" in osoby_v["@I2@"]
       and "KOTVA" in osoby_v["@I2@"] and "FAMC" in osoby_v["@I2@"], osoby_v["@I2@"])
    ok("--rozdil: nová chráněná osoba dál bez údajů", all("RESN privacy" in b for k, b in osoby_v.items()
       if k not in ("@I2@", "@I3@") and ("Žijící osoba" in b or "Chráněná osoba" in b)))
    ok("--rozdil: přehled – kotvy, nové, postup", "## 1. Kotvy" in prehled and "## 2. Nové osoby" in prehled
       and "Kontrola duplicit" in prehled and "--ged-id --zapsat" in prehled, prehled[:600])
    ok("--rozdil: nová osoba na obsazeném místě ve stromu (4 × František Novák, jiný rok)",
       "Ve stromu je na tomto místě František Novák" in prehled and "zapis.py ged 4 @I4@" in prehled, prehled)
    ok("--rozdil: souhrn hlásí obsazená místa", "na místě, kde strom už někoho má" in r.stdout, r.stdout)
    ok("--rozdil: přehled uvádí dvojice ID ke spojení", "spojit **ID " in prehled and "× ID 2**" in prehled, prehled)
    r = spust(d, "ged_export.py", "--rozdil", "dokumenty/strom.ged", "--bez-obrazku", "--prepsat", "--se-zmenenymi")
    prehled = open(os.path.join(prac, "rozdil_zmeny.md"), encoding="utf-8").read()
    ok("--se-zmenenymi: přehled uvádí, že změněné jsou v souboru", r.returncode == 0 and "– v souboru, spojit" in prehled,
       r.stdout + r.stderr)
    r = spust(d, "ged_export.py", "--rozdil", "dokumenty/strom.ged", "--bez-obrazku")
    ok("--rozdil: existující výstup bez --prepsat odmítnut", r.returncode != 0, r.stderr)
    shutil.rmtree(os.path.dirname(d), ignore_errors=True)


if __name__ == "__main__":
    test_kostra()
    test_ged_id_ukazka()
    test_ged_id_dict()
    test_rozdil()
    print(f"\n{sum(vysledky)}/{len(vysledky)} v pořádku")
    sys.exit(0 if all(vysledky) else 1)
