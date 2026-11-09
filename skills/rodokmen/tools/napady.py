#!/usr/bin/env python3
"""Náměty na zajímavosti: projde data/osoby.py a vypíše věci, ze kterých bývají hezké „fun facts“.

Použití (z kořene projektu): python3 -I tools/napady.py [složka projektu]

Hledá: svatby krátce před porodem (a „přesné trefy“ devět měsíců po svatbě), děti narozené před svatbou,
velký věkový rozdíl manželů, sňatky velmi mladých a starých, vícenásobné sňatky, dlouhověkost, úmrtí matky
krátce po porodu, úmrtí v letech epidemií a válek, rod v jednom domě po generace, předky v rodokmenu vícekrát,
nejstarší předky, řemesla v rodech, narození o Vánocích.

Jsou to jen NÁMĚTY z dat – každý ověř v zápisu (data bývají nejistá) a teprve pak napiš do data/zajimavosti.md
jako krátký příběh (viz reference/pribehy.md).
"""
import datetime, os, re, sys
if sys.argv[1:2] in (["-h"], ["--help"]):   # nápověda místo pádu
    sys.exit(__doc__.strip())
from collections import defaultdict
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})"
EPIDEMIE = {1771: "hladomor", 1772: "hladomor a tyfus", 1805: "tyfus", 1831: "cholera", 1832: "cholera", 1836: "cholera",
            1849: "cholera", 1850: "cholera", 1855: "cholera", 1866: "cholera a prusko-rakouská válka",
            1873: "cholera", 1918: "španělská chřipka", 1919: "španělská chřipka"}


def load():
    ns = {}
    exec(open(os.path.join(ROOT, "data", "osoby.py"), encoding="utf-8-sig").read(), ns)
    return ns["P"], ns.get("LINES", {}), ns.get("SAME", {})


def event(p, sym):
    """Všechna data události (* × †) z faktů osoby."""
    out = []
    for f in p.get("f", []):
        if f.strip().startswith(sym):
            m = re.search(DATE, f)
            if m:
                try:
                    out.append((datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1))), f))
                except ValueError:
                    pass
    return out


def year_of(p, sym):
    for f in p.get("f", []):
        if f.strip().startswith(sym):
            m = re.search(r"\d{4}", f)
            if m:
                return int(m.group())
    return None


def line_of(k):
    while k > 15:
        k //= 2
    return k if k >= 8 else None


