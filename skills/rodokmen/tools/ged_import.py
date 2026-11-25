#!/usr/bin/env python3
"""Vytěží rodinný strom (GEDCOM .ged z MyHeritage, Geni, FamilySearch…) pro rodokmen.

Použití (z kořene projektu):
  python3 -I tools/ged_import.py dokumenty/strom.ged                 -> seznam osob (id | jméno | narození)
  python3 -I tools/ged_import.py dokumenty/strom.ged "Jméno Příjmení" -> předci této osoby s Kekulého čísly
                                                                        (1 = ona, 2 = otec, 3 = matka…), všechny
                                                                        události, poznámky a FRONTA ZÁPISŮ k vyhledání
  … "Jméno Příjmení" --osoby   -> totéž jako kostra pro data/osoby.py (stav "fam", ke kontrole a doplnění);
                                 u každé osoby i ged="@I…@" a uid (_UID) – vazba na tento strom pro pozdější
                                 sloučení s MyHeritage (ged_export.py)
  … "Jméno Příjmení" --ged-id [--zapsat]
                              -> doplní vazbu do existujícího data/osoby.py (projekt, který strom importoval dřív):
                                 projde strom od výchozí osoby, stejné Kekulé číslo = stejná osoba, ověří jméno
                                 a rok narození; vypíše shody a neshody. S --zapsat shody zapíše (zapis.py ged).

Fronta zápisů: u každého předka nejmladší známá událost s místem (úmrtí, pak sňatek, pak narození) –
úmrtní a oddací zápisy uvádějí datum a místo narození i rodiče, proto se hledá od nejmladšího zápisu.
E-maily a adresy ze stromu se nevypisují.
Kódování: UTF-8; starší soubory s hlavičkou „1 CHAR ANSI“ (Brother's Keeper) se čtou jako Windows-1250 a česká data
(„SRPEN 1945“, „PODZIM 1951“, „1926 NEBO 1927“, „11.11.1934“) se převedou na tvar „8. 1945“, „podzim 1951“…
"""
import datetime, os, re, sys, unicodedata
# Modul jde i importovat (read() používají ged_export.py a testy) – nápověda a nastavení výstupu jsou proto v main().

EVENTS = {"BIRT": "*", "CHR": "* (křest)", "DEAT": "†", "BURI": "† (pohřeb)", "MARR": "×"}
MONTHS = {m: i for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}
# česká data z Brother's Keeperu („SRPEN 1945“, „PODZIM 1951“, „1926 NEBO 1927“, „ASI 1930“, „11.11.1934“)
CZ_MONTHS = {m: i for i, m in enumerate("LEDEN ÚNOR BŘEZEN DUBEN KVĚTEN ČERVEN ČERVENEC SRPEN ZÁŘÍ ŘÍJEN LISTOPAD PROSINEC".split(), 1)}
CZ_WORDS = {"JARO": "jaro", "LÉTO": "léto", "PODZIM": "podzim", "ZIMA": "zima", "NEBO": "nebo", "ASI": "asi",
            "OKOLO": "asi", "PŘED": "před", "PO": "po", "MEZI": "mezi", "A": "a"}


def decode(data):
    """UTF-8, a když soubor UTF-8 není a hlavička říká „1 CHAR ANSI“ (Brother's Keeper aj.), pak Windows-1250."""
    # CONC spojit už v bajtech: MyHeritage dělí dlouhé řádky i uprostřed vícebajtového znaku UTF-8 („č“ → „��“)
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):   # UTF-16 („1 CHAR UNICODE“, starší Family Tree Maker, Legacy…)
        data = data.decode("utf-16").encode("utf-8")
    data = re.sub(rb"\r?\n[ \t]*\d+[ \t]+CONC(?: |(?=\r?\n))", b"", data)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    m = re.search(rb"^\s*1\s+CHAR\s+(\S+)", data[:5000], re.M)
    char = m.group(1).decode("ascii", "replace").upper() if m else ""
    if char in ("ANSI", "WINDOWS-1250", "CP1250"):
        return data.decode("cp1250", "replace")
    if char == "ANSEL":
        print("POZOR: strom je v kódování ANSEL – čeština může být rozbitá; vyexportuj ho znovu v UTF-8.", file=sys.stderr)
    return data.decode("utf-8", "replace")


