"""Test nástroje osobních odkazů skills/rodokmen/tools/pozvanky.py.

Z kořene repozitáře:
  python3 -I tests/pozvanky/test_pozvanky.py
  (Windows: python -I -X utf8 …)
Každý případ pracuje ve vlastní dočasné složce data/. Nic nestahuje, jen standardní knihovna.
"""
import contextlib, hashlib, io, json, os, re, shutil, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "skills", "rodokmen", "tools"))
import pozvanky  # noqa: E402

DNES = "2026-11-04"
VYSLEDKY = []


def ok(nazev, podminka, detail=""):
    VYSLEDKY.append(bool(podminka))
    print(("OK  " if podminka else "CHYBA ") + nazev)
    if not podminka and detail:
        print("    " + str(detail).replace("\n", "\n    "))


def slozka(adresa="https://rod.netlify.app"):
    tmp = tempfile.mkdtemp(prefix="pozvanky_")
    if adresa is not None:
        with open(os.path.join(tmp, "web.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"prihlaseni": {"adresa": adresa}}, f)
    return tmp


def run(data, *argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = pozvanky.main(list(argv), data, DNES)
    return code, out.getvalue() + err.getvalue()


def ulozene(data):
    with open(os.path.join(data, "pozvanky.json"), encoding="utf-8") as f:
        return json.load(f)


def surove(data):
    with open(os.path.join(data, "pozvanky.json"), "rb") as f:
        return f.read()


def klic_z(out):
    m = re.search(r"\?k=([A-Za-z0-9_-]+)", out)
    return m.group(1) if m else ""


def sha(t):
    return hashlib.sha256(t.encode()).hexdigest()


slozky = []
try:
    # pridej: vypíše odkaz jednou, uloží jen otisk
    d = slozka(); slozky.append(d)
    code, out = run(d, "pridej", "Teta Jana")
    klic = klic_z(out)
    ok("pridej skončí 0", code == 0, out)
    ok("pridej vypíše celý odkaz", f"https://rod.netlify.app/?k={klic}" in out, out)
    ok("klíč má 22 znaků (128 bitů)", len(klic) == 22, klic)
    ok("pozvanky.json má id, jméno, otisk a datum",
       ulozene(d) == [{"id": "p1", "jmeno": "Teta Jana", "otisk": sha(klic), "vytvoreno": DNES}], ulozene(d))
    ok("klíč sám v souboru není", klic.encode() not in surove(d))
    ok("soubor má LF", b"\r\n" not in surove(d))
    ok("pridej připomene nasazení", "npm run nasadit" in out, out)
    ok("dvakrát stejný příkaz dá jiný klíč", klic_z(run(d, "pridej", "Teta Jana")[1]) != klic)

    # seznam neukazuje klíče
    run(d, "pridej", "Strýc Karel")
    code, out = run(d, "seznam")
    ok("seznam skončí 0", code == 0)
    ok("seznam ukáže id a jména", all(t in out for t in ("p1", "Teta Jana", "p3", "Strýc Karel")), out)
    ok("seznam neukáže odkaz", "?k=" not in out, out)

    # prejmenuj
    code, out = run(d, "prejmenuj", "p1", "Jana Nováková")
    ok("prejmenuj změní jméno", code == 0 and ulozene(d)[0]["jmeno"] == "Jana Nováková", out)
    ok("prejmenuj nemění otisk", ulozene(d)[0]["otisk"] == sha(klic))
    code, out = run(d, "prejmenuj", "p1", "  ")
    ok("prejmenuj na prázdné jméno skončí 1", code == 1 and ulozene(d)[0]["jmeno"] == "Jana Nováková", out)

    # nova: nový klíč, stejné id, starý otisk pryč
    code, out = run(d, "nova", "p1")
    novy = klic_z(out)
    z = ulozene(d)[0]
    ok("nova skončí 0 a vypíše odkaz", code == 0 and len(novy) == 22, out)
    ok("nova uloží otisk nového klíče pod stejným id", z["id"] == "p1" and z["otisk"] == sha(novy), z)
    ok("starý otisk zmizel", all(x["otisk"] != sha(klic) for x in ulozene(d)))
    ok("nova řekne, že starý odkaz přestane platit", "přestane platit" in out, out)

    # zrus
    code, out = run(d, "zrus", "p2")
    p2 = next(x for x in ulozene(d) if x["id"] == "p2")
    ok("zrus smaže otisk a zapíše datum zrušení", code == 0 and "otisk" not in p2 and p2.get("zruseno") == DNES, p2)
    ok("seznam zrušený odkaz neukáže", "p2" not in run(d, "seznam")[1])
    run(d, "pridej", "Babička")
    ok("id se po zrušení neopakuje", [x["id"] for x in ulozene(d)] == ["p1", "p2", "p3", "p4"], ulozene(d))
    run(d, "zrus", "p4")
    run(d, "pridej", "Děda")
    ok("id se neopakuje ani po zrušení posledního", ulozene(d)[-1]["id"] == "p5", ulozene(d))

    # neznámé nebo zrušené id a špatné argumenty soubor nezmění
    pred = surove(d)
    for argv in (["zrus", "p9"], ["nova", "p9"], ["prejmenuj", "p9", "X"], ["zrus", "p2"], ["nova", "p2"],
                 ["prejmenuj", "p2", "X"], ["pridej", ""], ["pridej"], ["xyz"], []):
        code, out = run(d, *argv)
        ok(f"{' '.join(argv) or '(nic)'} skončí 1 a soubor nezmění", code == 1 and surove(d) == pred, out)

    # bez souboru a bez adresy
    d = slozka(None); slozky.append(d)
    code, out = run(d, "seznam")
    ok("seznam bez souboru", code == 0 and "Žádné odkazy" in out, out)
    ok("load bez souboru vrátí []", pozvanky.load(d) == [])
    code, out = run(d, "pridej", "Teta Jana")
    ok("pridej bez adresy webu vypíše cestu a upozorní", code == 0 and "/?k=" in out and "prihlaseni.adresa" in out, out)

    d = slozka("https://rod.netlify.app/"); slozky.append(d)
    _, out = run(d, "pridej", "A")
    ok("lomítko na konci adresy se nezdvojí", "https://rod.netlify.app/?k=" in out, out)

    # nepovedený zápis nechá původní soubor
    d = slozka(); slozky.append(d)
    run(d, "pridej", "Teta Jana")
    pred = surove(d)
    puvodni = pozvanky.json.dump

    def rozbity(*a, **k):
        raise OSError("disk je plný")
    pozvanky.json.dump = rozbity
    try:
        run(d, "pridej", "Strýc Karel")
        spadlo = False
    except OSError:
        spadlo = True
    finally:
        pozvanky.json.dump = puvodni
    ok("chyba zápisu: výjimka a původní soubor beze změny", spadlo and surove(d) == pred)
    ok("chyba zápisu: dočasný soubor nezůstane", sorted(os.listdir(d)) == ["pozvanky.json", "web.json"], os.listdir(d))

    ok("otisk je SHA-256", pozvanky.otisk("abc") == hashlib.sha256(b"abc").hexdigest())
finally:
    for d in slozky:
        shutil.rmtree(d, ignore_errors=True)

print(f"\n{sum(VYSLEDKY)} z {len(VYSLEDKY)} v pořádku")
sys.exit(0 if all(VYSLEDKY) else 1)
