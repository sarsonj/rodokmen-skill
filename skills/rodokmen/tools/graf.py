#!/usr/bin/env python3
"""Kontrola rodiny jako grafu (rodič → dítě): chyby, které v seznamu osob nejsou vidět.

Použití (z kořene projektu):
  python3 -I tools/graf.py strom dokumenty/strom.ged ["Jméno Příjmení"]
      kontrola stromu z GEDCOMu před ged_import.py:
      - osoba svým vlastním předkem (cyklus – chyba ve stromu, návratový kód 1)
      - dítě ve dvou rodinách (cizí strom ho vede třeba u obou manželek otce); ged_import.py bere první rodinu,
        nástroj ukáže, která je podle dat možná
      - chronologie: věk rodiče při narození dítěte, dítě narozené po smrti matky nebo víc než rok po smrti otce,
        úmrtí před narozením, věk přes 105 let
      - možní dvojníci: stejné křestní jméno (Jan = Johann, Marie = Maria) a příjmení (Novák = Nowak, -ová),
        rok narození ±2, ne sourozenci ani předek a potomek
      - se jménem výchozí osoby: předek, který je v rodokmenu víckrát (vzdálení příbuzní se vzali), a návrh SAME
  python3 -I tools/graf.py predci
      totéž pro data/osoby.py: věk rodičů 2k a 2k+1 při narození dítěte k, úmrtí rodiče před narozením a stejná
      osoba na dvou číslech bez SAME. Tyto hlášky vypisuje i kontrola.py.

Všechno jsou upozornění k ověření v matrice, ne opravy. Nic nestahuje, jen standardní knihovna.
"""
import os, re, sys, unicodedata
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ged_import as gi

for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

MATKA, OTEC = (15, 50), (16, 75)      # věk rodiče při narození dítěte, mimo rozsah = upozornění
JMENA = [g.split() for g in (
    "jan johann johannes joannes hans", "josef joseph josephus", "frantisek franz franciscus", "marie maria",
    "anna", "antonin anton antonius", "antonie antonia", "karel karl carl carolus", "matej mathias matthias",
    "katerina katharina catharina", "alzbeta elisabeth elisabetha", "vaclav wenzel wenceslaus", "jakub jakob jacob",
    "terezie theresia therese", "barbora barbara", "johana johanna", "filip philipp", "pavel paul paulus",
    "tomas thomas", "vojtech adalbert", "rozalie rosalia", "ludmila ludmilla", "anezka agnes", "vavrinec lorenz",
    "mikulas nikolaus", "jiri georg", "petr peter", "ondrej andreas", "ignac ignaz", "marketa margaretha")]
KANON = {v: g[0] for g in JMENA for v in g}


