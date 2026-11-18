#!/usr/bin/env python3
"""Kontrola rodiny jako grafu (rodič → dítě): chyby, které v seznamu osob nejsou vidět.

Použití (z kořene projektu):
  python3 -I tools/graf.py strom dokumenty/strom.ged ["Jméno Příjmení"]
      kontrola stromu z GEDCOMu před ged_import.py:
      - osoba svým vlastním předkem (cyklus – chyba ve stromu, návratový kód 1)
      - dítě ve dvou rodinách (cizí strom ho vede třeba u obou manželek otce); ged_import.py bere první rodinu,
        nástroj ukáže, která je podle dat možná
      - chronologie: věk rodiče při narození dítěte, dítě narozené po smrti matky nebo víc než 9 měsíců po smrti
        otce, úmrtí před narozením, věk přes 105 let (pravidla z tools/chronologie.py, stejná jako pro osoby.py)
      - možní dvojníci: stejné křestní jméno (Jan = Johann, Marie = Maria) a příjmení (Novák = Nowak, -ová),
        rok narození ±2, ne sourozenci ani předek a potomek
      - se jménem výchozí osoby: předek, který je v rodokmenu víckrát (vzdálení příbuzní se vzali), a návrh SAME
  python3 -I tools/graf.py predci
      data/osoby.py: stejná osoba na dvou číslech bez SAME (stejné jméno a rok narození). Hlásí i kontrola.py.
      Věk rodičů a další časovou návaznost v osoby.py hlídá tools/chronologie.py (taky součást kontrola.py).

Všechno jsou upozornění k ověření v matrice, ne opravy. Nic nestahuje, jen standardní knihovna.
"""
import os, re, sys, unicodedata
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ged_import as gi  # noqa: E402
import chronologie as ch  # noqa: E402 – pravidla časové návaznosti (jediné místo s věkem rodičů)
from datumy import MAX, MIN, ged as ged_datum  # noqa: E402 – čtení dat (společné pro všechny kontroly)
from jmena import krestni_klic, prijmeni_klic  # noqa: E402 – volné porovnání jmen (i rodiny.py)

for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

