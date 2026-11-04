"""Testy aktualizace projektu přes tools/novy_projekt.py: tříčestné rozhodnutí podle uložené šablony (.skill_sablona/).

Skript si v dočasné složce postaví malý falešný skill (template/ a tools/ s kopií novy_projekt.py), založí z něj
projekt, mění šablonu i projekt a spouští aktualizaci. Nic nestahuje, potřebuje jen Python (a git pro slučování).
Z kořene repozitáře:
  python3 -I tests/aktualizace/test_aktualizace.py skills/rodokmen
Na Windows `python -I -X utf8`. Skončí kódem 1, když některý případ selže.
"""
import glob, os, shutil, subprocess, sys, tempfile, time, traceback

SKILL = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "skills/rodokmen")
RADKY = [f"radek {i}" for i in range(1, 21)]
POCET = 20   # počet případů v pripady()
PRESKOCENO = "přeskočeno: "   # případ, který tu nejde vyzkoušet (počítá se zvlášť)


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
    for n in ("index.astro", "uvod.astro", "zrus.astro", "mapa.astro", os.path.join("slozka", "x.astro")):
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

    # 6b. --vyreseno po ručním sloučení uloží jako základ návrh, který uživatel dostal (A), ne mezitím novější šablonu
    #     (B); další aktualizace pak doplní změnu z B
    navrh = zmen(nove2, 10, "radek 11 jinak v sablone")
    zapis(sab("src", "styl.css"), text(zmen(navrh, 14, "radek 15 sablona B")))   # skill se mezitím posunul
    rucne = zmen(zmen(vlastni, 19, "radek 20 z dalsi sablony"), 10, "radek 11 vlastni + jinak")
    zapis(proj("web", "src", "styl.css"), text(rucne))
    out = spust(s, p, "--vyreseno", "web/src/styl.css")
    assert cti(proj("web", "src", "styl.css")) == text(rucne), out
    assert cti(proj(".skill_sablona", "web", "src", "styl.css")) == text(navrh), out
    cekajici = proj(".skill_sablona", "cekajici.json")   # prázdný záznam se smaže
    assert not os.path.exists(cekajici) or "web/src/styl.css" not in cti(cekajici), out
    out = spust(s, p)
    assert "web/src/styl.css" not in sekce(out, "Ke kontrole"), out
    assert "web/src/styl.css" in sekce(out, "Sloučeno"), out
    assert cti(proj("web", "src", "styl.css")) == text(zmen(rucne, 14, "radek 15 sablona B")), out
    yield "--vyreseno uloží zaznamenaný návrh, novější šablona se pak sloučí"

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

    # 10. šablona soubor odstranila: nic nemazat ani nepřesouvat, jen hlásit (neupravený i upravený)
    zapis(proj("web", "src", "zrus.astro"), text(zmen(RADKY, 4, "radek 5 vlastni")))
    os.remove(os.path.join(s, "tools", "stary.py"))
    os.remove(sab("src", "zrus.astro"))
    for _ in range(2):
        out = spust(s, p)
        assert cti(proj("tools", "stary.py")) == "print('zrusim')\n", out
        assert os.path.isfile(proj(".skill_sablona", "tools", "stary.py")), out
        assert cti(proj("web", "src", "zrus.astro")) == text(zmen(RADKY, 4, "radek 5 vlastni")), out
        assert {"tools/stary.py", "web/src/zrus.astro"} <= set(sekce(out, "Šablona už nemá")), out
    assert not zalohy(p, "odstraneno"), out
    yield "soubor odstraněný ze šablony zůstane a hlásí se"

    # 10b. --vyreseno u souboru, který šablona už nemá, smaže jen základ; bez záznamu konfliktu uloží aktuální šablonu
    out = spust(s, p, "--vyreseno", "web/src/zrus.astro", "--vyreseno", "tools/stary.py")
    assert not os.path.exists(proj(".skill_sablona", "web", "src", "zrus.astro")), out
    assert not os.path.exists(proj(".skill_sablona", "tools", "stary.py")), out
    out = spust(s, p)
    assert not set(sekce(out, "Šablona už nemá")) & {"tools/stary.py", "web/src/zrus.astro"}, out
    assert cti(proj("web", "src", "zrus.astro")) == text(zmen(RADKY, 4, "radek 5 vlastni")), out
    assert os.path.isfile(proj("tools", "stary.py")), out
    out = spust(s, p, "--vyreseno", "web/src/index.astro")
    assert "není zaznamenaný" in out, out
    yield "odstranění ze šablony se hlásí, dokud není vyřešené"

    # 10c. složka v projektu, kde má nová šablona soubor: nespadnout, nic nepřepsat, hlásit
    os.remove(sab("src", "slozka", "x.astro"))
    os.rmdir(sab("src", "slozka"))
    zapis(sab("src", "slozka"), "teď soubor\n")
    out = spust(s, p)
    assert "POZOR" in out, out
    assert os.path.isfile(proj("web", "src", "slozka", "x.astro")), out
    assert any(f.startswith("web/src/slozka") for f in sekce(out, "Ke kontrole")), out
    yield "složka místo souboru se ohlásí"

    # 10d. přejmenování jen ve velikosti písmen (Windows, macOS): jeden soubor, nezapisovat dvakrát, hlásit
    if os.name == "nt" or sys.platform == "darwin":
        os.remove(sab("src", "mapa.astro"))
        zapis(sab("src", "Mapa.astro"), text(zmen(RADKY, 0, "radek 1 Mapa")))
        out = spust(s, p)
        assert os.path.isfile(proj("web", "src", "mapa.astro")), out
        assert cti(proj("web", "src", "mapa.astro")) == text(RADKY), out
        assert os.path.isfile(proj(".skill_sablona", "web", "src", "mapa.astro")), out
        assert any(f.lower().startswith("web/src/mapa.astro") for f in sekce(out, "Ke kontrole")), out
        yield "přejmenování jen ve velikosti písmen se ohlásí"
    else:
        yield PRESKOCENO + "velikost písmen (souborový systém ji rozlišuje)"

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

    # 12b. package-lock.json mění npm install: změněný jen v projektu zůstane, změněný i v šabloně se nahradí (bez slučování)
    zapis(sab("package-lock.json"), text(RADKY))
    spust(s, p)
    zapis(proj("web", "package-lock.json"), text(zmen(RADKY, 5, "radek 6 od npm")))
    out = spust(s, p)
    assert cti(proj("web", "package-lock.json")) == text(zmen(RADKY, 5, "radek 6 od npm")), out
    zapis(sab("package-lock.json"), text(zmen(RADKY, 18, "radek 19 nova sablona")))
    out = spust(s, p)
    assert cti(proj("web", "package-lock.json")) == text(zmen(RADKY, 18, "radek 19 nova sablona")), out
    assert not any("package-lock" in f for f in sekce(out, "Ke kontrole")), out
    zal = zalohy(p, "puvodni", "web", "package-lock.json")
    assert zal and cti(zal[-1]) == text(zmen(RADKY, 5, "radek 6 od npm")), out
    yield "package-lock.json se neslučuje: nový ze šablony, starý v záloze"

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
            odkaz = None
    if odkaz:
        try:
            out = spust(s, p)
            assert cti(os.path.join(venku, "poznamky.txt")) == "cizi\n", out
            assert sorted(os.listdir(venku)) == ["poznamky.txt"], out
            assert "POZOR" in out, out
        finally:
            os.unlink(odkaz) if os.path.islink(odkaz) else os.rmdir(odkaz)
        yield "odkaz z .skill_sablona/ mimo projekt se odmítne"
    else:
        yield PRESKOCENO + "odkaz na složku nejde vytvořit (chybí oprávnění)"

    # 14. záloha starého projektu: cíl zálohy je předem odkaz ven (soubor symlink, jinak junction) → nezapsat, nepřepsat
    shutil.rmtree(proj(".skill_sablona"))
    zapis(proj("tools", "nastroj.py"), text(zmen(RADKY, 6, "radek 7 vlastni")))
    zapis(os.path.join(s, "tools", "nastroj.py"), text(zmen(RADKY, 8, "radek 9 novy")))
    cil = os.path.join(venku, "cil.txt")
    zapis(cil, "cizi cil\n")
    odkazy, druh = [], None
    for z in zalohy(p):   # zálohy předchozích případů (mohou mít stejnou sekundu)
        shutil.rmtree(z)
    ted = time.time()
    for t in range(-1, 15):   # název zálohy má čas na sekundy – připravit odkazy pro nejbližší sekundy
        leaf = proj("pracovni", "zaloha_" + time.strftime("%Y%m%d-%H%M%S", time.localtime(ted + t)),
                    "puvodni", "tools", "nastroj.py")
        os.makedirs(os.path.dirname(leaf), exist_ok=True)
        try:
            if druh != "junction":
                os.symlink(cil, leaf)
                druh = "symlink"
            else:
                raise OSError
        except (OSError, NotImplementedError):
            try:
                import _winapi
                _winapi.CreateJunction(venku, leaf)
                druh = "junction"
            except (ImportError, OSError):
                break
        odkazy.append(leaf)
    if odkazy:
        out = spust(s, p)
        for leaf in odkazy:
            os.unlink(leaf) if os.path.islink(leaf) else os.rmdir(leaf)
        assert cti(cil) == "cizi cil\n", out
        assert sorted(os.listdir(venku)) == ["cil.txt", "poznamky.txt"], out
        assert "POZOR" in out, out
        assert cti(proj("tools", "nastroj.py")) == text(zmen(RADKY, 6, "radek 7 vlastni")), out
        yield f"cíl zálohy jako odkaz ({druh}) se odmítne"
    else:
        yield PRESKOCENO + "odkaz na místě zálohy nejde vytvořit (chybí oprávnění)"


def main():
    koren = tempfile.mkdtemp(prefix="test_aktualizace_")
    ok = preskoceno = 0
    try:
        for popis in pripady(koren):
            if popis.startswith(PRESKOCENO):
                preskoceno += 1
                print("  [PŘESKOČENO]", popis[len(PRESKOCENO):])
            else:
                ok += 1
                print("  [OK]", popis)
    except Exception:   # i chybějící soubor je selhání případu
        print("  [CHYBA] případ", ok + preskoceno + 1, "\n", traceback.format_exc())
    finally:
        shutil.rmtree(koren, ignore_errors=True)
    print(f"== aktualizace: {ok} z {POCET} správně, přeskočeno {preskoceno}")
    sys.exit(0 if ok + preskoceno == POCET else 1)


if __name__ == "__main__":
    main()