def fold(s):
    s = "".join(c for c in unicodedata.normalize("NFD", (s or "").lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z ]", "", s).strip()


def klic_jmena(givn, surn):
    """('Johann', 'Nowak') a ('Jan', 'Nováková') → ('jan', 'novak')."""
    g = fold(givn).split()
    s = fold(surn).replace("w", "v").replace(" ", "")
    for suf in ("ova", "a"):
        if s.endswith(suf) and len(s) > 4:
            s = s[: -len(suf)]
            break
    return (KANON.get(g[0], g[0]) if g else ""), s


# ---- strom z GEDCOMu --------------------------------------------------------------------------------------------

def nacti_strom(path):
    """{'osoby': {id: …}, 'rodiny': {id: {h, w, deti}}, 'puvod': {id: [rodiny v pořadí FAMC]}} z GEDCOMu."""
    recs = gi.read(path)
    osoby, rodiny, puvod = {}, {}, defaultdict(list)
    for i, r in recs.items():
        if r["_type"] == "INDI":
            raw = gi.first(r, "NAME")
            m = re.match(r"^([^/]*)/([^/]*)/", raw)
            ev = {n["tag"]: gi.year(gi.first(n, "DATE")) for n in r["_sub"] if n["tag"] in ("BIRT", "CHR", "DEAT", "BURI")}
            osoby[i] = dict(jmeno=gi.name(r), givn=(m.group(1) if m else raw).strip(), surn=(m.group(2) if m else "").strip(),
                            sex=gi.first(r, "SEX"), nar=ev.get("BIRT") or ev.get("CHR"), zem=ev.get("DEAT") or ev.get("BURI"))
            for n in gi.sub(r, "FAMC"):
                puvod[i].append(n["val"].strip())
        elif r["_type"] == "FAM":
            rodiny[i] = dict(h=gi.first(r, "HUSB"), w=gi.first(r, "WIFE"), deti=[n["val"].strip() for n in gi.sub(r, "CHIL")])
    for f, r in rodiny.items():               # dítě uvedené jen v CHIL rodiny se počítá taky
        for c in r["deti"]:
            if c in osoby and f not in puvod[c]:
                puvod[c].append(f)
    puvod = {i: [f for f in fs if f in rodiny] for i, fs in puvod.items()}
    return dict(osoby=osoby, rodiny=rodiny, puvod=puvod)


def rodice(t, i, rodina=None):
    fams = [rodina] if rodina else t["puvod"].get(i, [])
    out = []
    for f in fams:
        for p in (t["rodiny"][f]["h"], t["rodiny"][f]["w"]):
            if p in t["osoby"] and p not in out:
                out.append(p)
    return out


def _chybi_vek(t, rodic, dite):
    """Důvod, proč `rodic` nemohl být rodičem `dite` (nebo None)."""
    r, d = t["osoby"][rodic], t["osoby"][dite]
    if not d["nar"]:
        return None
    zena = r["sex"] == "F"
    lo, hi = MATKA if zena else OTEC
    if r["nar"] and not lo <= d["nar"] - r["nar"] <= hi:
        return ("věk matky" if zena else "věk otce"), d["nar"] - r["nar"]
    if r["zem"] and d["nar"] > r["zem"] + (0 if zena else 1):
        return ("narozen(a) po smrti matky" if zena else "narozen(a) po smrti otce"), d["nar"] - r["zem"]
    return None


def chronologie(t):
    """[(druh, hodnota, rodič, dítě)]; u úmrtí před narozením a věku přes 105 let je rodič = dítě = osoba."""
    out = []
    for c in t["osoby"]:
        for p in rodice(t, c):
            why = _chybi_vek(t, p, c)
            if why:
                out.append((why[0], why[1], p, c))
    for i, o in t["osoby"].items():
        if o["nar"] and o["zem"] and o["zem"] < o["nar"]:
            out.append(("úmrtí před narozením", o["zem"] - o["nar"], i, i))
        elif o["nar"] and o["zem"] and o["zem"] - o["nar"] > 105:
            out.append(("věk přes 105 let", o["zem"] - o["nar"], i, i))
    return out


def vic_rodin(t):
    """Osoby ve více rodinách původu: {osoba, rodiny, prvni (bere ji ged_import.py), mozne (chronologicky)}."""
    out = []
    for i, fs in t["puvod"].items():
        if len(fs) < 2:
            continue
        mozne = [f for f in fs if not any(_chybi_vek(t, p, i) for p in rodice(t, i, f))]
        out.append(dict(osoba=i, rodiny=fs, prvni=fs[0], mozne=mozne))
    return out


def _rodina(t, i):
    """Rodina původu pro Kekulého čísla: první chronologicky možná, jinak první."""
    fs = t["puvod"].get(i, [])
    ok = [f for f in fs if not any(_chybi_vek(t, p, i) for p in rodice(t, i, f))]
    return (ok or fs or [None])[0]


def cykly(t):
    """Cykly rodič → dítě (osoba svým vlastním předkem), každý jako seznam osob s opakovaným začátkem na konci."""
    barva, nalez = {}, []
    for start in t["osoby"]:
        if start in barva:
            continue
        barva[start], cesta, zasob = 1, [start], [(start, iter(rodice(t, start)))]
        while zasob:
            uzel, it = zasob[-1]
            dalsi = next(it, None)
            if dalsi is None:
                barva[uzel] = 2
                zasob.pop()
                cesta.pop()
            elif barva.get(dalsi) == 1:
                nalez.append(cesta[cesta.index(dalsi):] + [dalsi])
            elif dalsi not in barva:
                barva[dalsi] = 1
                cesta.append(dalsi)
                zasob.append((dalsi, iter(rodice(t, dalsi))))
    return nalez


def predkove(t, i):
    seen, stack = set(), [i]
    while stack:
        for p in rodice(t, stack.pop()):
            if p not in seen:
                seen.add(p)
                stack.append(p)
    return seen


def dvojnici(t):
    """[(skóre, a, b)] – možná tatáž osoba zapsaná dvakrát; vyšší skóre = víc shodných údajů."""
    bloky = defaultdict(list)
    for i, o in t["osoby"].items():
        if o["nar"]:
            bloky[klic_jmena(o["givn"], o["surn"])].append(i)
    out = []
    for ids in bloky.values():
        for n, a in enumerate(ids):
            for b in ids[n + 1:]:
                oa, ob = t["osoby"][a], t["osoby"][b]
                if abs(oa["nar"] - ob["nar"]) > 2 or set(rodice(t, a)) & set(rodice(t, b)):
                    continue                  # sourozenci stejného jména: dítě pojmenované po zemřelém
                if a in predkove(t, b) or b in predkove(t, a):
                    continue
                ra = {klic_jmena(t["osoby"][x]["givn"], "")[0] for x in rodice(t, a)}
                rb = {klic_jmena(t["osoby"][x]["givn"], "")[0] for x in rodice(t, b)}
                skore = 1 + 2 * (oa["nar"] == ob["nar"]) + 2 * len(ra & rb) - 3 * bool(ra and rb and not ra & rb)
                if skore >= 1:
                    out.append((skore, a, b))
    return sorted(out, reverse=True)


def kekule(t, koren, hloubka=16):
    """{osoba: {všechna Kekulého čísla}} – předek v rodokmenu víckrát má víc čísel."""
    kek, stack = defaultdict(set), [(koren, 1)]
    while stack:
        i, k = stack.pop()
        if k >= 2 ** hloubka:
            continue
        kek[i].add(k)
        f = _rodina(t, i)
        if f:
            r = t["rodiny"][f]
            for p, kk in ((r["h"], 2 * k), (r["w"], 2 * k + 1)):
                if p in t["osoby"]:
                    stack.append((p, kk))
    return dict(kek)


def navrh_same(kek):
    """{alias: hlavní číslo} pro data/osoby.py → SAME (hlavní = nejmenší číslo osoby)."""
    return {k: min(ks) for ks in kek.values() if len(ks) > 1 for k in sorted(ks) if k != min(ks)}


# ---- data/osoby.py ----------------------------------------------------------------------------------------------

def _roky(p):
    """(rok narození, rok úmrtí) z y ("1850–1910", "asi 1720–1785", "* 1931", "† 1773") a z faktů * a †."""
    nar = zem = None
    y = p.get("y") or ""
    if y.strip().startswith("†"):
        zem = gi.year(y)
    else:
        casti = re.split(r"\s*–\s*", y.lstrip("* "), maxsplit=1)
        if casti and not re.search(r"před|po\b", casti[0]):
            nar = gi.year(casti[0])
        if len(casti) > 1 and not re.search(r"před|po\b", casti[1]):
            zem = gi.year(casti[1])
    for f in p.get("f", []):
        m = re.match(r"^\s*([*†])\s*(?!.*(?:před|po)\s)(.*)", f)
        if m and gi.year(m.group(2)):
            if m.group(1) == "*":
                nar = gi.year(m.group(2))
            else:
                zem = gi.year(m.group(2))
    return nar, zem


def _neznamy(p):
    return p.get("st") == "unk" or p.get("n", "").startswith(("otec neuveden", "matka neuvedena"))


def predci(P, SAME):
    """Upozornění pro kontrola.py: věk rodičů a stejná osoba na dvou číslech bez SAME."""
    out = []
    hlavni = lambda k: SAME.get(k, k)
    for k, p in sorted(P.items()):
        if not isinstance(k, int) or k in SAME or _neznamy(p):
            continue
        nar, _ = _roky(p)
        if not nar:
            continue
        for pk, zena in ((2 * k, False), (2 * k + 1, True)):
            h = hlavni(pk)
            r = P.get(h)
            if not r or _neznamy(r):
                continue
            rn, rz = _roky(r)
            lo, hi = MATKA if zena else OTEC
            if rn and not lo <= nar - rn <= hi:
                out.append(f"osoba {h} ({r.get('n')}) by při narození dítěte {k} ({p.get('n')}, * {nar}) bylo "
                           f"{nar - rn} let – ověřit rok narození nebo vazbu (graf.py)")
            if rz and nar > rz + (0 if zena else 1):
                out.append(f"osoba {h} ({r.get('n')}) {'zemřela' if zena else 'zemřel'} {rz}, před narozením dítěte "
                           f"{k} ({p.get('n')}, * {nar}) – ověřit (graf.py)")
    skupiny = defaultdict(list)
    for k, p in P.items():
        if isinstance(k, int) and k > 1 and k not in SAME and not _neznamy(p) and _roky(p)[0]:
            skupiny[(fold(p.get("n")), _roky(p)[0])].append(k)
    for ks in skupiny.values():
        ks = sorted(ks)
        for a in ks[1:]:
            out.append(f"osoba {a} ({P[a].get('n')}) je nejspíš tatáž jako {ks[0]} (stejné jméno a rok narození; "
                       f"vzdálení příbuzní se vzali) – ověřit a zapsat SAME = {{{a}: {ks[0]}}} (graf.py)")
    return out


# ---- výpis ------------------------------------------------------------------------------------------------------

def _popis(t, i):
    o = t["osoby"][i]
    return f"{o['jmeno']} ({o['nar'] or '?'}–{o['zem'] or '?'}) {i}"


def _rodina_popis(t, f):
    r = t["rodiny"][f]
    return f"{f} " + " × ".join(t["osoby"][p]["jmeno"] for p in (r["h"], r["w"]) if p in t["osoby"])


def main(argv):
    if not argv or argv[0] not in ("strom", "predci") or (argv[0] == "strom" and len(argv) < 2):
        sys.exit(__doc__)
    if argv[0] == "predci":
        ns = {}
        exec(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "osoby.py"),
                  encoding="utf-8").read(), ns)
        u = predci(ns.get("P", {}), ns.get("SAME", {}))
        print("\n".join(f"upozornění: {x}" for x in u) or "Vše v pořádku.")
        return 0
    t = nacti_strom(argv[1])
    print(f"{len(t['osoby'])} osob, {len(t['rodiny'])} rodin")
    cyk = cykly(t)
    for c in cyk:
        print("CHYBA: osoba svým vlastním předkem:", " → ".join(_popis(t, x) for x in c))
    for v in vic_rodin(t):
        mozne = ", ".join(_rodina_popis(t, f) for f in v["mozne"]) or "žádná"
        print(f"upozornění: {_popis(t, v['osoba'])} je dítětem ve {len(v['rodiny'])} rodinách; ged_import.py bere "
              f"{_rodina_popis(t, v['prvni'])}, podle dat možná: {mozne}")
    for druh, h, p, c in chronologie(t):
        print(f"upozornění: {druh} ({h}): " + (_popis(t, p) if p == c else f"{_popis(t, p)} → {_popis(t, c)}"))
    for s, a, b in dvojnici(t):
        print(f"možný dvojník ({s}): {_popis(t, a)} ~ {_popis(t, b)}")
    if len(argv) > 2:
        recs = gi.read(argv[1])
        start = recs.get(argv[2]) or gi.find(recs, argv[2])     # id (@I12@) nebo jméno, jako ged_import.py
        kek = kekule(t, start["_id"])
        same = navrh_same(kek)
        for i, ks in sorted(kek.items(), key=lambda x: min(x[1])):
            if len(ks) > 1:
                print(f"předek v rodokmenu víckrát: {_popis(t, i)} na číslech {', '.join(map(str, sorted(ks)))}")
        if same:
            print(f"Do data/osoby.py (po ověření v matrikách): SAME = {dict(sorted(same.items()))}")
    return 1 if cyk else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