def main():
    P, LINES, SAME = load()
    real = {k: p for k, p in P.items() if k not in SAME}
    name = lambda k: f"{P[k]['n']} ({k})"
    ideas = defaultdict(list)

    for k, p in real.items():
        births, marr, deaths = event(p, "*"), event(p, "×"), event(p, "†")
        b = births[0][0] if births else None
        # svatba × narození dítěte v přímé linii (dítě předka k je k // 2)
        if k >= 2 and k % 2 == 0 and marr and (k // 2) in P:
            cb = event(P[k // 2], "*")
            wife = P.get(k + 1, {}).get("n", "").split()
            mine = [m for m in marr if wife and wife[-1][:5] in m[1]] or (marr if len(marr) == 1 else [])
            if cb:
                for md, _ in mine:
                    days = (cb[0][0] - md).days
                    if -3650 < days < 0:
                        ideas["Dítě narozené před svatbou"].append(f"{name(k // 2)} se narodil(a) {-days} dní PŘED svatbou rodičů {name(k)} a {name(k + 1)} – legitimace?")
                    elif 0 <= days < 245:
                        ideas["Svatba na poslední chvíli"].append(f"{name(k // 2)} se narodil(a) {days} dní po svatbě rodičů {name(k)} × {name(k + 1)}")
                    elif 255 <= days <= 280:
                        ideas["Přesná trefa (≈ 9 měsíců po svatbě)"].append(f"{name(k // 2)} se narodil(a) {days} dní po svatbě rodičů")
        # věk při sňatku, věkový rozdíl manželů
        if b and marr:
            for md, f in marr:
                age = (md - b).days / 365.25
                if age < 19:
                    ideas["Velmi mladý sňatek"].append(f"{name(k)} se vdávala/ženil v {age:.0f} letech ({f})")
                elif age > 45:
                    ideas["Sňatek ve zralém věku"].append(f"{name(k)} se ženil/vdávala v {age:.0f} letech ({f})")
        if k % 2 == 0 and (k + 1) in real and b:
            wb = event(real[k + 1], "*")
            if wb:
                diff = (wb[0][0] - b).days / 365.25
                if abs(diff) >= 12:
                    older = name(k) if diff > 0 else name(k + 1)
                    ideas["Velký věkový rozdíl manželů"].append(f"{name(k)} × {name(k + 1)}: rozdíl {abs(diff):.0f} let (starší {older})")
        txt = " | ".join(p.get("f", []) + [p.get("note", "")])
        m = re.search(r"[^|]{0,60}\b(vdov|podruhé|potřetí)[^|]{0,80}", txt)
        if len([f for f in p.get("f", []) if f.strip().startswith("×")]) >= 2 or m:
            ideas["Více sňatků / vdovství"].append(f"{name(k)}: " + ("; ".join(f for f in p.get("f", []) if f.strip().startswith("×")) if not m else m.group(0).strip())[:200])
        # dlouhověkost, úmrtí po porodu, epidemie
        if b and deaths:
            age = (deaths[0][0] - b).days / 365.25
            if age >= 85:
                ideas["Dlouhověkost"].append(f"{name(k)} se dožil(a) {age:.0f} let")
        if k % 2 == 1 and k >= 3 and deaths and (k // 2) in P:
            cb = event(P[k // 2], "*")
            if cb and 0 <= (deaths[0][0] - cb[0][0]).days <= 60:
                ideas["Matka zemřela krátce po porodu"].append(f"{name(k)} zemřela {(deaths[0][0] - cb[0][0]).days} dní po narození {name(k // 2)}")
        dy = year_of(p, "†")
        if dy in EPIDEMIE:
            ideas["Úmrtí v roce epidemie / války"].append(f"{name(k)} † {dy} – {EPIDEMIE[dy]}? (ověř příčinu v zápisu)")
        if b and b.month == 12 and b.day in (24, 25):
            ideas["Narození o Vánocích"].append(f"{name(k)} * {b.day}. 12. {b.year}")

    # rod v jednom domě: stejná obec a číslo popisné přes generace v otcovské linii
    shown = {}
    for k in sorted(real):
        if k % 2 == 1 or (k // 2 in real and k // 2 >= 2 and (k // 2) % 2 == 0):
            continue   # začni od nejmladšího muže řetězce
        chain, kk = [], k
        while kk in real:
            houses = re.findall(r"([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][\wáčďéěíňóřšťúůýž]+(?: [\wáčďéěíňóřšťúůýž]+)?) (?:čp\.|č\.|No\.?|N\.)\s*(\d+)", " ".join(real[kk].get("f", [])))
            keys = {}
            for o, n in houses:
                keys.setdefault(" ".join(w[:4] for w in o.split()) + f" {n}", f"{o} čp. {n}")   # kmen obce kvůli skloňování
            shown.update({kk2: v for kk2, v in keys.items() if kk2 not in shown})
            chain.append((kk, set(keys)))
            kk *= 2
        for i in range(len(chain)):
            for h in chain[i][1]:
                run = [c[0] for c in chain[i:] if h in c[1]]
                j = i
                while j < len(chain) and h in chain[j][1]:
                    j += 1
                if j - i >= 3 and (i == 0 or h not in chain[i - 1][1]):
                    ideas["Rod v jednom domě"].append(f"{shown[h]}: {j - i} {'generace' if j - i < 5 else 'generací'} ({', '.join(name(c) for c in run[: j - i])})")

    for alias, main_k in SAME.items():
        ideas["Předek v rodokmenu vícekrát (sňatek příbuzných)"].append(f"{name(main_k)} je zároveň předkem č. {alias}")
    oldest = sorted((y, k) for k, p in real.items() if p.get("st") == "doc" for y in [year_of(p, "*") or year_of(p, "×")] if y)[:3]
    for y, k in oldest:
        ideas["Nejstarší doložení předci"].append(f"{name(k)} – {y}")
    trades = defaultdict(set)
    for k, p in real.items():
        for f in p.get("f", []):
            if re.match(r"\s*[*×†]", f) or re.search(r"\d{4}", f):
                continue
            for t in re.split(r"[;,(]", f):
                t = re.sub(r"\s+(v|ve|na|z|ze|u)\s.*$", "", t.strip())
                if t and t[0].islower() and not re.match(r"(dcera|syn|z|ze|provd|později|rodem|nemanž|vdova|obyvatel)\b", t) and len(t) < 30 \
                        and not re.search(r"\)|^a |čp|panství|fara|strom|čten|zjištěn|narození|děti|pověsti|nečiteln", t):
                    trades[LINES.get(line_of(k), ("?",))[0] if line_of(k) else "výchozí rodina"].add(t)
    for line, t in sorted(trades.items()):
        ideas["Řemesla a postavení v rodech"].append(f"{line}: {', '.join(sorted(t))[:300]}")

    if not ideas:
        print("Zatím nic – doplň do osob data narození, sňatků a úmrtí (fakta začínající *, ×, †).")
    for title, items in ideas.items():
        print(f"\n## {title}")
        for i in items[:12]:
            print(" -", i)
    print("\nJsou to jen náměty z dat. Každý ověř v zápisu, pak ho napiš jako krátký příběh do data/zajimavosti.md.")


if __name__ == "__main__":
    main()
