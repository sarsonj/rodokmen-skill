#!/usr/bin/env python3
"""Ověření čtení (např. po pomocníkovi): výřez zápisu rozdělený na dvě poloviny, každá nejvýš 1900 px.

Použití:
  overit.py <snímek.jpg> x0,y0,x1,y1 <prefix> [v] [--vylepsit]
      x0..y1  oblast zápisu jako zlomky šířky a výšky snímku (0..1), ne pixely
      v       dělit vodorovně (horní a dolní polovina); bez něj levá a pravá
      --vylepsit  šedá, vyrovnaný kontrast a doostření – pro vybledlé a tmavé snímky (jen ke čtení)
Uloží <prefix>_0.jpg a <prefix>_1.jpg; poloviny se překrývají o 8 % oblasti, aby slovo na hraně nebylo rozseknuté.
Potřebuje ImageMagick (příkaz magick).
"""
import glob, os, shutil, subprocess, sys
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

PREKRYV = 0.08   # podíl oblasti, o který se poloviny překrývají


def magick():
    """Cesta k ImageMagicku; když chybí, skončí hned srozumitelnou hláškou."""
    m = (shutil.which("magick") or next(iter(sorted(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe"))), None)
         or (os.name != "nt" and shutil.which("convert")))   # ImageMagick 6 bez magick; na Windows je convert.exe jiný program
    if not m:
        sys.exit("Chybí ImageMagick (příkaz magick). Nainstaluj ho (macOS: brew install imagemagick, "
                 "Windows: winget install ImageMagick.ImageMagick a restart Claude Code) a spusť nástroj znovu.")
    return m


def vylepseni(m):
    """Úprava vybledlého snímku (#37). -clahe (místní vyrovnání kontrastu) umí jen novější ImageMagick – bez něj
    zbytek úprav."""
    clahe = subprocess.run([m, "-size", "8x8", "xc:gray", "-clahe", "25x25%+128+4", "null:"],
                           capture_output=True).returncode == 0
    return (["-colorspace", "Gray"] + (["-clahe", "25x25%+128+4"] if clahe else [])
            + ["-contrast-stretch", "1%x50%", "-level", "5%,70%", "-unsharp", "0x1.2+1.2+0.02"])


def main():
    args = [a for a in sys.argv[1:] if a != "--vylepsit"]
    if len(args) < 3:
        sys.exit(__doc__)
    f, box, pre = args[:3]
    vodorovne = len(args) > 3 and args[3] == "v"
    m = magick()
    try:
        x0, y0, x1, y1 = map(float, box.split(","))
    except ValueError:
        sys.exit(f"Oblast {box} má být x0,y0,x1,y1 – čtyři zlomky 0..1 oddělené čárkou.")
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        sys.exit(f"Oblast {box} musí být zlomky 0..1 (x0 < x1, y0 < y1), ne pixely.")
    W, H = map(int, subprocess.run([m, f + "[0]", "-format", "%w %h", "info:"],
                                   capture_output=True, text=True, check=True).stdout.split())
    if vodorovne:
        ym, p = (y0 + y1) / 2, PREKRYV * (y1 - y0) / 2
        parts = [(x0, y0, x1, ym + p), (x0, ym - p, x1, y1)]
    else:
        xm, p = (x0 + x1) / 2, PREKRYV * (x1 - x0) / 2
        parts = [(x0, y0, xm + p, y1), (xm - p, y0, x1, y1)]
    uprava = vylepseni(m) if "--vylepsit" in sys.argv else []
    os.makedirs(os.path.dirname(os.path.abspath(pre)), exist_ok=True)   # výstupní složka (pracovni/overeni/…) nemusí existovat
    for i, (a, b, c, d) in enumerate(parts):
        o = f"{pre}_{i}.jpg"
        crop = "%dx%d+%d+%d" % ((c - a) * W, (d - b) * H, a * W, b * H)
        # do čtverce 1900×1900: malý výřez se zvětší ke čtení, dlouhý úzký pruh se nenafoukne na 1900×7600 (#37)
        subprocess.run([m, f, "-crop", crop, "+repage"] + uprava + ["-resize", "1900x1900", o], check=True)
        print(o)


if __name__ == "__main__":
    main()
