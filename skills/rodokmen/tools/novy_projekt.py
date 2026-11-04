#!/usr/bin/env python3
"""Založí nový projekt rodokmenu ze šablony skillu.

Použití: python3 <skill>/tools/novy_projekt.py <cílová složka> [--ukazka] [--hlidac | --bez-hlidace]
  --ukazka        nakopíruje i vymyšlená ukázková data (rodina Novákových), aby šel web hned vyzkoušet
  --hlidac        zapne hlídač sítě (hook v .claude/settings.json, tools/hlidac_site.py): zamítne příkazy,
                  které jdou na web archivu mimo brzdu tools/slusne.py; --bez-hlidace ho vypne

Vytvoří: data/ (prázdné kostry nebo ukázka), web/ (Astro web), tools/ (kopie nástrojů),
vyrezy/, zdroje/, dokumenty/, pracovni/, CLAUDE.md, .gitignore, .gitattributes (konce řádků LF i na Windows)
a .claude/launch.json (náhled v Claude desktop). Do .claude/settings.json doplní zákaz přímého curl/wget
(stahování z archivů jde přes brzdu tools/slusne.py); ostatní nastavení v souboru nechá beze změny.
Existující data nepřepisuje.
Do .skill_sablona/ uloží kopii šablony web/ a tools/, ze které projekt vznikl (patří do gitu s projektem).
Aktualizace staršího projektu (znovu spustit na stejnou složku) rozhodne o každém souboru web/ a tools/ podle
tří verzí (uložená šablona, projekt, nová šablona): neupravený soubor přepíše, vlastní úpravu nechá, když se šablona
nezměnila, a jinak sloučí po řádcích (git merge-file). Při konfliktu, bez gitu, u souboru přidaného projektem
i šablonou a u souboru smazaného v projektu, který šablona změnila, soubor nechá a novou verzi uloží do
pracovni/zaloha_<datum>/nova_sablona/ (s gitem i návrh se značkami konfliktů); hlásí ho, dokud změnu nepřevezmete.
Soubor, který šablona už nemá, přesune do pracovni/zaloha_<datum>/odstraneno/ (upravený nechá).
Projekt bez .skill_sablona/ (ze starší verze) přepíše a původní verze změněných souborů uloží do
pracovni/zaloha_<datum>/puvodni/.
"""
import json, os, shutil, subprocess, sys, tempfile, time
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def copy(src, out):
    if os.path.islink(out):   # nepsat přes symlink mimo projekt
        os.remove(out)
    shutil.copy2(src, out)


SKIP = ("node_modules", "dist", ".astro", "__pycache__")
SABLONA = ".skill_sablona"   # kopie šablony, ze které projekt vznikl (základ pro tříčestnou aktualizaci)


def copy_tree(src, dst):
    """Zkopíruje chybějící soubory."""
    for base, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SKIP]
        rel = os.path.relpath(base, src)
        os.makedirs(os.path.join(dst, rel), exist_ok=True)
        for f in files:
            new, out = os.path.join(base, f), os.path.join(dst, rel, f)
            if not os.path.lexists(out):
                copy(new, out)


def soubory(src):
    """Relativní cesty souborů šablony (bez závislostí a buildu)."""
    for base, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            yield os.path.relpath(os.path.join(base, f), src)


def cti(p):
    with open(p, "rb") as f:
        return f.read()


def zapis(p, data, mode_z=None):
    if os.path.islink(p):   # nepsat přes symlink mimo projekt
        os.remove(p)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(data)
    if mode_z:
        shutil.copymode(mode_z, p)


def lf(data):
    """Konce řádků LF – CRLF z gitu na Windows se nepočítá jako úprava (binární soubory beze změny)."""
    return data if b"\0" in data else data.replace(b"\r\n", b"\n")


