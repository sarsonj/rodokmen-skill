#!/usr/bin/env python3
"""Statistiky rodokmenu pro web: čte web/src/data/site.json (předky a zápisy z exportu) a zapíše
web/src/data/statistiky.json. Volá ho tools/export_web.py na konci exportu; jde spustit i samostatně.

Počítá se jen z faktů předků (pole `facts`), boční příbuzní se nepočítají:
  narození „* 12. 3. 1873 Obec čp. 5“, úmrtí „† 14. 5. 1902“, sňatek „× 28. 1. 1897 Obec Jméno“,
  věk „(24 let při sňatku)“, povolání podle klíčových slov, církve podle slov „církev, vyznání“.
"""
import json, os, re, sys
from collections import Counter, defaultdict
from datetime import date

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "web", "src", "data", "site.json")
OUT = os.path.join(ROOT, "web", "src", "data", "statistiky.json")

DATE = r"(\d{1,2})\.\s*(?:\((\d{1,2})\.\?\)|(\d{1,2}))\.\s*(\d{4})"
MESICE = ["leden", "únor", "březen", "duben", "květen", "červen", "červenec", "srpen", "září", "říjen", "listopad", "prosinec"]

# klíčové slovo (začátek slova, malými písmeny – „Kovář“ s velkým je příjmení) → (povolání, skupina);
# rozhoduje první shoda v pořadí seznamu, proto obecná slova (dělník, mistr) až nakonec
POVOLANI = [
    ("tkad", "tkadlec", "řemeslo"), ("tkalc", "tkadlec", "řemeslo"), ("soukeník", "soukeník", "řemeslo"),
    ("obuvn", "obuvník", "řemeslo"), ("švec", "obuvník", "řemeslo"), ("krejč", "krejčí", "řemeslo"),
    ("kovář", "kovář", "řemeslo"), ("kolář", "kolář", "řemeslo"), ("zedník", "zedník", "řemeslo"), ("tesař", "tesař", "řemeslo"),
    ("truhlář", "truhlář", "řemeslo"), ("bednář", "bednář", "řemeslo"), ("sklenář", "sklenář", "řemeslo"),
    ("hrnčíř", "hrnčíř", "řemeslo"), ("jirchář", "jirchář", "řemeslo"), ("koželuh", "koželuh", "řemeslo"),
    ("mlynář", "mlynář", "řemeslo"), ("pekař", "pekař", "řemeslo"), ("řezník", "řezník", "řemeslo"), ("sládek", "sládek", "řemeslo"),
    ("sedlák", "sedlák", "zemědělství"), ("rolník", "rolník", "zemědělství"), ("hospodář", "hospodář", "zemědělství"),
    ("chalupník", "chalupník", "zemědělství"), ("domkář", "domkář", "zemědělství"), ("podsedník", "podsedník", "zemědělství"),
    ("familiant", "familiant", "zemědělství"), ("výměnk", "výměnkář", "zemědělství"), ("na výměnku", "výměnkář", "zemědělství"),
    ("podruh", "podruh", "zemědělství"), ("čeledín", "čeledín", "zemědělství"), ("děveč", "děvečka", "zemědělství"),
    ("zahradník", "zahradník", "zemědělství"), ("pastýř", "pastýř", "zemědělství"), ("ovčák", "ovčák", "zemědělství"),
    ("hajný", "hajný", "les"), ("myslivec", "myslivec", "les"), ("lesník", "lesník", "les"), ("lesní", "lesník", "les"),
    ("strojvůd", "strojvůdce", "doprava"), ("výpravčí", "výpravčí", "doprava"), ("průvodčí", "průvodčí", "doprava"),
    ("železničář", "železničář", "doprava"), ("na dráze", "železničář", "doprava"), ("při dráze", "železničář", "doprava"),
    ("kočí", "kočí", "doprava"), ("povozník", "povozník", "doprava"), ("vozka", "kočí", "doprava"),
    ("kupec", "kupec", "obchod"), ("obchodník", "obchodník", "obchod"), ("hokynář", "hokynář", "obchod"),
    ("hostinsk", "hostinský", "úřad a služby"), ("šenkýř", "hostinský", "úřad a služby"), ("učitel", "učitel", "úřad a služby"),
    ("kantor", "učitel", "úřad a služby"), ("úředník", "úředník", "úřad a služby"), ("četník", "četník", "úřad a služby"),
    ("policajt", "policista", "úřad a služby"), ("strážník", "policista", "úřad a služby"), ("rychtář", "rychtář", "úřad a služby"),
    ("soudní sluha", "soudní sluha", "úřad a služby"), ("sluha", "sluha", "úřad a služby"), ("služka", "služka", "úřad a služby"),
    ("voják", "voják", "úřad a služby"), ("kaprál", "voják", "úřad a služby"), ("vysloužil", "voják", "úřad a služby"),
    ("havíř", "horník", "dělník"), ("horník", "horník", "dělník"), ("nádeník", "nádeník", "dělník"),
    ("tovární", "tovární dělník", "dělník"), ("dělník v továrně", "tovární dělník", "dělník"), ("dělník", "dělník", "dělník"),
    ("mistr", "mistr řemesla", "řemeslo"),   # „tkalcovský mistr“ dopadne jako tkadlec, „purkmistr“ se nepočítá (začátek slova)
]
POVOLANI_RE = [(re.compile(r"(?<!\w)" + re.escape(kw)), name, grp) for kw, name, grp in POVOLANI]


