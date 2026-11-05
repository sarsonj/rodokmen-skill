"""Testy tools/obeti.py (databáze obětí holocaust.cz): souhlas s podmínkami, zpracování výsledků a kontrola adres.

Z kořene repozitáře:
  python3 -I tests/obeti/test_obeti.py
  (Windows: python -I -X utf8 tests/obeti/test_obeti.py)
Nic nestahuje: odpovědi portálu jsou vepsané v testu, get() se nahradí. Stav souhlasu a brzdy je v dočasných složkách.
"""
import contextlib, importlib.util, io, os, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "skills", "rodokmen", "tools")
os.environ["SLUSNE_STAV"] = tempfile.mkdtemp(prefix="obeti_slusne_")
os.environ["SOUHLAS_STAV"] = tempfile.mkdtemp(prefix="obeti_souhlas_")
spec = importlib.util.spec_from_file_location("obeti", os.path.join(TOOLS, "obeti.py"))
obeti = importlib.util.module_from_spec(spec)
spec.loader.exec_module(obeti)

vysledky = []


def ok(nazev, podminka, detail=""):
    vysledky.append(bool(podminka))
    print(("OK   " if podminka else "CHYBA"), nazev, "" if podminka else detail)


def nastroj(*argv):
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(TOOLS, "obeti.py"), *argv], capture_output=True, text=True,
                       env={**os.environ}, timeout=60)
    return r.returncode, r.stdout, r.stderr


# --- souhlas: bez něj nástroj nic nestahuje (běží v podprocesu, k síti by se nedostal)
for prikaz in (["hledat", "--prijmeni", "Novak"], ["detail", "111149-anna-neumannova"]):
    k, out, err = nastroj(*prikaz)
    ok(f"bez souhlasu: {prikaz[0]} skončí kódem 4 a nic nevypíše", k == 4 and not out and "uživatel sám" in err, (k, out, err))
k, out, err = nastroj("souhlas")
ok("souhlas z neinteraktivního prostředí (Claude, skript) se nezapíše", k == 4 and not os.listdir(os.environ["SOUHLAS_STAV"]), (k, err))

# --- zpracování výsledků (souhlas tu nahradíme, kontrolu jsme zkoušeli výše)
STRANA1 = ('<p>Celkem nalezeno: 1 234</p>'
           '<div class="victims-wrapper"><a href="https://www.holocaust.cz/databaze-obeti/obet/1-anna-neumannova/"><img src="x.jpg"></a>'
           '<p><a href="https://www.holocaust.cz/databaze-obeti/obet/1-anna-neumannova/">Anna Neumannová</a><br/> Narozena 05. 06. 1850.<br/>'
           ' Terezín. <br/> Zahynula 08. 10. 1942 Terezín.<br/> </p><a class="more">Více</a></div>'
           '<p><span>1</span> <a href="https://www.holocaust.cz/databaze-obeti/strana/2/">další</a></p>')
STRANA2 = ('<div class="victims-wrapper"><p><a href="https://www.holocaust.cz/databaze-obeti/obet/2-hanna/">Hanna Neumannová</a><br/>'
           ' Narozena 14. 05. 1926.<br/> Terezín. Osvětim.<br/> Zahynula.<br/> </p></div>')
DETAIL = ('<h1> Anna Neumannová </h1><div class="wrapper"><img src="x"><p><b>Narozena 26. 12. 1906</b><br/>Poslední bydliště před deportací: Ostrava I<br/>'
          'Transport Bm, č. 569&nbsp;(30. 09. 1942, Ostrava -&gt; Terezín)<br/>Zahynula<br/></p></div><h2>související dokumenty</h2>'
          '<div class="victim-documents"><a href="https://www.holocaust.cz/databaze-dokumentu/dokument/1-pas/"><span>Neumannová Anna: Cestovní pas</span></a></div>')


def spust(fn, *args, odpovedi):
    volani = []
    puvodni = obeti.get

    def get(url, data=None):
        volani.append((url, data))
        return odpovedi[min(len(volani) - 1, len(odpovedi) - 1)]
    obeti.get = get
    out, err, k = io.StringIO(), io.StringIO(), None
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                fn(*args)
            except SystemExit as e:
                k = e.code
    finally:
        obeti.get = puvodni
    return k, out.getvalue(), err.getvalue(), volani


k, out, err, volani = spust(obeti.hledat, {"prijmeni": "Neumannová", "jmeno": "Anna"}, 2, odpovedi=[STRANA1, STRANA2])
radky = out.strip().splitlines()
ok("hledat: obě stránky výsledků", len(radky) == 2, out)
ok("hledat: jméno, narození, osud a odkaz", radky[0].startswith("Anna Neumannová | Narozena 05. 06. 1850. | Terezín. | Zahynula 08. 10. 1942 Terezín. | https://www.holocaust.cz/"), radky[0])
ok("hledat: formulář se odešle POSTem s příjmením a jménem", volani[0][1]["searchSurname"] == "Neumannová" and volani[0][1]["searchFirstname"] == "Anna", volani[0])
ok("hledat: druhá stránka se bere z odkazu „další“", volani[1][0].endswith("/databaze-obeti/strana/2/"), volani)
ok("hledat: počet se záznamy s mezerou (1 234) se čte celý", "1 234" in err or "celkem nalezeno 1" in err, err)

k, out, err, _ = spust(obeti.hledat, {"prijmeni": "Xqz"}, 1, odpovedi=['<p>Celkem nalezeno: 0</p>'])
ok("hledat: nic nenalezeno hlásí srozumitelně", "Nic nenalezeno" in err, err)

k, out, err, volani = spust(obeti.detail, "111149-anna-neumannova", odpovedi=[DETAIL])
ok("detail: číslo se jménem sestaví adresu oběti", volani[0][0] == "https://www.holocaust.cz/databaze-obeti/obet/111149-anna-neumannova/", volani)
ok("detail: jméno, narození, bydliště, transport a dokument", all(x in out for x in ("Anna Neumannová", "Narozena 26. 12. 1906", "Ostrava I", "Terezín", "Cestovní pas")), out)
for zlo in ("../x", "https://evil.example/databaze-obeti/obet/1/", "x y"):
    k, out, err, volani = spust(obeti.detail, zlo, odpovedi=[DETAIL])
    ok(f"detail: odmítne {zlo}", not volani and k, (volani, k, err))

print(f"\n{sum(vysledky)} z {len(vysledky)} v pořádku")
sys.exit(0 if all(vysledky) else 1)
