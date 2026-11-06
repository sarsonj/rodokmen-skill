#!/usr/bin/env python3
"""Kontrola verze na začátku konverzace: nainstalovaný skill × projekt × nejnovější vydání na GitHubu.
Použití: python3 -I <skill>/tools/verze.py [<složka projektu>]

GitHubu se ptá nejvýš jednou za 24 hodin (mezipaměť ~/.cache/rodokmen_verze.json, Windows %LOCALAPPDATA%),
bez sítě nebo při chybě se ho prostě nezeptá. Poslední řádek začíná „→“ a klíčovým slovem pro Clauda:
  NOVA_VERZE_SKILLU   na GitHubu je novější verze než nainstalovaný skill – ať uživatel aktualizuje skill
                      (projekt se pak aktualizuje z nového skillu, ne z GitHubu)
  AKTUALIZUJ_PROJEKT  nainstalovaný skill je novější než projekt – nabídni novy_projekt.py
  PROJEKT_NOVEJSI     projekt vznikl novějším skillem než ten nainstalovaný (stará kopie skillu) – projekt neměnit
  AKTUALNI            vše sedí
Kód je vždy 0 (kontrola nesmí zastavit práci).
"""
import json, os, re, sys, time, urllib.request

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


def main():
    skill = cti(os.path.join(SKILL, "VERZE"))
    projekt_dir = sys.argv[1] if len(sys.argv) > 1 else None
    projekt = cti(os.path.join(projekt_dir, ".skill_verze")) if projekt_dir else None
    gh = github()

    print(f"Skill (nainstalovaný): {skill}")
    if projekt_dir:
        print(f"Projekt: {projekt or 'bez .skill_verze (starší než 0.4)'}")
    print(f"GitHub (nejnovější vydání): {gh or 'nezjištěno (bez sítě nebo GitHub neodpověděl)'}")

    s, p, g = cislo(skill), cislo(projekt), cislo(gh)
    if g and s and g > s:
        print(f"→ NOVA_VERZE_SKILLU: vyšla verze {gh}, nainstalovaný skill je {skill}. Řekni to uživateli jednou větou a poraď,\n"
              "  jak skill aktualizovat: Claude Code (plugin) – `claude plugin marketplace update rodokmen-skill` a\n"
              "  `claude plugin update rodokmen@rodokmen-skill`, pak restart Claude Code (natrvalo: v /plugin zapnout\n"
              "  automatické aktualizace); jinak podle README (část Instalace). Projekt aktualizuj až z nového skillu.")
    elif projekt_dir and p and s and p > s:
        print(f"→ PROJEKT_NOVEJSI: projekt je z verze {projekt}, nainstalovaný skill je starší ({skill}). Projekt neaktualizuj\n"
              "  (vrátil bys ho ke starší verzi); ať uživatel aktualizuje skill (viz README, část Instalace).")
    elif projekt_dir and s and (not p or s > p):
        print(f"→ AKTUALIZUJ_PROJEKT: skill {skill} je novější než projekt. Nabídni aktualizaci projektu:\n"
              f"  python3 -I {os.path.join(SKILL, 'tools', 'novy_projekt.py')} <složka projektu>")
    else:
        print("→ AKTUALNI")


if __name__ == "__main__":
    main()
