#!/usr/bin/env python3
"""Folio nebo strana → číslo snímku: odhad z několika dvojic, které jsi už viděl v knize.

Použití:
  folio.py <snímek>=<folio> [<snímek>=<folio> …] <hledané folio> [<hledané folio> …] [--pagina]
      folio: 12 nebo 12r = líc listu 12, 12v = rub; s --pagina jsou čísla stránky (paginace), ne folia.
      Příklad: folio.py 14=5r 31=13v 52=24r 9v 20r  → odhad snímku pro folio 9v a 20r

Otevři 2–3 snímky v různých částech knihy (u knih psaných po vsích v oddílu té vsi), zapiš dvojice
snímek=folio a nástroj dopočítá snímek lineárně mezi nejbližšími známými body – posun, který se v knize mění
(vlepené listy, chybějící snímky, oddíly vsí), tak nevadí, dokud máš dvojici před i za hledaným místem.
Mimo známé body prodlužuje nejbližší úsek a upozorní. Výsledek je odhad: na snímku vždy ověř číslo listu.
Dvojice z různých oddílů s vlastním číslováním nemíchej – pro každý oddíl spusť nástroj zvlášť.
Bez sítě, nic nezapisuje.
"""
import re, sys

FOLIO = re.compile(r"(\d+)\s*([rv]?)", re.I)


def poradi(text, pagina=False):
    """Pořadí stránky v knize: folio n r = 2n, n v = 2n + 1; strana (pagina) p = p."""
    m = FOLIO.fullmatch(text.strip())
    if not m or (pagina and m.group(2)):
        raise ValueError(text)
    n = int(m.group(1))
    return n if pagina else 2 * n + (m.group(2).lower() == "v")


def odhad(dvojice, cil):
    """(snímek, poznámka) pro pořadí cil z dvojic [(pořadí, snímek)] seřazených podle pořadí."""
    if len(dvojice) == 1:   # jediný bod: dvoustrana = 2 stránky na snímek (nejčastější u skenů knih)
        p, s = dvojice[0]
        return s + (cil - p) / 2, "jen jedna dvojice – počítám se 2 stránkami na snímek (dvoustrana); přidej druhou"
    for (p0, s0), (p1, s1) in zip(dvojice, dvojice[1:]):
        if p0 <= cil <= p1:
            return s0 + (s1 - s0) * (cil - p0) / (p1 - p0), ""
    (p0, s0), (p1, s1) = dvojice[:2] if cil < dvojice[0][0] else dvojice[-2:]
    hrana = dvojice[0][0] if cil < dvojice[0][0] else dvojice[-1][0]
    return s0 + (s1 - s0) * (cil - p0) / (p1 - p0), f"mimo známé body (o {abs(cil - hrana)} stran) – přidej dvojici blíž"


def main(argv):
    for s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")
    pagina = "--pagina" in argv
    argv = [a for a in argv if a != "--pagina"]
    if not argv or argv[0] in ("-h", "--help"):
        sys.exit(__doc__.strip())
    zname, hledane = [], []
    try:
        for a in argv:
            if "=" in a:
                s, f = a.split("=", 1)
                zname.append((poradi(f, pagina), int(s), f.strip()))
            else:
                hledane.append((poradi(a, pagina), a))
    except ValueError as e:
        sys.exit(f"nerozumím „{e}“ – dvojice piš jako snímek=folio (14=5r, 31=13v), hledané folio jako 30r"
                 + (" (s --pagina jen čísla stran, bez r/v)" if pagina else ""))
    if not zname or not hledane:
        sys.exit("potřebuju aspoň jednu dvojici snímek=folio a aspoň jedno hledané folio (folio.py -h)")
    zname.sort()
    for (p0, s0, f0), (p1, s1, f1) in zip(zname, zname[1:]):
        if p0 == p1 and s0 != s1:
            sys.exit(f"folio {f0} je u dvou snímků ({s0} a {s1}) – oprav dvojice")
        if s1 < s0:
            print(f"POZOR: snímek {s1} ({f1}) je před snímkem {s0} ({f0}) – jiný oddíl s vlastním číslováním, "
                  "nebo překlep? Oddíly počítej zvlášť.")
    body = [(p, s) for p, s, _ in zname]
    for p, text in hledane:
        s, pozn = odhad(body, p)
        n = round(s)
        rozpeti = "" if abs(s - n) < 0.25 else f" (mezi {int(s)} a {int(s) + 1})"
        print(f"{'pagina' if pagina else 'folio'} {text} → snímek ≈ {n}{rozpeti}" + (f"  – {pozn}" if pozn else ""))
    print("Odhad – na snímku ověř číslo listu; když nesedí, přidej tu dvojici a spusť znovu.")


if __name__ == "__main__":
    main(sys.argv[1:])
