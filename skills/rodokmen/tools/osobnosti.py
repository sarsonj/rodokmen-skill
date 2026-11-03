#!/usr/bin/env python3
"""Významné osobnosti rodokmenu: najde předky (a boční příbuzné) s výjimečným povoláním nebo postavením.

Použití: python3 -I tools/osobnosti.py [--vse]
Prochází data/osoby.py (P a SIDE): fakta (ne poznámky – ty popisují i rodiče) a ruční pole `vyz` (vlastní popis významnosti).
Vypíše je po kategoriích s tipy, kde hledat víc (noviny, ročenky, slovníky). --vse vypíše i slabé shody.
Stejné kategorie používá web (stránka /osobnosti/), ruční `vyz` má vždy přednost.
"""
import re
import runpy
import sys
from pathlib import Path

# kategorie: (název, regulární výraz kmenů slov, tip kde hledat)
KATEGORIE = [
    ("Vzdělanci a duchovní", r"\b(farář|kaplan|kněz|děkan|vikář|kanovník|biskup|páter|učitel|řídící|profesor|ředitel škol|doktor|dr\.|lékař|ranhojič|chirurg|advokát|notář|soudce|inženýr|ing\.|architekt|lékárník|studoval|absolvent|maturit|univerzit)",
     "Katalogy duchovenstva (Catalogus cleri), školní výroční zprávy, Kramerius, NDK"),
    ("Vědci a vynálezci", r"\b(vědec|badatel|vynález|patent|astronom|chemik|fyzik|botanik|přírodověd|historik|archivář|akademi)",
     "Ottův slovník naučný, Biografický slovník českých zemí (biography.hiu.cas.cz)"),
    ("Umělci", r"\b(malíř|sochař|hudebník|muzikant|kapelník|varhaník|ředitel kůru|regenschori|skladatel|zpěvák|herec|herečka|spisovatel|básník|fotograf|kreslíř|řezbář)",
     "Kramerius (noviny), Abart (databáze umělců), Český hudební slovník"),
    ("Funkcionáři a úředníci", r"\b(starosta|purkmistr|rychtář|radní|obecní|poslanec|senátor|úředník|správce|vrchní|hejtman|purkrabí|důchodní|direktor|předseda|místopředseda|jednatel|okresní|zemský|četník|četnick|celník|poštmistr|přednosta)",
     "Úřední listy, Hof- und Staatshandbuch, schematismy, obecní kroniky"),
    ("Vojáci a důstojníci", r"\b(důstojník|poručík|nadporučík|setník|kapitán|major|plukovník|generál|šikovatel|legionář|legie|vyznamenán|medail)",
     "VÚA – kartotéky legionářů (legie100.com), kvalifikační listiny, Verlustliste"),
    ("Sportovci", r"\b(sportov|sokol|závodník|reprezent|olympi|mistr republiky|fotbal|hokej|lyžař|atlet|gymnast|cvičitel)",
     "Kramerius (sportovní rubriky), Sokolské věstníky, archivy klubů"),
    ("Podnikatelé a velcí hospodáři", r"\b(továrník|majitel továrny|podnikatel|statkář|velkostatk|sedlák|mlynář|sládek|pivovar|hostinsk|obchodník|kupec|stavitel|mistr|firma)",
     "Adresáře (Compass), živnostenské rejstříky, noviny"),
]
RX = [(n, re.compile(rx, re.I), tip) for n, rx, tip in KATEGORIE]
SLABE = {"Podnikatelé a velcí hospodáři"}  # běžné na vsi – vypisuje se jen s --vse


def kategorie(text):
    return [(n, m.group(0), tip) for n, rx, tip in RX if (m := rx.search(text))]


def main():
    vse = "--vse" in sys.argv
    d = runpy.run_path(str(Path("data/osoby.py")))
    kandidati = []
    for k, p in sorted(d.get("P", {}).items()):
        text = " ".join(p.get("f", []))  # jen vlastní údaje; poznámky zmiňují i rodiče
        kandidati.append((f"{k:>4}", p.get("n", "?"), p.get("y", ""), p.get("vyz", ""), text))
    for s in d.get("SIDE", []):
        kandidati.append((f"s{s.get('k', '?')}", s.get("n", "?"), "", s.get("vyz", ""), s.get("t", "")))

    po_kat = {}
    for cis, jm, y, vyz, text in kandidati:
        if vyz:
            po_kat.setdefault("Ručně označení (vyz)", []).append((cis, jm, y, vyz))
            continue
        for n, slovo, tip in kategorie(text):
            if n in SLABE and not vse:
                continue
            po_kat.setdefault(n, []).append((cis, jm, y, f"„{slovo}“ – {text.strip()[:110]}"))
    if not po_kat:
        print("Žádný předek s výjimečným povoláním zatím v datech není.")
        return
    tipy = {n: tip for n, _, tip in KATEGORIE}
    for n, lidi in po_kat.items():
        print(f"\n## {n} ({len(lidi)})")
        if n in tipy:
            print(f"   kde hledat víc: {tipy[n]}")
        for cis, jm, y, co in lidi:
            print(f" {cis}  {jm} {y}: {co}")
    print("\nJen náměty podle slov v datech. Ověř v zápisu; potvrzeným doplň do osoby pole vyz=\"krátký popis\" (pak jsou na webu nahoře).")


if __name__ == "__main__":
    main()
