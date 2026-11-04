"""Testy tools/mista.py (výběr sídla z odpovědi Nominatimu, varování u vzdáleného bodu) a nápovědy v kontrole mapy.

Z kořene repozitáře:
  python3 -I tests/mista/test_mista.py
  (Windows: python -I -X utf8 tests/mista/test_mista.py)
Nic nestahuje: odpovědi Nominatimu jsou vepsané v testu, geocode() se nahradí. Kontrola běží v dočasném projektu.
"""
import contextlib, importlib.util, io, json, os, shutil, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "skills", "rodokmen", "tools")
os.environ.setdefault("SLUSNE_STAV", tempfile.mkdtemp(prefix="mista_slusne_"))   # brzda při importu nesahá na skutečný stav
spec = importlib.util.spec_from_file_location("mista", os.path.join(TOOLS, "mista.py"))
mista = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mista)

BAR = {"class": "amenity", "type": "bar", "lat": "50.7741", "lon": "15.0632",
       "display_name": "Andelka;Herna Bar, Letná, Liberec III-Jeřáb, Liberec, okres Liberec, Liberecký kraj, Česko"}
VES = {"class": "place", "type": "village", "lat": "50.9890", "lon": "15.1076",
       "display_name": "Andělka, Višňová, okres Liberec, Liberecký kraj, Česko"}
OBEC = {"class": "boundary", "type": "administrative", "addresstype": "municipality", "place_rank": 14,
        "lat": "49.9606", "lon": "13.9622",
        "display_name": "Korycany, okres Beroun, Středočeský kraj, Česko"}

vysledky = []


def ok(nazev, podminka, detail=""):
    vysledky.append(bool(podminka))
    print(("OK   " if podminka else "CHYBA"), nazev, "" if podminka else detail)


def spust_mista(cache, argv, odpovedi):
    """main() v dočasné složce; odpovedi = {dotaz: seznam výsledků Nominatimu (bez featuretype, se settlement)}."""
    d = tempfile.mkdtemp(prefix="mista_")
    out = os.path.join(d, "mista.json")
    json.dump(cache, open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False)
    dotazy = []

    def nominatim(par):
        dotazy.append(par)
        sidla = par.get("featuretype") == "settlement"
        return [r for r in odpovedi.get(par["q"], []) if not sidla or r["class"] in ("place", "boundary")]

    puvodni = mista.OUT, mista.nominatim, sys.argv
    mista.OUT, mista.nominatim, sys.argv = out, nominatim, ["mista.py"] + argv
    vystup = io.StringIO()
    try:
        with contextlib.redirect_stdout(vystup):
            mista.main()
    finally:
        mista.OUT, mista.nominatim, sys.argv = puvodni
    return vystup.getvalue(), json.load(open(out, encoding="utf-8")), dotazy


# vyber(): první sídlo, jinak první výsledek s příznakem
ok("vyber: bar přeskočí, vezme ves", mista.vyber([BAR, VES]) == (VES, True), mista.vyber([BAR, VES]))
ok("vyber: boundary je obec", mista.vyber([OBEC]) == (OBEC, True))
ok("vyber: jen bar = nalez s příznakem", mista.vyber([BAR]) == (BAR, False))
ok("vyber: nic = None", mista.vyber([]) is None)

# vzdalenost_km(): Praha – Brno vzdušnou čarou asi 185 km
km = mista.vzdalenost_km((50.0755, 14.4378), (49.1951, 16.6068))
ok("vzdalenost_km Praha–Brno", 180 < km < 190, km)
ok("vzdalenost_km stejný bod", mista.vzdalenost_km((50, 15), (50, 15)) < 1e-9)

# nejblizsi(): jiné místo se souřadnicemi, ne samo sebe, ne místa bez souřadnic
c = {"A": {"lat": 50.0, "lon": 15.0}, "B": {"lat": 50.1, "lon": 15.0}, "C": {"lat": 49.0, "lon": 15.0}, "D": {}}
n = mista.nejblizsi("A", c)
ok("nejblizsi: B", n and n[1] == "B" and 10 < n[0] < 12, n)
ok("nejblizsi: jediné místo = None", mista.nejblizsi("A", {"A": {"lat": 50, "lon": 15}, "D": {}}) is None)

# main(): dotaz na sídla, bar odmítnut
vystup, cache, dotazy = spust_mista({"Liberec": {"re": "Libere", "lat": 50.767, "lon": 15.056}},
                                    ["pridej", "Andělka", "Anděl", "Andělka, Liberec"], {"Andělka, Liberec": [BAR, VES]})
ok("main: první dotaz má featuretype=settlement", dotazy and dotazy[0].get("featuretype") == "settlement", dotazy)
ok("main: uloží ves, ne bar", cache["Andělka"].get("lat") == 50.989, cache["Andělka"])
ok("main: ves 25 km od Liberce bez varování", "POZOR" not in vystup, vystup)

