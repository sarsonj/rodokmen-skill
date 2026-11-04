#!/usr/bin/env python3
"""Rámeček zvýraznění – které místo výřezu čteme (data/zvyrazneni.json).

Použití:
  ramecek.py <klic> x0,y0,x1,y1 [x0,y0,x1,y1 ...] [--pozn "poznámka"]
      POZOR: souřadnice jsou zlomky šířky a výšky VÝŘEZU vyrezy/<klic>.jpg (0..1), ne celé stránky.
      0,0,1,1 = celý výřez; 0,0.5,1,1 = jeho dolní polovina.
  ramecek.py <klic> --stranka x0,y0,x1,y1 [...] [--vyrez X0,Y0,X1,Y1] [--pozn "poznámka"]
      souřadnice jsou zlomky celé STRÁNKY (snímku), stejně jako u vyrez.py a overit.py; nástroj je přepočítá
      na výřez podle oblasti, kterou si zapamatoval vyrez.py (pracovni/vyrezy_oblasti.json). Chybí-li tam,
      zadej oblast výřezu sám: --vyrez se stejnými čísly, jaká dostal vyrez.py.
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


def volba(args, name):
    """Vyjme z args volbu s hodnotou (--pozn "text") a vrátí hodnotu, nebo None."""
    if name not in args:
        return None
    i = args.index(name)
    if i + 1 >= len(args):
        sys.exit(f"{name} potřebuje hodnotu.")
    hodnota = args[i + 1]
    del args[i:i + 2]
    return hodnota


def ctyri(text, co):
    try:
        b = [float(v) for v in text.split(",")]
    except ValueError:
        b = []
    if len(b) != 4 or not (0 <= b[0] < b[2] <= 1 and 0 <= b[1] < b[3] <= 1):
        sys.exit(f"Špatný {co} „{text}“: musí být x0,y0,x1,y1 jako zlomky 0..1 (x0<x1, y0<y1), ne pixely – "
                 "např. 0.1,0.25,0.9,0.6.")
    return b


def zapamatovana_oblast(key):
    path = os.path.join(ROOT, "pracovni", "vyrezy_oblasti.json")
    try:
        return json.load(open(path, encoding="utf-8"))[key]
    except (OSError, ValueError, KeyError, TypeError):
        sys.exit(f"Nevím, z které části stránky je výřez {key} (vyrez.py ho dělal před verzí, která si to pamatuje). "
                 "Zadej ji: --vyrez X0,Y0,X1,Y1 se stejnými čísly, jaká dostal vyrez.py – nebo výřez udělej znovu.")


def na_vyrez(b, oblast):
    """Rámeček v zlomcích stránky → zlomky výřezu (oříznutý na výřez)."""
    X0, Y0, X1, Y1 = oblast
    w, h = X1 - X0, Y1 - Y0
    r = [(b[0] - X0) / w, (b[1] - Y0) / h, (b[2] - X0) / w, (b[3] - Y0) / h]
    r = [min(1.0, max(0.0, v)) for v in r]
    if not (r[0] < r[2] and r[1] < r[3]):
        sys.exit(f"Rámeček {','.join(map(str, b))} leží celý mimo výřez {','.join(map(str, oblast))} (souřadnice stránky).")
    return r


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    key = sys.argv[1]
    magick()   # bez ImageMagicku skončit dřív, než se rámeček zapíše
    data = json.load(open(PATH, encoding="utf-8")) if os.path.exists(PATH) else {}
    if sys.argv[2] == "--nahled":
        print(preview(key, data.get(key, {}).get("boxes", [])))
        return
    args = sys.argv[2:]
    note = volba(args, "--pozn") or ""
    vyrez = volba(args, "--vyrez")
    stranka = "--stranka" in args
    args = [a for a in args if a != "--stranka"]
    if vyrez and not stranka:
        sys.exit("--vyrez má smysl jen s --stranka (souřadnice na celé stránce).")
    if not args:
        sys.exit(__doc__)
    boxes = [ctyri(a, "rámeček") for a in args]
    if stranka:
        oblast = ctyri(vyrez, "--vyrez") if vyrez else zapamatovana_oblast(key)
        boxes = [na_vyrez(b, oblast) for b in boxes]
    boxes = [[round(v, 3) for v in b] for b in boxes]
    data[key] = dict(boxes=boxes, status="ok", note=note)
    json.dump(data, open(PATH, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("zapsáno; zkontrolujte:", preview(key, boxes))
    if not stranka:
        print("(souřadnice byly brány jako zlomky výřezu vyrezy/" + key + ".jpg; měl-li jsi je na celé stránce, "
              "zopakuj příkaz s --stranka)")


if __name__ == "__main__":
    main()
