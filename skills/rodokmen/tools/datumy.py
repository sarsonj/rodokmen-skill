#!/usr/bin/env python3
"""Data a roky z rodokmenu na jednom místě: pole `y`, fakta `* × †`, data v zápisech a v GEDCOMu.

Modul pro ostatní nástroje (chronologie.py, kontrola_dat.py, graf.py, rodiny.py) – ať všechny čtou
„asi 1760–64“, „před 1740“ nebo „* asi 1620–1630“ stejně. Jen standardní knihovna.
Samostatně ukáže, jak čte zadaný text: `python -I -X utf8 tools/datumy.py "* asi 1760–64, † 1814"`.

Každé datum je interval „nejdřív – nejpozději“ podle toho, jak přesně je zapsané:
  „14. 2. 1890“ jeden den, „3/1867“ celý měsíc, „1890“ celý rok, „asi 1720“ ± ASI_ROKY let,
  „před 1740“ cokoli do konce roku 1740, „po 1921“ cokoli od roku 1921, „mezi 1700 a 1710“, „1805/06“ jeden z roků,
  „asi 1760–64“ (u narození nebo úmrtí) rozmezí 1760–1764 a k tomu ± ASI_ROKY, „(?)“ nejistý údaj ± 1 rok.
"""
import calendar, re, sys
from dataclasses import dataclass
from datetime import date

MIN, MAX = date(1, 1, 1), date(9999, 12, 31)   # otevřené meze („před“, „po“)
ASI_ROKY = 5                                    # tolerance „asi 1720“ (rok dopočítaný z věku bývá o pár let vedle)
NEJISTE_ROKY = 1                                # tolerance „1850 (?)“ (nejisté čtení)


@dataclass(frozen=True)
class Datum:
    od: date            # nejdřívější možné datum
    do: date            # nejpozdější možné datum
    approx: bool        # „asi“, „před“, „po“, „mezi“, „(?)“, „1805/06“, „1760–64“
    text: str           # zápis data bez místa: „14. 2. 1890“, „asi 1720“, „před 1740“
    rok: int = None     # rok, jak je napsaný (první z rozmezí), pro hlášky; u „mezi A a B“ None

    @property
    def otevrene(self):
        return self.od == MIN or self.do == MAX


_PRED = r"(?:(?P<asi>asi|≈|cca\.?|kolem|okolo|nejspíš|nejspíše|snad|pravděpodobně|zřejmě)\s*)?(?:(?P<pp>před|po)\s+)?"
_DEN = r"(?P<d>\d{1,2})\.\s*(?:\(\?\)\s*)?(?P<m>\d{1,2})\.\s*(?P<y>\d{4})"
_ROK = r"(?P<r>\d{4})(?:\s*/\s*(?P<alt>\d{4}|\d{2})(?!\d))?"
_ROZSAH = r"(?:\s*[–—-]\s*(?P<do>\d{4}|\d{2})(?![\d./]))?"
_NEJISTE = r"(?P<q>\s*\(\?\))?"
_DATUM = re.compile(_PRED + rf"(?:{_DEN}|(?P<mm>\d{{1,2}})/(?P<my>\d{{4}})|{_ROK})" + _NEJISTE)
_DATUM_ROZSAH = re.compile(_PRED + rf"(?:{_DEN}|(?P<mm>\d{{1,2}})/(?P<my>\d{{4}})|{_ROK}{_ROZSAH})" + _NEJISTE)
_MEZI = re.compile(r"(?:asi\s+)?mezi\s+(?:\d{1,2}\.\s*\d{1,2}\.\s*)?(\d{4})\s+a\s+(?:\d{1,2}\.\s*\d{1,2}\.\s*)?(\d{4})")
_PORADI = re.compile(r"\(?[1-4]\.\)\s*|[1-4]\.\s+(?=\d{1,2}\.\s*\d{1,2}\.\s*\d{4}|\d{4}|asi|před|po\b|mezi)")
_SLOVA = re.compile(r"(?:a\s+)?\(?(?:pokřtěn[aý]?|pokřt\.|křtěn[aý]?|křest|pohřeb|pohřben[aý]?|oddán[aiy]?)\)?[,:]?\s+")
_VOLNE = re.compile(r"\d[\d.\s/–-]*(?:(?:nebo|či|a)\s+[\d.\s/–-]*)*?(?<!\d)(\d{4})(?!\d)")


def _cely_rok(y):
    return date(y, 1, 1), date(y, 12, 31)


def _rok2(zaklad, dvojcisli):
    """„1760–64“ → 1764, „1699/1708“ → 1708; dvojčíslí se doplní stoletím prvního roku."""
    if len(dvojcisli) == 4:
        return int(dvojcisli)
    r = zaklad // 100 * 100 + int(dvojcisli)
    return r if r >= zaklad else r + 100


