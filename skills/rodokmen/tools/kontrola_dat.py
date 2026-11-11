#!/usr/bin/env python3
"""Obsahové kontroly dat, které dřív našla jen ruční kontrola vyšším modelem (Opus, 11. 11. 2026).

Volá je tools/kontrola.py (upozornění). Samostatně: `python -I -X utf8 tools/kontrola_dat.py` vypíše jen tyto nálezy.

Hlídá:
  1. roky v `y` nesedí s fakty `* …` a `† …` (web bere `y`, výpočty věku fakta)
  2. fakta mají rok narození / úmrtí, ale `y` ho nemá
  3. rok v `y` u doložené osoby pochází jen z cizího stromu (MyHeritage, „strom …“) – web ho ukáže jako doložený
  4. osoba cituje v `r` zápis, který sám o sobě říká, že je jen kandidát – web ho ukáže jako doklad
  5. zastaralé věty („V matrice neověřeno“, „křest se nečetl“) u osoby, která už zápis má
  6. ženich nebo nevěsta je v přepisu sňatku „ledig/svobodný“, ale osoba má u téhož sňatku „vdovec/vdova“ (nebo naopak)
"""
import json, os, re, sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROK = re.compile(r"(?<!\d)(1[0-9]{3}|20[0-9]{2})(?!\d)")
CIZI = re.compile(r"\bMH\b|MyHeritage|\bstrom\w*|Geni\b|FamilySearch.{0,20}strom", re.I)
KANDIDAT = re.compile(r"kandidát|jen kandid|nepotvrzen", re.I)
ZASTARALE = re.compile(r"V matrice neověřeno|(?:křest|sňatek|úmrtí|zápis)[^.]{0,30}\bse\s+nečetl[ay]?\b"
                       r"|\bnečetl[ay]?\s+se\b|matrika nečtena", re.I)
SVOBODNY = re.compile(r"\bledig\b|\bsvobodn[áýa]\b|\bcoelebs\b|\bvirgo\b|\bjuvenis\b", re.I)
VDOVEC = re.compile(r"\bWitwer\b|\bWitwe\b|\bvdov(?:ec|a)\b|\bviduus\b|\bvidua\b", re.I)
VDOVEC_M = re.compile(r"\bvdovec\b|\bWitwer\b|\bviduus\b", re.I)   # fakt o sobě: muž
VDOVA_Z = re.compile(r"\bvdova\b|\bWitwe\b|\bvidua\b", re.I)       # fakt o sobě: žena


def roky_y(y):
    """(narození, úmrtí) z pole y; „před/po/asi“ dává None u té strany, kde nejde o přesný rok."""
    y = (y or "").strip()
    if not y:
        return None, None
    if y.startswith("†"):
        m = ROK.search(y)
        return None, (int(m.group(1)) if m and not re.search(r"před|po\b", y) else None)
    casti = re.split(r"\s+[–—-]\s+|(?<=\d)[–—-](?=\d)|\s+[–—-](?=\s*$)", y.lstrip("* "), maxsplit=1)
    def rok(c):
        if c is None or re.search(r"před|po\b|\?", c):
            return None
        m = ROK.search(c)
        return int(m.group(1)) if m else None
    return rok(casti[0]), rok(casti[1] if len(casti) > 1 else None)


def fakta_rok(p, znak):
    """[(rok, text faktu)] z faktů začínajících * nebo † (ne „před/po“)."""
    out = []
    for f in p.get("f") or []:
        if isinstance(f, str) and f.lstrip().startswith(znak) and not re.search(r"\b(?:před|po)\s+\d", f.split("(")[0]):
            m = ROK.search(f)
            if m:
                out.append((int(m.group(1)), f))
    return out


def radky_snoubencu(orig):
    """Řádky přepisu, které popisují ženicha a nevěstu: (kdo, text)."""
    out = []
    for l in (orig or "").splitlines():
        m = re.match(r"\s*\[(Bräutigam|Braut|Sponsus|Sponsa|Ženich|Nevěsta|Copulati)[^\]]*\]\s*(.*)", l, re.I)
        if m:
            out.append((m.group(1).lower(), m.group(2)))
    return out


