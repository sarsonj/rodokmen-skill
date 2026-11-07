"""Tests for the Strom page data (template/web/scripts/strom.py) and the SIDE checks in tools/kontrola.py.

From the repository root:
  python3 -I tests/strom/test_strom.py skills/rodokmen
  (Windows: python -I -X utf8 …)
Every case builds its own temporary project with an invented family, copies the tested script into it and runs it.
Nothing is downloaded, standard library only.
"""
import json, os, shutil, subprocess, sys, tempfile

SKILL = os.path.abspath(sys.argv[1])
STROM = os.path.join(SKILL, "template", "web", "scripts", "strom.py")
KONTROLA = os.path.join(SKILL, "tools", "kontrola.py")
PY = [sys.executable, "-I", "-X", "utf8"]
RESULTS = []


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def person(k, name, years, father=None, mother=None):
    return dict(k=k, slug=name, name=name, years=years, sex="M" if k == 1 or k % 2 == 0 else "F", rel="", status="",
                st="fam", line=None, lineSlug=None, gen=0, facts=[], note="", records=[], father=father, mother=mother,
                docs=[])


SITE = dict(root="petr", aliases={}, lines={}, records=[], docs=[], people={
    "petr": person(1, "petr", "* 1980", father="josef", mother="eva"),
    "josef": person(2, "josef", "* 1952"),
    "eva": person(3, "eva", "* 1955"),
})


