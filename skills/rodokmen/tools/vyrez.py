#!/usr/bin/env python3
"""Výřez zápisu ze staženého snímku stránky (z jakéhokoli portálu).

Použití:
  vyrez.py <snimek.jpg> <klic> [x0,y0,x1,y1] [--vylepsit]
      x0..y1 = oblast zápisu jako zlomky šířky a výšky stránky (0..1); bez nich se bere celá stránka.
      --vylepsit = vybledlý nebo tmavý snímek: šedá, vyrovnaný kontrast, doostření (výřez na webu pak bude šedý;
      jen když originál nejde přečíst – na zkoušku nejdřív overit.py … --vylepsit).
      Uloží zdroje/<klic>.jpg (plné rozlišení) a vyrezy/<klic>.jpg (zmenšeno na max. 1800 px pro web).
      Oblast si zapamatuje v pracovni/vyrezy_oblasti.json – `ramecek.py <klic> --stranka …` pak bere
      souřadnice čteného místa na celé stránce (stejně jako tady a v overit.py) a sám je přepočítá na výřez.

Výřez dělejte velkoryse: celý zápis včetně hlavičky sloupců, okrajových poznámek a podpisů.
Potřebuje ImageMagick (příkaz `magick`).
"""
import glob, json, os, shutil, subprocess, sys
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
                 "Windows: winget install ImageMagick.ImageMagick a restart Claude Code) a spusť nástroj znovu.")
    return m


def vylepseni(m):
    """Úprava vybledlého snímku (#37), stejná jako v overit.py. -clahe umí jen novější ImageMagick – bez něj zbytek."""
    clahe = subprocess.run([m, "-size", "8x8", "xc:gray", "-clahe", "25x25%+128+4", "null:"],
                           capture_output=True).returncode == 0
    return (["-colorspace", "Gray"] + (["-clahe", "25x25%+128+4"] if clahe else [])
            + ["-contrast-stretch", "1%x50%", "-level", "5%,70%", "-unsharp", "0x1.2+1.2+0.02"])


def main():
    vylepsit = "--vylepsit" in sys.argv
    sys.argv = [a for a in sys.argv if a != "--vylepsit"]
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, key = sys.argv[1], sys.argv[2]
    MAGICK = magick()
    full = os.path.join(ROOT, "zdroje", key + ".jpg")
    small = os.path.join(ROOT, "vyrezy", key + ".jpg")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    os.makedirs(os.path.dirname(small), exist_ok=True)
    oblast = [0, 0, 1, 1]
    cmd = [MAGICK, src, "-auto-orient"]   # fotky z mobilu: otočit podle EXIF (EXIF i s GPS pak smaže +profile, barevný profil ICC zůstane)
    if len(sys.argv) > 3:
        x0, y0, x1, y1 = (float(v) for v in sys.argv[3].split(","))
        if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):   # pixely by ImageMagick jen varoval a uložil celou stránku
            sys.exit(f"Oblast {sys.argv[3]} musí být zlomky 0..1 (x0 < x1, y0 < y1), ne pixely – "
                     "např. 0.1,0.25,0.9,0.6 = od 10 % do 90 % šířky a od 25 % do 60 % výšky.")
        w, h = (int(v) for v in subprocess.run([MAGICK, src + "[0]", "-auto-orient", "-format", "%w %h", "info:"],
                                                capture_output=True, text=True, check=True).stdout.split())
        cmd += ["-crop", f"{round((x1 - x0) * w)}x{round((y1 - y0) * h)}+{round(x0 * w)}+{round(y0 * h)}", "+repage"]
        oblast = [x0, y0, x1, y1]
    if vylepsit:
        cmd += vylepseni(MAGICK)
    subprocess.run(cmd + ["+profile", "!icc,*", "+set", "comment", "-quality", "90", full], check=True)
    subprocess.run([MAGICK, full, "-resize", "1800x1800>", "-quality", "85", small], check=True)
    zapamatuj_oblast(key, oblast)
    print("uloženo:", full, "a", small)


def zapamatuj_oblast(key, oblast):
    """Oblast výřezu na stránce pro `ramecek.py --stranka` (pracovni/, na web nejde)."""
    path = os.path.join(ROOT, "pracovni", "vyrezy_oblasti.json")
    try:
        d = json.load(open(path, encoding="utf-8"))
        d = d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        d = {}
    d[key] = oblast
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main()
