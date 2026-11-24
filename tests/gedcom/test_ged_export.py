"""Testy tools/ged_export.py (export rodokmenu do GEDCOM 5.5.1).

Z kořene repozitáře:
  python3 -I tests/gedcom/test_ged_export.py
  (Windows: python -I -X utf8 tests/gedcom/test_ged_export.py)
Založí dočasné projekty přes novy_projekt.py (ukázka a malý umělý strom), spustí v nich export a výsledek načte
zpět přes ged_import.read(). Nic nestahuje.
"""
import importlib.util, json, os, re, shutil, subprocess, sys, tempfile, zipfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "skills", "rodokmen", "tools")


def module(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(TOOLS, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


gi = module("ged_import")
ge = module("ged_export")
vysledky = []


def ok(nazev, podminka, detail=""):
    vysledky.append(bool(podminka))
    print(("OK   " if podminka else "CHYBA"), nazev, "" if podminka else detail)


def projekt(ukazka):
    d = os.path.join(tempfile.mkdtemp(prefix="gedcom_"), "projekt")
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(TOOLS, "novy_projekt.py"), d]
                       + (["--ukazka"] if ukazka else []), capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return d


def spust(d, *args):
    return subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(d, "tools", "ged_export.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", cwd=d)


def export(d, *args):
    r = spust(d, *args)
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout


def test_vystup():
    """Kam se export zapíše: výchozí název podle kořene, nepřepisuje, ne do web/, přípona, upozornění na cloud."""
    d = projekt(True)
    prac = os.path.join(d, "pracovni")
    export(d)
    zip1 = os.path.join(prac, "rodokmen.zip")
    cas = os.path.getmtime(zip1)
    r = spust(d)
    ok("existující soubor se bez --prepsat nepřepíše", r.returncode != 0 and "--prepsat" in r.stderr
       and os.path.getmtime(zip1) == cas, r.stderr)
    ok("--prepsat přepíše", spust(d, "--prepsat").returncode == 0)
    export(d, "--koren", "3")
    ok("--koren: výchozí název s číslem kořene", os.path.isfile(os.path.join(prac, "rodokmen_koren3.zip")))
    r = spust(d, "--vystup", os.path.join(d, "web", "public", "strom.zip"))
    ok("výstup do web/ odmítnut", r.returncode != 0 and "web/" in r.stderr
       and not os.path.exists(os.path.join(d, "web", "public", "strom.zip")), r.stderr)
    r = spust(d, "--vystup", os.path.join(prac, "x.ged"))
    ok("ZIP do .ged odmítnut", r.returncode != 0 and ".zip" in r.stderr, r.stderr)
    r = spust(d, "--bez-obrazku", "--vystup", os.path.join(prac, "x.zip"))
    ok(".ged do .zip odmítnut", r.returncode != 0 and ".ged" in r.stderr, r.stderr)
    # --slozka: rozbalený export (rodokmen.ged + media/) pro Family Tree Builder a Gramps
    out = export(d, "--slozka")
    sl = os.path.join(prac, "rodokmen")
    surovy = open(os.path.join(sl, "rodokmen.ged"), "rb").read()
    # FTB bez BOM špatně přečte cestu s diakritikou – ve složce UTF-8 s BOM a CRLF (jako export MyHeritage)
    ok("--slozka: UTF-8 s BOM a konci řádků CRLF",
       surovy.startswith(b"\xef\xbb\xbf0 HEAD\r\n") and b"\n" not in surovy.replace(b"\r\n", b""))
    ged = surovy.decode("utf-8-sig").replace("\r\n", "\n")
    soubory = re.findall(r"^\d+ FILE (.+)$", ged, re.M)
    ok("--slozka: rodokmen.ged a media/ vedle sebe", soubory and all(os.path.isfile(os.path.join(sl, f)) for f in soubory))
    # Family Tree Builder relativní cesty nenačte („Failed to Load Image“) – ve složce absolutní cesty do media/
    ok("--slozka: FILE je absolutní cesta do media/ této složky",
       all(os.path.isabs(f) and os.path.normcase(f).startswith(os.path.normcase(os.path.join(sl, "media") + os.sep))
           for f in soubory), soubory[:3])
    # FTB obrázky z citací zahodí – ve složce jsou výřezy zápisů i přímo u osoby (1 OBJE), každý u osoby jednou
    klice = {z["klic"] for z in json.load(open(os.path.join(d, "data", "zaznamy.json"), encoding="utf-8"))}

    def vyrezy_u_osob(text):
        u_osob = {}
        for blok in re.split(r"(?m)^(?=0 )", text):
            m = re.match(r"0 (@I\d+@) INDI", blok)
            if m:
                fs = [os.path.splitext(os.path.basename(f.replace("\\", "/")))[0]
                      for f in re.findall(r"(?m)^1 OBJE\n2 FILE (.+)$", blok)]
                u_osob[m[1]] = [f for f in fs if f in klice]
        return u_osob
    slozka_vyrezy = vyrezy_u_osob(ged)
    ok("--slozka: výřezy zápisů i přímo u osob", sum(map(len, slozka_vyrezy.values())) > 0)
    ok("--slozka: výřez u osoby nejvýš jednou", all(len(v) == len(set(v)) for v in slozka_vyrezy.values()),
       {k: v for k, v in slozka_vyrezy.items() if len(v) != len(set(v))})
    zip_ged = zipfile.ZipFile(os.path.join(prac, "rodokmen.zip")).read("rodokmen.ged").decode("utf-8")
    ok("ZIP: výřezy zápisů jen v citacích, ne u osob", sum(map(len, vyrezy_u_osob(zip_ged).values())) == 0)

    # FTB dá obrázek ke zdroji (ne k citaci) – ve složce je zdroj = jeden zápis s jeho výřezem
    def zdroje(text):
        return [b for b in re.split(r"(?m)^(?=0 )", text) if re.match(r"0 @S\d+@ SOUR", b)]
    zs = zdroje(ged)
    obr = [re.findall(r"(?m)^1 OBJE\n2 FILE (.+)$", b) for b in zs]
    ok("--slozka: zdroj = zápis, nejvýš jeden výřez", zs and all(len(o) <= 1 for o in obr) and any(obr))
    ok("--slozka: zdroj-zápis má archiv svazku (REPO)", any("\n1 REPO @R" in b for b in zs))
    ok("--slozka: výřez zdroje je výřez téhož zápisu",
       all(os.path.splitext(os.path.basename(o[0].replace("\\", "/")))[0] in klice for o in obr if o))
    ok("ZIP: zdroj = svazek, bez obrázků", all("\n1 OBJE" not in b for b in zdroje(zip_ged))
       and len(zdroje(zip_ged)) < len(zs))

    # Ve složce obrázek v plném rozlišení ze zdroje/ (jako detail na webu), jinak z vyrezy/; ZIP bere vyrezy/
    vyrez = next(k for k in sorted(klice) if os.path.isfile(os.path.join(d, "vyrezy", k + ".jpg")))
    plne = b"\xff\xd8PLNE-ROZLISENI\xff\xd9"
    os.makedirs(os.path.join(d, "zdroje"), exist_ok=True)
    open(os.path.join(d, "zdroje", vyrez + ".jpg"), "wb").write(plne)
    plna = os.path.join(prac, "plne")
    export(d, "--slozka", "--plne-rozliseni", "--vystup", plna)
    ok("--slozka: obrázek v plném rozlišení ze zdroje/",
       open(os.path.join(plna, "media", vyrez + ".jpg"), "rb").read() == plne)
    ok("--slozka --plne-rozliseni: bez druhé kopie (media/plne/)", not os.path.exists(os.path.join(plna, "media", "plne")))
    def puvod(f):
        z = os.path.join(d, "zdroje", f)
        return open(z if os.path.isfile(z) else os.path.join(d, "vyrezy", f), "rb").read()
    ok("--slozka: každý obrázek ze zdroje/, není-li, z vyrezy/", all(
        open(os.path.join(plna, "media", f), "rb").read() == puvod(f)
        for f in os.listdir(os.path.join(plna, "media")) if f.endswith(".jpg")))
    os.remove(os.path.join(d, "zdroje", vyrez + ".jpg"))
    ok("--slozka: návod na import složky", "Family Tree Builderu importujte" in out, out)
    r = spust(d, "--slozka")
    ok("--slozka: existující export bez --prepsat odmítnut", r.returncode != 0 and "--prepsat" in r.stderr, r.stderr)
    stary = os.path.join(sl, "media", "stary.jpg")
    open(stary, "wb").write(b"x")
    ok("--slozka --prepsat: nahradí media/ (staré obrázky pryč)",
       spust(d, "--slozka", "--prepsat").returncode == 0 and not os.path.exists(stary))
    open(os.path.join(sl, "moje_poznamky.txt"), "w").write("x")
    r = spust(d, "--slozka", "--prepsat")
    ok("--slozka: složku s cizími soubory nepřepíše ani s --prepsat",
       r.returncode != 0 and os.path.exists(os.path.join(sl, "moje_poznamky.txt")), r.stderr)
    export(d, "--slozka", "--koren", "3")
    ok("--slozka --koren 3: pracovni/rodokmen_koren3/", os.path.isfile(os.path.join(prac, "rodokmen_koren3", "rodokmen.ged")))
    ok("--slozka s --bez-obrazku odmítnuto", spust(d, "--slozka", "--bez-obrazku").returncode != 0)
    ok("--slozka s výstupem .zip odmítnuto", spust(d, "--slozka", "--vystup", os.path.join(prac, "a.zip")).returncode != 0)
    r = spust(d, "--slozka", "--vystup", os.path.join(d, "web"))
    ok("--slozka: samotná složka web/ odmítnuta", r.returncode != 0 and "web/" in r.stderr, r.stderr)

    out = export(d, "--zijici", "--vystup", os.path.join(prac, "OneDrive", "vse.zip"))
    ok("--zijici v cloudové složce: upozornění", "synchronizované do cloudu (OneDrive)" in out, out)
    out = export(d, "--zijici", "--vystup", os.path.join(prac, "vse.zip"))
    ok("--zijici jinde: obecné upozornění na cloud", "synchronizuje-li ji cloud" in out, out)
    shutil.rmtree(os.path.dirname(d), ignore_errors=True)


def nacti_zip(path):
    z = zipfile.ZipFile(path)
    ged = z.read("rodokmen.ged").decode("utf-8")
    tmp = os.path.join(tempfile.mkdtemp(prefix="gedcom_cteni_"), "r.ged")
    open(tmp, "w", encoding="utf-8", newline="\n").write(ged)
    return ged, gi.read(tmp), set(z.namelist())


def tags(node):
    return [n["tag"] for n in node["_sub"]]


def sub(node, tag):
    return [n for n in node["_sub"] if n["tag"] == tag]


def first(node, tag):
    s = sub(node, tag)
    return s[0] if s else None


def cites(node):
    return [n["val"].strip() for n in sub(node, "SOUR")]


def page(recs, node):
    return [gi.first(c, "PAGE") for c in sub(node, "SOUR")]


def fam_of(recs, h, w):
    for r in recs.values():
        if r["_type"] == "FAM" and gi.first(r, "HUSB") == h and gi.first(r, "WIFE") == w:
            return r
    return None


def spolecne(ged, recs, files):
    """Kontroly pro každý výstup: délka řádků, obrázky v ZIP, chránění bez údajů."""
    ok("řádky nejvýš 255 znaků", all(len(line) <= 255 for line in ged.splitlines()))
    soubory = re.findall(r"^\d+ FILE (.+)$", ged, re.M)
    ok("každý FILE je v ZIP", all(f in files for f in soubory), [f for f in soubory if f not in files])
    chranene = [r for r in recs.values() if r["_type"] == "INDI" and gi.first(r, "NAME") == "Žijící osoba"]
    ok("chránění mají jen NAME/SEX/RESN/FAMC/FAMS",
       all(set(tags(r)) <= {"NAME", "SEX", "RESN", "FAMC", "FAMS"} for r in chranene),
       [(r["_id"], tags(r)) for r in chranene])
    return chranene


def test_ukazka():
    d = projekt(True)
    out = export(d)
    ged, recs, files = nacti_zip(os.path.join(d, "pracovni", "rodokmen.zip"))
    chranene = spolecne(ged, recs, files)

    ns = {}
    exec(open(os.path.join(d, "data", "osoby.py"), encoding="utf-8").read(), ns)
    P, SAME = ns["P"], ns.get("SAME", {})
    cekane = [k for k in P if k not in SAME and not ge.placeholder(P[k])]
    indi = [r for r in recs.values() if r["_type"] == "INDI"]
    ok("round-trip: počet osob", len(indi) == len(cekane), (len(indi), len(cekane)))
    ok("výchozí osoba a rodiče žijící", {"@I1@", "@I2@", "@I3@"} <= {r["_id"] for r in chranene})
    ok("zemřelý 1990 není chráněný (36 let)", gi.first(recs["@I4@"], "NAME") != "Žijící osoba")

    jan = recs["@I8@"]
    birt = first(jan, "BIRT")
    ok("datum 14. 2. 1890 → 14 FEB 1890", gi.first(birt, "DATE") == "14 FEB 1890")
    ok("místo z mista.json s hierarchií", gi.first(birt, "PLAC").startswith("Holice, okres Pardubice"))
    ok("souřadnice z mista.json", first(first(birt, "PLAC"), "MAP") is not None)
    ok("čp. v ADDR", gi.first(birt, "ADDR") == "čp. 112")
    ok("vlastní křest citován u narození", any("Křest Jana" in p for p in page(recs, birt)))
    ok("citace má obrázek výřezu", first(sub(birt, "SOUR")[0], "OBJE") is not None)

    vaclav = recs["@I16@"]
    ok("křest syna NENÍ citován u narození otce", not sub(first(vaclav, "BIRT"), "SOUR"))
    ok("křest syna citován u osoby otce s poznámkou",
       any("Křest Jana" in p for p in page(recs, vaclav))
       and any("jiné události" in gi.first(c, "NOTE") for c in sub(vaclav, "SOUR")))

    f = fam_of(recs, "@I16@", "@I17@")
    marr = first(f, "MARR") if f else None
    ok("rodina Václav + Barbora s dítětem Jan", f is not None and "@I8@" in [n["val"] for n in sub(f, "CHIL")])
    ok("sňatek citován pod MARR v rodině", marr is not None and any("Sňatek" in p for p in page(recs, marr)))
    ok("sňatek dcery NENÍ u MARR rodičů (Pokorný 18 + 19)",
       not any("Jana Nováka a Josefy" in p for p in page(recs, first(fam_of(recs, "@I18@", "@I19@"), "MARR"))))
    ok("příčina úmrtí před 100 lety v CAUS", gi.first(first(recs["@I64@"], "DEAT"), "CAUS") == "na choleru")
    ok("zástupný otec 58 se nevyváží", "@I58@" not in recs)
    f29 = next(r for r in recs.values() if r["_type"] == "FAM" and "@I29@" in [n["val"] for n in sub(r, "CHIL")])
    ok("rodina se zástupným otcem má jen matku", not sub(f29, "HUSB") and gi.first(f29, "WIFE") == "@I59@")
    ok("svazek jako SOUR s REPO", any(r["_type"] == "SOUR" and sub(r, "REPO") for r in recs.values()))
    ok("souhrn hlásí chybějící obrázky jednou větou", out.count("Chybí ") == 1, out)

    gp = os.path.join(d, "pracovni", "rodokmen.ged")
    export(d, "--bez-obrazku")
    text = open(gp, encoding="utf-8").read()
    ok("--bez-obrazku: .ged bez OBJE", os.path.isfile(gp) and " OBJE" not in text)

    export(d, "--zijici", "--vystup", os.path.join(d, "pracovni", "vse.zip"))
    _, recs2, _ = nacti_zip(os.path.join(d, "pracovni", "vse.zip"))
    ok("--zijici: výchozí osoba se jménem", gi.first(recs2["@I1@"], "NAME") == "Petr /Novák/")

    export(d, "--cp-v-miste", "--vystup", os.path.join(d, "pracovni", "cp.zip"))
    _, recs_cp, _ = nacti_zip(os.path.join(d, "pracovni", "cp.zip"))
    birt_cp = first(recs_cp["@I8@"], "BIRT")
    ok("--cp-v-miste: čp. v místě za obcí", gi.first(birt_cp, "PLAC").startswith("Holice čp. 112, okres Pardubice"),
       gi.first(birt_cp, "PLAC"))
    ok("--cp-v-miste: ADDR zůstane", gi.first(birt_cp, "ADDR") == "čp. 112")
    ok("--cp-v-miste: událost bez čp. beze změny", gi.first(first(recs_cp["@I8@"], "DEAT"), "PLAC").startswith("Holice, okres"))
    ok("bez --cp-v-miste: místo bez čp.", "čp." not in gi.first(birt, "PLAC"))

    out = export(d, "--koren", "3", "--vystup", os.path.join(d, "pracovni", "matka.zip"))
    ged3, recs3, files3 = nacti_zip(os.path.join(d, "pracovni", "matka.zip"))
    spolecne(ged3, recs3, files3)
    pod3 = {k for k in cekane if (lambda dd: dd >= 0 and k >> dd == 3)(k.bit_length() - 2)}
    ids3 = {r["_id"] for r in recs3.values() if r["_type"] == "INDI"}
    ok("--koren 3: jen matka a její předci", ids3 == {f"@I{k}@" for k in pod3}, sorted(ids3 ^ {f"@I{k}@" for k in pod3}))
    ok("--koren 3: bez otcovy strany a výchozí osoby", not ({"@I1@", "@I2@", "@I8@"} & ids3))
    ok("--koren 3: matka bez rodiny s dětmi", not sub(recs3["@I3@"], "FAMS") and sub(recs3["@I3@"], "FAMC"))
    ok("--koren 3: obrázky jen z větve (Novákovi ne)", files3 == {"rodokmen.ged"}, files3)
    ok("--koren 3: souhrn jmenuje kořen", "jen osoba č. 3" in out, out)
    shutil.rmtree(os.path.dirname(d), ignore_errors=True)


UMELE_OSOBY = '''
P = {
 1: dict(n="Anna Malá", y="* 1990", st="fam", f=["* 1990 Holice"], note="Žijící – údaje jen základní.", sex="F"),
 2: dict(n="Jan Malý", y="1890–1950", st="doc", f=["* asi 1890 Holice čp. 5", "× 1919 Holice Marie Nová",
         "† 1950 Holice, na tuberkulózu"], r=["holice_krest_jan_maly_1890"], note="Poznámka z nedávné doby"),
 3: dict(n="Marie Nová", y="1895–1980", st="fam", f=["* 1895 Lhota u Nikde", "provd. Malá", "× 1919 Holice Jan Malý",
         "† 1980 Holice"]),
 4: dict(n="otec neuveden", y="", st="unk", f=[]),
 5: dict(n="Kateřina Malá", y="1860–1920", st="prob", f=["* před 1860 Holice", "† 3/1920 Holice"],
         r=["holice_krest_jan_maly_1890"], note="Stará poznámka"),
 6: dict(n="Josef Nový", y="1850–1900", st="doc", f=["* mezi 1850 a 1852 Holice", "× 1880 Holice Anna Stará",
         "† 31. 13. 1900 Holice"], r=["holice_snatek_josef_novy_anna_stara_1880"]),
 7: dict(n="Anna Stará", y="1855–1900", st="doc", f=["* ≈1855 Holice", "× 1880 Holice Josef Nový", "† 1900 Holice"],
         r=["holice_snatek_josef_novy_anna_stara_1880"]),
 10: dict(n="Josef Nový", y="1850–1900", st="doc", f=["TÁŽ OSOBA jako 6"]),
 11: dict(n="Anna Stará", y="1855–1900", st="doc", f=["TÁŽ OSOBA jako 7"]),
}
SIDE = [dict(k=2, n="Petr Malý (1925–2001)", t="bratr"), dict(k=6, n="Karel Nový (1855–1900)", t="bratr Josefa")]
SAME = {10: 6, 11: 7}
'''


def test_umely():
    d = projekt(False)
    data = os.path.join(d, "data")
    open(os.path.join(data, "osoby.py"), "w", encoding="utf-8").write(UMELE_OSOBY)
    zaznamy = [dict(klic="holice_krest_jan_maly_1890", svazek="s1", snimek=12, druh="N", datum="2. 5. 1890",
                    nazev="Křest Jana Malého", shrnuti="Jan, syn Kateřiny Malé.", odkaz="https://example.org/1"),
               dict(klic="holice_snatek_josef_novy_anna_stara_1880", svazek="s2", snimek=7, druh="O", datum="1880",
                    nazev="Sňatek Josefa Nového a Anny Staré", shrnuti="Ženich Josef Nový, nevěsta Anna Stará.")]
    svazky = {"s1": dict(archiv="SOA Zámrsk", portal="ARON", svazek="N Holice 1880–1900, sign. 1234", url="https://example.org"),
              "s2": dict(archiv="SOA Zámrsk", portal="ARON", svazek="O Holice 1870–1890")}
    mista = {"Holice": dict(re="Holic", dotaz="Holice, Česko", lat=50.0663, lon=15.9859)}
    docs = [dict(img="katerina_mala_portret", popis="Kateřina Malá", osoby=[5]),
            dict(img="svatba_1919", popis="Svatba Jana a Marie", osoby=[2, 3]),
            dict(img="rodina_1995", popis="Babička s vnučkou", osoby=[3, 1])]
    for name, obj in (("zaznamy.json", zaznamy), ("svazky.json", svazky), ("mista.json", mista), ("dokumenty.json", docs)):
        json.dump(obj, open(os.path.join(data, name), "w", encoding="utf-8"), ensure_ascii=False)
    for key in ("holice_krest_jan_maly_1890", "katerina_mala_portret", "svatba_1919", "rodina_1995"):
        open(os.path.join(d, "vyrezy", key + ".jpg"), "wb").write(b"\xff\xd8\xff\xd9")
    open(os.path.join(d, "zdroje", "holice_krest_jan_maly_1890.jpg"), "wb").write(b"\xff\xd8\xff\xd9")

    out = export(d, "--plne-rozliseni")
    ged, recs, files = nacti_zip(os.path.join(d, "pracovni", "rodokmen.zip"))
    spolecne(ged, recs, files)

    ok("alias SAME se nevyváží", "@I10@" not in recs and "@I11@" not in recs)
    f67 = fam_of(recs, "@I6@", "@I7@")
    ok("pár přes SAME = jedna rodina se dvěma dětmi",
       f67 is not None and sorted(n["val"] for n in sub(f67, "CHIL")) == ["@I3@", "@I5@"])
    ok("sňatek 1880 citován v rodině", f67 is not None and any("Sňatek Josefa" in p for p in page(recs, first(f67, "MARR"))))
    f2 = next(r for r in recs.values() if r["_type"] == "FAM" and gi.first(r, "CHIL") == "@I2@")
    ok("rodina se zástupným otcem", not sub(f2, "HUSB") and gi.first(f2, "WIFE") == "@I5@")

    jan = recs["@I2@"]
    ok("asi 1890 → ABT 1890", gi.first(first(jan, "BIRT"), "DATE") == "ABT 1890")
    ok("křest citován u narození (rok sedí)", any("Křest Jana" in p for p in page(recs, first(jan, "BIRT"))))
    ok("citace s plným rozlišením (2 OBJE)", len(sub(sub(first(jan, "BIRT"), "SOUR")[0], "OBJE")) == 2)
    ok("úmrtí 1950: příčina vynechána", gi.first(first(jan, "DEAT"), "CAUS") == "")
    ok("úmrtí 1950: poznámka vynechána", not any("nedávné" in n["val"] for n in sub(jan, "NOTE")))
    ok("boční příbuzný z poslední doby vynechán", not any("Petr Malý" in n["val"] for n in sub(jan, "NOTE")))
    ok("boční příbuzný starší exportován", any("Karel Nový" in n["val"] for n in sub(recs["@I6@"], "NOTE")))
    ok("svatební fotka u obou manželů", "OBJE" in tags(jan) and "OBJE" in tags(recs["@I3@"]))
    ok("fotka s žijící osobou vynechána", "media/rodina_1995.jpg" not in files)

    marie = recs["@I3@"]
    ok("provd. → druhé NAME married", any(gi.first(n, "TYPE") == "married" and "/Malá/" in n["val"] for n in sub(marie, "NAME")))
    ok("neznámá obec zůstane jako text", gi.first(first(marie, "BIRT"), "PLAC") == "Lhota u Nikde")
    ok("Původ údajů u fam", any("od rodiny" in n["val"] for n in sub(marie, "NOTE")))

    kat = recs["@I5@"]
    ok("před 1860 → BEF 1860", gi.first(first(kat, "BIRT"), "DATE") == "BEF 1860")
    ok("3/1920 → MAR 1920", gi.first(first(kat, "DEAT"), "DATE") == "MAR 1920")
    ok("křest syna u matky jen u osoby", not sub(first(kat, "BIRT"), "SOUR") and any("Křest Jana" in p for p in page(recs, kat)))
    ok("portrét s _PRIM Y", any(gi.first(o, "_PRIM") == "Y" for o in sub(kat, "OBJE")))
    ok("stará poznámka exportována", any("Stará poznámka" in n["val"] for n in sub(kat, "NOTE")))

    josef = recs["@I6@"]
    ok("mezi 1850 a 1852 → BET … AND …", gi.first(first(josef, "BIRT"), "DATE") == "BET 1850 AND 1852")
    ok("≈1855 → ABT 1855", gi.first(first(recs["@I7@"], "BIRT"), "DATE") == "ABT 1855")
    ok("nepřevedené datum jako fráze", gi.first(first(josef, "DEAT"), "DATE") == "(31. 13. 1900)")
    ok("nepřevedené datum v souhrnu", "31. 13. 1900" in out, out)
    ok("chráněná výchozí osoba", gi.first(recs["@I1@"], "NAME") == "Žijící osoba")
    sv = [r for r in recs.values() if r["_type"] == "SOUR"]
    ok("signatura v CALN", any(gi.first(first(r, "REPO"), "CALN") == "1234" for r in sv if first(r, "REPO")))

    # --koren 5: rodiče Kateřiny (10, 11) jsou aliasy osob 6 a 7 z jiné větve – vezmou se i ty
    export(d, "--koren", "5", "--vystup", os.path.join(d, "pracovni", "k5.zip"))
    _, recs5, files5 = nacti_zip(os.path.join(d, "pracovni", "k5.zip"))
    ids5 = {r["_id"] for r in recs5.values() if r["_type"] == "INDI"}
    ok("--koren 5: osoba a předci přes SAME", ids5 == {"@I5@", "@I6@", "@I7@"}, ids5)
    f5 = fam_of(recs5, "@I6@", "@I7@")
    ok("--koren 5: rodina rodičů jen s dítětem z větve", f5 is not None and [n["val"] for n in sub(f5, "CHIL")] == ["@I5@"])
    ok("--koren 5: portrét a křest syna zůstanou", "media/katerina_mala_portret.jpg" in files5
       and any("Křest Jana" in p for p in page(recs5, recs5["@I5@"])))
    ok("--koren 5: svatební fotka Jana a Marie ne", "media/svatba_1919.jpg" not in files5)
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(d, "tools", "ged_export.py"), "--koren", "99"],
                       capture_output=True, text=True, encoding="utf-8", cwd=d)
    ok("--koren s neexistujícím číslem skončí chybou", r.returncode != 0 and "99" in r.stderr, r.stderr)

    # Osobní fotka FTB (okénko osoby ve stromu): portrét jako dvojice jako v exportu FTB; ověřeno zkouškami ve FTB –
    # nutné RIN osob a čísla fotek od 500001 (malá kolidují s čísly ostatních obrázků)
    sl = os.path.join(d, "pracovni", "slozka")
    export(d, "--slozka", "--vystup", sl)
    text = open(os.path.join(sl, "rodokmen.ged"), encoding="utf-8-sig").read()
    bloky = {re.match(r"0 (@I\d+@)", b)[1]: b for b in re.split(r"(?m)^(?=0 )", text) if re.match(r"0 @I\d+@ INDI", b)}
    ok("--slozka: RIN u každé osoby", all(re.search(rf"(?m)^1 RIN MH:I{k[2:-1]}$", b) for k, b in bloky.items()))
    kat_s = bloky["@I5@"]
    rodic = re.search(r"(?m)^1 OBJE\n2 FILE (.+katerina_mala_portret\.jpg)\n(?:[2-9] .*\n)*?2 _PRIM_CUTOUT Y\n"
                      r"2 _PHOTO_RIN MH:P(\d+)\n", kat_s)
    osobni = re.search(r"(?m)^1 OBJE\n2 FILE (.+katerina_mala_portret_osobni\.jpg)\n(?:[2-9] .*\n)*?2 _CUTOUT Y\n"
                       r"2 _PHOTO_RIN MH:P(\d+)\n2 _FILESIZE \d+\n2 _PARENTRIN @P(\d+)@", kat_s)
    ok("--slozka: portrét = fotka (_PRIM_CUTOUT) + osobní fotka (_CUTOUT, _PARENTRIN)",
       rodic and osobni and osobni[3] == rodic[2] and int(rodic[2]) > 500000
       and os.path.isfile(rodic[1]) and os.path.isfile(osobni[1]), kat_s)
    rins = re.findall(r"(?m)^\d+ _PHOTO_RIN MH:P(\d+)$", text)
    ok("--slozka: každý obrázek má vlastní _PHOTO_RIN a _FILESIZE (jako export FTB)",
       len(rins) == text.count(" OBJE\n") == len(re.findall(r"(?m)^\d+ _FILESIZE \d+$", text))
       and len(set(rins)) == len(rins) and min(map(int, rins)) > 500000, (len(rins), text.count(" OBJE\n")))
    ok("ZIP: bez osobní fotky FTB", not any(gi.first(o, "_CUTOUT") or gi.first(o, "_PRIM_CUTOUT") for o in sub(kat, "OBJE")))
    shutil.rmtree(os.path.dirname(d), ignore_errors=True)


def test_data():
    for vstup, cil in (("14. 2. 1890", "14 FEB 1890"), ("1797", "1797"), ("3/1867", "MAR 1867"), ("asi 1720", "ABT 1720"),
                       ("po 1921", "AFT 1921"), ("mezi 1720 a 1725", "BET 1720 AND 1725"), ("", "")):
        ok(f"datum „{vstup}“", ge.ged_date(vstup)[0] == cil, ge.ged_date(vstup))
    ok("nesmysl jako fráze", ge.ged_date("podzim 1951") == ("(podzim 1951)", False))


def test_import_bez_argumentu():
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c",
                        f"import sys; sys.argv=['x']; sys.path.insert(0, {TOOLS!r}); import ged_import; print('ok')"],
                       capture_output=True, text=True, encoding="utf-8")
    ok("ged_import jde importovat bez argumentů", r.stdout.strip() == "ok", r.stdout + r.stderr)


if __name__ == "__main__":
    test_data()
    test_import_bez_argumentu()
    test_ukazka()
    test_umely()
    test_vystup()
    print(f"\n{sum(vysledky)}/{len(vysledky)} v pořádku")
    sys.exit(0 if all(vysledky) else 1)