def strom(side):
    """Builds web/src/data/site.json + data/osoby.py, runs strom.py, returns the nodes of strom.json."""
    tmp = tempfile.mkdtemp(prefix="strom_")
    try:
        write(os.path.join(tmp, "web", "src", "data", "site.json"), json.dumps(SITE, ensure_ascii=False))
        write(os.path.join(tmp, "data", "osoby.py"), f"P = {{}}\nSIDE = {side!r}\n")
        os.makedirs(os.path.join(tmp, "web", "scripts"))
        shutil.copy(STROM, os.path.join(tmp, "web", "scripts", "strom.py"))
        r = subprocess.run(PY + [os.path.join(tmp, "web", "scripts", "strom.py")], capture_output=True, text=True,
                           encoding="utf-8")
        if r.returncode:
            return {"_error": r.stdout + r.stderr}
        with open(os.path.join(tmp, "web", "src", "generated", "strom.json"), encoding="utf-8") as f:
            return json.load(f)["nodes"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def kontrola(side):
    """Output of kontrola.py for a project with persons 1–3 and the given SIDE."""
    tmp = tempfile.mkdtemp(prefix="strom_kontrola_")
    try:
        P = {1: dict(n="Petr Novák", y="* 1980", st="fam", f=[]), 2: dict(n="Josef Novák", y="* 1952", st="fam", f=[]),
             3: dict(n="Eva Dvořáková", y="* 1955", st="fam", f=[])}
        write(os.path.join(tmp, "data", "osoby.py"), f"P = {P!r}\nSIDE = {side!r}\n")
        write(os.path.join(tmp, "data", "zaznamy.json"), "[]")
        write(os.path.join(tmp, "data", "prepisy.json"), "{}")
        os.makedirs(os.path.join(tmp, "tools"))
        shutil.copy(KONTROLA, os.path.join(tmp, "tools", "kontrola.py"))
        r = subprocess.run(PY + [os.path.join(tmp, "tools", "kontrola.py")], capture_output=True, text=True,
                           encoding="utf-8")
        return r.stdout + r.stderr
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def case(name, ok, detail=""):
    RESULTS.append(ok)
    print(("OK   " if ok else "CHYBA") + " " + name + ("" if ok else f"\n      {detail}"))


# --- strom.py ---------------------------------------------------------------------------------------------------
side = [
    dict(k=1, id="jana", n="Jana Nováková (* 1983)", t="Sestra Petra."),
    dict(k=1, id="pavel", rodice="otec", n="Pavel Novák (* 1975)", t="Nevlastní bratr – jen otec."),
    dict(k=1, id="tomas", v="manz", koho="jana", n="Tomáš Malý (* 1981)", t="Manžel Jany."),
    dict(k=1, id="ema", v="dite", koho="jana", n="Ema Malá (* 2010)", t="Dcera Jany a Tomáše."),
    dict(k=2, n="Karel Novák (1950–2001)", t="Bratr Josefa – bez id, do stromu se nekreslí."),
    dict(k=1, id="petr_pav", v="dite", koho="pavel", rodice="otec", n="Petr (Peter) Novák (* 2005)", t="Syn Pavla z jiného vztahu."),
    dict(k=1, id="olga", v="manz", koho="pavel", n="Olga (?)", t="Manželka Pavla, rodné příjmení neznámé."),
    dict(k=1, id="lida", v="dite", koho="pavel", n="Lída Nováková (* 2012)", t="Dcera Pavla a Olgy."),
]
n = strom(side)
case("strom.py doběhne", "_error" not in n, n.get("_error", ""))
if "_error" not in n:
    case("předci zůstanou a mají rodiče", n["petr"]["parents"] == ["josef", "eva"], n["petr"]["parents"])
    case("sourozenec bez v dostane oba rodiče předka", n["s-jana"]["parents"] == ["josef", "eva"], n["s-jana"]["parents"])
    case("rodice='otec' = jen otec", n["s-pavel"]["parents"] == ["josef"], n["s-pavel"]["parents"])
    case("v='manz' s koho = manželé oboustranně",
         n["s-tomas"]["spouses"] == ["s-jana"] and "s-tomas" in n["s-jana"]["spouses"], (n["s-tomas"], n["s-jana"]))
    case("v='dite' s koho = dítě obou manželů", sorted(n["s-ema"]["parents"]) == ["s-jana", "s-tomas"], n["s-ema"]["parents"])
    case("záznam bez id se nekreslí", not any(x["name"].startswith("Karel") for x in n.values()))
    case("jméno a roky z n", n["s-jana"]["name"] == "Jana Nováková" and n["s-jana"]["years"] == "* 1983",
         (n["s-jana"]["name"], n["s-jana"]["years"]))
    case("pohlaví podle koncovky", n["s-jana"]["sex"] == "F" and n["s-tomas"]["sex"] == "M")
    case("jméno se závorkou: roky jen z poslední závorky",
         n["s-petr_pav"]["name"] == "Petr (Peter) Novák" and n["s-petr_pav"]["years"] == "* 2005",
         (n["s-petr_pav"]["name"], n["s-petr_pav"]["years"]))
    case("závorka bez čísla patří ke jménu", n["s-olga"]["name"] == "Olga (?)" and n["s-olga"]["years"] == "",
         (n["s-olga"]["name"], n["s-olga"]["years"]))
    case("v='dite' s rodice = dítě jen osoby koho", n["s-petr_pav"]["parents"] == ["s-pavel"], n["s-petr_pav"]["parents"])
    case("v='dite' bez rodice = dítě obou manželů", sorted(n["s-lida"]["parents"]) == ["s-olga", "s-pavel"],
         n["s-lida"]["parents"])
    case("děti seřazené podle roku", n["josef"]["children"] == ["s-pavel", "petr", "s-jana"], n["josef"]["children"])
n0 = strom([])
case("prázdné SIDE: jen předci", "_error" not in n0 and sorted(n0) == ["eva", "josef", "petr"], n0)

# --- kontrola.py ------------------------------------------------------------------------------------------------
out = kontrola([dict(k=1, id="a", n="A", t=""), dict(k=1, id="a", n="B", t="")])
case("kontrola: dvakrát stejné id = chyba", "id 'a' je víckrát" in out, out)
out = kontrola([dict(k=1, id="a", v="manz", koho="neni", n="A", t="")])
case("kontrola: koho na neexistující id = chyba", "koho='neni'" in out, out)
out = kontrola([dict(k=1, id="a", v="bratr", n="A", t="")])
case("kontrola: neznámé v = upozornění", "neznámý vztah v='bratr'" in out, out)
out = kontrola([dict(k=1, v="manz", n="A", t="")])
case("kontrola: vztah bez id = upozornění", "chybí mu id" in out, out)
out = kontrola([dict(k=1, n="A", t="Bratr.")])
case("kontrola: starý formát bez id projde bez hlášky o Stromu", "Strom" not in out, out)

print(f"\n{sum(RESULTS)}/{len(RESULTS)} v pořádku")
sys.exit(0 if all(RESULTS) else 1)
