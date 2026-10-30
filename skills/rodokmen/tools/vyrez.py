#!/usr/bin/env python3
"""Výřez zápisu ze staženého snímku stránky (z jakéhokoli portálu).

Použití:
  vyrez.py <snimek.jpg> <klic> [x0,y0,x1,y1]
      x0..y1 = oblast zápisu jako zlomky šířky a výšky stránky (0..1); bez nich se bere celá stránka.
      Uloží zdroje/<klic>.jpg (plné rozlišení) a vyrezy/<klic>.jpg (zmenšeno na max. 1800 px pro web).

Výřez dělejte velkoryse: celý zápis včetně hlavičky sloupců, okrajových poznámek a podpisů.
Potřebuje ImageMagick (příkaz `magick`).
"""
import glob, os, shutil, subprocess, sys
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def magick():
    """Cesta k ImageMagicku; když chybí, skončí hned (před stahováním) srozumitelnou hláškou."""
    m = (shutil.which("magick") or next(iter(sorted(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe"))), None)
         or (os.name != "nt" and shutil.which("convert")))   # ImageMagick 6 bez magick; na Windows je convert.exe jiný program
    if not m:
        sys.exit("Chybí ImageMagick (příkaz magick). Nainstaluj ho (macOS: brew install imagemagick, "
                 "Windows: winget install ImageMagick.ImageMagick a restart Claude Code / Codexu / OMP) a spusť nástroj znovu.")
    return m


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, key = sys.argv[1], sys.argv[2]
    MAGICK = magick()
    full = os.path.join(ROOT, "zdroje", key + ".jpg")
    small = os.path.join(ROOT, "vyrezy", key + ".jpg")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    os.makedirs(os.path.dirname(small), exist_ok=True)
    cmd = [MAGICK, src, "-auto-orient"]   # fotky z mobilu: otočit podle EXIF (EXIF i s GPS pak smaže +profile, barevný profil ICC zůstane)
    if len(sys.argv) > 3:
        x0, y0, x1, y1 = (float(v) for v in sys.argv[3].split(","))
        if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):   # pixely by ImageMagick jen varoval a uložil celou stránku
            sys.exit(f"Oblast {sys.argv[3]} musí být zlomky 0..1 (x0 < x1, y0 < y1), ne pixely – "
                     "např. 0.1,0.25,0.9,0.6 = od 10 % do 90 % šířky a od 25 % do 60 % výšky.")
        w, h = (int(v) for v in subprocess.run([MAGICK, src + "[0]", "-auto-orient", "-format", "%w %h", "info:"],
                                                capture_output=True, text=True, check=True).stdout.split())
        cmd += ["-crop", f"{round((x1 - x0) * w)}x{round((y1 - y0) * h)}+{round(x0 * w)}+{round(y0 * h)}", "+repage"]
    subprocess.run(cmd + ["+profile", "!icc,*", "+set", "comment", "-quality", "90", full], check=True)
    subprocess.run([MAGICK, full, "-resize", "1800x1800>", "-quality", "85", small], check=True)
    print("uloženo:", full, "a", small)


if __name__ == "__main__":
    main()