def sloucit(nase, zaklad, nova):
    """Sloučí po řádcích přes `git merge-file`. Vrátí (výsledek, bez konfliktu); bez gitu nebo při chybě (None, False)."""
    git = shutil.which("git")
    if not git:
        return None, False
    d = tempfile.mkdtemp(prefix="slouceni_")
    try:
        cesty = [os.path.join(d, n) for n in ("projekt", "puvodni_sablona", "nova_sablona")]
        for p, data in zip(cesty, (nase, zaklad, nova)):
            zapis(p, data)
        r = subprocess.run([git, "merge-file", "-p", "-L", "projekt", "-L", "puvodni_sablona", "-L", "nova_sablona",
                            *cesty], capture_output=True)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    if not 0 <= r.returncode <= 127:   # chyba (např. binární soubor); 1–127 = počet konfliktů
        return None, False
    return r.stdout, r.returncode == 0


def aktualizuj(src, dst, cast, jmena, zaloha, vysl, stary):
    """Aktualizuje dst/cast podle tří verzí: původní šablona (dst/.skill_sablona/cast), projekt a nová šablona
    (soubory `jmena` ze src). Projde i soubory, které nová šablona už nemá. Uloženou šablonu posune jen tam, kde se
    nová verze do projektu dostala. stary=True: projekt bez .skill_sablona/. Výsledek přidá do vysl[kategorie]."""
    puvodni = os.path.join(dst, SABLONA, cast)
    for rel in sorted(set(jmena) | set(soubory(puvodni) if os.path.isdir(puvodni) else ())):
        new, out, puv = os.path.join(src, rel), os.path.join(dst, cast, rel), os.path.join(puvodni, rel)
        nova = cti(new) if rel in jmena else None
        if nova is not None and rel.endswith(".sh"):   # skill naklonovaný na Windows (core.autocrlf) má CRLF
            nova = nova.replace(b"\r\n", b"\n")
        nase = lf(cti(out)) if os.path.isfile(out) and not os.path.islink(out) else None
        zaklad = lf(cti(puv)) if os.path.isfile(puv) else None
        jmeno = cast + "/" + rel.replace(os.sep, "/")
        nova_zal = os.path.join(zaloha, "nova_sablona", cast, rel)   # při konfliktu sem nová verze, projekt zůstane
        if nova is None:   # šablona soubor odstranila
            if nase is not None and nase == zaklad:
                keep = os.path.join(zaloha, "odstraneno", cast, rel)
                os.makedirs(os.path.dirname(keep), exist_ok=True)
                shutil.move(out, keep)
                vysl["odstraneno"].append(jmeno)
            elif nase is not None:
                vysl["odstraneno_upraveno"].append(jmeno)
            os.remove(puv)
            continue
        if os.path.islink(out) or (nase is None and zaklad is None):   # symlink jen přepsat; nový soubor doplnit
            if os.path.lexists(out):
                vysl["prepsano"].append(jmeno)
            zapis(out, nova, new)
        elif nase is None:   # smazaný v projektu
            if zaklad == lf(nova):
                vysl["smazano"].append(jmeno)
                continue
            zapis(nova_zal, nova, new)
            vysl["konflikt"].append(jmeno + " (smazáno v projektu)")
            continue
        elif nase == lf(nova):
            pass
        elif nase == zaklad:   # bez vlastních úprav
            vysl["prepsano"].append(jmeno)
            zapis(out, nova, new)
        elif zaklad == lf(nova):   # šablona beze změny
            vysl["ponechano"].append(jmeno)
            continue
        elif zaklad is None and stary:   # projekt ze starší verze bez uložené šablony: přepsat, starou verzi zazálohovat
            keep = os.path.join(zaloha, "puvodni", cast, rel)
            os.makedirs(os.path.dirname(keep), exist_ok=True)
            shutil.copy2(out, keep)
            zapis(out, nova, new)
            vysl["zalohovano"].append(jmeno)
        elif zaklad is None:   # soubor přidal projekt i nová šablona
            zapis(nova_zal, nova, new)
            vysl["konflikt"].append(jmeno + " (nový v šabloně i v projektu)")
            continue
        else:
            sloucene, ok = sloucit(nase, zaklad, lf(nova))
            if not ok:
                zapis(nova_zal, nova, new)
                if sloucene is not None:
                    zapis(nova_zal + ".konflikt", sloucene)   # s gitem i návrh se značkami konfliktů
                vysl["konflikt"].append(jmeno)
                continue
            zapis(out, sloucene)
            vysl["slouceno"].append(jmeno)
        if zaklad != lf(nova) or not os.path.isfile(puv):   # nová verze je v projektu: posunout uloženou šablonu
            zapis(puv, nova, new)


