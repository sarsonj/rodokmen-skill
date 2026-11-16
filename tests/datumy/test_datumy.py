"""Testy společného čtení dat (skills/rodokmen/tools/datumy.py) a pravidel, která na něm stojí.

Tvary jsou z našich skutečných projektů (dřív falešné poplachy). Jen standardní knihovna, nic nestahují.
Z kořene repozitáře: python -I -X utf8 tests/datumy/test_datumy.py
"""
import os, sys
from datetime import date

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "skills", "rodokmen", "tools"))
from datumy import MAX, MIN, fakt, ged, najdi, z_y  # noqa: E402
import chronologie  # noqa: E402


def roky(d):
    return (d.od.year, d.do.year) if d else None


def test_y_rozmezi_narozeni():   # č. 512: dřív „zemřel 1630“
    n, u = z_y("* asi 1620–1630")
    assert roky(n) == (1615, 1635) and u is None and n.approx


def test_y_zkraceny_rok_a_umrti():
    n, u = z_y("* asi 1760–64, † 1814")
    assert roky(n) == (1755, 1769) and roky(u) == (1814, 1814) and n.rok == 1760


def test_y_alternativy_a_mezi():
    assert roky(z_y("asi 1699/1708–1771")[0]) == (1694, 1713)
    assert roky(z_y("1850 – mezi 1900 a 1905")[1]) == (1900, 1905)
    assert roky(z_y("* 1850 – † před 1900")[1]) == (1, 1900)


def test_y_birth_death_zkracene():
    n, u = z_y("1720–85")
    assert roky(n) == (1720, 1720) and roky(u) == (1785, 1785)


def test_y_nejiste():
    n, _ = z_y("1860 (?) – 1920")
    assert roky(n) == (1859, 1861) and n.approx


def test_fakta_tvary():
    assert fakt("× 1. 27. 1. 1788 Chřešťovice")[1].od == date(1788, 1, 27)   # pořadí sňatku „1.“
    assert fakt("× (2.) 14. 9. 1835 Odřepsy")[1].od == date(1835, 9, 14)
    assert fakt("* a pokřtěn 16. 9. 1772 Velká Doubrava")[1].od == date(1772, 9, 16)
    assert fakt("křest 4. 12. 1786 Dymokury čp. 6") == ("*", fakt("* 4. 12. 1786")[1])   # č. 65 v Jitce
    assert fakt("pohřbena 24. 4. 1716 Žimutice")[0] == "†"
    d = fakt("× 25. (?) 10. 1683 Přeštice")[1]
    assert (d.od, d.do, d.approx) == (date(1683, 10, 1), date(1683, 10, 31), True)
    assert roky(fakt("* asi 1805/06 (28 let)")[1]) == (1800, 1811)               # č. 26 v Jitce
    assert fakt("† (pohřeb) Chrášťany")[1] is None
    assert fakt("křest dcery Anny 1809") is None
    assert fakt("kovář") is None


def test_najdi():
    assert najdi("Křest 3. 3. 1760, Lhota č. 5").od == date(1760, 3, 3)
    assert najdi("fol. 12, asi 1760").rok == 1760
    assert najdi("bez data") is None


def test_ged():
    assert ged("12 MAR 1850").od == date(1850, 3, 12)
    assert roky(ged("ABT 1850")) == (1845, 1855)
    assert ged("BEF 1850").od == MIN and ged("AFT 1850").do == MAX
    assert roky(ged("BET 1840 AND 1845")) == (1840, 1845)
    assert roky(ged("1750/51")) == (1750, 1751)
    assert ged("8. 1945").od == date(1945, 8, 1)   # česká data z Brother's Keeperu po převodu


def test_otec_po_75():
    P = {8: dict(n="Milena Vokněrová", f=["* 1884"]), 16: dict(n="Matěj Vokněr", f=["* 1807"])}
    v = chronologie.kontrola(P)
    assert [(x.k, x.pravidlo) for x in v] == [(8, "vek-otce")] and "nejméně 76 let" in v[0].text


def test_vysoky_vek():
    v = chronologie.kontrola({8: dict(n="A B", f=["* 1700", "† 1810"])})
    assert [(x.k, x.pravidlo) for x in v] == [(8, "vysoky-vek")]


def test_krest_jako_narozeni():
    P = {8: dict(n="Jan Novák", f=["křest 4. 12. 1786"]), 17: dict(n="Anna Malá", f=["† 1780"])}
    assert [(x.k, x.pravidlo) for x in chronologie.kontrola(P)] == [(8, "matka-zemrela")]


if __name__ == "__main__":
    testy = [f for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    chyby = 0
    for t in testy:
        try:
            t()
        except Exception as e:  # noqa: BLE001 – vypsat všechny selhané testy, ne jen první
            chyby += 1
            print(f"FAIL {t.__name__}: {type(e).__name__} {e}")
    print(f"OK {len(testy)} testů" if not chyby else f"{chyby} z {len(testy)} testů selhalo")
    sys.exit(1 if chyby else 0)
