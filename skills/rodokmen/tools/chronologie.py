#!/usr/bin/env python3
"""Časová návaznost v rodokmenu: data narození, sňatku a úmrtí z data/osoby.py jako intervaly.

Modul bez vlastního spouštění. Používá ho tools/kontrola.py (upozornění v terminálu)
a tools/export_web.py (stránka Časová osa na webu). Jen standardní knihovna.

Každé datum je interval „nejdřív – nejpozději“ podle toho, jak přesně je zapsané:
„14. 2. 1890“ jeden den, „3/1867“ celý měsíc, „1890“ celý rok, „asi 1720“ ± ASI_ROKY let,
„před 1740“ cokoli do konce roku 1740, „po 1921“ cokoli od roku 1921.
"""
import calendar, re
from dataclasses import dataclass
from datetime import date

MIN, MAX = date(1, 1, 1), date(9999, 12, 31)   # otevřené meze („před“, „po“)
ASI_ROKY = 5                                    # tolerance údaje „asi 1720“ (rok dopočítaný z věku bývá o pár let vedle)

_DATUM = re.compile(r"(?:(?P<pre>asi|≈|kolem|cca|před|po)\s*)?"
                    r"(?:(?P<d>\d{1,2})\.\s*(?P<m>\d{1,2})\.\s*(?P<y>\d{4})|(?P<mm>\d{1,2})/(?P<my>\d{4})|(?P<r>\d{4}))\b")


@dataclass(frozen=True)
class Datum:
    od: date      # nejdřívější možné datum
    do: date      # nejpozdější možné datum
    approx: bool  # „asi“, „≈“, „kolem“, „před“, „po“
    text: str     # zápis data bez místa: „14. 2. 1890“, „asi 1720“, „před 1740“


def _cast(text):
    """Datum na začátku textu (po případné předponě), jinak None."""
    m = _DATUM.match(text.strip())
    if not m:
        return None
    if m["r"]:
        y = int(m["r"])
        od, do = date(y, 1, 1), date(y, 12, 31)
    else:
        y, mes = (int(m["y"]), int(m["m"])) if m["y"] else (int(m["my"]), int(m["mm"]))
        if not 1 <= mes <= 12:
            od, do = date(y, 1, 1), date(y, 12, 31)
        else:
            od, do = date(y, mes, 1), date(y, mes, calendar.monthrange(y, mes)[1])
            if m["d"] and 1 <= int(m["d"]) <= do.day:   # neplatný den („30. 2.“) → celý měsíc
                od = do = date(y, mes, int(m["d"]))
    pre = m["pre"]
    if pre == "před":
        od = MIN
    elif pre == "po":
        do = MAX
    elif pre:
        od, do = date(od.year - ASI_ROKY, 1, 1), date(do.year + ASI_ROKY, 12, 31)
    return Datum(od, do, bool(pre), re.sub(r"\s+", " ", m.group(0)))


def datum(fakt):
    """Datum hned za značkou faktu (* narození, × sňatek, † úmrtí). Číslo domu dál ve větě rok není."""
    fakt = fakt.lstrip()
    return _cast(fakt[1:]) if fakt[:1] in ("*", "×", "†") else None


def _z_y(y):
    """Narození a úmrtí z pole y („asi 1720–1785“, „1680 – před 1740“, „† 1940“, „* 1895“)."""
    y = (y or "").strip()
    if not re.search(r"\d{4}", y):
        return None, None
    if y.startswith("†"):
        return None, _cast(y[1:])
    if y.startswith("*"):
        return _cast(y[1:]), None
    head, dash, tail = y.partition("–")
    if not dash and re.match(r"po\b", y):   # „po 1921“ = ještě žil, ne narození
        return None, None
    return _cast(head), (_cast(tail) if dash else None)


def zastupna(p):
    """Místo v rodokmenu bez skutečné osoby („otec neuveden“) – stejná podmínka jako export_web.placeholder."""
    n = p.get("n", "")
    return n.startswith(("otec neuveden", "matka neuvedena")) or n in ("", "?")


def udalosti(P, k):
    """Narození, sňatek s druhým rodičem z rodokmenu a úmrtí osoby k: {"narozeni", "snatek", "umrti"} → Datum | None."""
    p = P[k]
    fakty = [x for x in p.get("f", []) if isinstance(x, str)]

    def prvni(znak, fakty=fakty):
        return next((d for x in fakty if x.lstrip().startswith(znak) for d in [datum(x)] if d), None)

    yb, yd = _z_y(p.get("y"))
    snatky = [x for x in fakty if x.lstrip().startswith("×") and datum(x)]
    druhy = P.get(k ^ 1) if k > 1 else None
    prijmeni = (druhy or {}).get("n", "").split()[-1:] or [""]
    prijmeni = prijmeni[0].strip("()?")[:5]
    snatek = [x for x in snatky if prijmeni and prijmeni in x] or snatky
    return {"narozeni": prvni("*") or yb, "snatek": datum(snatek[0]) if snatek else None, "umrti": prvni("†") or yd}


PRAVIDLA = ("umrti-pred-narozenim", "snatek-mlady", "snatek-po-umrti", "otec-zemrel", "matka-zemrela",
            "vek-matky", "vek-otce")