def _interval(m):
    g = m.groupdict()
    if g.get("r"):
        rok = konec = int(g["r"])
        for k in ("alt", "do"):
            if g.get(k):
                konec = max(konec, _rok2(rok, g[k]))
        od, do = date(rok, 1, 1), date(konec, 12, 31)
    else:
        y, mes = (int(g["y"]), int(g["m"])) if g.get("y") else (int(g["my"]), int(g["mm"]))
        rok = y
        if not 1 <= mes <= 12:
            od, do = _cely_rok(y)
        else:
            od, do = date(y, mes, 1), date(y, mes, calendar.monthrange(y, mes)[1])
            if g.get("d") and 1 <= int(g["d"]) <= do.day and "(?)" not in m.group(0):   # „30. 2.“, „25. (?) 10.“ → měsíc
                od = do = date(y, mes, int(g["d"]))
    approx = bool(g.get("asi") or g.get("pp") or g.get("alt") or g.get("do") or "(?)" in m.group(0))
    if g.get("pp") == "před":
        od = MIN
    elif g.get("pp") == "po":
        do = MAX
    elif g.get("asi"):
        od, do = date(od.year - ASI_ROKY, 1, 1), date(do.year + ASI_ROKY, 12, 31)
    elif g.get("q"):
        od, do = date(od.year - NEJISTE_ROKY, 1, 1), date(do.year + NEJISTE_ROKY, 12, 31)
    return Datum(od, do, approx, re.sub(r"\s+", " ", m.group(0)).strip(), rok)


def cast(text, rozsah=False):
    """Datum na začátku textu (po případné předponě „asi/před/po“, pořadí „2.“ a slovu „pokřtěn“), jinak None.

    rozsah=True: „1760–64“ je rozmezí jednoho data (u narození nebo úmrtí); jinak pomlčka datum končí."""
    t = (text or "").strip()
    for _ in range(3):   # „* a pokřtěn …“, „× (2.) …“, „† (pohřeb) …“
        m = _SLOVA.match(t) or _PORADI.match(t)
        if not m:
            break
        t = t[m.end():]
    try:
        m = _MEZI.match(t)
        if m:
            a, b = sorted((int(m.group(1)), int(m.group(2))))
            return Datum(date(a, 1, 1), date(b, 12, 31), True, m.group(0), None)
        m = (_DATUM_ROZSAH if rozsah else _DATUM).match(t)
        if m and not t[m.end():m.end() + 1].isdigit():
            return _interval(m)
        m = _VOLNE.match(t)   # „12. nebo 13. 5. 1790“ – aspoň rok
        if m and m.start(1) > 0 and len(m.group(0)) < 30:
            r = int(m.group(1))
            return Datum(*_cely_rok(r), True, m.group(0).strip(), r)
    except ValueError:   # rok 0000, „asi 0003“ – překlep, ne datum
        return None
    return None


def najdi(text):
    """První datum kdekoli v textu („Křest 3. 3. 1760, Lhota“) – pro pole datum v zápisech a případech."""
    text = text or ""
    for m in re.finditer(r"(?:(?:asi|před|po|mezi)\s+)?\d", text):
        if m.start() and text[m.start() - 1].isdigit():
            continue
        d = cast(text[m.start():], rozsah=True)
        if d:
            return d
    return None


ZNAKY = ("*", "×", "†")
_KREST = re.compile(r"\s*(?:pokřtěn[aý]?|křtěn[aý]?|křest)\s+(?=\d|asi|před|po\b|mezi)", re.I)
_POHREB = re.compile(r"\s*(?:pohřben[aý]?|pohřeb)\s+(?=\d|asi|před|po\b|mezi)", re.I)


def fakt(f):
    """(znak, Datum | None) pro fakt o narození (* nebo „pokřtěn 4. 12. 1786“), sňatku (×) či úmrtí († nebo
    „pohřben …“); jiný fakt → None. Datum musí být hned za značkou – číslo domu dál ve větě rok není."""
    if not isinstance(f, str):
        return None
    s = f.lstrip()
    if s[:1] in ZNAKY:
        return s[0], cast(s[1:], rozsah=s[0] != "×")
    for rx, znak in ((_KREST, "*"), (_POHREB, "†")):
        m = rx.match(s)
        if m:
            return znak, cast(s[m.end():], rozsah=True)
    return None


def datum(f):
    """Datum hned za značkou faktu (* narození, × sňatek, † úmrtí), jinak None."""
    x = fakt(f)
    return x[1] if x and f.lstrip()[:1] in ZNAKY else None


