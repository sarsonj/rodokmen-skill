"""Test režimu --sloupce v mapa_knihy.py (rejstřík po sloupcích v plném rozlišení).

Z kořene repozitáře:
  python3 -I tests/mapa/test_sloupce.py skills/rodokmen/tools
  (Windows: python -I -X utf8 …)
Pracuje jen se soubory (`soubory`), nic nestahuje; potřebuje ImageMagick (magick).
"""
import glob, os, shutil, subprocess, sys, tempfile

TOOLS = os.path.abspath(sys.argv[1])
PY = [sys.executable, "-I", "-X", "utf8"]
MAGICK = shutil.which("magick") or next(iter(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe")), None) or "convert"
VYSLEDKY = []


def ma(nazev, ok, detail=""):
    VYSLEDKY.append(ok)
    print(("OK  " if ok else "CHYBA ") + nazev + ("" if ok else f"\n    {detail}"))


def rozmer(f):
    w, h = subprocess.run([MAGICK, f, "-format", "%w %h", "info:"], capture_output=True, text=True, check=True).stdout.split()
    return int(w), int(h)


def spust(tmp, *args):
    return subprocess.run(PY + [os.path.join(TOOLS, "mapa_knihy.py"), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=tmp)


tmp = tempfile.mkdtemp(prefix="mapa_sloupce_")
try:
    snimek = os.path.join(tmp, "rejstrik_12.jpg")
    subprocess.run([MAGICK, "-size", "4000x3200", "xc:white", snimek], check=True)
    out = os.path.join(tmp, "out", "s.jpg")

    r = spust(tmp, "soubory", snimek, "--sloupce", "4", "-o", out)
    pruhy = sorted(glob.glob(os.path.join(tmp, "out", "s_sn12_s*.jpg")))
    ma("4 pruhy × 3 díly (3200 px > 1500 px)", r.returncode == 0 and len(pruhy) == 12, r.stderr + r.stdout)
    if pruhy:
        w, h = rozmer(pruhy[0])
        ma("plné rozlišení: pruh ~1000 px + překryv, díl ≤ 1500 px + popisek", 1000 <= w <= 1100 and h <= 1500 + 60,
           f"{w}x{h}")

    shutil.rmtree(os.path.join(tmp, "out"))
    r = spust(tmp, "soubory", snimek, "--sloupce", "0.3,0.55,0.8", "--vyrez", "0,0,0.5,0.4", "-o", out)
    pruhy = sorted(glob.glob(os.path.join(tmp, "out", "s_sn12_s*.jpg")))
    ma("vlastní hranice + výřez: 4 pruhy, jeden díl", r.returncode == 0 and len(pruhy) == 4, r.stderr + r.stdout)
    if pruhy:
        w, h = rozmer(pruhy[0])
        ma("první pruh = 30 % z 2000 px (+ překryv)", 600 <= w <= 650 and h <= 1280 + 60, f"{w}x{h}")

    r = spust(tmp, "soubory", snimek, "--sloupce", "0.5,0.3")
    ma("klesající hranice odmítne", r.returncode != 0 and "rostoucí" in (r.stderr + r.stdout), r.stderr)
    r = spust(tmp, "soubory", snimek, "--sloupce", "1")
    ma("1 pruh odmítne", r.returncode != 0, r.stderr)
    r = spust(tmp, "aron", "x", "1", "9", "--sloupce", "3")
    ma("víc než 4 snímky z archivu odmítne (nic nestahuje)", r.returncode != 0 and "nejvýš 4" in (r.stderr + r.stdout),
       r.stderr)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\n{sum(VYSLEDKY)}/{len(VYSLEDKY)} v pořádku")
sys.exit(0 if all(VYSLEDKY) else 1)
