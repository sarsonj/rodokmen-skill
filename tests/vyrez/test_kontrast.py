"""Test přepínače --kontrast ve vyrez.py a overit.py (vybledlé snímky).

Z kořene repozitáře:
  python3 -I tests/vyrez/test_kontrast.py skills/rodokmen/tools
  (Windows: python -I -X utf8 …)
Každý případ si postaví dočasný projekt s vymyšleným bledým snímkem (světle šedé písmo na šedém papíře),
zkopíruje do něj nástroj a pustí ho. Nic nestahuje; potřebuje ImageMagick (magick).
"""
import glob, os, shutil, subprocess, sys, tempfile

TOOLS = os.path.abspath(sys.argv[1])
PY = [sys.executable, "-I", "-X", "utf8"]
MAGICK = shutil.which("magick") or next(iter(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe")), None) or "convert"
VYSLEDKY = []


def ma(nazev, ok, detail=""):
    VYSLEDKY.append(ok)
    print(("OK  " if ok else "CHYBA ") + nazev + ("" if ok else f"\n    {detail}"))


def rozptyl(f):
    """Směrodatná odchylka jasu (0..1) – u vybledlého obrázku malá, po zvýšení kontrastu větší."""
    out = subprocess.run([MAGICK, f, "-colorspace", "gray", "-format", "%[fx:standard_deviation]", "info:"],
                         capture_output=True, text=True, check=True).stdout
    return float(out)


def projekt():
    tmp = tempfile.mkdtemp(prefix="vyrez_kontrast_")
    os.makedirs(os.path.join(tmp, "tools"))
    for n in ("vyrez.py", "overit.py"):
        shutil.copy(os.path.join(TOOLS, n), os.path.join(tmp, "tools", n))
    os.makedirs(os.path.join(tmp, "pracovni"))
    snimek = os.path.join(tmp, "pracovni", "bledy.jpg")
    # Bledý „zápis“: papír 85 % šedi, tahy písma 70 % – rozdíl jako u vybledlé matriky (bez fontů, jen čáry).
    tahy = []
    for y in range(150, 800, 90):
        for x in range(80, 1100, 60):
            tahy += ["-draw", f"line {x},{y} {x + 35},{y - 45}"]
    subprocess.run([MAGICK, "-size", "1200x900", "xc:gray85", "-stroke", "gray70", "-strokewidth", "5", *tahy, snimek],
                   check=True)
    return tmp, snimek


def spust(tmp, *args):
    return subprocess.run(PY + list(args), cwd=tmp, capture_output=True, text=True)


# vyrez.py bez přepínače: výřez zůstane bledý jako originál
tmp, snimek = projekt()
try:
    r = spust(tmp, "tools/vyrez.py", snimek, "zaklad", "0,0,1,1")
    zdroj = os.path.join(tmp, "zdroje", "zaklad.jpg")
    ma("vyrez.py bez --kontrast uloží výřez", r.returncode == 0 and os.path.exists(zdroj), r.stderr)
    s_zaklad = rozptyl(zdroj) if os.path.exists(zdroj) else 0

    # vyrez.py s přepínačem za oblastí: zdroje/ i vyrezy/ mají vyšší kontrast
    r = spust(tmp, "tools/vyrez.py", snimek, "kontrast", "0,0,1,1", "--kontrast")
    zdroj, web = (os.path.join(tmp, d, "kontrast.jpg") for d in ("zdroje", "vyrezy"))
    ok = r.returncode == 0 and os.path.exists(zdroj) and os.path.exists(web)
    ma("vyrez.py --kontrast uloží výřez", ok, r.stderr)
    if ok:
        ma("vyrez.py --kontrast zvýší kontrast ve zdroje/", rozptyl(zdroj) > 2 * s_zaklad,
           f"rozptyl {rozptyl(zdroj):.3f} vs. bez přepínače {s_zaklad:.3f}")
        ma("vyrez.py --kontrast zvýší kontrast i ve vyrezy/ (web)", rozptyl(web) > 2 * s_zaklad,
           f"rozptyl {rozptyl(web):.3f} vs. bez přepínače {s_zaklad:.3f}")

    # přepínač bez oblasti (celá stránka) a před ostatními argumenty
    r = spust(tmp, "tools/vyrez.py", "--kontrast", snimek, "cela")
    zdroj = os.path.join(tmp, "zdroje", "cela.jpg")
    ma("vyrez.py --kontrast bez oblasti (celá stránka)",
       r.returncode == 0 and os.path.exists(zdroj) and rozptyl(zdroj) > 2 * s_zaklad, r.stderr)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# overit.py: obě poloviny s vyšším kontrastem
tmp, snimek = projekt()
try:
    pre_z, pre_k = (os.path.join(tmp, "pracovni", "overeni", n) for n in ("z", "k"))
    r0 = spust(tmp, "tools/overit.py", snimek, "0,0,1,1", pre_z)
    r1 = spust(tmp, "tools/overit.py", snimek, "0,0,1,1", pre_k, "--kontrast")
    ok = r0.returncode == 0 and r1.returncode == 0 and all(os.path.exists(f"{p}_{i}.jpg") for p in (pre_z, pre_k) for i in (0, 1))
    ma("overit.py --kontrast uloží obě poloviny", ok, r0.stderr + r1.stderr)
    if ok:
        ma("overit.py --kontrast zvýší kontrast", all(rozptyl(f"{pre_k}_{i}.jpg") > 2 * rozptyl(f"{pre_z}_{i}.jpg") for i in (0, 1)))
    r2 = spust(tmp, "tools/overit.py", snimek, "0,0,1,1", pre_k + "v", "v", "--kontrast")
    ma("overit.py --kontrast spolu s dělením vodorovně (v)",
       r2.returncode == 0 and os.path.exists(pre_k + "v_1.jpg"), r2.stderr)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\n{sum(VYSLEDKY)} z {len(VYSLEDKY)} v pořádku")
sys.exit(0 if all(VYSLEDKY) else 1)
