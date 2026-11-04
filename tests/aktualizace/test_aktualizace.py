"""Testy aktualizace projektu přes tools/novy_projekt.py: tříčestné rozhodnutí podle uložené šablony (.skill_sablona/).

Skript si v dočasné složce postaví malý falešný skill (template/ a tools/ s kopií novy_projekt.py), založí z něj
projekt, mění šablonu i projekt a spouští aktualizaci. Nic nestahuje, potřebuje jen Python (a git pro slučování).
Z kořene repozitáře:
  python3 -I tests/aktualizace/test_aktualizace.py skills/rodokmen
Na Windows `python -I -X utf8`. Skončí kódem 1, když některý případ selže.
"""
import glob, os, shutil, subprocess, sys, tempfile, traceback

SKILL = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "skills/rodokmen")
RADKY = [f"radek {i}" for i in range(1, 21)]


def zapis(p, text, nl="\n"):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline=nl) as f:
        f.write(text)


def cti(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def text(radky):
    return "\n".join(radky) + "\n"


def zmen(radky, i, novy):
    r = list(radky)
    r[i] = novy
    return r


def falesny_skill(koren):
    s = os.path.join(koren, "skill")
    os.makedirs(os.path.join(s, "tools"))
    shutil.copy2(os.path.join(SKILL, "tools", "novy_projekt.py"), os.path.join(s, "tools"))
    zapis(os.path.join(s, "VERZE"), "9.9.9\n")
    zapis(os.path.join(s, "tools", "nastroj.py"), text(RADKY))
    zapis(os.path.join(s, "tools", "skript.sh"), "#!/bin/sh\necho ahoj\n", nl="\r\n")   # skill z Windows s CRLF
    zapis(os.path.join(s, "template", "web", "src", "styl.css"), text(RADKY))
    zapis(os.path.join(s, "template", "web", "src", "index.astro"), text(RADKY))
    zapis(os.path.join(s, "template", "web", "node_modules", "x.js"), "nekopirovat\n")
    zapis(os.path.join(s, "template", "data", "STAV.md"), "# Stav\n")
    for n in ("CLAUDE.md", ".gitignore", ".gitattributes", "poznamky_pro_skill.md", os.path.join(".claude", "launch.json")):
        zapis(os.path.join(s, "template", n), "{}\n" if n.endswith(".json") else "x\n")
    return s


def spust(skill, projekt, env=None):
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(skill, "tools", "novy_projekt.py"), projekt],
                       capture_output=True, encoding="utf-8", env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout


def sekce(vystup, zacatek):
    """Soubory vypsané pod řádkem, který začíná `zacatek` (odsazené řádky až do dalšího neodsazeného)."""
    radky, uvnitr, sez = vystup.splitlines(), False, []
    for r in radky:
        if r.startswith(zacatek):
            uvnitr = True
        elif uvnitr and r.startswith("  "):
            sez.append(r.strip())
        else:
            uvnitr = False
    return sez


def zalohy(projekt, *cesta):
    return glob.glob(os.path.join(projekt, "pracovni", "zaloha_*", *cesta))


