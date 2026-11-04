"""Testy pravidel časové návaznosti (skills/rodokmen/tools/chronologie.py).

Ve složce skillu nejsou, aby se nekopírovaly uživatelům. Jen standardní knihovna, nic nestahují.
Z kořene repozitáře: python -I -X utf8 tests/chronologie/test_chronologie.py
"""
import os, sys
from datetime import date

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "skills", "rodokmen", "tools"))
from chronologie import MIN, MAX, datum, kontrola, radky, rok, udalosti, zije  # noqa: E402


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


# --- pravidla ---------------------------------------------------------------------------------------------------
JISTE, NEJISTE = " – jeden z údajů asi nesedí.", " – údaje jsou nejisté, možná nesedí."


def rodina(otec=(), matka=(), dite=("* 1890",), st_otce="doc"):
    """Syn Jan Novák (8), otec Václav Novák (16), matka Barbora Malá (17)."""
    return {8: dict(n="Jan Novák", f=list(dite), st="doc"), 16: dict(n="Václav Novák", f=list(otec), st=st_otce),
            17: dict(n="Barbora Malá", f=list(matka), st="doc")}


def nalez(P, SAME=None):
    return [(v.k, v.pravidlo) for v in kontrola(P, SAME)]


def test_otec_zemrel_text():
    v = kontrola(rodina(otec=["† 1887"]))
    assert [(x.k, x.pravidlo, x.osoby, x.mozna) for x in v] == [(8, "otec-zemrel", (8, 16), False)]
    assert v[0].text == "Václav Novák zemřel 1887, syn Jan Novák se narodil 1890" + JISTE


def test_pohrobek_jen_roky():
    assert nalez(rodina(otec=["† 1889"])) == []


def test_pohrobek_cela_data():
    assert nalez(rodina(otec=["† 1. 1. 1890"], dite=["* 1. 12. 1890"])) == [(8, "otec-zemrel")]
    assert nalez(rodina(otec=["† 1. 4. 1890"], dite=["* 1. 12. 1890"])) == []


def test_matka_zemrela():
    assert nalez(rodina(matka=["† 1890"])) == []
    v = kontrola(rodina(matka=["† 1889"]))
    assert [(x.k, x.pravidlo, x.osoby) for x in v] == [(8, "matka-zemrela", (8, 17))]
    assert v[0].text == "Barbora Malá zemřela 1889, syn Jan Novák se narodil 1890" + JISTE


def test_vek_matky():
    assert nalez(rodina(matka=["* 1875"])) == []
    assert nalez(rodina(matka=["* 1839"])) == []
    v = kontrola(rodina(matka=["* 1876"]))
    assert v[0].text == "Barbora Malá: při narození syna (Jan Novák, 1890) by jí bylo nejvýš 14 let" + JISTE
    v = kontrola(rodina(matka=["* 1830"]))
    assert v[0].text == "Barbora Malá: při narození syna (Jan Novák, 1890) by jí bylo nejméně 59 let" + JISTE


def test_vek_otce():
    v = kontrola(rodina(otec=["* 1877"]))
    assert [(x.k, x.pravidlo) for x in v] == [(8, "vek-otce")]
    assert v[0].text == "Václav Novák: při narození syna (Jan Novák, 1890) by mu bylo nejvýš 13 let" + JISTE


def test_snatek_mlady():
    v = kontrola({9: dict(n="Josefa Pokorná", f=["* 1900", "× 1913 Holice Jan Novák"])})
    assert [(x.k, x.pravidlo) for x in v] == [(9, "snatek-mlady")]
    assert v[0].text == "Josefa Pokorná: při sňatku (1913) by jí bylo nejvýš 13 let" + JISTE


def test_snatek_po_umrti():
    v = kontrola({8: dict(n="Jan Novák", f=["× 1920 Holice", "† 1918"])})
    assert [(x.k, x.pravidlo) for x in v] == [(8, "snatek-po-umrti")]
    assert v[0].text == "Jan Novák: sňatek (1920) je až po úmrtí (1918)" + JISTE


def test_umrti_pred_narozenim():
    v = kontrola({8: dict(n="Jan Novák", f=["* 1900", "† 1890"])})
    assert [(x.k, x.pravidlo) for x in v] == [(8, "umrti-pred-narozenim")]
    assert v[0].text == "Jan Novák: úmrtí (1890) je dřív než narození (1900)" + JISTE


def test_nejiste_mirnejsi():
    v = kontrola(rodina(otec=["† 1887"], st_otce="prob"))
    assert v[0].mozna and v[0].text.endswith(NEJISTE)


