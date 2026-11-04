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


def zije(p, ud, dnes):
    """Žijící: poznámka „Žijící…“ (reference/soukromi.md), nebo bez úmrtí a narozen v posledních 100 letech."""
    if (p.get("note") or "").startswith("Žijící"):
        return True
    b = ud.get("narozeni")
    return ud.get("umrti") is None and b is not None and b.od != MIN and b.od.year >= dnes.year - 100
