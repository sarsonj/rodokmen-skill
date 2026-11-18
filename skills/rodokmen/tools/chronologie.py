#!/usr/bin/env python3
"""Časová návaznost v rodokmenu: data narození, sňatku a úmrtí z data/osoby.py jako intervaly.

Používá ho tools/kontrola.py (upozornění v terminálu), tools/export_web.py (stránka Časová osa na webu)
a tools/graf.py (stejná pravidla pro strom z GEDCOMu). Jediné místo s pravidly o věku rodičů.
Samostatně: `python -I -X utf8 tools/chronologie.py` vypíše jen tato upozornění. Jen standardní knihovna.

Data čte tools/datumy.py (společné pro všechny kontroly): každé datum je interval „nejdřív – nejpozději“ podle toho,
jak přesně je zapsané: „14. 2. 1890“ jeden den, „3/1867“ celý měsíc, „1890“ celý rok, „asi 1720“ ± ASI_ROKY let,
„před 1740“ cokoli do konce roku 1740, „po 1921“ cokoli od roku 1921, „asi 1760–64“ rozmezí. Hlásí se jen rozpor,
který platí pro všechna možná data. Ověřený neobvyklý údaj se odškrtne polem `overeno` u osoby (reference/data.md).
"""
import calendar, os, sys
from fractions import Fraction
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # python -I nepřidává složku skriptu
from datumy import ASI_ROKY, MAX, MIN, Datum, datum, fakt, vek as _vek, z_y as _z_y  # noqa: E402,F401


def zastupna(p):
    """Místo v rodokmenu bez skutečné osoby („otec neuveden“) – stejná podmínka jako export_web.placeholder."""
    n = p.get("n", "")
    return n.startswith(("otec neuveden", "matka neuvedena")) or n in ("", "?")


def udalosti(P, k):
    """Narození, sňatek s druhým rodičem z rodokmenu a úmrtí osoby k: {"narozeni", "snatek", "umrti"} → Datum | None.

    Fakta mají přednost před y; za narození se bere i „pokřtěn 4. 12. 1786“, za úmrtí „pohřben …“."""
    p = P[k]
    fakty = [(f, x) for f in p.get("f", []) for x in [fakt(f)] if x and x[1]]

    def prvni(znak):
        return next((d for _f, (z, d) in fakty if z == znak), None)

    yb, yd = _z_y(p.get("y"))
    snatky = [(f, d) for f, (z, d) in fakty if z == "×"]
    druhy = P.get(k ^ 1) if k > 1 else None
    prijmeni = (druhy or {}).get("n", "").split()[-1:] or [""]
    prijmeni = prijmeni[0].strip("()?")[:5]
    snatek = [x for x in snatky if prijmeni and prijmeni in x[0]] or snatky
    return {"narozeni": prvni("*") or yb, "snatek": snatek[0][1] if snatek else None, "umrti": prvni("†") or yd}


PRAVIDLA = ("umrti-pred-narozenim", "snatek-mlady", "snatek-po-umrti", "otec-zemrel", "matka-zemrela",
            "vek-matky", "vek-otce", "vysoky-vek")
POHROBEK_DNI = 280                    # dítě se může narodit až ~9 měsíců po smrti otce
MATKA_VEK, OTEC_VEK = (15, 50), (15, 75)   # věk rodiče při narození dítěte, mimo rozsah = upozornění
SNATEK_VEK = 15
NEJVYSSI_VEK = 105
NEJISTE_STAVY = ("prob", "mh", "fam")
_JISTE, _NEJISTE = " – jeden z údajů asi nesedí.", " – údaje jsou nejisté, možná nesedí."


@dataclass(frozen=True)
class Varovani:
    k: int                  # osoba, u které se ukazuje ⚠ (u pravidel rodič–dítě dítě)
    pravidlo: str           # klíč z PRAVIDLA (do pole overeno)
    text: str               # neutrální věta pro web i terminál
    mozna: bool             # nejisté údaje („asi“, stav prob/mh/fam) – mírnější znění
    osoby: tuple            # dotčené osoby (hlavní čísla): k a případně rodič


# ---- pravidla nad dvojicí dat (sdílí kontrola() pro osoby.py i graf.py pro GEDCOM) -------------------------------

def vek_rodice(b, rb, zena):
    """Věk rodiče narozeného `rb` při narození dítěte `b`: None (možné), ("pred", None) – rodič se narodil až po
    dítěti, ("mlady", nejvýš let), ("stary", nejméně let). Hranice MATKA_VEK, OTEC_VEK."""
    lo, hi = MATKA_VEK if zena else OTEC_VEK
    if b.do < rb.od:
        return "pred", None
    if _vek(rb.od, b.do) < lo:
        return "mlady", _vek(rb.od, b.do)
    if _vek(rb.do, b.od) > hi:
        return "stary", _vek(rb.do, b.od)
    return None


def po_smrti_rodice(b, rd, zena):
    """Dní mezi úmrtím rodiče `rd` a narozením dítěte `b`, když je to víc, než jde (matka 0, otec POHROBEK_DNI)."""
    dni = (b.od - rd.do).days
    return dni if dni > (0 if zena else POHROBEK_DNI) else None


