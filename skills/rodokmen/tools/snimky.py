#!/usr/bin/env python3
"""Společný rejstřík prohlížených snímků a seznam čtení k ověření – aby se k nim mohla vracet i jiná AI.

Proč: celé snímky z archivů (mezipaměť, `pracovni/`) jsou jen na jednom počítači a v gitu nejsou. Do gitu jde jen
tento malý soubor `data/snimky.tsv` (jeden řádek = jeden prohlédnutý snímek nebo úsek snímků), takže kdokoli
(jiná AI, vyšší model, Ladislav) ví, KDE co bylo čteno, a může si snímek znovu stáhnout (`tools/aron_img.py <kniha> <sn>`)
nebo otevřít přes odkaz. Soubor se slučuje po řádcích (`.gitattributes`: merge=union), víc AI může přidávat zároveň.

Použití (z kořene projektu):
  snimky.py pridej <archiv> <kniha> <snimek> "<co tam je>" [--denik N] [--stav STAV] [--cetl KDO]
      archiv   aron | mza | soa-praha | soa-trebon | matricula | jiny
      kniha    ARON: apu_id svazku; MZA: číslo knihy nebo id z adresy (detail/<id>); jinak popis
      snimek   číslo snímku, nebo úsek „10-12“ (jedna položka na úsek)
      co       krátce: rejstřík narozených R 1756–68; křty 1773 str. 15; …
      --denik  číslo řádku deníku, kde je výsledek
      --stav   precteno (výchozí) | nejisty | k-overeni | zapsano | zbytecne
               (zapsano = z toho vznikl záznam v data/zaznamy.json; k-overeni = čtení si žádá druhé oči)
  snimky.py sestav          vytvoří čitelný přehled data/SNIMKY.md (po knihách; neukládá se do gitu)
  snimky.py zdeniku         jednorázově doplní rejstřík z řádků deníku, kde jsou apu_id a „sn. N“ (kdo je, přeskočí)
  snimky.py k-overeni       vytvoří data/K_OVERENI.md: nejistá čtení, osoby `prob`/`mh`, rozpory (neukládá se do gitu)
  snimky.py hledej <text>   vypíše řádky rejstříku obsahující text

Záznamy jsou ověřitelné: u řádků s `zapsano` je vždy i klíč zápisu, který existuje v data/zaznamy.json.
"""
import csv, datetime, io, json, os, re, subprocess, sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TSV = os.path.join(ROOT, "data", "snimky.tsv")
HEAD = ["datum", "archiv", "kniha", "snimek", "co", "stav", "denik", "cetl"]
STAVY = {"precteno", "nejisty", "k-overeni", "zapsano", "zbytecne"}
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def nacti():
    if not os.path.exists(TSV):
        return []
    with open(TSV, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def uloz_radek(r):
    nove = not os.path.exists(TSV) or os.path.getsize(TSV) == 0
    with open(TSV, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEAD, delimiter="\t", lineterminator="\n")
        if nove:
            w.writeheader()
        w.writerow(r)


def klic(r):
    return (r["archiv"], r["kniha"], r["snimek"], r["denik"])


def pridej(arg):
    pos = [a for a in arg if not a.startswith("--")]
    opt = {}
    i = 0
    clean = []
    while i < len(arg):
        if arg[i].startswith("--") and i + 1 < len(arg):
            opt[arg[i][2:]] = arg[i + 1]
            i += 2
        else:
            clean.append(arg[i])
            i += 1
    if len(clean) < 4:
        sys.exit(__doc__)
    archiv, kniha, snimek, co = clean[:4]
    stav = opt.get("stav", "precteno")
    if stav not in STAVY:
        sys.exit(f"stav musí být jeden z: {', '.join(sorted(STAVY))}")
    r = dict(datum=datetime.date.today().isoformat(), archiv=archiv, kniha=kniha, snimek=snimek.replace("–", "-"),
             co=co.replace("\t", " ").replace("\n", " "), stav=stav, denik=opt.get("denik", ""),
             cetl=opt.get("cetl", "Claude"))
    if any(klic(x) == klic(r) for x in nacti()):
        print("už v rejstříku je (stejná kniha, snímek a deník)")
        return
    uloz_radek(r)
    print(f"zapsáno: {archiv} {kniha} sn. {r['snimek']} – {co}")


def zdeniku():
    ex = {klic(r) for r in nacti()}
    pocet = 0
    dp = os.path.join(ROOT, "data", "research_log.md")
    for l in open(dp, encoding="utf-8"):
        if not re.match(r"\| \d+ \|", l):
            continue
        sl = [c.strip() for c in l.split("|")]
        if len(sl) < 6:
            continue
        cislo, datum, kde, rozsah, cil = sl[1], sl[2], sl[3], sl[4], sl[5]
        uu = re.findall(UUID, kde)
        if not uu:
            continue
        # snímky z části „kde“ (a z rozsahu): „sn. 49“, „sn. 22–30“, „sn. 25, 26“
        txt = kde + " " + rozsah
        sn = []
        for m in re.finditer(r"sn\.?\s*(\d+)(?:\s*[–-]\s*(\d+))?", txt):
            sn.append(f"{m.group(1)}-{m.group(2)}" if m.group(2) else m.group(1))
        if not sn:
            continue
        co = re.sub(r"\s+", " ", cil)[:90]
        arch = "aron"
        for u in uu[:1]:
            for s in sn[:6]:
                r = dict(datum=datum, archiv=arch, kniha=u, snimek=s, co=co, stav="precteno", denik=cislo, cetl="Claude (z deníku)")
                if klic(r) in ex:
                    continue
                ex.add(klic(r))
                uloz_radek(r)
                pocet += 1
    print(f"doplněno {pocet} řádků z deníku (jen řádky s apu_id; ostatní doplňte ručně přes „pridej“)")


def svazky():
    try:
        return json.load(open(os.path.join(ROOT, "data", "svazky.json"), encoding="utf-8"))
    except Exception:
        return {}


def sestav():
    rad = nacti()
    sv = svazky()
    kn = {}
    for r in rad:
        kn.setdefault((r["archiv"], r["kniha"]), []).append(r)
    out = ["# Přehled prohlížených snímků (generováno `tools/snimky.py sestav`, neukládat do gitu)\n",
           "Zdroj: `data/snimky.tsv`. Snímek se znovu stáhne `python -I -X utf8 tools/aron_img.py <apu_id> <snímek> 0 pracovni/x.jpg` (ARON; "
           "MZA jen ručně přes prohlížeč). Stavy: precteno, nejisty, **k-overeni**, zapsano, zbytecne.\n"]
    for (arch, k), lst in sorted(kn.items()):
        nm = ""
        if arch == "aron":
            s = sv.get(k[:8], {})
            nm = s.get("svazek", "")
        out.append(f"\n## {arch} · {k} {('– ' + nm) if nm else ''}\n")
        out.append("| snímek | co | stav | deník | datum |\n|---|---|---|---|---|")
        def kk(r):
            m = re.match(r"\d+", r["snimek"])
            return int(m.group()) if m else 0
        for r in sorted(lst, key=kk):
            out.append(f"| {r['snimek']} | {r['co']} | {r['stav']} | {r['denik']} | {r['datum']} |")
    p = os.path.join(ROOT, "data", "SNIMKY.md")
    open(p, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print(f"{p}: {len(rad)} řádků, {len(kn)} knih")


def k_overeni():
    sys.path.insert(0, os.path.join(ROOT, "data"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("osoby", os.path.join(ROOT, "data", "osoby.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    P, SIDE = getattr(m, "P", {}), getattr(m, "SIDE", [])
    zaz = json.load(open(os.path.join(ROOT, "data", "zaznamy.json"), encoding="utf-8"))
    out = ["# Čtení a ztotožnění k ověření (generováno `tools/snimky.py k-overeni`, neukládat do gitu)\n",
           "Pro vyšší model: porovnej s výřezem zápisu (`vyrezy/<klíč>.jpg`, plné rozlišení `zdroje/<klíč>.jpg`) a případně se snímkem "
           "z archivu (`data/snimky.tsv`, `odkaz` v `zaznamy.json`).\n", "\n## Osoby se stavem prob / mh (neověřené)\n"]
    for k, o in sorted(P.items()):
        if o.get("st") in ("prob", "mh"):
            out.append(f"- **{k}** {o['n']} ({o.get('y','')}) [{o['st']}] – {o.get('note','')[:200]}")
    out.append("\n## Osoby s nejistým čtením ve jméně nebo faktech\n")
    for k, o in sorted(P.items()):
        t = o["n"] + " " + " ".join(o.get("f", []))
        if "(?)" in t or "nejist" in t.lower():
            out.append(f"- **{k}** {o['n']} – {'; '.join(o.get('f', []))[:200]}")
    out.append("\n## Zápisy s nejistým čtením\n")
    for r in zaz:
        t = r.get("shrnuti", "")
        if "(?)" in t or "nejist" in t.lower():
            out.append(f"- `{r['klic']}` ({r.get('datum','')}) – {t[:160]}")
    out.append("\n## Otevřené otázky a rozpory (ISSUES)\n")
    for q, a in getattr(m, "ISSUES", []):
        if not a.startswith("Vyřešeno"):
            out.append(f"- {q} → {a[:220]}")
    p = os.path.join(ROOT, "data", "K_OVERENI.md")
    open(p, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print(p)


def hledej(arg):
    t = " ".join(arg).lower()
    for r in nacti():
        if t in "\t".join(r.values()).lower():
            print(f"{r['archiv']} {r['kniha']} sn. {r['snimek']} [{r['stav']}] #{r['denik']} {r['co']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    c, a = sys.argv[1], sys.argv[2:]
    {"pridej": lambda: pridej(a), "sestav": sestav, "zdeniku": zdeniku, "k-overeni": k_overeni,
     "hledej": lambda: hledej(a)}.get(c, lambda: sys.exit(__doc__))()
