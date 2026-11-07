"""Testy tools/brno_encyklopedie.py (zpracování výsledků hledání a kontrola adres u detailu).

Z kořene repozitáře:
  python3 -I tests/brno/test_brno_encyklopedie.py
  (Windows: python -I -X utf8 tests/brno/test_brno_encyklopedie.py)
Nic nestahuje: odpovědi portálu jsou vepsané v testu, get() se nahradí.
"""
import contextlib, importlib.util, io, json, os, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "skills", "rodokmen", "tools")
os.environ.setdefault("SLUSNE_STAV", tempfile.mkdtemp(prefix="brno_slusne_"))   # brzda při importu nesahá na skutečný stav
spec = importlib.util.spec_from_file_location("brno_encyklopedie", os.path.join(TOOLS, "brno_encyklopedie.py"))
brno = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brno)

vysledky = []


def ok(nazev, podminka, detail=""):
    vysledky.append(bool(podminka))
    print(("OK   " if podminka else "CHYBA"), nazev, "" if podminka else detail)


HLEDANI = json.dumps({"html": {"search-results": (
    '<p>Pro výraz <strong>&quot;Novak&quot;</strong> nalezeno 667 odkazů.</p>'
    '<div class="col-md-10"><a href="?acc=profil-osobnosti&load=15#generator" title="&raquo; přejít na: Břetislav Bakala">Břetislav Bakala</a>\n'
    '<p>všestranný hudebník, dirigent</p></div>'
    '<div class="col-md-10"><a href="?acc=profil-ulice&load=7#generator" title="x">Králova</a>\n'
    '<p>[[Solniční]] ((Heslo|text s odkazem)) ulice</p></div>')}})
DETAIL = ('<html><head><title>Břetislav Bakala - Profil osobnosti</title></head><body>Menu Vyhledat '
          'Břetislav Bakala * 12.2.1897 Fryšták – † 1.4.1958 Brno bydliště Brno: - Husova 8a '
          'čestný hrob Ústřední hřbitov města Brna, skup. 25e, hrob č. 58 poznámky ' + 'Dlouhý text hesla. ' * 15 + 'Facebook zbytek stránky</body></html>')


def spust(argv, odpoved):
    adresy = []
    puvodni = brno.get, sys.argv
    brno.get = lambda url: (adresy.append(url), odpoved)[1]
    sys.argv = ["brno_encyklopedie.py"] + argv
    out, err = io.StringIO(), io.StringIO()
    kod = 0
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                if argv[0] == "hledat":
                    brno.hledat(argv[1])
                else:
                    brno.detail(argv[1])
            except SystemExit as e:
                kod = e.code or 1
    finally:
        brno.get, sys.argv = puvodni
    return out.getvalue(), err.getvalue() + (str(kod) if isinstance(kod, str) else ""), adresy


out, err, adresy = spust(["hledat", "Novak"], HLEDANI)
radky = out.strip().splitlines()
ok("hledat: dva zásahy", len(radky) == 2, out)
ok("hledat: typ a název osobnosti", radky[0].startswith("osobnost | Břetislav Bakala | všestranný hudebník, dirigent | "), radky[0])
ok("hledat: odkaz na heslo", radky[0].endswith("?acc=profil-osobnosti&load=15"), radky[0])
ok("hledat: značky ((…|…)) a [[…]] se z úryvku odstraní", "Solniční Heslo ulice" in radky[1] and "[[" not in radky[1] and "((" not in radky[1], radky[1])
ok("hledat: upozornění, že je zásahů víc", "celkem 667" in err, err)
ok("hledat: dotaz jde v adrese zakódovaný", "q=Novak" in adresy[0] and "json=search-v2" in adresy[0], adresy)

out, err, _ = spust(["hledat", "Xqz"], json.dumps({"html": {"search-results": "<p>nic</p>"}}))
ok("hledat: nic nenalezeno hlásí srozumitelně", "Nic nenalezeno" in err and not out, err)
out, err, _ = spust(["hledat", "x"], "tohle není JSON")
ok("hledat: neočekávaná odpověď portálu končí hláškou, ne tracebackem", "neočekávanou odpověď" in err or "neočekávanou" in err, err)

out, err, adresy = spust(["detail", "osobnosti:15"], DETAIL)
ok("detail: typ:id sestaví adresu hesla", adresy and adresy[0].endswith("?acc=profil-osobnosti&load=15"), adresy)
ok("detail: text hesla je za formulářem hledání", "Bakala * 12.2.1897" in out and "Menu" not in out, out)
ok("detail: text končí před patičkou", "zbytek stránky" not in out, out)
ok("detail: hrob s číslem je vidět", "hrob č. 58" in out, out)
for zla in ("https://evil.example/?acc=profil-osobnosti&load=1", "https://encyklopedie.brna.cz/?acc=../x&load=1",
            "https://encyklopedie.brna.cz/?acc=profil-osobnosti&load=abc", "neco:15"):
    out, err, adresy = spust(["detail", zla], DETAIL)
    ok(f"detail: odmítne {zla[:48]}", not adresy and "Zadej odkaz" in err, (adresy, err))

ZNACKY = json.dumps({"html": {"search-results": '<p>nalezeno 1 odkazů.</p><a href="?acc=profil-osobnosti&load=9#generator" title="x">Jan <em>Novák</em></a>\n<p>klempíř</p>'}})
out, err, _ = spust(["hledat", "Novák"], ZNACKY)
ok("hledat: zásah se značkou ve jméně se nevynechá", "osobnost | Jan Novák | klempíř" in out, (out, err))

print(f"\n{sum(vysledky)} z {len(vysledky)} v pořádku")
sys.exit(0 if all(vysledky) else 1)
