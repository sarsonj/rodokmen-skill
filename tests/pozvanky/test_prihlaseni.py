"""Test přihlašovací brány z skills/rodokmen/tools/export_web.py: rodinná otázka a osobní odkazy.

Z kořene repozitáře:
  python3 -I tests/pozvanky/test_prihlaseni.py
  (Windows: python -I -X utf8 …)
Každý případ zkopíruje šablony přihlášení do dočasné složky web/ a zavolá login_files() s vymyšleným nastavením.
Nic nestahuje, jen standardní knihovna.
"""
import contextlib, hashlib, io, json, os, re, shutil, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "skills", "rodokmen", "tools"))
import export_web  # noqa: E402

SABLONY = ["prihlaseni.sablona.html", "nginx.sablona.conf", os.path.join("netlify", "brana.sablona.js")]
O1, O2 = hashlib.sha256(b"klic-1").hexdigest(), hashlib.sha256(b"klic-2").hexdigest()
OTAZKA_HASH = hashlib.sha256(b"rodokmen:kovar").hexdigest()
CFG = {"nazev": "Rodokmen Novákových", "kontakt": {"jmeno": "Petrovi", "kdo": "Petr", "email": "petr@example.cz"},
       "prihlaseni": {"uvod": "Tenhle web je jen pro rodinu.", "otazka": "Jaké řemeslo?", "odpoved": "Kovář"}}
BEZ_OTAZKY = dict(CFG, prihlaseni={"uvod": "Tenhle web je jen pro rodinu."})
VYSLEDKY = []
SLOZKY = []


def ok(nazev, podminka, detail=""):
    VYSLEDKY.append(bool(podminka))
    print(("OK  " if podminka else "CHYBA ") + nazev)
    if not podminka and detail:
        print("    " + str(detail).replace("\n", "\n    "))


