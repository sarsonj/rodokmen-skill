"""Test tools/podpis.py (podpisy a křížky předků pro stránku Podpisy).

Z kořene repozitáře:
  python3 -I tests/podpis/test_podpis.py skills/rodokmen/tools
  (Windows: python -I -X utf8 …)
Postaví dočasný projekt s vymyšlenou rodinou a snímkem zápisu, zkopíruje do něj nástroje a ověří přidání, nahrazení,
křížky, smazání a chybové případy. Nic nestahuje; potřebuje ImageMagick (magick).
"""
import glob, json, os, shutil, subprocess, sys, tempfile

TOOLS = os.path.abspath(sys.argv[1])
PY = [sys.executable, "-I", "-X", "utf8"]
MAGICK = shutil.which("magick") or next(iter(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe")), None) or "convert"
VYSLEDKY = []
K = "holice_snatek_vaclav_novak_barbora_mala_1884"


def ma(nazev, ok, detail=""):
    VYSLEDKY.append(ok)
    print(("OK  " if ok else "CHYBA ") + nazev + ("" if ok else f"\n    {detail}"))


tmp = tempfile.mkdtemp(prefix="podpis_")
try:
    os.makedirs(os.path.join(tmp, "tools"))
    for n in ("podpis.py", "zapis.py", "vyrez.py"):
        shutil.copy(os.path.join(TOOLS, n), os.path.join(tmp, "tools", n))
    os.makedirs(os.path.join(tmp, "data"))
    os.makedirs(os.path.join(tmp, "zdroje"))
    subprocess.run([MAGICK, "-size", "1000x700", "xc:white", os.path.join(tmp, "zdroje", K + ".jpg")], check=True)
    with open(os.path.join(tmp, "data", "zaznamy.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump([dict(klic=K, datum="12. 5. 1884", nazev="Sňatek")], f, ensure_ascii=False, indent=1)
    with open(os.path.join(tmp, "data", "osoby.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write("P = {\n 4: dict(n='Václav Novák', y='1858–1920', r=['%s']),\n 5: dict(n='Barbora Malá', y='1860–1930', r=['%s']),\n"
                " 6: dict(n='Jan Novák', y='1830', r=[]),\n}\nSIDE = [dict(k=4, n='Josef Novák (1860)', t='', r=[])]\nSAME = {}\n" % (K, K))

    def spust(*args):
        return subprocess.run(PY + [os.path.join("tools", "podpis.py"), *args], cwd=tmp, capture_output=True, text=True, encoding="utf-8")

    def polozky():
        return json.load(open(os.path.join(tmp, "data", "podpisy.json"), encoding="utf-8"))

    r = spust(K, "4", "podpis", "--text", "Wáclaw Nowak", "--vyrez", "0.5,0.6,0.9,0.7", "--popis", "podpis ženicha")
    p = polozky() if r.returncode == 0 else []
    ma("podpis se přidá", r.returncode == 0 and len(p) == 1 and p[0]["id"] == "vaclav_novak_1884" and p[0]["rok"] == 1884
       and p[0]["osoba"] == "vaclav-novak-1858" and p[0]["kruzky"] is False and p[0]["text"] == "„Wáclaw Nowak“", r.stderr + r.stdout)
    ma("obrázek vznikl", os.path.exists(os.path.join(tmp, "podpisy", "vaclav_novak_1884.jpg")))
    r = spust(K, "Václav", "podpis", "--text", "Václav Novák", "--popis", "nový popis")
    p = polozky()
    ma("stejné id nahradí a ponechá obrázek", r.returncode == 0 and len(p) == 1 and p[0]["text"] == "„Václav Novák“", r.stderr + r.stdout)
    r = spust(K, "5", "krizky", "--text", "Barbora Malá", "--vyrez", "0.1,0.6,0.4,0.7")
    p = polozky()
    ma("křížky dostanou +++", r.returncode == 0 and len(p) == 2 and p[1]["kruzky"] is True and p[1]["text"] == "„+++ Barbora Malá“", r.stderr + r.stdout)
    for popis, args in (("osoba bez zápisu v r", [K, "6", "podpis", "--text", "x", "--vyrez", "0.1,0.1,0.5,0.2"]),
                        ("neznámý zápis", ["nema", "4", "podpis", "--text", "x", "--vyrez", "0.1,0.1,0.5,0.2"]),
                        ("neznámá osoba", [K, "99", "podpis", "--text", "x", "--vyrez", "0.1,0.1,0.5,0.2"]),
                        ("boční příbuzný", [K, "Josef", "podpis", "--text", "x", "--vyrez", "0.1,0.1,0.5,0.2"]),
                        ("pixely místo zlomků", [K, "4", "podpis", "--text", "x", "--id", "a", "--vyrez", "10,10,500,200"]),
                        ("chybí výřez u nového", [K, "4", "podpis", "--text", "x", "--id", "b"])):
        r = spust(*args)
        ma("chyba: " + popis, r.returncode != 0 and len(polozky()) == 2, r.stdout + r.stderr)
    r = spust("--smazat", "vaclav_novak_1884")
    p = polozky()
    ma("smazání", r.returncode == 0 and [x["id"] for x in p] == ["barbora_mala_1884"]
       and not os.path.exists(os.path.join(tmp, "podpisy", "vaclav_novak_1884.jpg")), r.stderr + r.stdout)
    spust("--smazat", "barbora_mala_1884")
    ma("smazání posledního", polozky() == [])
finally:
    shutil.rmtree(tmp, ignore_errors=True)
sys.exit(0 if all(VYSLEDKY) else 1)