def read(path):
    raw = decode(open(path, "rb").read()).lstrip("﻿")
    recs, cur, stack = {}, None, []
    for line in raw.splitlines():
        m = re.match(r"\s*(\d+)\s+(@[^@]+@\s+)?(\S+)\s?(.*)$", line)
        if not m:
            continue
        lvl, xref, tag, val = int(m.group(1)), (m.group(2) or "").strip(), m.group(3), m.group(4)
        if lvl == 0:
            cur = {"_id": xref, "_type": tag, "_sub": [], "val": val} if xref else None   # val: text sdílené poznámky
            if cur:
                recs[xref] = cur
            stack = [cur]
            continue
        if cur is None:
            continue
        stack = stack[:lvl]
        parent = stack[-1] if stack else cur
        if tag in ("CONC", "CONT") and parent is not None:
            parent["val"] = parent.get("val", "") + ("\n" if tag == "CONT" else "") + val
            stack.append(parent)
            continue
        node = {"tag": tag, "val": val, "_sub": []}
        parent["_sub"].append(node)
        stack.append(node)
    return recs


def sub(node, tag):
    return [n for n in node["_sub"] if n["tag"] == tag]


def first(node, tag, default=""):
    s = sub(node, tag)
    return s[0].get("val", "").strip() if s else default


def cz_date(d):
    """'14 FEB 1890' -> '14. 2. 1890', 'ABT 1850' -> 'asi 1850'."""
    d = d.strip()
    pre = ""
    for k, v in (("ABT", "asi "), ("EST", "asi "), ("CAL", "asi "), ("BEF", "před "), ("AFT", "po "), ("BET", "mezi ")):
        if d.startswith(k):
            pre, d = v, d[len(k):].strip()
    d = d.replace(" AND ", " a ")
    def one(m):
        day, mon, yr = m.group(1), m.group(2), m.group(3)
        return f"{day + '. ' if day else ''}{str(MONTHS[mon]) + '. ' if mon else ''}{yr}"
    d = re.sub(r"(?:(\d{1,2}) )?(?:(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC) )?(\d{3,4})", one, d)
    if re.search(r"[A-ZÁ-Ž]{2,}|\d\.\d", d) and not re.search(r"[a-z]", d.replace("asi ", "")):   # jen česká data, ne anglický GEDCOM
        d = re.sub(r"\b(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})\b", lambda m: f"{int(m[1])}. {int(m[2])}. {m[3]}", d)
        d = re.sub(r"[A-ZÁ-Ž]+", lambda m: f"{CZ_MONTHS[m[0]]}." if m[0] in CZ_MONTHS else CZ_WORDS.get(m[0], m[0]), d)
    return pre + d


def year(d):
    m = re.search(r"\d{4}", d or "")
    return int(m.group()) if m else None


def name(ind):
    n = first(ind, "NAME").replace("/", "").strip()
    return re.sub(r"\s+", " ", n) or "(beze jména)"


def events(ind, recs):
    out = []
    for n in ind["_sub"]:
        if n["tag"] in EVENTS:
            d, p = first(n, "DATE"), first(n, "PLAC")
            extra = first(n, "CAUS")
            out.append((n["tag"], cz_date(d) if d else "", p, extra))
    for fam_id in [n["val"] for n in sub(ind, "FAMS")]:
        fam = recs.get(fam_id.strip())
        if not fam:
            continue
        spouse = [recs.get(n["val"].strip()) for n in fam["_sub"] if n["tag"] in ("HUSB", "WIFE") and n["val"].strip() != ind["_id"]]
        for m in sub(fam, "MARR"):
            d, p = first(m, "DATE"), first(m, "PLAC")
            out.append(("MARR", cz_date(d) if d else "", p, name(spouse[0]) if spouse and spouse[0] else ""))
    return out


def parents(ind, recs):
    for n in sub(ind, "FAMC"):
        fam = recs.get(n["val"].strip())
        if fam:
            h, w = first(fam, "HUSB"), first(fam, "WIFE")
            return recs.get(h), recs.get(w)
    return None, None


def ancestors(recs, start):
    """Předci výchozí osoby s Kekulého čísly {1: osoba, 2: otec, 3: matka, …}."""
    tree, todo = {1: start}, [1]
    while todo:
        k = todo.pop(0)
        f, m = parents(tree[k], recs)
        for kk, p in ((2 * k, f), (2 * k + 1, m)):
            if p:
                linie, j = [], k   # vlastní linie nad kk: dítě, vnuk… až po výchozí osobu
                while j >= 1:
                    linie.append(tree[j]["_id"])
                    j //= 2
                if p["_id"] in linie:   # chyba ve stromu: osoba je sama sobě předkem → nekonečná smyčka
                    print(f"POZOR: smyčka ve stromu – {name(p)} je zapsaný jako vlastní předek (chyba ve stromu, "
                          "zkontroluj s rodinou); tuhle větev dál nesleduji.", file=sys.stderr)
                    continue
                tree[kk] = p
                todo.append(kk)
    return tree