SIT_ZAKAZ = ["Bash(curl:*)", "Bash(wget:*)"]   # stahování z archivů jen přes tools/slusne.py (curl přes něj jde)
# Hlídač spustit, jen když soubor existuje: chybějící skript by Python ukončil kódem 2 a ten by zablokoval každý příkaz.
# mimo Windows ne cestu s číslem verze (po aktualizaci Pythonu by zmizela); na Windows lomítka (projdou Git Bash i cmd)
KOD = ("import os,runpy;p=os.path.join(os.environ.get('CLAUDE_PROJECT_DIR','.'),'tools','hlidac_site.py');"
       "os.path.isfile(p) and runpy.run_path(p,run_name='__main__')")
PY = sys.executable.replace("\\", "/") if os.name == "nt" else "python3"
HLIDAC = f'"{PY}" -I -c "{KOD}"'   # tvar se shellem (macOS, Linux)
MATCHER = "Bash|PowerShell|Monitor"   # Monitor spouští příkaz v bashi stejně jako Bash


def _python_windows():
    """Python pro hook na Windows: z PATH (projde i projekt sdílený přes OneDrive na dvou počítačích), jinak plná cesta.
    Zástupce z Microsoft Store (WindowsApps) se nepočítá – bez nainstalovaného Pythonu jen otevře obchod."""
    p = shutil.which("python")
    return "python" if p and "windowsapps" not in p.lower() else sys.executable


def hook_hlidace():
    """Hook hlídače. Na Windows bez shellu (command + args): hooky tam běží v Git Bashi, nebo v PowerShellu, když
    Git Bash chybí – a tam by příkaz s uvozovkami byl chyba syntaxe a Claude Code by pak zamítal každý příkaz."""
    if os.name == "nt":
        return {"type": "command", "command": _python_windows(), "args": ["-I", "-X", "utf8", "-c", KOD], "timeout": 10}
    return {"type": "command", "command": HLIDAC, "timeout": 10}


