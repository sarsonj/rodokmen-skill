"""Test ukládání snímků z prohlížeče do mezipaměti (tools/cache.py uloz / najdi) – eBadatelna a FamilySearch.

Z kořene repozitáře:
  python3 -I tests/brzda/test_prohlizec.py skills/rodokmen/tools
Mezipaměť je v dočasné složce (RODOKMEN_SNIMKY). Nic nestahuje, ImageMagick nepotřebuje.
"""
import base64, json, os, shutil, subprocess, sys, tempfile

TOOLS = os.path.abspath(sys.argv[1])
CACHE = os.path.join(TOOLS, "cache.py")
JPG = b"\xff\xd8\xff\xe0" + bytes(range(256)) * 40 + b"\xff\xd9"
ARK = "3:1:3Q9M-CS54-T34P-Y"
FS_DIST = f"https://www.familysearch.org/service/records/storage/deepzoomcloud/dz/v1/{ARK}/$dist"
vysledky = []


def check(nazev, ok, detail=""):
    vysledky.append(ok)
    print(f"[{'OK ' if ok else 'CHYBA'}] {nazev} {'' if ok else detail}", flush=True)


tmp = tempfile.mkdtemp(prefix="cache_prohlizec_")
env = dict(os.environ, RODOKMEN_SNIMKY=os.path.join(tmp, "mezipamet"), SLUSNE_STAV=os.path.join(tmp, "stav"))


def cache(*a):
    return subprocess.run([sys.executable, "-I", "-X", "utf8", CACHE, *a], cwd=tmp, env=env,
                          capture_output=True, text=True)


def json_ze_prohlizece(adresa, data=JPG):
    p = os.path.join(tmp, "snimek.json")
    d = {"w": 4000, "h": 3000, "adresa": adresa, "data": "data:image/jpeg;base64," + base64.b64encode(data).decode()}
    with open(p, "w") as f:
        json.dump(json.dumps(d), f)   # browser_evaluate s filename ukládá výsledek jako řetězec JSON
    return p


try:
    # eBadatelna (stávající chování)
    r = cache("uloz", json_ze_prohlizece("https://ebadatelna.soapraha.cz/d/11269/40"))
    check("eBadatelna: uloz", r.returncode == 0 and "uloženo" in r.stdout, r.stdout + r.stderr)
    r = cache("najdi", "https://ebadatelna.soapraha.cz/d/11269/40")
    check("eBadatelna: najdi", r.returncode == 0 and r.stdout.strip().endswith(".jpg"), r.stdout + r.stderr)

    # FamilySearch: uloží se podle ARK snímku
    r = cache("uloz", json_ze_prohlizece(FS_DIST), "pracovni/fs.jpg")
    check("FamilySearch: uloz", r.returncode == 0 and "uloženo" in r.stdout, r.stdout + r.stderr)
    check("FamilySearch: kopie do projektu", os.path.exists(os.path.join(tmp, "pracovni", "fs.jpg")))
    ulozene = [os.path.join(d, f) for d, _, fs in os.walk(env["RODOKMEN_SNIMKY"]) for f in fs if "familysearch" in d]
    check("FamilySearch: soubor bez dvojteček v názvu (Windows)", bool(ulozene) and not any(":" in os.path.basename(p) for p in ulozene),
          ulozene)
    check("FamilySearch: json po uložení smazán", not os.path.exists(os.path.join(tmp, "snimek.json")))

    # najdi: stejný snímek pod adresou $dist i pod trvalým odkazem ark
    for adresa in (FS_DIST, f"https://www.familysearch.org/ark:/61903/{ARK}?i=5&cc=1554443"):
        r = cache("najdi", adresa)
        check(f"FamilySearch: najdi {adresa[:60]}…", r.returncode == 0 and r.stdout.strip().endswith(".jpg"),
              r.stdout + r.stderr)
    r = cache("najdi", f"https://www.familysearch.org/ark:/61903/3:1:XXXX-YYYY-ZZZ")
    check("FamilySearch: jiný snímek nenajde", r.returncode == 1, r.stdout + r.stderr)

    # useknutý obrázek ani cizí adresa se neuloží
    r = cache("uloz", json_ze_prohlizece(f"https://www.familysearch.org/ark:/61903/3:1:AAAA-BBBB-CCC", JPG[:500]))
    check("FamilySearch: useknutý snímek odmítnut", r.returncode != 0, r.stdout + r.stderr)
    r = cache("uloz", json_ze_prohlizece("https://example.org/obrazek.jpg"))
    check("cizí adresa odmítnuta", r.returncode != 0, r.stdout + r.stderr)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\n{sum(vysledky)} z {len(vysledky)} správně")
sys.exit(0 if all(vysledky) else 1)
