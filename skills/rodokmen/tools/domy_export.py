#!/usr/bin/env python3
"""Domy předků pro web (stránka /domy/): čte data/domy/domy.geojson (výstup skillu stare-adresy, `mapa.py`)
a web/src/data/site.json, zapíše web/src/data/domy.json a zkopíruje výřezy skic do web/public/domy/vyrezy/.
Volá ho tools/export_web.py; bez data/domy/domy.geojson zapíše prázdný domy.json a stránka Domy se v menu neukáže.

Zmínky „<obec> čp. <číslo>“ (i skloněné „v Holicích čp. 12“) hledá ve faktech a poznámkách předků, v textech
bočních příbuzných (SIDE) a v souhrnech zápisů. Obec pozná podle data/mista.json (pole `re`, volitelně `zkratky`,
např. "zkratky": ["HL"] pro „HL čp. 12“) a podle obcí v domy.geojson; vzor `re` z mista.json má
vždy přednost (u obcí, kde se kmen při skloňování mění: Praha → v Praze). Holé „v čp. 48“ přiřadí k obci, kterou
osoba jinde zmiňuje nejčastěji. Přiřadí zmínky ke geokódovaným domům (odkazy oběma směry) a adresy, které
na mapě chybí, uloží do data/domy/chybi.txt (podklad pro další geokódování)."""
import json, os, re, shutil, sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "domy")
SITE = os.path.join(ROOT, "web", "src", "data", "site.json")
OUT = os.path.join(ROOT, "web", "src", "data", "domy.json")
PUB = os.path.join(ROOT, "web", "public", "domy")

UP, LO = "A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ", "a-záčďéěíňóřšťúůýž"
SLOVO = rf"[{UP}][{LO}]+"
# „Obec čp. 12“, „Obec (Ort) No. 12“; holé „č.“ jen s nejvýš trojmístným číslem („č. 1834“ bývá rok nebo strana)
CP_RE = re.compile(rf"(?P<obec>{SLOVO}(?:[ -](?:{SLOVO}|u|nad|pod)){{0,3}})\s+(?:\([^)]*\)\s+)?"
                   rf"(?:(?:čp\.|č\.\s?p\.|No\.?)\s?(?P<cp>\d+)|č\.\s?(?P<cp2>\d{{1,3}})\b)")
ROK_RE = re.compile(r"\b(1[6-9]\d\d)\b")
BARE_RE = re.compile(r"(?:\bv |/ )čp\.\s?(\d+)")


def vzor_obce(nazev):
    """„Vysoké Mýto“ → regulární výraz i pro skloněné tvary („ve Vysokém Mýtě“, „Kostelec“ → „v Kostelci“)."""
    slova = []
    for w in re.split(r"[\s-]+", nazev.split(" (")[0].strip()):
        if len(w) > 3 and w.endswith("ec"):       # Kostelec → v Kostelci, Hradec → Hradce
            kmen = re.escape(w[:-2]) + "(?:ec|c)"
        elif len(w) > 3 and w[-2:] in ("ha", "ka"):  # Lhotka → v Lhotce (Praha → v Praze řeš vzorem v mista.json)
            kmen = re.escape(w[:-2]) + ("(?:h|z)" if w[-2] == "h" else "(?:k|c)")
        elif len(w) > 3 and w[-1] in "aáeéěiíoóuůyý":
            kmen = re.escape(w[:-1])
        elif len(w) > 3 and w[-1] in "ňťď":            # Roveň → v Rovni (i s vypadávajícím e)
            kmen = re.escape(w[:-2]) + ("e?" if w[-2] == "e" else re.escape(w[-2])) + "[" + w[-1] + "ntd"["ňťď".index(w[-1])] + "]"
        else:
            kmen = re.escape(w)
        slova.append(kmen + rf"[{LO}]*")
    return r"\b" + r"[\s-]+".join(slova) + r"\b"