def find(recs, query):
    q = query.lower().split()
    hits = [r for r in recs.values() if r["_type"] == "INDI" and all(w in name(r).lower() for w in q)]
    if not hits:
        sys.exit(f"Osoba „{query}“ ve stromu není. Spusť bez jména pro seznam osob.")
    if len(hits) > 1:
        print("Víc osob odpovídá, použij id místo jména:", file=sys.stderr)
        for h in hits:
            print(f"  {h['_id']} | {name(h)}", file=sys.stderr)
        sys.exit(1)
    return hits[0]


def tokens(text, keep_brackets=False):
    """Slova jména bez diakritiky, malými písmeny, bez „?“; text v závorkách jen s keep_brackets."""
    text = text or ""
    text = unicodedata.normalize("NFD", text if keep_brackets else re.sub(r"\([^)]*\)", " ", text))
    text = "".join(c for c in text if not unicodedata.combining(c)).casefold()
    return [w for w in re.split(r"[^\w]+", text.replace("/", " ")) if w]


def same_name(project_name, tree_name, married=()):
    """Shoda: první křestní jméno a příjmení z projektu jsou ve jménu ve stromu (strom má navíc druhá jména…).
    Příjmení se porovná podle začátku (Novák × Nováková, Dvořák × Dvořáková); married = příjmení po sňatku
    z faktu „provd. Nováková“ (strom ženu často vede pod ním)."""
    a = tokens(project_name)
    alt = [w for w in tokens(project_name, True) if w not in a]   # „Martin Novák (Vopat)“ – druhé příjmení v závorce
    if len(a) >= 2 and any(same_name(f"{a[0]} {m}", tree_name) for m in [*married, *alt]):
        return True
    b = tokens(tree_name, True)   # strom: „MARTIN VOPAT (NOVÝ)“ – i závorka
    if len(a) < 2 or not b:
        return bool(a) and a[0] in b
    def similar(x, y, least):   # společný začátek: Novák/Nováková, Dvořák/Dvořáková (dvorak × dvorakova)
        common = len(os.path.commonprefix([x, y]))
        return x == y or (common >= least and common >= min(len(x), len(y)) - 2)
    # křestní jméno podle začátku aspoň 4 znaků: Anton × Antonín, Johanna × Johana (Martin × Marie ne);
    # příjmení stačí 3: Kočí × Kočová (Rosalie × Rozálie ne – ověří člověk)
    return any(similar(a[0], w, 4) for w in b) and any(similar(a[-1], w, 3) for w in b[1:] or b)