def kontroly(P, SIDE, zaz, prep):
    warn = []
    zaz_k = {z.get("klic"): z for z in zaz}
    for k, p in sorted(P.items()):
        n = p.get("n")
        if p.get("st") == "unk":
            continue
        yn, yz = roky_y(p.get("y"))
        fn, fz = fakta_rok(p, "*"), fakta_rok(p, "†")
        # 1 a 2: y × fakta
        if yn and fn and all(abs(yn - r) > 1 for r, _ in fn):
            warn.append(f"osoba {k} ({n}): y má narození {yn}, fakta {fn[0][0]} – sjednoť (web bere y)")
        if yz and fz and all(abs(yz - r) > 1 for r, _ in fz):
            warn.append(f"osoba {k} ({n}): y má úmrtí {yz}, fakta {fz[0][0]} – sjednoť (web bere y)")
        y = p.get("y") or ""
        vlastni_fn = [x for x in fn if not CIZI.search(x[1])]   # rok jen z cizího stromu do y nepatří
        if vlastni_fn and p.get("st") != "fam":
            if not y.strip():
                warn.append(f"osoba {k} ({n}): fakta mají narození {vlastni_fn[0][0]}, ale y je prázdné – doplň y (web ukazuje y)")
        # 3: rok v y jen z cizího stromu u doložené osoby
        if p.get("st") == "doc":
            for rok, f in fn + fz:
                if CIZI.search(f) and re.search(rf"{rok}(?!\s*\(\?\))", y):   # „1930 (?)“ = nejistota přiznaná
                    warn.append(f"osoba {k} ({n}): rok {rok} v y je jen z cizího stromu („{f[:60]}“) – "
                                "u doložené osoby ho web ukáže jako doložený; dej do y jen roky ze zápisů")
                    break
        # 4: citovaný zápis je jen kandidát
        for r in p.get("r") or []:
            z = zaz_k.get(r) or {}
            if KANDIDAT.search(str(z.get("nazev", ""))) or re.search(r"^[^.]{0,80}\bjen kandidát", str(z.get("shrnuti", "")), re.I):
                warn.append(f"osoba {k} ({n}): cituje zápis {r}, který je podle názvu/shrnutí jen kandidát – "
                            "web ho ukáže jako doklad; přesuň do poznámky, HYPOTEZY nebo SIDE")
        # 5: zastaralé věty
        if p.get("r"):
            m = ZASTARALE.search(str(p.get("note", "")))
            if m:
                warn.append(f"osoba {k} ({n}): poznámka říká „{m.group(0)}“, ale osoba už cituje {len(p['r'])} zápis(ů) – "
                            "zastaralá věta?")
        # 6: svobodný × vdovec u sňatku
        for r in p.get("r") or []:
            z = zaz_k.get(r) or {}
            if z.get("druh") != "O":
                continue
            rok = ROK.search(str(z.get("datum", "")))
            if not rok:
                continue
            fakt = [f for f in p.get("f") or [] if isinstance(f, str) and "×" in f and rok.group(1) in f]
            if not fakt:
                continue
            muz = k % 2 == 0 if k > 1 else p.get("sex") == "M"
            # „vdovec“ u muže / „vdova“ u ženy – jinak jde o partnera („× … Sedláková (vdova)“)
            osoba_vdov = any((VDOVEC_M if muz else VDOVA_Z).search(f) for f in fakt)
            radky = radky_snoubencu((prep.get(r) or {}).get("orig", ""))
            for kdo, text in radky:
                je_on = kdo in ("bräutigam", "sponsus", "ženich")
                if muz is None or je_on != muz or kdo == "copulati":
                    continue
                if osoba_vdov and SVOBODNY.search(text) and not VDOVEC.search(text):
                    warn.append(f"osoba {k} ({n}): u sňatku {r} má fakta „vdovec/vdova“, přepis „{SVOBODNY.search(text).group(0)}“ – "
                                "přečti na výřezu sloupec ledig/Witwer (porovnej s řádkem nad a pod)")
    return warn


def main():
    ns = {}
    exec(open(os.path.join(ROOT, "data", "osoby.py"), encoding="utf-8-sig").read(), ns)
    j = lambda f, d: json.load(open(os.path.join(ROOT, "data", f), encoding="utf-8-sig")) if os.path.exists(os.path.join(ROOT, "data", f)) else d
    w = kontroly(ns.get("P", {}), ns.get("SIDE", []), j("zaznamy.json", []), j("prepisy.json", {}))
    for x in w:
        print("upozornění:", x)
    print(f"{len(w)} upozornění" if w else "Bez nálezů.")


if __name__ == "__main__":
    main()