def test_otevrene_meze():
    v = kontrola(rodina(otec=["† před 1740"], dite=["* 1745"]))
    assert [(x.pravidlo, x.mozna) for x in v] == [("otec-zemrel", True)]
    assert nalez(rodina(otec=["† po 1700"], dite=["* 1745"])) == []


def test_overeno():
    P = rodina(otec=["† 1887"])
    P[8]["overeno"] = {"otec-zemrel": "pohrobek, zápis křtu to výslovně uvádí"}
    assert nalez(P) == []


def test_overeno_u_aliasu():
    P = rodina(otec=["† 1887"])
    P[20] = dict(n="Jan Novák", f=["TÁŽ OSOBA jako 8"], overeno={"otec-zemrel": "ověřeno"})
    assert nalez(P, {20: 8}) == []


def test_same_jednou():
    P = rodina(otec=["† 1887"])
    P[20] = dict(n="Jan Novák", f=["TÁŽ OSOBA jako 8"])
    P[10] = dict(n="Anna Králová", f=["* 1915"])
    assert nalez(P, {20: 8}) == [(8, "otec-zemrel")]


def test_zastupna_osoba():
    P = rodina()
    P[16] = dict(n="otec neuveden", f=["† 1887"], st="unk")
    assert nalez(P) == []


def test_ukazka_bez_varovani():
    ns = {}
    exec(open(os.path.join(REPO, "skills", "rodokmen", "template", "ukazka", "osoby.py"), encoding="utf-8").read(), ns)
    assert kontrola(ns["P"], ns.get("SAME", {})) == []


# --- řádky osy -------------------------------------------------------------------------------------------------
def test_radky_poradi():
    P = {k: dict(n=f"O{k}", f=[]) for k in range(1, 8)}
    assert [p for p, _ in radky(P)] == [4, 2, 5, 1, 6, 3, 7]


def test_radky_same_zrcadli_vetev():
    P = {k: dict(n=f"O{k}", f=[]) for k in (1, 2, 3, 4, 5, 6, 7, 8, 9)}
    P[6] = dict(n="TÁŽ", f=["TÁŽ OSOBA jako 4"])
    r = radky(P, {6: 4})
    assert (12, 8) in r and (13, 9) in r and (6, 4) in r
    assert [p for p, _ in r] == [8, 4, 9, 2, 5, 1, 12, 6, 13, 3, 7]


def test_radky_bez_zastupnych():
    P = {1: dict(n="A", f=[]), 2: dict(n="otec neuveden", f=[]), 3: dict(n="B", f=[])}
    assert [p for p, _ in radky(P)] == [1, 3]


def test_radky_s_mezerou():
    P = {1: dict(n="A", f=[]), 4: dict(n="B", f=[])}   # otec 2 chybí, dědeček 4 je známý
    assert [p for p, _ in radky(P)] == [4, 1]


def test_rok():
    assert rok(date(1890, 1, 1)) == 1890.0
    assert abs(rok(date(1890, 7, 2)) - 1890.5) < 0.01


# --- nálezy závěrečné revize -------------------------------------------------------------------------------------
def test_po_v_y_je_umrti_po():
    u = udalosti({8: dict(n="A B", y="po 1921", f=[])}, 8)
    assert u["narozeni"] is None and (u["umrti"].od, u["umrti"].do) == (date(1921, 1, 1), MAX)


def test_spojovnik_v_y():
    u = udalosti({8: dict(n="A B", y="1930-2015", f=[])}, 8)
    assert u["narozeni"].od.year == 1930 and u["umrti"].od.year == 2015


def test_rok_nula_nespadne():
    assert datum("* 0000 Holice") is None
    assert udalosti({8: dict(n="A B", y="asi 0003", f=["† 0000"])}, 8) == {"narozeni": None, "snatek": None, "umrti": None}


def test_matka_narozena_po_diteti():
    v = kontrola(rodina(matka=["* 1895"]))
    assert [(x.k, x.pravidlo) for x in v] == [(8, "vek-matky")]
    assert v[0].text == "Barbora Malá se podle údajů narodila (1895) až po narození syna (Jan Novák, 1890)" + JISTE


def test_otec_narozen_po_diteti():
    v = kontrola(rodina(otec=["* 1895"]))
    assert [(x.k, x.pravidlo) for x in v] == [(8, "vek-otce")]
    assert v[0].text == "Václav Novák se podle údajů narodil (1895) až po narození syna (Jan Novák, 1890)" + JISTE


def test_snatek_pred_narozenim():
    v = kontrola({8: dict(n="Jan Novák", f=["* 1900", "× 1890 Holice"])})
    assert [(x.k, x.pravidlo) for x in v] == [(8, "snatek-mlady")]
    assert v[0].text == "Jan Novák: sňatek (1890) je dřív než narození (1900)" + JISTE


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
