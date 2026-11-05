"""Testy tools/mauthausen.py (Raum der Namen – zemřelí v Mauthausenu): zpracování výsledků, stránkování, duplicity.

Z kořene repozitáře:
  python3 -I tests/mauthausen/test_mauthausen.py
  (Windows: python -I -X utf8 tests/mauthausen/test_mauthausen.py)
Nic nestahuje: odpovědi portálu jsou vepsané v testu, get() se nahradí.
"""
import contextlib, importlib.util, io, os, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "skills", "rodokmen", "tools")
os.environ["SLUSNE_STAV"] = tempfile.mkdtemp(prefix="mauthausen_slusne_")
spec = importlib.util.spec_from_file_location("mauthausen", os.path.join(TOOLS, "mauthausen.py"))
mauthausen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mauthausen)
mauthausen.time.sleep = lambda s: None   # pauzy mezi stránkami v testu nepotřebujeme

vysledky = []


def ok(nazev, podminka, detail=""):
    vysledky.append(bool(podminka))
    print(("OK   " if podminka else "CHYBA"), nazev, "" if podminka else detail)


def osoba(href, jmeno, roky=None, sub=None):
    return (f'<div class="entry"><div class="column-main"><h1><a href="{href}">{jmeno}'
            + (f' <span class="years">{roky}</span>' if roky else '') + '</a></h1>'
            + (f'<p class="subtext"> {sub} </p>' if sub else '') + '<p><a href="x">weiterlesen</a></p></div></div>')


STRANA1 = ('<a class="searchResult-menu-item" href="#aPersons">723 Personen</a>'
           + osoba("https://raumdernamen.mauthausen-memorial.org/?id=4&amp;p=157130", "Novak Oparušić", "1909 - 1944",
                   "Geboren 7.7.1909 in Donji Petrovci<br> Gestorben 25.7.1944 in Linz")
           + osoba("https://raumdernamen.mauthausen-memorial.org/?id=4&amp;p=162178", "Novak Ranđelović"))
STRANA2 = ('<a class="searchResult-menu-item" href="#aPersons">723 Personen</a>'
           + osoba("https://raumdernamen.mauthausen-memorial.org/?id=4&amp;p=157130", "Novak Oparušić", "1909 - 1944", "Geboren 7.7.1909")   # duplicita
           + osoba("https://raumdernamen.mauthausen-memorial.org/?id=4&amp;p=20438", "Ivan Novak", "1903 - 1945",
                   "Geboren 11.3.1903 in Rakek<br> Gestorben 30.1.1945 in St. Valentin"))


def spust(argv_stran, odpovedi):
    adresy = []
    puvodni = mauthausen.get

    def get(url):
        adresy.append(url)
        return odpovedi[min(len(adresy) - 1, len(odpovedi) - 1)]
    mauthausen.get = get
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            mauthausen.hledat(*argv_stran)
    finally:
        mauthausen.get = puvodni
    return out.getvalue(), err.getvalue(), adresy


out, err, adresy = spust(("Novak", 2), [STRANA1, STRANA2, ""])
radky = out.strip().splitlines()
ok("tři různé osoby (duplicita ze 2. strany se vynechá)", len(radky) == 3, out)
ok("jméno, roky, narození, úmrtí a odkaz", radky[0] == "Novak Oparušić | 1909 - 1944 | nar. 7.7.1909 in Donji Petrovci | zem. 25.7.1944 in Linz | "
   "https://raumdernamen.mauthausen-memorial.org/?id=4&p=157130", radky[0])
ok("osoba bez údajů o narození a úmrtí se vypíše s pomlčkami", radky[1] == "Novak Ranđelović | - | nar. - | zem. - | https://raumdernamen.mauthausen-memorial.org/?id=4&p=162178", radky[1])
ok("upozornění, že je osob víc (723)", "celkem 723" in err, err)
ok("strany portálu se číslují od 1", "page=1&" in adresy[0] and "page=2&" in adresy[1], adresy)
ok("dotaz je v adrese zakódovaný", "txtFullSearch=Novak" in adresy[0], adresy)

out, err, adresy = spust(("Xqz Ž", 2), ["<html>nic</html>"])
ok("nic nenalezeno hlásí srozumitelně a zbytečně nestránkuje", "Nic nenalezeno" in err and len(adresy) == 1, (err, adresy))
ok("diakritika v dotazu se zakóduje", "%C5%BD" in adresy[0], adresy)

BEZ_POCTU = STRANA2.replace('<a class="searchResult-menu-item" href="#aPersons">723 Personen</a>', '')
out, err, adresy = spust(("Novak", 2), [STRANA1, BEZ_POCTU, ""])
ok("počet nalezených osob se bere z první stránky, která ho má", "celkem 723 osob" in err, err)

print(f"\n{sum(vysledky)} z {len(vysledky)} v pořádku")
sys.exit(0 if all(vysledky) else 1)
