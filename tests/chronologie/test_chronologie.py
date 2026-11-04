"""Testy pravidel časové návaznosti (skills/rodokmen/tools/chronologie.py).

Ve složce skillu nejsou, aby se nekopírovaly uživatelům. Jen standardní knihovna, nic nestahují.
Z kořene repozitáře: python -I -X utf8 tests/chronologie/test_chronologie.py
"""
import os, sys
from datetime import date

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "skills", "rodokmen", "tools"))
from chronologie import MIN, MAX, datum, udalosti, zije  # noqa: E402


def test_cele_datum():
    d = datum("* 14. 2. 1890 Holice čp. 112")
    assert (d.od, d.do, d.approx, d.text) == (date(1890, 2, 14), date(1890, 2, 14), False, "14. 2. 1890")


def test_mesic():
    d = datum("× 3/1867 Holice")
    assert (d.od, d.do) == (date(1867, 3, 1), date(1867, 3, 31))


def test_rok():
    d = datum("† 1855 Holice, na choleru")
    assert (d.od, d.do, d.text) == (date(1855, 1, 1), date(1855, 12, 31), "1855")


def test_asi():
    d = datum("* asi 1720")
    assert (d.od, d.do, d.approx, d.text) == (date(1715, 1, 1), date(1725, 12, 31), True, "asi 1720")


def test_pred_po():
    assert (datum("† před 1740").od, datum("† před 1740").do) == (MIN, date(1740, 12, 31))
    assert (datum("† po 1921").od, datum("† po 1921").do) == (date(1921, 1, 1), MAX)
    assert datum("† před 1740").approx and datum("† před 1740").text == "před 1740"


def test_cislo_domu_neni_rok():
    assert datum("* Holice čp. 1234") is None
    assert datum("kovář") is None


def test_neplatny_den():
    d = datum("* 30. 2. 1890")
    assert (d.od, d.do) == (date(1890, 2, 1), date(1890, 2, 28))


def test_y_misto_faktu():
    u = udalosti({8: dict(n="A B", y="asi 1720–1785", f=[])}, 8)
    assert u["narozeni"].od == date(1715, 1, 1) and u["umrti"].do == date(1785, 12, 31) and not u["umrti"].approx
    u = udalosti({8: dict(n="A B", y="1680 – před 1740", f=[])}, 8)
    assert u["narozeni"].od == date(1680, 1, 1) and u["umrti"].od == MIN
    u = udalosti({8: dict(n="A B", y="† 1940", f=[])}, 8)
    assert u["narozeni"] is None and u["umrti"].od.year == 1940
    u = udalosti({8: dict(n="A B", y="* 1895", f=[])}, 8)
    assert u["umrti"] is None and u["narozeni"].od.year == 1895


def test_snatek_s_druhym_rodicem():
    P = {8: dict(n="Jan Novák", f=["× 1915 Praha Anna Malá", "× 20. 6. 1919 Holice Josefa Pokorná"]),
         9: dict(n="Josefa Pokorná", f=[])}
    assert udalosti(P, 8)["snatek"].od == date(1919, 6, 20)


def test_zije():
    d = date(2026, 11, 4)
    assert zije(dict(note="Žijící – údaje jen základní."), {"umrti": None, "narozeni": None}, d)
    assert zije({}, {"umrti": None, "narozeni": datum("* 1950")}, d)
    assert not zije({}, {"umrti": None, "narozeni": datum("* 1900")}, d)


if __name__ == "__main__":
    testy = [f for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for t in testy:
        t()
    print(f"OK {len(testy)} testů")