def fold(s):
    s = "".join(c for c in unicodedata.normalize("NFD", (s or "").lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z ]", "", s).strip()


def klic_jmena(givn, surn):
    """('Johann', 'Nowak') a ('Jan', 'Nováková') → ('jan', 'novak')."""
    return krestni_klic(givn), prijmeni_klic(surn)


# ---- strom z GEDCOMu --------------------------------------------------------------------------------------------

def _rok(d):
    """Rok pro porovnání dvojníků; rozmezí a meze (BEF, AFT, BET … AND …, FROM, TO) nejsou přesný rok → None."""
    if not d or d.rok is None or d.od == MIN or d.do == MAX or d.do.year - d.od.year > 2 * ch.ASI_ROKY:
        return None
    return d.rok


def nacti_strom(path):
    """{'osoby': {id: …}, 'rodiny': {id: {h, w, deti}}, 'famc': {id: [rodiny z FAMC, jak je čte ged_import.py]},
    'puvod': {id: [rodiny z FAMC i z CHIL]}} z GEDCOMu."""
    recs = gi.read(path)
    osoby, rodiny, puvod = {}, {}, defaultdict(list)
    for i, r in recs.items():
        if r["_type"] == "INDI":
            raw = gi.first(r, "NAME")
            m = re.match(r"^([^/]*)/([^/]*)/", raw)
            ev = {n["tag"]: ged_datum(gi.first(n, "DATE")) for n in r["_sub"]
                  if n["tag"] in ("BIRT", "CHR", "DEAT", "BURI")}
            dn, dz = ev.get("BIRT") or ev.get("CHR"), ev.get("DEAT") or ev.get("BURI")
            osoby[i] = dict(jmeno=gi.name(r), givn=(m.group(1) if m else raw).strip(), surn=(m.group(2) if m else "").strip(),
                            sex=gi.first(r, "SEX"), nar=_rok(dn), zem=_rok(dz), dnar=dn, dzem=dz)
            for n in gi.sub(r, "FAMC"):
                if n["val"].strip() not in puvod[i]:
                    puvod[i].append(n["val"].strip())
        elif r["_type"] == "FAM":
            rodiny[i] = dict(h=gi.first(r, "HUSB"), w=gi.first(r, "WIFE"), deti=[n["val"].strip() for n in gi.sub(r, "CHIL")])
    famc = {i: [f for f in fs if f in rodiny] for i, fs in puvod.items()}
    for f, r in rodiny.items():               # dítě uvedené jen v CHIL rodiny se počítá do kontrol taky
        for c in r["deti"]:
            if c in osoby and f not in puvod[c]:
                puvod[c].append(f)
    puvod = {i: [f for f in fs if f in rodiny] for i, fs in puvod.items()}
    return dict(osoby=osoby, rodiny=rodiny, puvod=puvod, famc=famc)


def rodice(t, i, rodina=None):
    fams = [rodina] if rodina else t["puvod"].get(i, [])
    out = []
    for f in fams:
        for p in (t["rodiny"][f]["h"], t["rodiny"][f]["w"]):
            if p in t["osoby"] and p not in out:
                out.append(p)
    return out


def _zena(t, rodic, dite):
    """Matka, nebo otec: podle SEX, a když chybí, podle role WIFE v rodině dítěte."""
    sex = t["osoby"][rodic]["sex"]
    if sex in ("F", "M"):
        return sex == "F"
    return any(t["rodiny"][f]["w"] == rodic for f in t["puvod"].get(dite, []))


def _chybi_vek(t, rodic, dite):
    """Důvod, proč `rodic` nemohl být rodičem `dite` (nebo None) – pravidla z chronologie.py.
    Hodnota: věk rodiče (záporná, když se narodil až po dítěti), u úmrtí rodiče počet let po něm."""
    r, d = t["osoby"][rodic], t["osoby"][dite]
    b = d["dnar"]
    if not b:
        return None
    zena = _zena(t, rodic, dite)
    if r["dnar"]:
        v = ch.vek_rodice(b, r["dnar"], zena)
        if v:
            return ("věk matky" if zena else "věk otce"), (v[1] if v[1] is not None else b.do.year - r["dnar"].od.year)
    if r["dzem"]:
        dni = ch.po_smrti_rodice(b, r["dzem"], zena)
        if dni:
            return ("narozen(a) po smrti matky" if zena else "narozen(a) po smrti otce"), round(dni / 365.25, 1)
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
        z = ch.zivot(o["dnar"], o["dzem"]) if o["dnar"] and o["dzem"] else None
        if z and z[0] == "umrti-pred-narozenim":
            out.append(("úmrtí před narozením", o["dzem"].do.year - o["dnar"].od.year, i, i))
        elif z:
            out.append((f"věk přes {ch.NEJVYSSI_VEK} let", z[1], i, i))
    return out


def vic_rodin(t):
    """Osoby ve více rodinách původu: {osoba, rodiny, prvni (bere ji ged_import.py), mozne (chronologicky)}."""
    out = []
    for i, fs in t["puvod"].items():
        if len(fs) < 2:
            continue
        mozne = [f for f in fs if not any(_chybi_vek(t, p, i) for p in rodice(t, i, f))]
        prvni = (t["famc"].get(i) or [None])[0]   # ged_import.py bere první rodinu z FAMC, CHIL nečte
        out.append(dict(osoba=i, rodiny=fs, prvni=prvni, mozne=mozne))
    return out


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
        klic = klic_jmena(o["givn"], o["surn"])
        if o["nar"] and all(klic):            # bez křestního jména nebo příjmení (přivdané ženy) nejde porovnat
            bloky[klic].append(i)
    out = []
    for ids in bloky.values():
        for n, a in enumerate(ids):
            for b in ids[n + 1:]:
                oa, ob = t["osoby"][a], t["osoby"][b]
                if abs(oa["nar"] - ob["nar"]) > 2:
                    continue
                if oa["nar"] != ob["nar"] and set(t["puvod"].get(a, [])) & set(t["puvod"].get(b, [])):
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
    """{osoba: {všechna Kekulého čísla}} – předek v rodokmenu víckrát má víc čísel. Čísluje jako ged_import.py
    (první rodina z FAMC), aby návrh SAME seděl na čísla v data/osoby.py."""
    kek, stack = defaultdict(set), [(koren, 1)]
    while stack:
        i, k = stack.pop()
        if k >= 2 ** hloubka:
            continue
        kek[i].add(k)
        f = (t["famc"].get(i) or [None])[0]
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
    """(rok narození, rok úmrtí) z faktů * a † a z y (fakta mají přednost), jak je čte tools/datumy.py."""
    u = ch.udalosti({1: p}, 1)
    return tuple(d.rok if d and d.rok and not d.otevrene else None for d in (u["narozeni"], u["umrti"]))


def _neznamy(p):
    return p.get("st") == "unk" or p.get("n", "").startswith(("otec neuveden", "matka neuvedena"))


def predci(P, SAME):
    """Upozornění pro kontrola.py: stejná osoba na dvou číslech bez SAME. Věk rodičů hlídá chronologie.py."""
    out, skupiny = [], defaultdict(list)
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
    nar, zem = (o[k] or (o["d" + k].text if o["d" + k] else "?") for k in ("nar", "zem"))
    return f"{o['jmeno']} ({nar}–{zem}) {i}"


def _rodina_popis(t, f):
    r = t["rodiny"][f]
    return f"{f} " + " × ".join(t["osoby"][p]["jmeno"] for p in (r["h"], r["w"]) if p in t["osoby"])


def main(argv):
    if not argv or argv[0] not in ("strom", "predci") or (argv[0] == "strom" and len(argv) < 2):
        sys.exit(__doc__)
    if argv[0] == "predci":
        ns = {}
        exec(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "osoby.py"),
                  encoding="utf-8-sig").read(), ns)
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
        bere = _rodina_popis(t, v["prvni"]) if v["prvni"] else "žádnou (dítě je jen v CHIL, chybí FAMC)"
        print(f"upozornění: {_popis(t, v['osoba'])} je dítětem ve {len(v['rodiny'])} rodinách; ged_import.py bere "
              f"{bere}, podle dat možná: {mozne}")
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