def zivot(b, d):
    """Rozpor narození × úmrtí jedné osoby: None, ("umrti-pred-narozenim", None), ("vysoky-vek", nejméně let)."""
    if d.do < b.od:
        return "umrti-pred-narozenim", None
    if _vek(b.do, d.od) > NEJVYSSI_VEK:
        return "vysoky-vek", _vek(b.do, d.od)
    return None


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
        z = zivot(b, d) if b and d else None
        if z and z[0] == "umrti-pred-narozenim":
            pridej(k, z[0], f"{n}: úmrtí ({d.text}) je dřív než narození ({b.text})", (b, d), (k,))
        elif z:
            pridej(k, z[0], f"{n}: mezi narozením ({b.text}) a úmrtím ({d.text}) je nejméně {_let(z[1])}", (b, d), (k,))
        if b and m and _vek(b.od, m.do) < SNATEK_VEK:
            pridej(k, "snatek-mlady", f"{n}: sňatek ({m.text}) je dřív než narození ({b.text})" if m.do < b.od else
                   f"{n}: při sňatku ({m.text}) by {jemu} bylo nejvýš {_let(_vek(b.od, m.do))}", (b, m), (k,))
        if m and d and m.od > d.do:
            pridej(k, "snatek-po-umrti", f"{n}: sňatek ({m.text}) je až po úmrtí ({d.text})", (m, d), (k,))
        if not b:
            continue
        syn, syna, narodil = ("syn", "syna", "narodil") if muz(k) else ("dcera", "dcery", "narodila")
        for pozice, zena in ((2 * k, False), (2 * k + 1, True)):
            r = rodic(pozice)
            if not r:
                continue
            rb, rd, rn = ud[r]["narozeni"], ud[r]["umrti"], P[r]["n"]
            if rd and po_smrti_rodice(b, rd, zena):
                pridej(k, "matka-zemrela" if zena else "otec-zemrel",
                       f"{rn} {'zemřela' if zena else 'zemřel'} {rd.text}, {syn} {n} se {narodil} {b.text}", (b, rd), (k, r))
            v = vek_rodice(b, rb, zena) if rb else None
            if not v:
                continue
            pravidlo, jemu_r = ("vek-matky", "jí") if zena else ("vek-otce", "mu")
            if v[0] == "pred":
                text = (f"{rn} se podle údajů {'narodila' if zena else 'narodil'} ({rb.text}) až po narození "
                        f"{syna} ({n}, {b.text})")
            else:
                text = (f"{rn}: při narození {syna} ({n}, {b.text}) by {jemu_r} bylo "
                        f"{'nejvýš' if v[0] == 'mlady' else 'nejméně'} {_let(v[1])}")
            pridej(k, pravidlo, text, (b, rb), (k, r))
    return out


def radky(P, SAME=None):
    """Řádky časové osy [(pozice, hlavní číslo)]: otec nad dítětem, matka pod ním (průchod stromem in-order).

    Předek v rodokmenu vícekrát (SAME = {alias: hlavní}) se na místě aliasu zopakuje i s celou větví předků
    – stejně jako ve vějíři (fan_chart.py, #31). Zástupné osoby („otec neuveden“) řádek nemají.
    """
    SAME = SAME or {}
    mapa = {k: k for k in P if isinstance(k, int) and k >= 1 and k not in SAME}
    vlastni = sorted(mapa)
    for a, c in sorted(SAME.items()):
        for k in vlastni:
            d = k.bit_length() - c.bit_length()
            if d >= 0 and k >> d == c:
                mapa.setdefault((a << d) | (k - (c << d)), k)

    def poradi(k):   # pořadí uzlu k v nekonečném binárním stromu při průchodu in-order (mezery ve stromu nevadí)
        g = k.bit_length() - 1
        return Fraction(2 * (k - (1 << g)) + 1, 1 << (g + 1))
    return [(k, mapa[k]) for k in sorted(mapa, key=poradi) if not zastupna(P[mapa[k]])]


def rok(d):
    """Desetinný rok pro kreslení osy (2. 7. 1890 ≈ 1890,5)."""
    return d.year + (d.timetuple().tm_yday - 1) / (366 if calendar.isleap(d.year) else 365)


def zije(p, ud, dnes):
    """Žijící: poznámka „Žijící…“ (reference/soukromi.md), nebo bez úmrtí a narozen v posledních 100 letech."""
    if (p.get("note") or "").startswith("Žijící"):
        return True
    b = ud.get("narozeni")
    return ud.get("umrti") is None and b is not None and b.od != MIN and b.od.year >= dnes.year - 100


def main():
    if sys.argv[1:2] in (["-h"], ["--help"]):
        sys.exit(__doc__.strip())
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ns = {}
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exec(open(os.path.join(root, "data", "osoby.py"), encoding="utf-8-sig").read(), ns)
    v = kontrola(ns.get("P", {}), ns.get("SAME", {}))
    for x in v:
        print(f"upozornění: časová návaznost u osoby {x.k}: {x.text} Pokud údaj platí, přidej k osobě {x.k} "
              f"do overeno: \"{x.pravidlo}\": \"proč údaj platí\"")
    print(f"{len(v)} upozornění" if v else "Časová návaznost bez nálezů.")


if __name__ == "__main__":
    main()
