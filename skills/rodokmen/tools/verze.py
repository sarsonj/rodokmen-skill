#!/usr/bin/env python3
"""Kontrola verze na začátku konverzace: nainstalovaný skill × projekt × nejnovější vydání na GitHubu.
Použití: python3 -I <skill>/tools/verze.py [<složka projektu>]

GitHubu se ptá nejvýš jednou za 24 hodin (mezipaměť ~/.cache/rodokmen_verze.json, Windows %LOCALAPPDATA%),
bez sítě nebo při chybě se ho prostě nezeptá. Poslední řádek začíná „→“ a klíčovým slovem pro Clauda:
  NOVA_VERZE_SKILLU   na GitHubu je novější verze než nainstalovaný skill – ať uživatel aktualizuje skill
                      (projekt se pak aktualizuje z nového skillu, ne z GitHubu)
  AKTUALIZUJ_PROJEKT  nainstalovaný skill je novější než projekt – nabídni novy_projekt.py
  PROJEKT_NOVEJSI     projekt vznikl novějším skillem než ten nainstalovaný (stará kopie skillu) – projekt neměnit
  SKILL_NEZJISTEN     spuštěno z kopie v projektu a nainstalovaný skill se nenašel – verze skillu neověřena
  AKTUALNI            vše sedí
Kopie v tools/ projektu najde nainstalovaný skill sama (registr pluginů Claude Code, ~/.claude/skills/rodokmen).
Kód je vždy 0 (kontrola nesmí zastavit práci).
"""
import glob, json, os, re, sys, time, urllib.request
if sys.argv[1:2] in (["-h"], ["--help"]):   # nápověda místo kontroly (jinak by „--help“ bral jako složku projektu)
    print(__doc__.strip())
    sys.exit(0)   # kód vždy 0, viz výše
if len(sys.argv) > 1 and (sys.argv[1].startswith("-") or not os.path.isdir(sys.argv[1])):
    print(f"verze.py: „{sys.argv[1]}“ není složka projektu – zadej cestu ke složce projektu (nebo nic).")
    sys.exit(0)

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = os.environ.get("RODOKMEN_VERZE_URL", "https://api.github.com/repos/sarsonj/rodokmen-skill/releases/latest")
CACHE = os.path.join(os.environ.get("RODOKMEN_CACHE") or os.environ.get("LOCALAPPDATA")
                     or os.path.join(os.path.expanduser("~"), ".cache"), "rodokmen_verze.json")
DEN = 24 * 3600


def cislo(v):
    """„v0.10.0“ → (0, 10, 0); nesrozumitelná verze → None."""
    m = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", (v or "").strip())
    return tuple(int(x) for x in m.groups()) if m else None