def parse_date(text):
    m = re.search(DATE, text)
    if not m:
        return None
    d, mq, mo, y = m.groups()
    try:
        return date(int(y), int(mq or mo), int(d)), bool(mq)
    except ValueError:
        return None


def first(facts, sign):
    return [f for f in facts if f.startswith(sign)]


def place_of(text):
    """„* 28. 7. 1870 Horní Lhota čp. 45“ → „Horní Lhota“."""
    m = re.search(DATE + r"\s+(.+)", text)
    if not m:
        return None
    rest = m.group(5)
    rest = re.split(r"\s+čp\.|\s*\(|,|\s+–", rest)[0].strip()
    return rest or None


def age(a, b):
    return b.year - a.year - ((b.month, b.day) < (a.month, a.day))


def main():
    site = json.load(open(SITE, encoding="utf-8"))
    people = list(site["people"].values())
    anc = [p for p in people if p.get("k", 0) >= 1 and p.get("st") != "unk" and not p["name"].startswith(("otec ", "matka "))]
    bys = {p["slug"]: p for p in people}

    def ref(p, extra=None):
        r = {"slug": p["slug"], "name": p["name"], "years": p.get("years", "")}   # s "puvodni_jmena" v původním tvaru
        if extra is not None:
            r["val"] = extra
        return r

    born, died = {}, {}
    for p in anc:
        b = next((parse_date(f) for f in first(p["facts"], "*") if parse_date(f)), None)
        d = next((parse_date(f) for f in first(p["facts"], "†") if parse_date(f)), None)
        if b:
            born[p["slug"]] = b[0]
        if d:
            died[p["slug"]] = d[0]

    # věk dožití
    life = []
    for s, d in died.items():
        if s in born:
            life.append(ref(bys[s], age(born[s], d)))
    life.sort(key=lambda r: -r["val"])

    # sňatky: věk a měsíc
    wed_age = {"M": [], "F": []}
    months = Counter()
    seen = set()
    for p in anc:
        sex = p.get("sex") or ("M" if p["k"] % 2 == 0 else "F")
        for f in first(p["facts"], "×"):
            w = parse_date(f)
            if not w:
                continue
            key = (w[0], place_of(f))
            if key not in seen:
                seen.add(key)
                months[w[0].month] += 1
            a = None
            if p["slug"] in born:
                a = age(born[p["slug"]], w[0])
            else:
                m = next((re.search(r"(\d+) let při sňatku", g) for g in p["facts"] if "let při sňatku" in g), None)
                if m:
                    a = int(m.group(1))
            if a is not None and 14 <= a <= 80:
                wed_age[sex].append(ref(p, a))
            break   # jen první (nejstarší zapsaný) sňatek

    # věk otce a matky při narození dítěte (generační odstup)
    gap = {"M": [], "F": []}
    for p in anc:
        if p["slug"] not in born:
            continue
        for par, sex in (("father", "M"), ("mother", "F")):
            s = p.get(par)
            if s and s in born:
                gap[sex].append({"parent": ref(bys[s]), "child": ref(p), "val": age(born[s], born[p["slug"]])})

    # povolání
    occ = defaultdict(list)
    groups = Counter()
    for p in anc:
        found = []
        for f in p["facts"]:
            if f.startswith(("*", "†", "×")) or re.search(r"\bdcera\b|\bsyn\b", f):
                continue
            for rx, name, grp in POVOLANI_RE:
                if rx.search(f) and name not in [x[0] for x in found]:
                    found.append((name, grp))
                    break
        for name, grp in found:
            occ[(name, grp)].append(ref(p))
        if found:
            groups[found[0][1]] += 1
    occ_list = sorted(({"name": n, "group": g, "people": v} for (n, g), v in occ.items()), key=lambda x: (-len(x["people"]), x["name"]))

    # místa narození
    places = Counter()
    for p in anc:
        for f in first(p["facts"], "*"):
            pl = place_of(f)
            if pl and parse_date(f):
                pl = re.sub(r"\s+\(.*", "", pl)
                places[pl] += 1
                break

    # křestní jména
    names = {"M": Counter(), "F": Counter()}
    for p in anc:
        sex = p.get("sex") or ("M" if p["k"] % 2 == 0 else "F")
        fn = (p.get("modern") or p["name"]).split()[0]
        if fn[0].isupper() and fn not in ("Pozn.",):
            names[sex][fn] += 1

    # víra a církve
    faith = []
    for p in anc:
        for f in p["facts"]:
            if re.search(r"církv|vyznání|evangel|přestoupil|židovsk|izraelit", f, re.I):
                faith.append(ref(p, f))
    illeg = [ref(p) for p in anc if any(re.search(r"nemanželsk", f, re.I) for f in p["facts"] + [p.get("note") or ""])]
    legit = [ref(p) for p in anc if any(re.search(r"legitim", f, re.I) for f in p["facts"] + [p.get("note") or ""])]

    # zápisy
    recs = list(site["records"].values()) if isinstance(site["records"], dict) else site["records"]
    druh = Counter()
    arch = Counter()
    decades = Counter()
    for r in recs:
        dr = r.get("kind") or r.get("druh") or ""
        druh[{"N": "křty a narození", "O": "sňatky", "Z": "úmrtí"}.get(dr, "jiné")] += 1
        arch[r.get("portal") or "jiné"] += 1
        y = re.findall(r"\d{4}", r.get("datum") or r.get("date") or "")
        if y:
            decades[int(y[-1]) // 50 * 50] += 1

    gens = Counter(p.get("gen", 0) for p in anc)
    years_b = sorted(born.values())
    out = {
        "prehled": {
            "predku": len(anc),
            "dolozeno": sum(1 for p in anc if p.get("st") == "doc"),
            "generaci": max(gens) if gens else 0,
            "zapisu": len(recs),
            "nejstarsi_narozeni": years_b[0].year if years_b else None,
            "prijmeni": len({(p.get("modern") or p["name"]).split()[-1].replace("ová", "") for p in anc}),
            "mist": len(places),
        },
        "generace": [{"gen": g, "pocet": gens[g], "max": 2 ** g} for g in sorted(gens)],
        "povolani": occ_list,
        "povolani_skupiny": [{"name": k, "count": v} for k, v in groups.most_common()],
        "mista": [{"name": k, "count": v} for k, v in places.most_common(15)],
        "doziti": {"list": life, "prumer": round(sum(r["val"] for r in life) / len(life), 1) if life else None},
        "snatek_vek": {s: {"list": sorted(v, key=lambda r: r["val"]), "prumer": round(sum(r["val"] for r in v) / len(v), 1) if v else None}
                       for s, v in wed_age.items()},
        "snatek_mesice": [{"name": MESICE[m - 1], "count": months.get(m, 0)} for m in range(1, 13)],
        "rodice_vek": {s: {"prumer": round(sum(x["val"] for x in v) / len(v), 1) if v else None,
                           "nejmladsi": min(v, key=lambda x: x["val"]) if v else None,
                           "nejstarsi": max(v, key=lambda x: x["val"]) if v else None, "pocet": len(v)} for s, v in gap.items()},
        "jmena": {s: [{"name": k, "count": v} for k, v in c.most_common(8)] for s, c in names.items()},
        "vira": faith,
        "nemanzelske": illeg,
        "legitimace": legit,
        "zapisy_druh": [{"name": k, "count": v} for k, v in druh.most_common()],
        "zapisy_portal": [{"name": k, "count": v} for k, v in arch.most_common()],
        "zapisy_obdobi": [{"name": f"{d}–{d + 49}", "count": decades[d]} for d in sorted(decades)],
    }
    json.dump(out, open(OUT, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(f"statistiky: {len(anc)} předků, {len(life)} s věkem dožití, {sum(len(v) for v in wed_age.values())} s věkem při sňatku, "
          f"{len(occ_list)} povolání")


if __name__ == "__main__":
    main()