def pripady(koren):
    s = falesny_skill(koren)
    p = os.path.join(koren, "projekt")
    sab = lambda *c: os.path.join(s, "template", "web", *c)
    proj = lambda *c: os.path.join(p, *c)

    # 1. nový projekt: uloží se přesné kopie šablony, bez node_modules a bez novy_projekt.py; .sh má LF
    spust(s, p)
    assert cti(proj(".skill_sablona", "web", "src", "styl.css")) == text(RADKY)
    assert cti(proj(".skill_sablona", "tools", "nastroj.py")) == text(RADKY)
    assert not os.path.exists(proj(".skill_sablona", "web", "node_modules"))
    assert not os.path.exists(proj(".skill_sablona", "tools", "novy_projekt.py"))
    assert not os.path.exists(proj("tools", "novy_projekt.py"))
    assert cti(proj("tools", "skript.sh")) == "#!/bin/sh\necho ahoj\n"
    assert cti(proj(".skill_sablona", "tools", "skript.sh")) == "#!/bin/sh\necho ahoj\n"
    yield "nový projekt uloží šablonu do .skill_sablona/"

    # 2. neupravený soubor, šablona se změnila → přepsat bez zálohy
    nove = zmen(RADKY, 0, "radek 1 z nove sablony")
    zapis(sab("src", "styl.css"), text(nove))
    out = spust(s, p)
    assert cti(proj("web", "src", "styl.css")) == text(nove), out
    assert "web/src/styl.css" in sekce(out, "Přepsáno"), out
    assert not zalohy(p, "*", "web", "src", "styl.css"), out
    assert cti(proj(".skill_sablona", "web", "src", "styl.css")) == text(nove)
    yield "neupravený soubor se přepíše novou šablonou"

    # 3. upravený soubor, šablona beze změny → nechat
    vlastni = zmen(nove, 10, "radek 11 vlastni uprava")
    zapis(proj("web", "src", "styl.css"), text(vlastni))
    out = spust(s, p)
    assert cti(proj("web", "src", "styl.css")) == text(vlastni), out
    assert "web/src/styl.css" in sekce(out, "Ponecháno"), out
    yield "vlastní úprava zůstane, když se šablona nezměnila"

    # 4. upravený soubor, šablona změněná jinde → sloučit obě změny
    nove2 = zmen(nove, 19, "radek 20 z dalsi sablony")
    zapis(sab("src", "styl.css"), text(nove2))
    out = spust(s, p)
    assert cti(proj("web", "src", "styl.css")) == text(zmen(vlastni, 19, "radek 20 z dalsi sablony")), out
    assert "web/src/styl.css" in sekce(out, "Sloučeno"), out
    yield "nepřekrývající se změny se sloučí"

    # 5. upravený soubor, šablona změněná na stejném řádku → nechat projekt, novou verzi do zálohy, vypsat ke kontrole
    pred = cti(proj("web", "src", "styl.css"))
    zapis(sab("src", "styl.css"), text(zmen(nove2, 10, "radek 11 jinak v sablone")))
    out = spust(s, p)
    assert cti(proj("web", "src", "styl.css")) == pred, out
    assert "web/src/styl.css" in sekce(out, "Ke kontrole"), out
    nova = zalohy(p, "nova_sablona", "web", "src", "styl.css")
    assert nova and cti(nova[0]) == text(zmen(nove2, 10, "radek 11 jinak v sablone")), out
    yield "konflikt nechá projekt, novou verzi uloží do zálohy a vypíše"

    # 6. bez gitu v PATH se nesloučí ani nepřekrývající se změny: projekt zůstane a soubor je ke kontrole
    pred = cti(proj("web", "src", "styl.css"))
    zapis(sab("src", "styl.css"), text(zmen(zmen(nove2, 10, "radek 11 jinak v sablone"), 0, "radek 1 bez gitu")))
    out = spust(s, p, env={**os.environ, "PATH": os.path.dirname(sys.executable)})
    assert cti(proj("web", "src", "styl.css")) == pred, out
    assert "web/src/styl.css" in sekce(out, "Ke kontrole"), out
    yield "bez gitu: projekt zůstane, soubor ke kontrole"

    # 7. projekt s CRLF (git na Windows), obsahem stejný jako šablona → bere se jako neupravený
    zapis(proj("web", "src", "index.astro"), text(RADKY), nl="\r\n")
    zapis(sab("src", "index.astro"), text(zmen(RADKY, 5, "radek 6 novy")))
    out = spust(s, p)
    assert cti(proj("web", "src", "index.astro")) == text(zmen(RADKY, 5, "radek 6 novy")), out
    assert "web/src/index.astro" in sekce(out, "Přepsáno"), out
    yield "konce řádků CRLF se nepočítají jako vlastní úprava"

    # 8. starý projekt bez .skill_sablona/: přepsat jako dřív, ale zálohovat i tools/
    shutil.rmtree(proj(".skill_sablona"))
    zapis(proj("tools", "nastroj.py"), text(zmen(RADKY, 3, "radek 4 vlastni")))
    zapis(os.path.join(s, "tools", "nastroj.py"), text(zmen(RADKY, 15, "radek 16 novy")))
    out = spust(s, p)
    assert cti(proj("tools", "nastroj.py")) == text(zmen(RADKY, 15, "radek 16 novy")), out
    zal = zalohy(p, "puvodni", "tools", "nastroj.py")
    assert zal and cti(zal[0]) == text(zmen(RADKY, 3, "radek 4 vlastni")), out
    assert "tools/nastroj.py" in sekce(out, "Přepsáno, původní verze"), out
    assert os.path.isfile(proj(".skill_sablona", "tools", "nastroj.py"))
    yield "starý projekt bez uložené šablony: tools/ se zálohují"


def main():
    koren = tempfile.mkdtemp(prefix="test_aktualizace_")
    ok = 0
    try:
        for popis in pripady(koren):
            ok += 1
            print("  [OK]", popis)
    except Exception:   # i chybějící soubor je selhání případu
        print("  [CHYBA] případ", ok + 1, "\n", traceback.format_exc())
    finally:
        shutil.rmtree(koren, ignore_errors=True)
    print(f"== aktualizace: {ok} z 8 správně")
    sys.exit(0 if ok == 8 else 1)


if __name__ == "__main__":
    main()