def nastaveni(dst, hlidac):
    """Doplní do .claude/settings.json zákaz curl/wget; hlidac=True/False zapne/vypne hook, None nechá, jak je."""
    path = os.path.join(dst, ".claude", "settings.json")
    data = {}
    if os.path.exists(path):
        try:
            data = json.load(open(path, encoding="utf-8"))
        except ValueError:
            print(f"POZOR: {path} není platný JSON – nastavení brzdy jsem nedoplnil. Oprav ho a spusť znovu.")
            return
    puvodni = json.dumps(data, sort_keys=True)
    deny = data.setdefault("permissions", {}).setdefault("deny", [])
    deny += [r for r in SIT_ZAKAZ if r not in deny]
    pre = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
    nase = [h for h in pre if "hlidac_site.py" in json.dumps(h)]
    for h in nase:   # aktualizace projektu: hook obnovit (cesta k Pythonu i tvar se mohly změnit)
        h["matcher"] = MATCHER
        h["hooks"] = [hook_hlidace()]
    if hlidac is True and not nase:
        pre.append({"matcher": MATCHER, "hooks": [hook_hlidace()]})
    elif hlidac is False:
        pre[:] = [h for h in pre if h not in nase]
    if not pre:
        del data["hooks"]["PreToolUse"]
    if not data["hooks"]:
        del data["hooks"]
    if json.dumps(data, sort_keys=True) != puvodni:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
    zapnuty = any("hlidac_site.py" in json.dumps(h) for h in data.get("hooks", {}).get("PreToolUse", []))
    print("Hlídač sítě:", "zapnutý" if zapnuty else "vypnutý (zapnout: --hlidac)")


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        sys.exit(__doc__)
    dst = os.path.abspath(os.path.expanduser(sys.argv[1]))
    demo = "--ukazka" in sys.argv
    os.makedirs(dst, exist_ok=True)
    copy_tree(os.path.join(SKILL, "template", "ukazka" if demo else "data"), os.path.join(dst, "data"))
    if demo:
        for sub in ("vyrezy", "zdroje"):
            src = os.path.join(SKILL, "template", "ukazka_" + sub)
            if os.path.isdir(src):
                copy_tree(src, os.path.join(dst, sub))
    zaloha = os.path.join(dst, "pracovni", "zaloha_" + time.strftime("%Y%m%d-%H%M%S"))
    vysl = {k: [] for k in ("prepsano", "zalohovano", "slouceno", "ponechano", "smazano", "odstraneno",
                            "odstraneno_upraveno", "konflikt")}
    stary = not os.path.isdir(os.path.join(dst, SABLONA))   # projekt ze starší verze (nebo nový)
    sablona_webu = os.path.join(SKILL, "template", "web")
    aktualizuj(sablona_webu, dst, "web", sorted(soubory(sablona_webu)), zaloha, vysl, stary)
    tools = os.path.join(dst, "tools")
    os.makedirs(tools, exist_ok=True)
    nastroje = sorted(f for f in os.listdir(os.path.join(SKILL, "tools"))
                      if f.endswith((".py", ".sh")) and f != "novy_projekt.py")
    aktualizuj(os.path.join(SKILL, "tools"), dst, "tools", nastroje, zaloha, vysl, stary)
    for f in nastroje:   # i ponechaný vlastní .sh s CRLF: Git Bash by skript nespustil
        p = os.path.join(tools, f)
        if f.endswith(".sh") and os.path.isfile(p) and not os.path.islink(p):
            data = cti(p)
            if b"\r\n" in data:
                zapis(p, data.replace(b"\r\n", b"\n"))
    for d in ("vyrezy", "zdroje", "dokumenty", "pracovni"):
        os.makedirs(os.path.join(dst, d), exist_ok=True)
    os.makedirs(os.path.join(dst, ".claude"), exist_ok=True)
    for name in ("CLAUDE.md", ".gitignore", ".gitattributes", "poznamky_pro_skill.md", os.path.join(".claude", "launch.json")):
        out = os.path.join(dst, name)
        if not os.path.lexists(out):
            copy(os.path.join(SKILL, "template", name), out)
    nastaveni(dst, True if "--hlidac" in sys.argv else False if "--bez-hlidace" in sys.argv else None)
    with open(os.path.join(dst, ".skill_verze"), "w", encoding="utf-8") as f:   # SKILL.md podle něj nabídne aktualizaci
        f.write(open(os.path.join(SKILL, "VERZE"), encoding="utf-8").read())
    print("Projekt připraven:", dst)
    for k, popis in (("prepsano", "Přepsáno novou verzí (bez vlastních úprav)"),
                     ("zalohovano", "Přepsáno, původní verze je v " + os.path.join(zaloha, "puvodni")
                      + " (projekt neměl uloženou šablonu – vlastní úpravy převezměte ze zálohy)"),
                     ("slouceno", "Sloučeno (vlastní úpravy i změny šablony)"),
                     ("ponechano", "Ponecháno (vlastní úpravy, šablona beze změny)"),
                     ("smazano", "Smazáno v projektu, ponecháno smazané (šablona beze změny)"),
                     ("odstraneno", "Odstraněno (šablona ho už nemá), přesunuto do " + os.path.join(zaloha, "odstraneno")),
                     ("odstraneno_upraveno", "Šablona už nemá, ale v projektu je upravený – ponechán"),
                     ("konflikt", "Ke kontrole (soubor zůstal beze změny, nová verze je v "
                      + os.path.join(zaloha, "nova_sablona") + ", s gitem i návrh sloučení se značkami jako .konflikt;"
                      " hlásí se znovu, dokud změny šablony nepřevezmete)")):
        if vysl[k]:
            print(f"{popis}, {len(vysl[k])}:")
            for f in vysl[k]:
                print("  " + f)
    if any(f.startswith("web/") for k in ("prepsano", "zalohovano", "slouceno", "odstraneno") for f in vysl[k]):
        print("Ve web/ pak `npm install` a `npm run data`.")


if __name__ == "__main__":
    main()
