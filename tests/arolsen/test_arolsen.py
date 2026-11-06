"""Testy tools/arolsen.py (Arolsen Archives): souhlas s podmínkami, filtry, stránkování a výpis, kontrola adresy obrázku.

Z kořene repozitáře:
  python3 -I tests/arolsen/test_arolsen.py
  (Windows: python -I -X utf8 tests/arolsen/test_arolsen.py)
Nic nestahuje: API Arolsenu se nahradí simulací (post()). Stav souhlasu a brzdy je v dočasných složkách.
"""
import contextlib, importlib.util, io, os, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "skills", "rodokmen", "tools")
os.environ["SLUSNE_STAV"] = tempfile.mkdtemp(prefix="arolsen_slusne_")
os.environ["SOUHLAS_STAV"] = tempfile.mkdtemp(prefix="arolsen_souhlas_")
spec = importlib.util.spec_from_file_location("arolsen", os.path.join(TOOLS, "arolsen.py"))
arolsen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arolsen)

vysledky = []


def ok(nazev, podminka, detail=""):
    vysledky.append(bool(podminka))
    print(("OK   " if podminka else "CHYBA"), nazev, "" if podminka else detail)


def nastroj(*argv):
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(TOOLS, "arolsen.py"), *argv], capture_output=True, text=True,
                       env={**os.environ}, timeout=60)
    return r.returncode, r.stdout, r.stderr


# --- souhlas: bez něj nástroj nic nestahuje
for prikaz in (["hledat", "Novak"], ["karta", "10717351", "x.jpg"]):
    k, out, err = nastroj(*prikaz)
    ok(f"bez souhlasu: {prikaz[0]} skončí kódem 4 a nic nevypíše", k == 4 and not out and "uživatel sám" in err, (k, out, err))
k, out, err = nastroj("souhlas")
ok("souhlas z neinteraktivního prostředí (Claude, skript) se nezapíše", k == 4 and not os.listdir(os.environ["SOUHLAS_STAV"]), (k, err))
ok("znění souhlasu je původní prohlášení portálu", "Declaration of consent" in arolsen.SOUHLAS_ZNENI and "criminal charges" in arolsen.SOUHLAS_ZNENI)
for chybne in (["hledat", "Novak", "--max"], ["hledat", "Novak", "--rodne", "--max", "5"], ["hledat", "Novak", "--jazyk", "cs"]):
    k, out, err = nastroj(*chybne)
    ok(f"neplatná volba {' '.join(chybne[2:])} skončí hláškou", k not in (0, None) and "neplatná" in err, (k, err))

# --- simulace API
RADEK = {"ObjId": 10717351, "LastName": "NOWAK", "FirstName": "Josef", "MaidenName": "", "Dob": "03/05/1923", "PlaceBirth": "Praha",
         "PrisonerNumber": "103258", "Nationality": "Czech", "Signature": "1.1.6.7 - Office Cards Dachau A-Z", "Father": "Jan",
         "Date_of_decease": "12/31/1944", "Last_residence_town": "Brno"}
RADEK2 = {"ObjId": 2, "LastName": None, "FirstName": None, "Dob": "", "Signature": "x"}
TAGY = [{"id": 17012569, "desc": "Czech", "count": 94}, {"id": 9446, "desc": "Czechoslovakian", "count": 230}]


def spust(dotaz, maxn=40, filtry=None, od=0, podrobne=False, radky=(RADEK, RADEK2), celkem="2"):
    volani = []

    def post(metoda, data):
        volani.append((metoda, data))
        return {"GetCount": celkem, "GetPersonList": list(radky), "GetTagList": TAGY}.get(metoda, True)
    puvodni = arolsen.post
    arolsen.post = post
    out, err, k = io.StringIO(), io.StringIO(), None
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                arolsen.hledat(dotaz, maxn, "en", filtry, od, podrobne)
            except SystemExit as e:
                k = e.code
    finally:
        arolsen.post = puvodni
    return k, out.getvalue(), err.getvalue(), volani


