#!/usr/bin/env python3
"""Souhlas uživatele s podmínkami portálu s citlivými údaji (Arolsen Archives, databáze obětí holocaust.cz).

Tyto portály žádají při vstupu o potvrzení podmínek (osobní odpovědnost za nakládání s údaji o obětech). Nástroj prohlížeč
nemá, takže bez tohoto modulu by potvrzení přeskočil. Proto nástroj bez zapsaného souhlasu nic nestahuje a skončí s kódem 4.
Souhlas smí zapsat jen uživatel sám: příkaz `souhlas` příslušného nástroje ukáže znění a vyžaduje odpověď „ano“ zadanou
ručně v terminálu. Claude ho nespouští a nikdy ho nepotvrzuje za uživatele (v Claude Code ho uživatel spustí s předponou `!`).

POZOR: jde o pojistku proti nedopatření, ne o technickou ochranu – soubor stavu si může zapsat kdokoli, kdo smí psát
do domovské složky (nebo přesměrovat SOUHLAS_STAV). Že Claude souhlas nepotvrzuje, drží pravidlo, ne kód.

Souhlas platí 30 dní na tomto počítači a jen pro dané znění podmínek (změní-li se, zeptá se znovu).
Stav: ~/.cache/rodokmen_souhlas/<portál>.json (Windows %LOCALAPPDATA%\\rodokmen_souhlas), jen malý soubor JSON.
"""
import hashlib, json, os, sys, time

PLATNOST = 30 * 24 * 3600
KOD = 4


def _slozka():
    return os.environ.get("SOUHLAS_STAV") or os.path.join(
        os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".cache"), "rodokmen_souhlas")


def _otisk(zneni):
    return hashlib.sha256(zneni.encode("utf-8")).hexdigest()[:16]


def ma_souhlas(klic, zneni):
    try:
        with open(os.path.join(_slozka(), klic + ".json"), encoding="utf-8") as fh:
            d = json.load(fh)
        return d.get("otisk") == _otisk(zneni) and -300 < time.time() - float(d.get("cas", 0)) < PLATNOST
    except (OSError, ValueError, TypeError):
        return False


def vyzaduj(klic, nazev, zneni, prikaz):
    """Skončí (kód 4), pokud uživatel souhlas nezapsal. `prikaz` = jak ho zapsat (např. „tools/arolsen.py souhlas“)."""
    if ma_souhlas(klic, zneni):
        return
    sys.stderr.write(
        f"{nazev} žádá při vstupu o souhlas s podmínkami (citlivé údaje o obětech). Nástroj bez něj nic nestahuje.\n"
        f"Souhlas musí potvrdit uživatel sám: ať v terminálu spustí `python3 -I {prikaz}` (v Claude Code s předponou `!`),\n"
        "přečte si znění a odpoví ručně „ano“. Claude souhlas nikdy nepotvrzuje za uživatele.\n")
    sys.exit(KOD)


def _je_terminal():
    return sys.stdin.isatty() and sys.stdout.isatty()


def potvrd(klic, nazev, zneni, url, prikaz):
    """Ukáže znění a zapíše souhlas, jen když uživatel v terminálu ručně odpoví „ano“."""
    if not _je_terminal():
        sys.stderr.write("Souhlas jde zapsat jen v interaktivním terminálu, kam píše uživatel. Spusť příkaz sám "
                         f"(v Claude Code `!python3 -I {prikaz}`); Claude ho nesmí potvrdit za tebe.\n")
        sys.exit(KOD)
    print(f"{nazev} – podmínky vstupu:\n\n{zneni}\n\nPodmínky a pravidla: {url}\n")
    odpoved = input("Souhlasíš a přebíráš odpovědnost za nakládání s těmito údaji? Napiš „ano“: ").strip().lower()
    if odpoved != "ano":
        print("Souhlas nezapsán.")
        sys.exit(KOD)
    os.makedirs(_slozka(), exist_ok=True)
    cil = os.path.join(_slozka(), klic + ".json")
    tmp = cil + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"portal": nazev, "cas": time.time(), "datum": time.strftime("%Y-%m-%d"), "otisk": _otisk(zneni)}, fh)
    os.replace(tmp, cil)
    print(f"Souhlas zapsán (platí 30 dní na tomto počítači): {cil}")