def ged_id(recs, tree, write):
    """Vazba existujícího data/osoby.py na strom: stejné Kekulé číslo = stejná osoba, ověří jméno a rok narození."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ns = {}
    try:
        exec(open(os.path.join(root, "data", "osoby.py"), encoding="utf-8-sig").read(), ns)
    except Exception as e:  # noqa: BLE001
        sys.exit(f"data/osoby.py nejde načíst ({e}) – oprav ho nejdřív.")
    P, SAME = ns.get("P", {}), ns.get("SAME", {})
    ok, bad, have, conflict = [], [], [], []
    for k in sorted(P):
        if k in SAME or k not in tree:
            continue
        p, ind = P[k], tree[k]
        gid, uid = ind["_id"], first(ind, "_UID").strip()
        by = next((year(d) for t, d, pl, x in events(ind, recs) if t in ("BIRT", "CHR") and year(d)), None)
        py = next((int(m) for m in re.findall(r"\b(\d{4})\b", str(p.get("y", "")) + " " + " ".join(
            f for f in p.get("f", []) if str(f).lstrip().startswith("*")))), None)
        row = (k, p.get("n", ""), name(ind), gid, uid, py, by)
        married = [m for f in p.get("f", []) for m in re.findall(r"provd\.\s+(\S+)", str(f))]
        if p.get("ged"):
            (have if p["ged"] == gid else conflict).append(row)
        elif not same_name(p.get("n", ""), name(ind), married) or (py and by and abs(py - by) > 1):
            bad.append(row)
        else:
            ok.append(row)
    fmt = lambda r: f"  {r[0]:>4} {r[1]} ({r[5] or '?'}) ↔ {r[3]} {r[2]} ({r[6] or '?'})"
    print(f"Shoda ({len(ok)}):")
    for r in ok:
        print(fmt(r))
    if bad:
        print(f"\nNESEDÍ – jméno nebo rok narození se liší o víc než rok, nezapisuji ({len(bad)}); ověř a případně"
              " zapiš ručně: zapis.py ged <číslo> <@I…@> [<uid>]")
        for r in bad:
            print(fmt(r))
    if conflict:
        print(f"\nJINÉ ID – osoba už má ged, ale strom má na tomto místě jinou osobu ({len(conflict)}); nic neměním:")
        for r in conflict:
            print(fmt(r) + f"  (v datech {P[r[0]]['ged']})")
    if have:
        print(f"\nUž mají správné ged: {len(have)}")
    rest = [k for k in P if k not in SAME and k not in tree and not P[k].get("ged")]
    if rest:
        print(f"\nNejsou ve stromu (nově zjištění předci, při sloučení budou nové osoby): {len(rest)} – "
              + ", ".join(str(k) for k in sorted(rest)[:30]) + (" …" if len(rest) > 30 else ""))
    if not write:
        if ok:
            print("\nZapsat shody: totéž s --zapsat.")
        return
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import zapis
    for k, n, tn, gid, uid, py, by in ok:
        zapis.nastav(k, {"ged": gid, **({"uid": uid} if uid else {})})


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):   # nápověda místo pádu
        sys.exit(__doc__.strip())
    for s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")
    recs = read(sys.argv[1])
    args = [a for a in sys.argv[2:] if not a.startswith("--")]
    as_py = "--osoby" in sys.argv
    if not args:
        for r in recs.values():
            if r["_type"] == "INDI":
                b = next((e for e in events(r, recs) if e[0] == "BIRT"), None)
                print(f"{r['_id']} | {name(r)} | {('* ' + b[1] + ' ' + b[2]).strip() if b and (b[1] or b[2]) else ''}")
        return
    start = recs.get(args[0]) or find(recs, args[0])
    tree = ancestors(recs, start)
    if "--ged-id" in sys.argv:
        return ged_id(recs, tree, "--zapsat" in sys.argv)
    queue = []
    if as_py:
        print("P = {")
    for k in sorted(tree):
        ind = tree[k]
        ev = events(ind, recs)
        facts = []
        for tag, d, p, extra in ev:
            if tag == "MARR":
                facts.append(" ".join(x for x in ("×", d, p, extra) if x))
            elif d or p:   # příčinu úmrtí jen do výpisu, ne do kostry dat (zdravotní údaj)
                facts.append(" ".join(x for x in (EVENTS[tag], d, p) if x) + (f" ({extra})" if extra and not as_py else ""))
        facts += [first(n, "OCCU") or n.get("val", "") for n in sub(ind, "OCCU")]
        notes = [n.get("val", "") for n in sub(ind, "NOTE")]
        notes = [(recs.get(t.strip(), {}).get("val", "") if re.fullmatch(r"\s*@[^@]+@\s*", t) else t) for t in notes]   # sdílená poznámka @N1@
        notes = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).strip() for t in notes]
        notes = [n for n in notes if n]
        b = next((year(d) for t, d, p, x in ev if t == "BIRT"), None)
        dd = next((year(d) for t, d, p, x in ev if t == "DEAT"), None)
        y = f"{b}–{dd}" if b and dd else (f"* {b}" if b else (f"† {dd}" if dd else ""))
        if as_py:
            note = " ".join(notes)   # !r = platný Python i pro uvozovky a „\“ ve jménech a poznámkách (osoby.py se spouští přes exec)
            ids = f", ged={ind['_id']!r}" + (f", uid={first(ind, '_UID').strip()!r}" if first(ind, "_UID").strip() else "")
            print(f' {k}: dict(n={name(ind)!r}, y={y!r}, st="fam", f={facts!r}, r=[]' + ids
                  + (f', note={note[:300]!r}' if note else "") + "),")
        else:
            print(f"\n{k} | {name(ind)} | {y}")
            for f in facts:
                print("   ", f)
            for n in notes:
                print("    pozn.:", n.replace("\n", " ")[:600])
        dated = [(t, d, p) for t, d, p, x in ev if p or d]
        for pref in ("DEAT", "BURI", "MARR", "BIRT", "CHR"):
            hit = [e for e in dated if e[0] == pref and e[2]]
            if hit:
                t, d, p = max(hit, key=lambda e: year(e[1]) or 0)
                queue.append((k, name(ind), {"DEAT": "úmrtí", "BURI": "úmrtí", "MARR": "sňatek"}.get(t, "narození"), d, p))
                break
    if as_py:
        print("}")
        return
    print("\nFRONTA ZÁPISŮ (nejmladší známá událost s místem; lhůty pro archiv: narození 100, sňatky 75, úmrtí 30 let):")
    now = datetime.date.today().year
    for k, n, what, d, p in queue:
        y = year(d)
        limit = {"úmrtí": 30, "sňatek": 75}.get(what, 100)
        where = "" if not y else ("  → matriky online" if now - y > limit else "  → zatím jen matriční úřad (lhůta)")
        print(f"  {k:>4} {n}: {what} {d} {p}".rstrip() + where)


if __name__ == "__main__":
    main()