def main():
    gj = os.path.join(SRC, "domy.geojson")
    shutil.rmtree(os.path.join(PUB, "vyrezy"), ignore_errors=True)   # bez starých výřezů smazaných domů
    if not os.path.exists(gj):
        json.dump({"domy": [], "osoby": {}, "zapisy": {}, "rody": []}, open(OUT, "w", encoding="utf-8", newline="\n"))
        return
    feats = json.load(open(gj, encoding="utf-8"))["features"]
    site = json.load(open(SITE, encoding="utf-8"))
    people, records = site["people"], site["records"]
    records = records if isinstance(records, dict) else {r["key"]: r for r in records}
    mp = os.path.join(ROOT, "data", "mista.json")
    mista = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
    # vzory z mista.json (spravuje uživatel) mají přednost; obce z geojsonu jen tam, kde žádný nesedí. Vzor z mista.json
    # tedy rozhoduje i o tom, co je táž obec („Řetov“ = Řetová i Velká Řetová) – musí být jednoznačný
    # (Lhota vs. Dolní Lhota: „(?<!Dolní )Lhot“, viz reference/data.md)
    mpats = [(n, re.compile(e["re"])) for n, e in mista.items() if e.get("re")]
    gpats = [(f["properties"]["obec"], re.compile(vzor_obce(f["properties"]["obec"])))
             for f in feats if f["properties"].get("obec")]
    zkratky = {z: n for n, e in mista.items() for z in e.get("zkratky", [])}
    ZK_RE = re.compile(r"\b(" + "|".join(map(re.escape, zkratky)) + r")\s+(?:čp\.|č\.)\s?(\d+)") if zkratky else None

    def nejdelsi(pats, text, hledat):
        """Obec s nejdelší shodou („Dolní Lhota“ před „Lhota“); při stejné délce ta dřív uvedená."""
        best = max(((len(m.group(0)), -i, n) for i, (n, p) in enumerate(pats) for m in [hledat(p, text)] if m), default=None)
        return best[2] if best else None

    def obec_norm(text):
        """Obec zmíněná kdekoli v textu."""
        return nejdelsi(mpats, text, re.Pattern.search) or nejdelsi(gpats, text, re.Pattern.search)

    def nazev_norm(nazev):
        """Název obce (z geojsonu nebo zachycený před „čp.“). „Hořice (Horschitz)“ i holé „Hořice“ dopadnou stejně;
        mezera na konci kvůli vzorům z mista.json typu „Hořic[eí ]“. Obce z geojsonu se hledají od začátku, nejdřív
        celý název, pak bez slov zleva („Josef Kovář Holice“ → „Holice“)."""
        kus = nazev.split(" (")[0] + " "
        o = nejdelsi(mpats, kus, re.Pattern.search)
        slova = kus.split()
        for i in range(len(slova)):
            o = o or nejdelsi(gpats, " ".join(slova[i:]) + " ", re.Pattern.match)
        return o

    # geokódované domy podle (obec, čp)
    domy, by_key = [], {}
    os.makedirs(os.path.join(PUB, "vyrezy"), exist_ok=True)
    for f in feats:
        pr = dict(f["properties"])
        lon, lat = f["geometry"]["coordinates"]
        v = pr.get("vyrez")
        pr["vyrez"] = "/domy/vyrezy/" + os.path.basename(v) if v and os.path.exists(os.path.join(SRC, v)) else None
        d = dict(pr, lat=lat, lon=lon, predci=[], zapisy=[], _vyrez=v)
        domy.append(d)
        by_key[(nazev_norm(pr.get("obec", "")) or pr.get("obec"), int(pr.get("cp") or 0))] = d

    def zminky(text):
        out = []
        for m in CP_RE.finditer(text or ""):
            o = nazev_norm(m.group("obec"))
            if o:
                out.append((o, int(m.group("cp") or m.group("cp2"))))
        if ZK_RE:
            out += [(zkratky[m.group(1)], int(m.group(2))) for m in ZK_RE.finditer(text or "")]
        return out

    osoby_domy, zapisy_domy, chybi = {}, {}, {}

    def zapis(key, kdo, rok, kam_id, kam_list, item):
        d = by_key.get(key)
        if d:
            if item not in d[kam_list]:
                d[kam_list].append(item)
            lst = kam_id.setdefault(item["slug"] if kam_list == "predci" else item["key"], [])
            if d["id"] not in lst:
                lst.append(d["id"])
        else:
            c = chybi.setdefault(key, {"kdo": [], "roky": set()})
            if kdo not in c["kdo"]:
                c["kdo"].append(kdo)
            if rok:
                c["roky"].add(rok)

    lines_by_k = {str(l["k"]): l for l in site["lines"].values()}
    by_k = {p.get("k"): p for p in people.values()}

    def rod_of(p):
        """Rod osoby; u rodičů a prarodičů (č. 2–7) rod po otci (nejbližší pradědeček č. 8–15)."""
        k = p.get("k") or 0
        ln = lines_by_k.get(str(p.get("line")))
        while not ln and 0 < k < 8:
            k *= 2
            ln = lines_by_k.get(str(by_k.get(k, {}).get("line"))) or lines_by_k.get(str(k) if k >= 8 else "")
        return ln["slug"] if ln else None

    for p in people.values():
        name = p["name"]   # s "puvodni_jmena" v původním tvaru, jako všude na webu
        item = {"slug": p["slug"], "name": name, "years": p.get("years", ""), "rel": p.get("rel", ""), "rod": rod_of(p)}
        # (text, kdo v domě žil, kam zapsat odkaz osoba → dům); adresy bočních příbuzných patří jim, ne předkovi –
        # u domu se ukážou jménem příbuzného s odkazem na jeho kartičku u předka, předkovi se dům nepřipíše
        texty = [(t, item, osoby_domy) for t in p.get("facts", []) + [p.get("note") or ""]]
        for i, s in enumerate(p.get("side", [])):
            if isinstance(s, dict):
                sn = s.get("name") or ""
                m = re.match(r"(.*?)\s*\(([^)]*)\)$", sn)
                si = {"slug": p["slug"], "name": m.group(1) if m else sn, "years": m.group(2) if m else "",
                      "rel": f"{p.get('rel', '')} {name}".strip(), "rod": item["rod"], "bocni": f"pribuzny-{i}"}
                texty.append((s.get("text") or "", si, {}))
        plne = [z for t, _, _ in texty for z in zminky(t)]
        vychozi = max({o for o, _ in plne}, key=[o for o, _ in plne].count) if plne else obec_norm(" ".join(t for t, _, _ in texty))
        for t, kdo, kam in texty:
            klice = zminky(t)
            if vychozi:
                klice += [(vychozi, int(m.group(1))) for m in BARE_RE.finditer(t)]
            for key in dict.fromkeys(klice):
                roky = [int(r) for r in ROK_RE.findall(t)]
                zapis(key, kdo["name"], min(roky) if roky else None, kam, "predci", kdo)
    for r in records.values():
        item = {"key": r["key"], "title": r["title"], "date": r.get("date", "")}
        for key in zminky((r.get("summary") or "") + " " + (r.get("cs") or "")):
            roky = [int(x) for x in ROK_RE.findall(r.get("date") or "")]
            zapis(key, "zápis: " + r["title"], roky[0] if roky else None, zapisy_domy, "zapisy", item)

    # domy bez předka i bez zápisu do rodokmenu nepatří (třeba adresy z jiného projektu ve sdíleném adresy.json)
    vyrazene = [d["id"] for d in domy if not d["predci"] and not d["zapisy"]]
    domy = [d for d in domy if d["predci"] or d["zapisy"]]
    for d in domy:
        v = d.pop("_vyrez")
        if d["vyrez"]:
            shutil.copy2(os.path.join(SRC, v), os.path.join(PUB, "vyrezy", os.path.basename(v)))
        d["predci"].sort(key=lambda p: bool(p.get("bocni")))   # přímí předci první, boční příbuzní za nimi
        # rod domu (barva značky) = rod, ke kterému patří nejvíc lidí, kteří v něm žili; jinak podle lidí ze zápisů
        cnt = {}
        for p in d["predci"]:
            if p.get("rod"):
                cnt[p["rod"]] = cnt.get(p["rod"], 0) + 1
        if not cnt:
            for z in d["zapisy"]:
                for s in records.get(z["key"], {}).get("people", []):
                    ln = lines_by_k.get(str(people.get(s, {}).get("line")))
                    if ln:
                        cnt[ln["slug"]] = cnt.get(ln["slug"], 0) + 1
        d["rod"] = max(cnt, key=cnt.get) if cnt else None
    rody = [{"slug": l["slug"], "name": l["name"], "color": l["color"]} for l in sorted(site["lines"].values(), key=lambda l: l["k"])]
    domy.sort(key=lambda d: (d.get("obec", ""), d.get("cp") or 0))
    json.dump({"domy": domy, "osoby": osoby_domy, "zapisy": zapisy_domy, "rody": rody},
              open(OUT, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    lines = []
    for (o, cp), c in sorted(chybi.items(), key=lambda x: (min(x[1]["roky"]) if x[1]["roky"] else 9999, x[0][0], x[0][1])):
        rok = f"{min(c['roky'])}" if c["roky"] else "?"
        lines.append(f"{o} čp. {cp}\t{rok}\t{'; '.join(c['kdo'][:4])}")
    open(os.path.join(SRC, "chybi.txt"), "w", encoding="utf-8", newline="\n").write(
        "# Adresy zmíněné v rodokmenu, které nejsou v domy.geojson (obec, čp., nejstarší rok, kdo)\n" + "\n".join(lines) + "\n")
    print(f"domy: {len(domy)} adres; {sum(1 for d in domy if any(not p.get('bocni') for p in d['predci']))} s předkem, "
          f"{sum(1 for d in domy if d['zapisy'])} se zápisem; {len(osoby_domy)} osob s domem; "
          f"chybí na mapě {len(chybi)} adres (data/domy/chybi.txt)"
          + (f"; vynecháno bez vazby na rodokmen: {', '.join(vyrazene)}" if vyrazene else ""))


if __name__ == "__main__":
    main()