POHROBEK_DNI = 280                    # dítě se může narodit až ~9 měsíců po smrti otce
NEJISTE_STAVY = ("prob", "mh", "fam")
_JISTE, _NEJISTE = " – jeden z údajů asi nesedí.", " – údaje jsou nejisté, možná nesedí."


@dataclass(frozen=True)
class Varovani:
    k: int                  # osoba, u které se ukazuje ⚠ (u pravidel rodič–dítě dítě)
    pravidlo: str           # klíč z PRAVIDLA (do pole overeno)
    text: str               # neutrální věta pro web i terminál
    mozna: bool             # nejisté údaje („asi“, stav prob/mh/fam) – mírnější znění
    osoby: tuple            # dotčené osoby (hlavní čísla): k a případně rodič


def _vek(od, do):
    """Celé roky mezi dvěma daty (u otevřených mezí vyjde nesmyslně velké nebo záporné číslo – pravidlo pak nevyjde)."""
    return do.year - od.year - ((do.month, do.day) < (od.month, od.day))


def _let(n):
    return f"{n} {'rok' if n == 1 else 'roky' if 2 <= n <= 4 else 'let'}"


def kontrola(P, SAME=None):
    """Rozpory v časové návaznosti, které platí pro všechna možná data v intervalech. Bez odškrtnutých (overeno)."""
    SAME = SAME or {}
    osoby = {k for k in P if isinstance(k, int) and k >= 1 and k not in SAME and not zastupna(P[k])}
    ud = {k: udalosti(P, k) for k in osoby}
    overeno = {}
    for k in P:
        o = P[k].get("overeno") if isinstance(P[k], dict) else None
        overeno.setdefault(SAME.get(k, k), set()).update(o if isinstance(o, dict) else ())

    def muz(k):
        return P[1].get("sex", "M") == "M" if k == 1 else k % 2 == 0

    def rodic(pozice):
        k = SAME.get(pozice, pozice)
        return k if k in osoby else None

    out = []

    def pridej(k, pravidlo, text, data, lide):
        if pravidlo in overeno.get(k, ()):
            return
        mozna = any(d.approx for d in data) or any(P[x].get("st") in NEJISTE_STAVY for x in lide)
        out.append(Varovani(k, pravidlo, text + (_NEJISTE if mozna else _JISTE), mozna, tuple(lide)))

    for k in sorted(osoby):
        n, u = P[k]["n"], ud[k]
        b, m, d = u["narozeni"], u["snatek"], u["umrti"]
        jemu = "mu" if muz(k) else "jí"
        if b and d and d.do < b.od:
            pridej(k, "umrti-pred-narozenim", f"{n}: úmrtí ({d.text}) je dřív než narození ({b.text})", (b, d), (k,))
        if b and m and _vek(b.od, m.do) < 15:
            pridej(k, "snatek-mlady", f"{n}: při sňatku ({m.text}) by {jemu} bylo nejvýš {_let(_vek(b.od, m.do))}",
                   (b, m), (k,))
        if m and d and m.od > d.do:
            pridej(k, "snatek-po-umrti", f"{n}: sňatek ({m.text}) je až po úmrtí ({d.text})", (m, d), (k,))
        if not b:
            continue
        syn, syna, narodil = ("syn", "syna", "narodil") if muz(k) else ("dcera", "dcery", "narodila")
        o, ma = rodic(2 * k), rodic(2 * k + 1)
        if o:
            ob, od_ = ud[o]["narozeni"], ud[o]["umrti"]
            on = P[o]["n"]
            if od_ and (b.od - od_.do).days > POHROBEK_DNI:
                pridej(k, "otec-zemrel", f"{on} zemřel {od_.text}, {syn} {n} se {narodil} {b.text}", (b, od_), (k, o))
            if ob and _vek(ob.od, b.do) < 15:
                pridej(k, "vek-otce", f"{on}: při narození {syna} ({n}, {b.text}) by mu bylo nejvýš {_let(_vek(ob.od, b.do))}",
                       (b, ob), (k, o))
        if ma:
            mb, md = ud[ma]["narozeni"], ud[ma]["umrti"]
            mn = P[ma]["n"]
            if md and b.od > md.do:
                pridej(k, "matka-zemrela", f"{mn} zemřela {md.text}, {syn} {n} se {narodil} {b.text}", (b, md), (k, ma))
            if mb:
                kolik = (f"nejvýš {_let(_vek(mb.od, b.do))}" if _vek(mb.od, b.do) < 15 else
                         f"nejméně {_let(_vek(mb.do, b.od))}" if _vek(mb.do, b.od) > 50 else None)
                if kolik:
                    pridej(k, "vek-matky", f"{mn}: při narození {syna} ({n}, {b.text}) by jí bylo {kolik}", (b, mb), (k, ma))
    return out


def zije(p, ud, dnes):
    """Žijící: poznámka „Žijící…“ (reference/soukromi.md), nebo bez úmrtí a narozen v posledních 100 letech."""
    if (p.get("note") or "").startswith("Žijící"):
        return True
    b = ud.get("narozeni")
    return ud.get("umrti") is None and b is not None and b.od != MIN and b.od.year >= dnes.year - 100
