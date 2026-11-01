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
Aktualizace staršího projektu (znovu spustit na stejnou složku): tools/ se přepíše vždy a soubory webu,
které se liší od nové šablony, taky – jejich staré verze se nejdřív uloží do pracovni/zaloha_web_<datum>/.
"""
import filecmp, json, os, shutil, sys, time
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def copy(src, out):
    if os.path.islink(out):   # nepsat přes symlink mimo projekt
        os.remove(out)
    shutil.copy2(src, out)


def copy_tree(src, dst, backup=None):
    """Zkopíruje chybějící soubory. S backup= přepíše i ty, které se liší, a starou verzi uloží do backup/."""
    changed = []
    for base, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "dist", ".astro", "__pycache__")]
        rel = os.path.relpath(base, src)
        os.makedirs(os.path.join(dst, rel), exist_ok=True)
        for f in files:
            new, out = os.path.join(base, f), os.path.join(dst, rel, f)
            if not os.path.lexists(out):
                copy(new, out)
            elif backup and (os.path.islink(out) or not filecmp.cmp(new, out, shallow=False)):
                keep = os.path.join(backup, os.path.normpath(os.path.join(rel, f)))
                os.makedirs(os.path.dirname(keep), exist_ok=True)
                if not os.path.islink(out):
                    shutil.copy2(out, keep)
                copy(new, out)
                changed.append(os.path.normpath(os.path.join(rel, f)))
    return changed


SIT_ZAKAZ = ["Bash(curl:*)", "Bash(wget:*)"]   # stahování z archivů jen přes tools/slusne.py (curl přes něj jde)
# Hlídač spustit, jen když soubor existuje: chybějící skript by Python ukončil kódem 2 a ten by zablokoval každý příkaz.
# mimo Windows ne cestu s číslem verze (po aktualizaci Pythonu by zmizela); na Windows lomítka (projdou Git Bash i cmd)
PY = sys.executable.replace("\\", "/") if os.name == "nt" else "python3"
HLIDAC = (f'"{PY}" -I -c "import os,runpy;p=os.path.join(os.environ.get(\'CLAUDE_PROJECT_DIR\',\'.\'),'
          f'\'tools\',\'hlidac_site.py\');os.path.isfile(p) and runpy.run_path(p,run_name=\'__main__\')"')


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
    for h in nase:   # aktualizace projektu: příkaz obnovit (cesta k Pythonu se mohla změnit)
        for x in h.get("hooks", []):
            x["command"] = HLIDAC
    if hlidac is True and not nase:
        pre.append({"matcher": "Bash|PowerShell", "hooks": [{"type": "command", "command": HLIDAC, "timeout": 10}]})
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
    web = os.path.join(dst, "web")
    backup = os.path.join(dst, "pracovni", "zaloha_web_" + time.strftime("%Y%m%d-%H%M%S"))
    changed = copy_tree(os.path.join(SKILL, "template", "web"), web, backup if os.path.isdir(web) else None)
    tools = os.path.join(dst, "tools")
    os.makedirs(tools, exist_ok=True)
    for f in os.listdir(os.path.join(SKILL, "tools")):
        if f.endswith((".py", ".sh")) and f != "novy_projekt.py":
            copy(os.path.join(SKILL, "tools", f), os.path.join(tools, f))   # nástroje vždy aktualizovat
            if f.endswith(".sh"):   # skill naklonovaný na Windows (core.autocrlf) má CRLF – Git Bash by skript nespustil
                p = os.path.join(tools, f)
                data = open(p, "rb").read()
                if b"\r\n" in data:
                    open(p, "wb").write(data.replace(b"\r\n", b"\n"))
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
    if changed:
        print(f"Web aktualizován na novou šablonu ({len(changed)} souborů). Původní verze jsou v {backup}:")
        for f in changed:
            print("  web/" + f)
        print("Pokud jste vzhled webu upravovali, převezměte úpravy ze zálohy. Pak `npm install` a `npm run data` ve web/.")


if __name__ == "__main__":
    main()