def web(nahrad=None):
    """Dočasná složka web/ se šablonami ze skillu; `nahrad` = {šablona: text} pro starší verze šablon."""
    tmp = tempfile.mkdtemp(prefix="prihlaseni_")
    SLOZKY.append(tmp)
    for s in SABLONY:
        os.makedirs(os.path.dirname(os.path.join(tmp, s)), exist_ok=True)
        shutil.copy(os.path.join(ROOT, "skills", "rodokmen", "template", "web", s), os.path.join(tmp, s))
    for s, text in (nahrad or {}).items():
        with open(os.path.join(tmp, s), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    export_web.WEB = tmp
    return tmp


def login(cfg, otisky):
    """login_files() s odchyceným výstupem: (vrácená hodnota nebo text chyby, výstup)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        try:
            r = export_web.login_files(cfg, otisky)
        except SystemExit as e:
            r = "EXIT " + str(e.code)
    return r, out.getvalue()


def cti(w, *cesta):
    p = os.path.join(w, *cesta)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return f.read()


def brana(w):
    return cti(w, "netlify", "edge-functions", "brana.js")


def mapa(w):
    return cti(w, "nginx.conf").split("map $cookie_rodokmen $rodokmen_ok {")[1].split("}")[0]


def stranka(w):
    return cti(w, "public", "prihlaseni.html")


try:
    # 1. jen otázka (dnešní stav)
    w = web()
    r, out = login(CFG, [])
    ok("otázka: brána zapnutá", r is True, r)
    ok("otázka: brána má otisk odpovědi a prázdnou sadu odkazů",
       f"'{OTAZKA_HASH}'" in brana(w) and "new Set([])" in brana(w), brana(w))
    ok("otázka: nginx pustí otisk odpovědi, jinak nikoho",
       mapa(w).count("default") == 1 and "default 0;" in mapa(w) and f'"{OTAZKA_HASH}" 1;' in mapa(w), mapa(w))
    ok("otázka: nginx bez varování", "POZOR" not in out, out)
    p = stranka(w)
    ok("otázka: stránka má formulář s otázkou", '<form id="f">' in p and "Jaké řemeslo?" in p, p)
    ok("otázka: nápověda s e-mailem", 'Neznáte odpověď? Napište Petrovi na <a href="mailto:petr@example.cz">' in p, p)
    ok("otázka: bez řádku o osobním odkazu (žádný není)", "Máte osobní odkaz?" not in p, p)
    ok("otázka: stránka umí neplatný odkaz", "Tenhle odkaz už neplatí" in p and "has('k')" in p, p)
    ok("otázka: počítá otisk s předponou rodokmen:", "'rodokmen:' + v" in p)

    # 2. jen osobní odkazy
    w = web()
    r, out = login(BEZ_OTAZKY, [O2, O1])
    ok("odkazy: brána zapnutá", r is True, r)
    ok("odkazy: brána má otisky a prázdný otisk otázky",
       "const HASH = '';" in brana(w) and json.dumps(sorted([O1, O2])) in brana(w), brana(w))
    ok("odkazy: klíče v bráně nejsou", "klic-1" not in brana(w))
    ok("odkazy: nginx nepustí nikoho", mapa(w).strip() == "default 0;", mapa(w))
    ok("odkazy: varování, že Docker/CapRover nikoho nepustí", "POZOR" in out and "CapRover" in out, out)
    p = stranka(w)
    ok("odkazy: stránka bez formuláře", "<form" not in p and "<input" not in p and "crypto.subtle" not in p, p)
    ok("odkazy: kdo posílá odkazy (1. pád)", "osobním odkazem, který posílá Petr." in p, p)
    ok("odkazy: jak získat nový, s e-mailem",
       'Napište Petrovi na <a href="mailto:petr@example.cz">petr@example.cz</a>, pošle vám nový.' in p, p)
    ok("odkazy: stav neplatného odkazu", "Tenhle odkaz už neplatí" in p and "has('k')" in p, p)

    # 3. obojí
    w = web()
    r, out = login(CFG, [O1])
    ok("obojí: brána zapnutá", r is True, r)
    ok("obojí: brána má otisk otázky i odkazů", f"'{OTAZKA_HASH}'" in brana(w) and O1 in brana(w), brana(w))
    ok("obojí: nginx pustí jen otázku", mapa(w).count("default") == 1 and f'"{OTAZKA_HASH}" 1;' in mapa(w)
       and O1 not in mapa(w), mapa(w))
    ok("obojí: varování, že na Docker/CapRover funguje jen otázka", "POZOR" in out and "jen přes rodinnou otázku" in out, out)
    p = stranka(w)
    ok("obojí: formulář zůstal", '<form id="f">' in p and "Jaké řemeslo?" in p, p)
    ok("obojí: řádek o osobním odkazu", "Máte osobní odkaz? Stačí ho otevřít" in p, p)
    ok("obojí: bez textu jen pro odkazy", "který posílá" not in p, p)

    # 4. otevřený web
    for otisky in ([O1], []):
        w = web()
        login(CFG, [O1])   # brána z minulého exportu musí zmizet
        r, out = login(dict(CFG, prihlaseni=dict(CFG["prihlaseni"], otevreny=True)), otisky)
        ok(f"otevřený ({len(otisky)} odkazů): bez brány", r is False and brana(w) is None, r)
        ok(f"otevřený ({len(otisky)} odkazů): nginx pustí každého", mapa(w).strip() == "default 1;", mapa(w))
        ok(f"otevřený ({len(otisky)} odkazů): bez varování", "POZOR" not in out, out)

    # 5. nic nenastaveno: místní náhled bez brány, nasazení skončí chybou
    w = web()
    login(CFG, [O1])
    r, out = login(BEZ_OTAZKY, [])
    ok("nic: bez brány a nginx pustí každého", r is False and brana(w) is None and mapa(w).strip() == "default 1;", r)
    chyba = export_web.deploy_error(BEZ_OTAZKY, [])
    ok("nic: nasazení skončí chybou s radou", chyba and "pozvanky.py pridej" in chyba and "odpoved" in chyba, chyba)
    ok("nasazení projde s otázkou", export_web.deploy_error(CFG, []) is None)
    ok("nasazení projde s odkazem", export_web.deploy_error(BEZ_OTAZKY, [O1]) is None)
    ok("nasazení projde s otevreny: true",
       export_web.deploy_error(dict(CFG, prihlaseni={"otevreny": True}), []) is None)
    for hodnota in ("true", 1, "ano", False):
        cfg = dict(CFG, prihlaseni={"otevreny": hodnota})
        ok(f"otevreny {hodnota!r} web neotevře", export_web.deploy_error(cfg, []) is not None)
        w = web()
        r, _ = login(dict(CFG, prihlaseni=dict(CFG["prihlaseni"], otevreny=hodnota)), [O1])
        ok(f"otevreny {hodnota!r}: brána zůstane", r is True and brana(w) is not None, r)

    # 6. nápověda pro odkazy bez e-mailu a bez jména, výchozí „kdo“
    w = web()
    login(dict(BEZ_OTAZKY, kontakt={"jmeno": "Petrovi", "email": ""}), [O1])
    ok("bez e-mailu: řekněte si", "Řekněte si o nový Petrovi." in stranka(w), stranka(w))
    ok("bez kdo: správce rodokmenu", "který posílá správce rodokmenu." in stranka(w), stranka(w))
    login(dict(BEZ_OTAZKY, kontakt={}), [O1])
    ok("bez kontaktu: obecná rada", "Řekněte si o nový tomu, kdo vám o webu řekl." in stranka(w), stranka(w))
    login(dict(BEZ_OTAZKY, kontakt={"email": "x@example.cz"}), [O1])
    ok("jen e-mail", 'Napište na <a href="mailto:x@example.cz">x@example.cz</a>, pošleme vám nový.' in stranka(w),
       stranka(w))

    # 7. HTML z web.json se escapuje
    zly = {"nazev": "<b>R&D</b>", "kontakt": {"jmeno": "<i>Petrovi</i>", "kdo": "<img src=x>", "email": 'a"b@x.cz'},
           "prihlaseni": {"uvod": "<script>u</script>", "otazka": "<script>o</script>", "odpoved": "x"}}
    for nazev, otisky, cfg in (("otázka", [], zly), ("odkazy", [O1], dict(zly, prihlaseni={"uvod": "<u>"}))):
        w = web()
        login(cfg, otisky)
        p = stranka(w)
        ok(f"escapování ({nazev})", all(t not in p for t in ("<b>", "<i>", "<img", "<script>u", "<script>o", "<u>", 'a"b'))
           and "&lt;b&gt;R&amp;D&lt;/b&gt;" in p, p)

    # 8. žádné nevyplněné značky ani značky sekcí
    for nazev, cfg, otisky in (("otázka", CFG, []), ("odkazy", BEZ_OTAZKY, [O1]), ("obojí", CFG, [O1])):
        w = web()
        login(cfg, otisky)
        vse = stranka(w) + brana(w) + cti(w, "nginx.conf")
        ok(f"{nazev}: žádné {{{{…}}}} ani <!--sekce-->", "{{" not in vse and not re.search(r"<!--/?(otazka|odkazy|odkaz)-->", vse),
           re.findall(r"\{\{\w+\}\}|<!--/?\w+-->", vse))

    # 9. starší šablony (projekt aktualizovaný jen zčásti)
    stara_stranka = "<p>{{NAZEV}} {{UVOD}}</p><label>{{OTAZKA}}</label><p>{{NAPOVEDA}}</p><script>'rodokmen:'</script>"
    stara_brana = "const HASH = '{{HASH}}';\n"
    stary_nginx = "map $cookie_rodokmen $rodokmen_ok {\n  default 0;\n{{ODPOVED}}\n}\n"
    w = web({"prihlaseni.sablona.html": "<p>{{OTAZKA}}</p>"})
    r, _ = login(CFG, [])
    ok("šablona do 0.4.0 (bez otisku) skončí chybou", str(r).startswith("EXIT CHYBA") and "Aktualizujte" in r, r)
    w = web({"prihlaseni.sablona.html": stara_stranka, os.path.join("netlify", "brana.sablona.js"): stara_brana,
             "nginx.sablona.conf": stary_nginx})
    r, _ = login(CFG, [])
    ok("starší šablony a jen otázka: funguje jako dřív", r is True and f"'{OTAZKA_HASH}'" in brana(w)
       and "Jaké řemeslo?" in stranka(w), r)
    ok("starší nginx: jediný default", mapa(w).count("default") == 1, mapa(w))
    login(dict(CFG, prihlaseni={"otevreny": True}), [])
    ok("starší nginx a otevřený web: jediný default 1", mapa(w).strip() == "default 1;", mapa(w))
    r, _ = login(CFG, [O1])
    ok("starší šablona stránky a odkazy: chyba s výzvou k aktualizaci", str(r).startswith("EXIT CHYBA")
       and "Aktualizujte" in r, r)
    w = web({os.path.join("netlify", "brana.sablona.js"): stara_brana})
    r, _ = login(CFG, [O1])
    ok("starší šablona brány a odkazy: chyba s výzvou k aktualizaci", str(r).startswith("EXIT CHYBA")
       and "Aktualizujte" in r, r)

    # 10. načtení otisků z data/pozvanky.json
    data = tempfile.mkdtemp(prefix="prihlaseni_data_")
    SLOZKY.append(data)
    export_web.DATA = data
    ok("bez pozvanky.json žádné otisky", export_web.load_otisky() == [])
    with open(os.path.join(data, "pozvanky.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump([{"id": "p1", "jmeno": "A", "otisk": O1, "vytvoreno": "2026-11-04"},
                   {"id": "p2", "jmeno": "B", "otisk": O2, "vytvoreno": "2026-11-04"}], f)
    ok("otisky z pozvanky.json", export_web.load_otisky() == [O1, O2], export_web.load_otisky())
    for spatny in ("klic-v-cisté-podobě", O1.upper(), O1[:-1], "'];alert(1);//" + O1):
        with open(os.path.join(data, "pozvanky.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump([{"id": "p1", "jmeno": "A", "otisk": spatny, "vytvoreno": "2026-11-04"}], f)
        try:
            export_web.load_otisky()
            r = None
        except SystemExit as e:
            r = str(e.code)
        ok(f"neplatný otisk {spatny[:12]}… skončí chybou", r and r.startswith("CHYBA") and "p1" in r, r)
finally:
    for d in SLOZKY:
        shutil.rmtree(d, ignore_errors=True)

print(f"\n{sum(VYSLEDKY)} z {len(VYSLEDKY)} v pořádku")
sys.exit(0 if all(VYSLEDKY) else 1)