def z_y(y):
    """(narození, úmrtí) z pole y: „asi 1720–1785“, „1680 – před 1740“, „† 1940“, „* 1895“, „* asi 1620–1630“
    (rozmezí narození), „* asi 1760–64, † 1814“, „1850 – mezi 1900 a 1905“, „po 1921“ (zemřel po)."""
    y = (y or "").strip()
    if not re.search(r"\d{4}", y):
        return None, None
    y = re.sub(r"(?<=\d)\s*-\s*(?=\d|\s|†|$)", "–", y.replace("—", "–"))   # „1930-2015“ jako „1930–2015“
    if "†" in y and not y.startswith("†"):                 # „* asi 1760–64, † 1814“, „* 1850 – † před 1900“
        hlava, _, ocas = y.partition("†")
        hlava = re.sub(r"[\s,;–]+$", "", hlava)
        return cast(hlava.lstrip("* "), rozsah=True), cast(ocas, rozsah=True)
    if y.startswith("†"):
        return None, cast(y[1:], rozsah=True)
    if y.startswith("*"):
        return cast(y[1:], rozsah=True), None
    m = re.search(r"\s*–\s*", y)
    if not m:
        if re.match(r"po\b", y):   # „po 1921“ = ještě žil, zemřel až po roce 1921
            return None, cast(y)
        return cast(y), None
    hlava, ocas = y[:m.start()], y[m.end():]
    nar, umrti = cast(hlava), cast(ocas)
    if umrti is None and nar and nar.rok and re.match(r"\d{2}(?!\d)", ocas):   # „1720–85“
        r = _rok2(nar.rok, ocas[:2])
        umrti = Datum(*_cely_rok(r), False, str(r), r)
    return nar, umrti


_MES = {m: i for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}


def ged(text):
    """Datum z GEDCOMu: „12 MAR 1850“, „MAR 1850“, „ABT 1850“, „BEF 1850“, „AFT 1850“, „BET 1840 AND 1845“,
    „FROM 1840 TO 1845“, „1750/51“. Nerozpoznané → první rok v textu (nejisté), jinak None."""
    t = (text or "").strip().upper()
    if not t:
        return None
    m = re.match(r"(?:BET|FROM)\s+(.+?)\s+(?:AND|TO)\s+(.+)", t)
    if m:
        a, b = ged(m.group(1)), ged(m.group(2))
        if a and b:
            return Datum(min(a.od, b.od), max(a.do, b.do), True, text.strip(), None)
    pre = re.match(r"(ABT|EST|CAL|BEF|AFT|FROM|TO|INT)\.?\s+", t)
    jadro = t[pre.end():] if pre else t
    m = re.match(r"(?:(\d{1,2})\s+)?(?:([A-Z]{3})\s+)?(\d{3,4})(?:/(\d{2,4}))?(?!\d)", jadro)
    try:
        if not m:   # česká data z Brother's Keeperu po převodu v ged_import.py („8. 1945“, „11.11.1934“)
            c = re.fullmatch(r"(\d{1,2})\.\s*(\d{4})", jadro)
            if c and 1 <= int(c.group(1)) <= 12:
                r, mes = int(c.group(2)), int(c.group(1))
                return Datum(date(r, mes, 1), date(r, mes, calendar.monthrange(r, mes)[1]), False, text.strip(), r)
            c = cast(text, rozsah=True)
            if c:
                return c
            r = re.search(r"(?<!\d)\d{4}(?!\d)", t)
            return Datum(*_cely_rok(int(r.group())), True, text.strip(), int(r.group())) if r else None
        rok = int(m.group(3))
        konec = _rok2(rok, m.group(4)) if m.group(4) else rok
        od, do = date(rok, 1, 1), date(konec, 12, 31)
        mes = _MES.get(m.group(2) or "")
        if mes and konec == rok:
            od, do = date(rok, mes, 1), date(rok, mes, calendar.monthrange(rok, mes)[1])
            if m.group(1) and 1 <= int(m.group(1)) <= do.day:
                od = do = date(rok, mes, int(m.group(1)))
        p = pre.group(1) if pre else ""
        if p in ("BEF", "TO"):
            od = MIN
        elif p in ("AFT", "FROM"):
            do = MAX
        elif p in ("ABT", "EST", "CAL"):
            od, do = date(od.year - ASI_ROKY, 1, 1), date(do.year + ASI_ROKY, 12, 31)
        return Datum(od, do, bool(p) or konec != rok, text.strip(), rok)
    except ValueError:
        return None


def prekryv(a, b, dni=0):
    """Mohou dvě data být totéž (intervaly se překrývají, s tolerancí `dni`)?"""
    return (a.od - b.do).days <= dni and (b.od - a.do).days <= dni


def vek(od, do):
    """Celé roky mezi dvěma daty (u otevřených mezí vyjde nesmyslně velké nebo záporné číslo – pravidlo pak nevyjde)."""
    return do.year - od.year - ((do.month, do.day) < (od.month, od.day))


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        sys.exit(__doc__.strip())
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for t in argv:
        f = fakt(t)
        if f:
            print(f"{t!r}: fakt {f[0]} → {f[1]}")
        else:
            n, u = z_y(t)
            print(f"{t!r}: jako y → narození {n}, úmrtí {u}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
