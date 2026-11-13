#!/usr/bin/env python3
"""Rámeček zvýraznění – které místo výřezu čteme (data/zvyrazneni.json).

Použití:
  ramecek.py <klic> x0,y0,x1,y1 [x0,y0,x1,y1 ...] [--pozn "poznámka"]
      souřadnice jsou zlomky šířky a výšky obrázku vyrezy/<klic>.jpg (0..1)
      Zapíše rámeček a vytvoří kontrolní obrázek pracovni/ramecek_<klic>.jpg – VŽDY si ho prohlédněte,
      jestli rámeček opravdu obepíná celý čtený zápis (jméno, data, rodiče, poznámky na okraji).
  ramecek.py <klic> --nahled      jen znovu vytvoří kontrolní obrázek
"""
import glob, json, os, shutil, subprocess, sys
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "zvyrazneni.json")


def magick():
    """Cesta k ImageMagicku; když chybí, skončí hned (před stahováním) srozumitelnou hláškou."""
    m = (shutil.which("magick") or next(iter(sorted(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe"))), None)
         or (os.name != "nt" and shutil.which("convert")))   # ImageMagick 6 bez magick; na Windows je convert.exe jiný program
    if not m:
        sys.exit("Chybí ImageMagick (příkaz magick). Nainstaluj ho (macOS: brew install imagemagick, "
                 "Windows: winget install ImageMagick.ImageMagick a restart Claude Code) a spusť nástroj znovu.")
    return m


def preview(key, boxes):
    MAGICK = magick()
    src = os.path.join(ROOT, "vyrezy", key + ".jpg")
    out = os.path.join(ROOT, "pracovni", f"ramecek_{key}.jpg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    w, h = (int(v) for v in subprocess.run([MAGICK, src + "[0]", "-format", "%w %h", "info:"],
                                            capture_output=True, text=True, check=True).stdout.split())
    cmd = [MAGICK, src, "-fill", "none", "-stroke", "#d7302a", "-strokewidth", str(max(3, w // 400))]
    for x0, y0, x1, y1 in boxes:
        cmd += ["-draw", f"rectangle {x0 * w:.0f},{y0 * h:.0f},{x1 * w:.0f},{y1 * h:.0f}"]
    subprocess.run(cmd + [out], check=True)
    return out


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    key = sys.argv[1]
    magick()   # bez ImageMagicku skončit dřív, než se rámeček zapíše
    if not os.path.exists(os.path.join(ROOT, "vyrezy", key + ".jpg")):   # rámeček se kreslí do výřezu – nejdřív výřez
        sys.exit(f"Chybí výřez vyrezy/{key}.jpg – nejdřív ho udělej (tools/vyrez.py), pak rámeček. Nic jsem nezapsal.")
    data = json.load(open(PATH, encoding="utf-8-sig")) if os.path.exists(PATH) else {}
    if sys.argv[2] == "--nahled":
        print(preview(key, data.get(key, {}).get("boxes", [])))
        return
    args, note = sys.argv[2:], ""
    if "--pozn" in args:
        i = args.index("--pozn")
        if i + 1 >= len(args):
            sys.exit('--pozn potřebuje text, např. --pozn "okraj vpravo nečitelný"')
        note = args[i + 1]
        args = args[:i] + args[i + 2:]
    try:
        boxes = [[round(float(v), 3) for v in a.split(",")] for a in args]
    except ValueError:
        sys.exit(f"Rámečky musí být čísla x0,y0,x1,y1 (zlomky 0..1, desetinná tečka), ne {' '.join(args)}")
    if not boxes:
        sys.exit(__doc__)
    for b in boxes:
        if len(b) != 4 or not (0 <= b[0] < b[2] <= 1 and 0 <= b[1] < b[3] <= 1):
            sys.exit(f"Špatný rámeček {b}: musí být x0,y0,x1,y1 v rozsahu 0..1 a x0<x1, y0<y1")
    data[key] = dict(boxes=boxes, status="ok", note=note)
    json.dump(data, open(PATH, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("zapsáno; zkontrolujte:", preview(key, boxes))


if __name__ == "__main__":
    main()
