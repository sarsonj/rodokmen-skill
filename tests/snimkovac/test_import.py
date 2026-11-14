"""Test tools/snimky_import.py (převzetí snímků uložených rozšířením Snímkovač) a syntaxe rozšíření.

Z kořene repozitáře:
  python3 -I tests/snimkovac/test_import.py skills/rodokmen
  (Windows: python -I -X utf8 …)
Postaví dočasný projekt s nástroji, vymyšlenými snímky všech druhů (eBadatelna, dlaždicový prohlížeč, Matricula,
obecný web, výřez, složka „_…“, neznámý druh) a dočasnou mezipamětí (RODOKMEN_SNIMKY). Nic nestahuje.
Má-li počítač Node.js, zkontroluje i syntaxi všech .js rozšíření (node --check).
"""
import base64, glob, json, os, shutil, subprocess, sys, tempfile

SKILL = os.path.abspath(sys.argv[1])
PY = [sys.executable, "-I", "-X", "utf8"]
JPG = base64.b64decode("/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkKDA8MCgsOCwkJDRENDg8Q"
                       "EBEQCgwSExIQEw8QEBD/wAALCAACAAIBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/"
                       "2gAIAQEAAD8AVN//2Q==")
VYSLEDKY = []


def ma(nazev, ok, detail=""):
    VYSLEDKY.append(ok)
    print(("OK  " if ok else "CHYBA ") + nazev + ("" if ok else f"\n    {detail}"))


def snimek(slozka, jmeno, meta):
    os.makedirs(slozka, exist_ok=True)
    with open(os.path.join(slozka, jmeno + ".jpg"), "wb") as f:
        f.write(JPG)
    with open(os.path.join(slozka, jmeno + ".json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)


def main():
    tmp = tempfile.mkdtemp(prefix="snimkovac_")
    try:
        tools = os.path.join(tmp, "projekt", "tools")
        os.makedirs(tools)
        for n in ("cache.py", "snimky_import.py"):
            shutil.copy(os.path.join(SKILL, "tools", n), tools)
        st = os.path.join(tmp, "stazene", "rodokmen-snimky")
        snimek(os.path.join(st, "Benešov 49"), "13841_78", {"druh": "d", "matrikaId": "13841", "snimek": 78,
               "kniha": "Benešov 49", "adresa": "https://ebadatelna.soapraha.cz/d/13841/78"})
        snimek(os.path.join(st, "Benešov 49"), "13841_79", {"druh": "d", "matrikaId": "13841", "snimek": 79,
               "kniha": "Benešov 49", "adresa": "https://ebadatelna.soapraha.cz/d/13841/79"})
        snimek(os.path.join(st, "Velký Újezd 11075"), "7080_70", {"druh": "osd", "host": "www.mza.cz", "matrikaId": "7080",
               "snimek": 70, "kniha": "Velký Újezd 11075", "pokryti": {"prehled_procent": 100, "ideal_procent": 80, "zapis_procent": 40}})
        snimek(os.path.join(st, "Matricula Gross 01,2,3-01"), "gross_01,2,3-01_213", {"druh": "matricula",
               "matrikaId": "gross_01,2,3-01", "snimek": 213, "dieceze": "wien", "farnost": "gross", "signatura": "01,2,3-01"})
        snimek(os.path.join(st, "jiny web"), "web_ab12", {"druh": "web", "matrikaId": "priklad.cz", "snimek": "ab12",
               "obrazek": "https://priklad.cz/obr/1.jpg"})
        snimek(os.path.join(st, "Velký Újezd 11075"), "7080_70_vyrez", {"druh": "osd", "matrikaId": "7080", "snimek": 70,
               "vyrez": [0.1, 0.1, 0.5, 0.5]})
        snimek(os.path.join(st, "_analyza"), "stary", {"druh": "d", "matrikaId": "1", "snimek": 1})
        snimek(os.path.join(st, "novy druh"), "x_1", {"druh": "budouci", "matrikaId": "x", "snimek": 1})
        snimek(os.path.join(st, "spatne"), "1_1", {"druh": "d", "matrikaId": "1", "snimek": 1, "adresa": "https://www.mza.cz/x"})

        env = dict(os.environ, RODOKMEN_SNIMKY=os.path.join(tmp, "cache"))
        r = subprocess.run(PY + [os.path.join(tools, "snimky_import.py"), st], capture_output=True, text=True,
                           encoding="utf-8", env=env, cwd=os.path.join(tmp, "projekt"))
        out = r.stdout + r.stderr
        ma("import doběhl", r.returncode == 0, out)
        ma("nově v mezipaměti 5", "nově v mezipaměti 5" in out, out)
        c = os.path.join(tmp, "cache")
        ma("eBadatelna v mezipaměti", len(glob.glob(os.path.join(c, "ebadatelna", "d", "13841", "sn007*.jpg"))) == 2,
           os.listdir(c) if os.path.isdir(c) else "žádná mezipaměť")
        ma("dlaždicový prohlížeč (osd)", os.path.exists(os.path.join(c, "osd", "www.mza.cz", "7080", "sn0070.jpg")))
        ma("Matricula", os.path.exists(os.path.join(c, "matricula", "wien", "gross", "01,2,3-01", "sn0213.jpg")))
        ma("rejstřík bez tools/snimky.py jen vypsán", "(rejstřík snímků v projektu není) soa-praha 13841 sn. 78-79" in out, out)
        ma("archiv MZA a Matricula", "mza 7080 sn. 70" in out and "matricula wien/gross/01,2,3-01 sn. 213" in out, out)
        ma("výřez ponechán", "výřez ponechán" in out and os.path.exists(os.path.join(st, "Velký Újezd 11075", "7080_70_vyrez.jpg")))
        ma("neznámý druh přeskočen", "neznámý druh" in out and os.path.exists(os.path.join(st, "novy druh", "x_1.jpg")))
        ma("eBadatelna jen s její adresou", "adresa není eBadatelna" in out)
        ma("složka _analyza netknutá", os.path.exists(os.path.join(st, "_analyza", "stary.jpg")))
        ma("zpracované v _importovano", os.path.exists(os.path.join(st, "_importovano", "Benešov 49", "13841_78.jpg"))
           and not os.path.exists(os.path.join(st, "Benešov 49", "13841_78.jpg")))
        r2 = subprocess.run(PY + [os.path.join(tools, "snimky_import.py"), st], capture_output=True, text=True,
                            encoding="utf-8", env=env)
        ma("podruhé nic nového", "nově v mezipaměti 0" in r2.stdout, r2.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    node = shutil.which("node")
    if node:
        for js in sorted(glob.glob(os.path.join(SKILL, "rozsireni", "snimkovac", "*.js"))):
            r = subprocess.run([node, "--check", js], capture_output=True, text=True)
            ma("syntaxe " + os.path.basename(js), r.returncode == 0, r.stderr)
    else:
        print("(Node.js není – syntaxe .js se nekontroluje)")
    with open(os.path.join(SKILL, "rozsireni", "snimkovac", "manifest.json"), encoding="utf-8") as f:
        m = json.load(f)
    ma("manifest MV3 s verzí", m.get("manifest_version") == 3 and bool(m.get("version")))
    print(f"\n{sum(VYSLEDKY)}/{len(VYSLEDKY)} v pořádku")
    sys.exit(0 if all(VYSLEDKY) else 1)


if __name__ == "__main__":
    main()
