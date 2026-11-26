"""Test sčítání lidu v portafontium.py (scitani, domy, info/link/svazek pro dům) – offline na uložených stránkách.

Z kořene repozitáře:
  python3 -I tests/portafontium/test_scitani.py skills/rodokmen/tools
Na archiv nechodí: get() se nahradí uloženými stránkami portálu (scitani_*.html, stav 12. 11. 2026):
přehled /contents/census, soudní okres Plánice 1880 a 1921, domy obce Neprochovy 1921 čp. 1 (první dům sady,
/iipimage/34427048) a čp. 12 (/iipimage/34427062).
Ostatní roky okresu vrací prázdnou stránku (obec v nich „není“).
"""
import contextlib, io, json, os, shutil, sys, tempfile

TOOLS = os.path.abspath(sys.argv[1])
TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
sys.argv = sys.argv[:1] + ["x"]   # portafontium.py bez argumentů vypíše nápovědu a skončí
import portafontium as pf  # noqa: E402

vysledky = []


def check(nazev, ok, detail=""):
    vysledky.append(bool(ok))
    print(f"[{'OK ' if ok else 'CHYBA'}] {nazev}{'' if ok else '  ' + str(detail)[:600]}", flush=True)


def stranka(n):
    return open(os.path.join(TU, n), encoding="utf-8").read()


ADRESY = []
STRANKY = {"/contents/census": "scitani_prehled.html",
           "/census/soap-kt/1880/okres-planice": "scitani_planice_1880.html",
           "/census/soap-kt/1921/okres-planice": "scitani_planice_1921.html",
           "/iipimage/34427048": "scitani_dum_34427048.html",
           "/iipimage/34427062": "scitani_dum_34427062.html"}


def fake_get(url, binary=False):
    ADRESY.append(url)
    return stranka(STRANKY[url]) if url in STRANKY else "<html>/census/ prázdná stránka okresu</html>"


def vystup(f, *a):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        f(*a)
    return out.getvalue()


tmp = tempfile.mkdtemp()
try:
    pf.get = fake_get
    pf.CACHE = os.path.join(tmp, "cache")
    pf.ROOT = tmp
    os.makedirs(os.path.join(tmp, "data"))

    prehled = pf.scitani_prehled()
    okresy = {(a, o): r for a, o, r in prehled}
    check("přehled: 32 soudních okresů", len(prehled) == 32, len(prehled))
    check("přehled: Plánice 1880–1921", okresy.get(("soap-kt", "okres-planice")) == [1880, 1890, 1900, 1910, 1921],
          okresy.get(("soap-kt", "okres-planice")))
    check("přehled: Domažlice od 1857", okresy.get(("soap-do", "okres-domazlice"), [0])[0] == 1857)

    obce = pf.scitani_okres("soap-kt", 1921, "okres-planice")
    nep = [x for x in obce if x[0].startswith("Neprochovy")]
    check("okres 1921: Neprochovy 38 domů, první dům 34427048",
          nep == [("Neprochovy (Neprachow, Neprachov)", 38, "34427048", "")], nep)
    check("okres 1921: německá část stránky se nezdvojí", len(nep) == 1, nep)
    obce80 = pf.scitani_okres("soap-kt", 1880, "okres-planice")
    jen_souhrn = [x for x in obce80 if x[0].startswith("Ústaleč") and not x[2]]
    check("okres 1880: obec jen se souhrnem (Ústaleč)", jen_souhrn and jen_souhrn[0][3] == "34441350", jen_souhrn)

    check("shoda názvu: osada jiné obce",
          pf._sedi("Těchonice - Neprochovy (Těchonitz - Neprachow, Těchonice - Neprachov)", "neprochovy"))
    check("shoda názvu: německý název", pf._sedi("Neprochovy (Neprachow, Neprachov)", "Neprachow"))
    check("shoda názvu: jen celé slovo", not pf._sedi("Neprochovy (Neprachow)", "Neproch"))

    ADRESY.clear()
    t = vystup(pf.scitani, "Neprochovy", "Plánice")
    check("hledání s okresem: jen stránky okresu Plánice", all("planice" in u for u in ADRESY), ADRESY)
    check("hledání: 1880 jako osada Těchonic",
          "1880 | Těchonice - Neprochovy (Těchonitz - Neprachow, Těchonice - Neprachov) | 31 domů | 34439398" in t, t)
    check("hledání: 1921", "1921 | Neprochovy (Neprachow, Neprachov) | 38 domů | 34427048" in t, t)
    check("hledání: hlásí roky okresu bez obce", "1890, 1900, 1910" in t, t)

    t = vystup(pf.domy, "34427062")
    check("domy: čp. 12 je aktuální stránka", "čp. 12 | 34427062" in t, t)
    check("domy: čísla s písmenem (1a)", "čp. 1a | 34427049" in t, t)
    check("domy: chybějící číslo se nedoplní", "čp. 36 |" not in t, t)
    radky = [r.split(" |")[0] for r in t.splitlines() if r.startswith("čp.")]
    check("domy: všech 38 čísel", len(radky) == 38, radky)
    check("domy: řazení podle čísla",
          [radky.index(f"čp. {c}") for c in ("1", "1a", "2", "9", "10", "12")]
          == sorted(radky.index(f"čp. {c}") for c in ("1", "1a", "2", "9", "10", "12")), radky[:14])
    check("domy: tentýž dům v jiných letech", "Tentýž dům (čp. 12) v jiných letech: 1890 -> 34426956" in t, t)

    # první dům sady: titulek číslo neuvádí, je jen zvýrazněné v seznamu domů
    t = vystup(pf.domy, "34427048")
    check("domy z prvního domu: čp. 1 v seznamu", "čp. 1 | 34427048" in t, t)
    check("domy z prvního domu: hlásí čp. 1", "Tentýž dům (čp. 1)" in t, t)
    check("info prvního domu: číslo v názvu",
          pf.info("34427048")[1].get("Název") == "Census 1921 Neprochovy (Neprachow, Neprachov), Nr. 1",
          pf.info("34427048")[1])

    k, f, s, l = pf.info("34427062")
    check("info: název a okres", f.get("Název") == "Census 1921 Neprochovy (Neprachow, Neprachov), Nr. 12"
          and f.get("Okres") == "Politický okres: Klatovy, Soudní okres: Plánice", f)
    check("info: 3 snímky", len(s) == 3, s)
    check("link: snímek 2", pf.BASE + pf.scan("34427062", 2)[3]
          == "https://www.portafontium.eu/iipimage/34427062/soap-kt_01159_census-1921-neprochovy-cp012_0020")

    vystup(pf.svazek, "34427062")
    sv = json.load(open(os.path.join(tmp, "data", "svazky.json"), encoding="utf-8"))["pf_34427062"]
    check("svazek: archiv SOkA Klatovy", sv["archiv"] == "SOkA Klatovy – sčítací operáty", sv)
    check("svazek: název s čp.", sv["svazek"] == "Sčítání lidu 1921 Neprochovy (Neprachow, Neprachov), čp. 12", sv)
    check("svazek: adresa domu", sv["url"] == "https://www.portafontium.eu/iipimage/34427062", sv)

    ADRESY.clear()
    pf.scitani_okres("soap-kt", 1921, "okres-planice")
    check("stránky okresu jsou v mezipaměti", ADRESY == [], ADRESY)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\n{sum(vysledky)} z {len(vysledky)} správně")
sys.exit(0 if all(vysledky) else 1)