k, out, err, volani = spust("Novak Josef 1923")
radky = out.strip().splitlines()
ok("hledat: pořadí volání dotaz → počet → seznam", [v[0] for v in volani] == ["BuildQueryGlobalForAngular", "GetCount", "GetPersonList"], volani)
ok("hledat: dotaz jde na server beze změny", volani[0][1]["strSearch"] == "Novak Josef 1923", volani[0])
ok("hledat: datum měsíc/den/rok se převede na den. měsíc. rok", "5. 3. 1923" in radky[0], radky[0])
ok("hledat: odkaz na dokument v archivu", radky[0].endswith("/en/document/10717351"), radky[0])
ok("hledat: záznam s prázdnými poli (None) nespadne, vypíše pomlčky", radky[1].startswith("2 | - | - | - | - |"), radky[1])

k, out, err, volani = spust("Novak", filtry={"misto": "Praha", "cislo": "A-1234", "narodnost": "czech"})
metody = [v[0] for v in volani]
grid = next(v[1] for v in volani if v[0] == "BuildGridFilter")["filter"]["Filters"]
ok("filtry: místo narození = „obsahuje“ a číslo vězně = „eq“", {(f["Field"], f["Operator"], f["Value"]) for f in grid} ==
   {("PlaceBirth", "contains", "Praha"), ("PrisonerNumber", "eq", "A-1234")}, grid)
ok("filtry: národnost se přeloží na id položky bez ohledu na velikost písmen", next(v[1] for v in volani if v[0] == "BuildFilter")["filter"] == {"per_nationality": [17012569]}, volani)
ok("filtry: počet se ptá s useFilter", next(v[1] for v in volani if v[0] == "GetCount")["useFilter"] is True, volani)
ok("filtry: číslo vězně může být text (A-1234)", k is None, (k, err))

k, out, err, volani = spust("Novak", filtry={"narodnost": "Klingon"})
ok("neznámá národnost: nabídne hodnoty a nehledá", k and "Czech (94)" in str(k) and "GetPersonList" not in [v[0] for v in volani], (k, volani))

k, out, err, volani = spust("Novak", od=1000, celkem="5000", radky=[RADEK] * 1000, maxn=2)
ok("stránkování: --od jde jako rowNum", next(v[1] for v in volani if v[0] == "GetPersonList")["rowNum"] == 1000, volani)
ok("stránkování: nápověda, jak zobrazit víc z načtených", "--max 1000" in err, err)
ok("stránkování: nápověda na další tisícovku", "--od 2000" in err, err)

k, out, err, _ = spust("Novak", radky=[], celkem="0")
ok("nic nenalezeno hlásí srozumitelně", "Nic nenalezeno" in err, err)
k, out, err, _ = spust("Novak", podrobne=True)
ok("--podrobne vypíše otce, úmrtí a bydliště", "otec: Jan" in out and "úmrtí: 31. 12. 1944" in out and "obec: Brno" in out, out)

# --- karta: obrázek jen z důvěryhodného serveru
puvodni = arolsen.post
arolsen.post = lambda m, d: [{"image": "https:\\\\evil.example/G/x.jpg", "title": "x", "relatedLink": "en/document/1"}]
err = io.StringIO()
try:
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
        arolsen.karta("1", os.path.join(tempfile.mkdtemp(), "x.jpg"))
    kod = None
except SystemExit as e:
    kod = e.code
arolsen.post = puvodni
ok("karta: obrázek z cizího serveru se nestáhne", kod and "Neočekávaný server" in str(kod), kod)
try:
    arolsen.karta("abc", "x.jpg")
except SystemExit as e:
    ok("karta: id musí být číslo", "číslo" in str(e.code), e.code)

print(f"\n{sum(vysledky)} z {len(vysledky)} v pořádku")
sys.exit(0 if all(vysledky) else 1)
