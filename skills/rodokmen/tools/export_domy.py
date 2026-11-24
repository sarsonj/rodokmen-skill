#!/usr/bin/env python3
"""Doplňková data pro stránky Domy předků: web/src/data/domy.json.

Volá se na konci tools/export_web.py (po zápisu site.json), jde ale spustit i samostatně.
Čísla popisná (čp.) se čtou z textů faktů osob a ze shrnutí a přepisů zápisů: „Holice čp. 112“,
„Dolní Roveň (mlýn) č. 7“. Obec se pozná podle míst v site.json (places; výraz `re` z data/mista.json,
jinak název místa) – dům tedy vznikne jen v obci, která je na mapě webu.
Dům se zobrazí, jen když se k němu váží aspoň 3 předci (MIN_PREDKU). Žijící osoby se nepočítají.
Soubor domy.json se píše vždy (bez domů jako []), web pak stránku Domy nevytvoří a nenabídne v menu."""
import datetime, json, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, "web", "src", "data", "site.json")
OUT = os.path.join(ROOT, "web", "src", "data", "domy.json")

MIN_PREDKU = 3
# „čp. 12“, „č. p. 12“, „č. 12“, před číslem případně doplněk v závorce: „Holice (mlýn) č. 12“
CP = r"(?:\s*\([^)]{1,40}\))?\s*(?:č\.\s*p\.|čp\.?|č\.)\s*(\d{1,4})\b"


def slugify(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def year_of(text):
    m = re.findall(r"\b(1[5-9]\d\d|20\d\d)\b", text)
    return int(m[0]) if m else None


def is_living(p, now):
    """Stejné pravidlo jako isLiving() v web/src/lib/zivoty.js: žijící, nebo by ještě mohla žít (narozená před < 110 lety bez úmrtí)."""
    facts = p.get("facts") or []
    y = p.get("y") or ""
    if re.match(r"Žijící", p.get("note") or "", re.I):
        return True
    has_death = any(f.startswith("†") for f in facts) or bool(re.search(r"[–†]", y))
    if p.get("st") == "fam" and re.fullmatch(r"\*\s*\d{4}\s*", y) and not any(f.startswith("†") for f in facts):
        if int(re.search(r"\d{4}", y).group()) > now - 110:
            return True
    by = None
    for f in facts:
        m = re.match(r"\*\s*(?:\(pokřtěn\)\s*)?(?:(?:před|po|asi|snad|kolem|≈)\s*)?(?:\d{1,2}\.\s*\d{1,2}\.\s*)?(\d{4})\b", f)
        if m:
            by = int(m.group(1))
            break
    if by is None:
        m = re.search(r"\d{4}", y)
        by = int(m.group()) if m else None
    return not has_death and by is not None and by > now - 110


def main():
    site = json.load(open(SITE, encoding="utf-8"))
    now = datetime.date.today().year
    # delší/konkrétnější výrazy první (aby „Horní Lhota u města“ vyhrálo nad „Horní Lhota“)
    pats = []
    for pl in sorted(site.get("places", []), key=lambda x: -len(x.get("re") or x["name"])):
        if pl.get("hypothesis"):
            continue
        try:
            pats.append((pl["name"], pl, re.compile(r"(?:" + (pl.get("re") or re.escape(pl["name"])) + r")\w*" + CP)))
        except re.error:
            pass
    places = {name: pl for name, pl, _ in pats}

    def find(text):
        """[(obec, čp)] – bez překryvů."""
        found, used = [], []
        for name, _, rx in pats:
            for m in rx.finditer(text):
                a, b = m.start(), m.end()
                if any(a < e and b > s for s, e in used):
                    continue
                used.append((a, b))
                found.append((name, int(m.group(m.lastindex))))
        return found

    houses = {}

    def house(obec, cp):
        key = f"{slugify(obec)}-{cp}"
        return houses.setdefault(key, dict(slug=key, obec=obec, cp=cp, people={}, facts=[], records=[]))

    for slug, p in site["people"].items():
        if is_living(p, now):
            continue
        for f in p.get("facts", []):
            for obec, cp in find(f):
                h = house(obec, cp)
                h["people"].setdefault(slug, []).append(f)
                h["facts"].append(dict(person=slug, text=f, year=year_of(f)))

    # zápisy, které dům zmiňují a týkají se někoho, kdo v domě žil
    for r in site.get("records", []):
        text = (r.get("summary") or "") + " " + (r.get("cs") or "")
        for o, c in set(find(text)):
            h = houses.get(f"{slugify(o)}-{c}")
            if h and set(r.get("people") or []) & set(h["people"]):
                h["records"].append(r["key"])

    out = []
    for h in houses.values():
        if len(h["people"]) < MIN_PREDKU:
            continue
        pl = places.get(h["obec"], {})
        h["lat"], h["lon"] = pl.get("lat"), pl.get("lon")
        h["records"] = sorted(set(h["records"]))
        out.append(h)
    out.sort(key=lambda h: (h["obec"], h["cp"]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(f"domy: {len(out)} domů s ≥{MIN_PREDKU} předky (z {len(houses)} nalezených čísel popisných) → web/src/data/domy.json")


if __name__ == "__main__":
    main()