# main(): jen bar → zkusí bez omezení, uloží s varováním
vystup, cache, dotazy = spust_mista({"Liberec": {"re": "Libere", "lat": 50.767, "lon": 15.056}},
                                    ["pridej", "Andělka", "Anděl", "Andělka, Liberec"], {"Andělka, Liberec": [BAR]})
ok("main: bez sídla druhý dotaz bez featuretype", len(dotazy) == 2 and "featuretype" not in dotazy[1], dotazy)
ok("main: bar uložen, ale hlášen jako ne-obec", "lat" in cache["Andělka"] and "není obec" in vystup, vystup)

# main(): bod daleko od ostatních → varování se vzdáleností a adresou z OSM
KORYCANY_KM = {"class": "boundary", "type": "administrative", "addresstype": "town", "place_rank": 16,
               "lat": "49.1063", "lon": "17.1645",
               "display_name": "Koryčany, okres Kroměříž, Zlínský kraj, Česko"}
vystup, cache, _ = spust_mista({"Beroun": {"re": "Beroun", "lat": 49.9638, "lon": 14.0720}},
                               ["pridej", "Korycany"], {"Korycany, Česko": [KORYCANY_KM]})
ok("main: vzdálené místo hlásí km a okres", "POZOR" in vystup and " km " in vystup and "Kroměříž" in vystup, vystup)
vystup, cache, _ = spust_mista({"Beroun": {"re": "Beroun", "lat": 49.9638, "lon": 14.0720}},
                               ["pridej", "Korycany"], {"Korycany, Česko": [OBEC]})
ok("main: blízké místo bez varování", "POZOR" not in vystup, vystup)
vystup, cache, _ = spust_mista({}, ["pridej", "Korycany"], {"Korycany, Česko": [KORYCANY_KM]})
ok("main: první místo projektu bez varování", "POZOR" not in vystup, vystup)

# vyber(): ostrov ani chráněné území nejsou sídlo, obecní hranice ano
OSTROV = {"class": "place", "type": "island", "lat": "50.0", "lon": "15.0", "display_name": "Ostrov, Česko"}
CHKO = {"class": "boundary", "type": "protected_area", "lat": "50.0", "lon": "15.0", "display_name": "CHKO, Česko"}
ok("vyber: ostrov před vsí – vezme ves", mista.vyber([OSTROV, VES]) == (VES, True), mista.vyber([OSTROV, VES]))
ok("vyber: chráněné území = s příznakem", mista.vyber([CHKO]) == (CHKO, False), mista.vyber([CHKO]))
ok("vyber: osada (hamlet) je obec", mista.vyber([dict(VES, type="hamlet")])[1] is True)

# nejblizsi(): souřadnice jako text, chybějící lon, None, nesmysl – nespadne, nepoužitelná místa přeskočí
c = {"A": {"lat": 50.0, "lon": 15.0}, "B": {"lat": "50.1", "lon": "15.0"}, "C": {"lat": 49.0},
     "D": {"lat": None, "lon": None}, "E": {"lat": "?", "lon": 15.0}}
try:
    n = mista.nejblizsi("A", c)
except Exception as e:  # noqa: BLE001
    n = e
ok("nejblizsi: text, chybějící lon, None", isinstance(n, tuple) and n[1] == "B" and 10 < n[0] < 12, n)
try:
    vystup, cache, _ = spust_mista({"Beroun": {"lat": "49.9638", "lon": "14.0720"}, "Zlom": {"lat": 50.0, "lon": None}},
                                   ["pridej", "Korycany"], {"Korycany, Česko": [OBEC]})
    ok("main: s rozbitými souřadnicemi jiných míst uloží nové místo", cache["Korycany"].get("lat") == 49.9606, cache)
except Exception as e:  # noqa: BLE001
    ok("main: s rozbitými souřadnicemi jiných míst uloží nové místo", False, repr(e))

# main(): vzdálenost se počítá až po celé dávce, nezávisle na pořadí
A = [{"class": "place", "type": "village", "lat": "50.0", "lon": "15.0", "display_name": "A, Česko"}]
B = [{"class": "place", "type": "village", "lat": "50.009", "lon": "15.0", "display_name": "B, Česko"}]
for poradi in (("A", "B"), ("B", "A")):
    cache0 = {"C": {"re": "C", "lat": 49.0, "lon": 15.0}, **{x: {"re": x} for x in poradi}}
    vystup, _, _ = spust_mista(cache0, [], {"A, Česko": A, "B, Česko": B})
    ok(f"main: pořadí {'+'.join(poradi)} – A ani B nejsou daleko (mají sebe)", "POZOR" not in vystup, vystup)