def cti(cesta):
    try:
        with open(cesta, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


def github():
    """Nejnovější vydání na GitHubu (text verze) nebo None; nejvýš jeden dotaz za 24 hodin."""
    try:
        with open(CACHE, encoding="utf-8") as f:
            c = json.load(f)
        if time.time() - c.get("cas", 0) < DEN and cislo(c.get("verze")):
            return c["verze"]
    except (OSError, ValueError, AttributeError):
        pass
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "rodokmen-skill", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            verze = json.load(r).get("tag_name", "").lstrip("v")
    except Exception:
        return None
    if not cislo(verze):
        return None
    try:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with open(CACHE, "w", encoding="utf-8") as f:
            json.dump({"cas": time.time(), "verze": verze}, f)
    except OSError:
        pass
    return verze


def nainstalovany(projekt_dir):
    """Kopie v tools/ projektu nemá vedle sebe VERZE – najde nainstalovaný skill: plugin z registru Claude Code
    (pro tento projekt, jinak pro uživatele), nebo ručně nakopírovaný ~/.claude/skills/rodokmen. Vrátí (verze, cesta)."""
    cfg = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    projekt = os.path.realpath(projekt_dir) if projekt_dir else None
    try:
        with open(os.path.join(cfg, "plugins", "installed_plugins.json"), encoding="utf-8") as f:
            zaznamy = json.load(f).get("plugins", {}).get("rodokmen@rodokmen-skill", [])
    except (OSError, ValueError, AttributeError):
        zaznamy = []
    poradi = []
    for z in zaznamy if isinstance(zaznamy, list) else []:
        pp = z.get("projectPath")
        if pp and projekt and os.path.realpath(pp) == projekt:
            poradi.insert(0, z)                      # instalace pro tento projekt má přednost
        elif z.get("scope") == "user":
            poradi.append(z)
    for z in poradi:
        cesta = os.path.join(z.get("installPath", ""), "skills", "rodokmen")
        verze = cti(os.path.join(cesta, "VERZE")) or z.get("version")
        if cislo(verze):
            return verze, cesta
    rucne = os.path.join(cfg, "skills", "rodokmen")
    verze = cti(os.path.join(rucne, "VERZE"))
    if cislo(verze):
        return verze, rucne
    return desktop()


def desktop():
    """Skill u účtu v aplikaci Claude desktop (Windows %LOCALAPPDATA%\\Claude-Data\\claude_…\\rpm\\…\\plugin_…\\
    skills\\rodokmen, obdobně na macOSu) – nejvyšší nalezená verze, jinak (None, None)."""
    zaklady = [os.path.join(os.environ.get("LOCALAPPDATA", ""), "Claude-Data"),
               os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Claude-Data")]
    nalez = []
    for z in zaklady:
        if not os.path.isdir(z):
            continue
        for vzor in ("*/rpm/plugin_*", "*/rpm/*/plugin_*", "*/rpm/*/*/plugin_*"):
            for d in glob.glob(os.path.join(z, vzor, "skills", "rodokmen")):
                v = cti(os.path.join(d, "VERZE"))
                if cislo(v):
                    nalez.append((cislo(v), v, d))
    if not nalez:
        return None, None
    _, v, d = max(nalez)
    return v, d


def main():
    global SKILL
    skill = cti(os.path.join(SKILL, "VERZE"))
    if skill is None:   # spuštěno z kopie v tools/ projektu
        skill, nalezeny = nainstalovany(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(SKILL))
        if nalezeny:
            SKILL = nalezeny
    projekt_dir = sys.argv[1] if len(sys.argv) > 1 else None
    projekt = cti(os.path.join(projekt_dir, ".skill_verze")) if projekt_dir else None
    gh = github()

    print(f"Skill (nainstalovaný): {skill}")
    if projekt_dir:
        print(f"Projekt: {projekt or 'bez .skill_verze (starší než 0.4)'}")
    print(f"GitHub (nejnovější vydání): {gh or 'nezjištěno (bez sítě nebo GitHub neodpověděl)'}")

    s, p, g = cislo(skill), cislo(projekt), cislo(gh)
    if g and s and g > s:
        if os.sep + "plugins" + os.sep in SKILL:   # nainstalovaný jako plugin (…/.claude/plugins/…)
            jak = ("jako plugin: `claude plugin marketplace update rodokmen-skill` a `claude plugin update\n"
                   "  rodokmen@rodokmen-skill`, pak restart Claude Code (natrvalo: v /plugin zapnout automatické aktualizace;\n"
                   "  když příkaz `claude` nejde spustit, stejné příkazy jdou v Claude Code přes /plugin)")
        else:                                       # nakopírovaný ručně (~/.claude/skills/rodokmen …)
            jak = (f"ručně nakopírovaný skill ({SKILL}): stáhnout novou verzi z https://github.com/sarsonj/rodokmen-skill\n"
                   "  (Code → Download ZIP), složkou skills/rodokmen nahradit tu stávající a restartovat Claude")
        print(f"→ NOVA_VERZE_SKILLU: vyšla verze {gh}, nainstalovaný skill je {skill}. Řekni to uživateli jednou větou a poraď,\n"
              f"  jak skill aktualizovat – {jak}. Projekt aktualizuj až z nového skillu.")
    elif projekt_dir and p and s and p > s:
        print(f"→ PROJEKT_NOVEJSI: projekt je z verze {projekt}, nainstalovaný skill je starší ({skill}). Projekt neaktualizuj\n"
              "  (vrátil bys ho ke starší verzi); ať uživatel aktualizuje skill (viz README, část Instalace).")
    elif projekt_dir and s and (not p or s > p):
        print(f"→ AKTUALIZUJ_PROJEKT: skill {skill} je novější než projekt. Nabídni aktualizaci projektu:\n"
              f"  python3 -I {os.path.join(SKILL, 'tools', 'novy_projekt.py')} <složka projektu>")
    elif not s:
        print("→ SKILL_NEZJISTEN: nainstalovaný skill jsem nenašel, verzi skillu neporovnávám. Spusť kontrolu ze složky\n"
              "  skillu: python3 -I SKILL_DIR/tools/verze.py <složka projektu>")
    else:
        print("→ AKTUALNI")


if __name__ == "__main__":
    main()
