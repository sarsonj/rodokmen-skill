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
POCET = 16   # počet případů v pripady()


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
    zapis(os.path.join(s, "tools", "stary.py"), "print('zrusim')\n")
    for n in ("index.astro", "uvod.astro", "zrus.astro"):
        zapis(os.path.join(s, "template", "web", "src", n), text(RADKY))
    zapis(os.path.join(s, "template", "web", "node_modules", "x.js"), "nekopirovat\n")
    zapis(os.path.join(s, "template", "data", "STAV.md"), "# Stav\n")
    for n in ("CLAUDE.md", ".gitignore", ".gitattributes", "poznamky_pro_skill.md", os.path.join(".claude", "launch.json")):
        zapis(os.path.join(s, "template", n), "{}\n" if n.endswith(".json") else "x\n")
    return s


def spust(skill, projekt, *volby, env=None):
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(skill, "tools", "novy_projekt.py"), projekt,
                        *volby], capture_output=True, encoding="utf-8", env=env)
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
    return sorted(glob.glob(os.path.join(projekt, "pracovni", "zaloha_*", *cesta)))   # poslední je nejnovější


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
    assert nova and cti(nova[-1]) == text(zmen(nove2, 10, "radek 11 jinak v sablone")), out
    yield "konflikt nechá projekt, novou verzi uloží do zálohy a vypíše"

    # 6. nevyřešený konflikt se při dalším spuštění hlásí znovu (uložená šablona se neposune)
    out = spust(s, p)
    assert cti(proj("web", "src", "styl.css")) == pred, out
    assert "web/src/styl.css" in sekce(out, "Ke kontrole"), out
    assert cti(proj(".skill_sablona", "web", "src", "styl.css")) == text(nove2), out
    yield "nevyřešený konflikt se hlásí znovu"

    # 6b. --vyreseno po ručním sloučení: uloží novou šablonu jako základ, projekt nechá; konflikt se už nehlásí
    out = spust(s, p, "--vyreseno", "web/src/styl.css")
    assert cti(proj("web", "src", "styl.css")) == pred, out
    assert cti(proj(".skill_sablona", "web", "src", "styl.css")) == text(zmen(nove2, 10, "radek 11 jinak v sablone"))
    out = spust(s, p)
    assert "web/src/styl.css" not in sekce(out, "Ke kontrole"), out
    assert cti(proj("web", "src", "styl.css")) == pred, out
    yield "--vyreseno ukončí hlášení konfliktu"

    # 7. bez gitu v PATH se nesloučí ani nepřekrývající se změny; s gitem se sloučí při dalším spuštění
    vlastni_uvod = zmen(RADKY, 2, "radek 3 vlastni")
    zapis(proj("web", "src", "uvod.astro"), text(vlastni_uvod))
    zapis(sab("src", "uvod.astro"), text(zmen(RADKY, 17, "radek 18 novy")))
    out = spust(s, p, env={**os.environ, "PATH": os.path.dirname(sys.executable)})
    assert cti(proj("web", "src", "uvod.astro")) == text(vlastni_uvod), out
    assert "web/src/uvod.astro" in sekce(out, "Ke kontrole"), out
    out = spust(s, p)
    assert cti(proj("web", "src", "uvod.astro")) == text(zmen(vlastni_uvod, 17, "radek 18 novy")), out
    assert "web/src/uvod.astro" in sekce(out, "Sloučeno"), out
    yield "bez gitu: soubor ke kontrole, s gitem se pak sloučí"

    # 8. soubor, který přidal uživatel i nová šablona → nechat uživatelův, verzi šablony do zálohy, hlásit i příště
    zapis(proj("web", "src", "fotky.astro"), "moje fotky\n")
    zapis(sab("src", "fotky.astro"), "fotky ze sablony\n")
    for _ in range(2):
        out = spust(s, p)
        assert cti(proj("web", "src", "fotky.astro")) == "moje fotky\n", out
        assert any(f.startswith("web/src/fotky.astro") for f in sekce(out, "Ke kontrole")), out
    nova = zalohy(p, "nova_sablona", "web", "src", "fotky.astro")
    assert nova and cti(nova[-1]) == "fotky ze sablony\n", out
    yield "nový soubor v šabloně i v projektu: zůstane uživatelův"

    # 8b. --vyreseno u souboru přidaného projektem i šablonou
    spust(s, p, "--vyreseno", "web/src/fotky.astro")
    out = spust(s, p)
    assert not any(f.startswith("web/src/fotky.astro") for f in sekce(out, "Ke kontrole")), out
    assert cti(proj("web", "src", "fotky.astro")) == "moje fotky\n", out
    yield "--vyreseno u souboru přidaného projektem i šablonou"

    # 9. soubor smazaný v projektu: nevrátit; změní-li se šablona, novou verzi jen do zálohy a hlásit
    os.remove(proj("web", "src", "uvod.astro"))
    out = spust(s, p)
    assert not os.path.exists(proj("web", "src", "uvod.astro")), out
    assert "web/src/uvod.astro" in sekce(out, "Smazáno v projektu"), out
    zapis(sab("src", "uvod.astro"), text(zmen(RADKY, 0, "radek 1 po smazani")))
    out = spust(s, p)
    assert not os.path.exists(proj("web", "src", "uvod.astro")), out
    assert any(f.startswith("web/src/uvod.astro") for f in sekce(out, "Ke kontrole")), out
    nova = zalohy(p, "nova_sablona", "web", "src", "uvod.astro")
    assert nova and cti(nova[-1]) == text(zmen(RADKY, 0, "radek 1 po smazani")), out
    yield "smazaný soubor se nevrátí"

    # 10. šablona soubor odstranila: neupravený přesunout do zálohy, upravený nechat a hlásit
    zapis(proj("web", "src", "zrus.astro"), text(zmen(RADKY, 4, "radek 5 vlastni")))
    os.remove(os.path.join(s, "tools", "stary.py"))
    os.remove(sab("src", "zrus.astro"))
    out = spust(s, p)
    assert not os.path.exists(proj("tools", "stary.py")), out
    assert not os.path.exists(proj(".skill_sablona", "tools", "stary.py")), out
    zal = zalohy(p, "odstraneno", "tools", "stary.py")
    assert zal and cti(zal[-1]) == "print('zrusim')\n", out
    assert "tools/stary.py" in sekce(out, "Odstraněno"), out
    assert cti(proj("web", "src", "zrus.astro")) == text(zmen(RADKY, 4, "radek 5 vlastni")), out
    assert "web/src/zrus.astro" in sekce(out, "Šablona už nemá"), out
    yield "soubor odstraněný ze šablony: neupravený do zálohy, upravený zůstane"

    # 10b. upravený soubor, který šablona už nemá, se hlásí dál, dokud ho --vyreseno nepřevezme jako vlastní
    out = spust(s, p)
    assert "web/src/zrus.astro" in sekce(out, "Šablona už nemá"), out
    spust(s, p, "--vyreseno", "web/src/zrus.astro")
    assert not os.path.exists(proj(".skill_sablona", "web", "src", "zrus.astro"))
    out = spust(s, p)
    assert "web/src/zrus.astro" not in sekce(out, "Šablona už nemá"), out
    assert cti(proj("web", "src", "zrus.astro")) == text(zmen(RADKY, 4, "radek 5 vlastni")), out
    yield "odstranění ze šablony se hlásí, dokud není vyřešené"

    # 11. projekt s CRLF (git na Windows), obsahem stejný jako šablona → bere se jako neupravený
    zapis(proj("web", "src", "index.astro"), text(RADKY), nl="\r\n")
    zapis(sab("src", "index.astro"), text(zmen(RADKY, 5, "radek 6 novy")))
    out = spust(s, p)
    assert cti(proj("web", "src", "index.astro")) == text(zmen(RADKY, 5, "radek 6 novy")), out
    assert "web/src/index.astro" in sekce(out, "Přepsáno"), out
    yield "konce řádků CRLF se nepočítají jako vlastní úprava"

    # 12. starý projekt bez .skill_sablona/: přepsat jako dřív, ale zálohovat i tools/
    shutil.rmtree(proj(".skill_sablona"))
    zapis(proj("tools", "nastroj.py"), text(zmen(RADKY, 3, "radek 4 vlastni")))
    zapis(os.path.join(s, "tools", "nastroj.py"), text(zmen(RADKY, 15, "radek 16 novy")))
    out = spust(s, p)
    assert cti(proj("tools", "nastroj.py")) == text(zmen(RADKY, 15, "radek 16 novy")), out
    zal = zalohy(p, "puvodni", "tools", "nastroj.py")
    assert zal and cti(zal[-1]) == text(zmen(RADKY, 3, "radek 4 vlastni")), out
    assert "tools/nastroj.py" in sekce(out, "Přepsáno, původní verze"), out
    assert os.path.isfile(proj(".skill_sablona", "tools", "nastroj.py"))
    yield "starý projekt bez uložené šablony: tools/ se zálohují"

    # 13. .skill_sablona/tools jako odkaz (symlink, na Windows junction) mimo projekt: nic venku nesmazat ani nezapsat
    venku = os.path.join(koren, "venku")
    zapis(os.path.join(venku, "poznamky.txt"), "cizi\n")
    shutil.rmtree(proj(".skill_sablona", "tools"))
    odkaz = proj(".skill_sablona", "tools")
    try:
        os.symlink(venku, odkaz, target_is_directory=True)
    except (OSError, NotImplementedError):
        try:
            import _winapi
            _winapi.CreateJunction(venku, odkaz)
        except (ImportError, OSError):
            print("  [PŘESKOČENO] odkaz na složku nejde vytvořit (chybí oprávnění)")
            yield "odkaz mimo projekt (přeskočeno)"
            return
    try:
        out = spust(s, p)
        assert cti(os.path.join(venku, "poznamky.txt")) == "cizi\n", out
        assert sorted(os.listdir(venku)) == ["poznamky.txt"], out
        assert "POZOR" in out, out
    finally:
        os.unlink(odkaz) if os.path.islink(odkaz) else os.rmdir(odkaz)
    yield "odkaz z .skill_sablona/ mimo projekt se odmítne"


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
    print(f"== aktualizace: {ok} z {POCET} správně")
    sys.exit(0 if ok == POCET else 1)


if __name__ == "__main__":
    main()