# vyber(): kraj nebo okres (boundary/administrative nad úrovní obce) není sídlo
KRAJ = {"class": "boundary", "type": "administrative", "addresstype": "state", "place_rank": 8,
        "lat": "50.6", "lon": "15.0", "display_name": "Liberecký kraj, Česko"}
OKRES = dict(KRAJ, addresstype="county", place_rank=12, display_name="okres Liberec, Liberecký kraj, Česko")
ok("vyber: kraj před vsí – vezme ves", mista.vyber([KRAJ, VES]) == (VES, True), mista.vyber([KRAJ, VES]))
ok("vyber: jen kraj = s příznakem", mista.vyber([KRAJ]) == (KRAJ, False), mista.vyber([KRAJ]))
ok("vyber: jen okres = s příznakem", mista.vyber([OKRES]) == (OKRES, False), mista.vyber([OKRES]))
ok("vyber: obecní hranice bez addresstype, place_rank 16 je obec",
   mista.vyber([{"class": "boundary", "type": "administrative", "place_rank": 16}])[1] is True)
POLE = {"class": "place", "type": "locality", "lat": "50.0", "lon": "15.0", "display_name": "Na Vinici, Česko"}
ok("vyber: pojmenované místo (locality) před vsí – vezme ves", mista.vyber([POLE, VES]) == (VES, True),
   mista.vyber([POLE, VES]))
ok("vyber: jen locality = s příznakem", mista.vyber([POLE]) == (POLE, False), mista.vyber([POLE]))

# bod(): nekonečno, NaN a souřadnice mimo rozsah jsou nepoužitelné; dávka se uloží
for spatne in ({"lat": "Infinity", "lon": "15"}, {"lat": "NaN", "lon": "15"}, {"lat": 50, "lon": "-inf"},
               {"lat": 91, "lon": 15}, {"lat": 50, "lon": 181}):
    ok(f"bod: {spatne} = None", mista.bod(spatne) is None, mista.bod(spatne))
try:
    vystup, cache, _ = spust_mista({"Beroun": {"lat": 49.9638, "lon": 14.0720}, "Inf": {"lat": "Infinity", "lon": "15"},
                                    "Nan": {"lat": "NaN", "lon": "15"}}, ["pridej", "Korycany"], {"Korycany, Česko": [OBEC]})
    ok("main: s Infinity/NaN u jiných míst uloží nové místo bez varování",
       cache["Korycany"].get("lat") == 49.9606 and "POZOR" not in vystup, vystup)
except Exception as e:  # noqa: BLE001
    ok("main: s Infinity/NaN u jiných míst uloží nové místo bez varování", False, repr(e))

# kontrola.slova_obce(): víceslovné názvy s přídavným jménem na -ích
spec = importlib.util.spec_from_file_location("kontrola", os.path.join(TOOLS, "kontrola.py"))
kontrola = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kontrola)
for fakt, cekam in (("v Horních Počernicích", "Horních Počernicích"), ("z Dolních Břežan", "Dolních Břežan")):
    ok(f"slova_obce: {fakt}", kontrola.slova_obce([fakt]) == [cekam], kontrola.slova_obce([fakt]))

# kontrola.py: u osoby bez obce ukáže slova z faktů, která vypadají jako obec
d = tempfile.mkdtemp(prefix="kontrola_")
os.makedirs(os.path.join(d, "tools"))
os.makedirs(os.path.join(d, "data"))
shutil.copy(os.path.join(TOOLS, "kontrola.py"), os.path.join(d, "tools"))
with open(os.path.join(d, "data", "osoby.py"), "w", encoding="utf-8", newline="\n") as f:
    f.write("P = {1: {'n': 'Jan Novák', 'st': 'doc', 'r': ['k'], 'f': ['* 3. 5. 1850 Přesece čp. 4', 'sedlák v Nové Vsi u Klikova',"
            " '† 1900 z Ostrovce']},\n     2: {'n': 'Josef Novák', 'st': 'doc', 'r': ['k'], 'f': ['* 1820 Holice']}}\n")
json.dump({"Holice": {"re": "Holic", "lat": 50.0, "lon": 15.9}, "Přesek": {"re": "Přesek", "lat": 49.0, "lon": 14.8}},
          open(os.path.join(d, "data", "mista.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False)
p = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(d, "tools", "kontrola.py")],
                   capture_output=True, text=True, encoding="utf-8")
radek = next((l for l in p.stdout.splitlines() if "mapa:" in l), "")
ok("kontrola: hlásí osobu 1 bez obce", "1 Jan Novák" in radek and "2 Josef" not in radek, p.stdout + p.stderr)
ok("kontrola: ukáže slova Přesece, Nové Vsi, Klikova, Ostrovce",
   all(s in radek for s in ("Přesece", "Nové Vsi", "Klikova", "Ostrovce")), radek)

print(f"\n{sum(vysledky)} z {len(vysledky)} v pořádku")
sys.exit(0 if all(vysledky) else 1)
