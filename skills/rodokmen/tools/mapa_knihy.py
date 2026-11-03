#!/usr/bin/env python3
"""Mapa knihy a montáž sloupců – rychlá orientace v knize bez stahování celých snímků (reference/matriky.md,
Knihy řazené po vsích).

Použití (z kořene projektu):
  mapa_knihy.py <archiv> <kniha> <od> <do> [krok] [volby]
    archiv  = aron (kniha = apu_id), pf (Porta fontium, kniha jako u portafontium.py), ahmp (kniha = XID)
    od, do  = rozsah snímků, krok = každý kolikátý snímek (výchozí 10)
  mapa_knihy.py soubory <obrázek> [<obrázek> …] [volby]   -> totéž ze snímků, které už máš (i snímky obrazovky)

Volby:
  --vyrez x0,y0,x1,y1  část snímku (zlomky 0–1); výchozí 0,0,1,0.15 = horní pruh se jménem vsi a rokem
  --vedle              výřezy vedle sebe (sloupec se jmény z několika snímků), jinak pod sebou (mapa knihy)
  --ostre              vyšší rozlišení (sloupec se jmény, drobné písmo); výchozí je náhled
  -o <vystup.jpg>      výchozí pracovni/mapa_<archiv>_<kniha>_<od>-<do>.jpg

Každý výřez má číslo snímku. Mapa knihy: rok a ves v záhlaví ukážou oddíly a pořadí let, pak čti v plném rozlišení jen
oddíl hledané vsi. Montáž sloupců: --vedle, krok 1, výřez sloupce se jmény (aspoň 35 % šířky strany), 4–8 snímků.
Velkou mapu nástroj rozdělí do víc obrázků (po 15 výřezech pod sebou, po 6 vedle sebe). Stahuje přes nástroje archivu
a brzdu (tools/slusne.py) – stahuj jen rozsah, který potřebuješ.
"""
import glob, os, re, shutil, subprocess, sys, tempfile
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
NA_OBRAZEK = 15   # výřezů pod sebou na jeden obrázek (víc už Claude nepřečte)
VEDLE = 6         # výřezů vedle sebe na jeden obrázek


def magick():
    m = (shutil.which("magick") or next(iter(sorted(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe"))), None)
         or (os.name != "nt" and shutil.which("convert")))   # ImageMagick 6 bez magick; na Windows je convert.exe jiný program
    if not m:
        sys.exit("Chybí ImageMagick (příkaz magick). Nainstaluj ho (macOS: brew install imagemagick, "
                 "Windows: winget install ImageMagick.ImageMagick a restart Claude Code) a spusť nástroj znovu.")
    return m


def pismo():
    """Soubor s písmem pro čísla snímků (ImageMagick z Homebrew výchozí písmo nemá); None = popisky bez písma nejdou."""
    for vzor in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf",
                 "/System/Library/Fonts/Helvetica.ttc", r"C:\Windows\Fonts\arial.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/**/DejaVuSans.ttf",
                 "/usr/share/fonts/**/*.ttf"):
        f = next(iter(sorted(glob.glob(vzor, recursive=True))), None)
        if f:
            return f
    return None


PISMO = pismo()


def stahni(archiv, kniha, n, vyrez, ostre, out):
    """Výřez snímku n nástrojem archivu (přes jeho brzdu). Vrací True, když obrázek vznikl."""
    v = ",".join(f"{x:g}" for x in vyrez)
    if archiv == "aron":
        cmd = ["aron_img.py", kniha, str(n), "1" if ostre else "2", out, v]
    elif archiv == "pf":
        cmd = ["portafontium.py", "snimek", kniha, str(n), out, v] + ([] if ostre else ["nahled"])
    elif archiv == "ahmp":
        cmd = ["ahmp_scan.py", kniha, str(n), out, "1" if ostre else "2", v]
    else:
        sys.exit(f"neznámý archiv „{archiv}“ – aron, pf, ahmp nebo soubory")
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(TOOLS, cmd[0]), *cmd[1:]],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode == 3:   # brzda: archiv nás zastavil – nic dalšího nestahovat
        sys.stderr.write(r.stderr)
        sys.exit(3)
    if r.returncode or not os.path.exists(out):
        chyba = (r.stderr.strip().splitlines() or r.stdout.strip().splitlines() or ["?"])[-1]
        print(f"  snímek {n}: nepodařilo se ({chyba})", file=sys.stderr)
        return False
    return True


def oznac(M, src, n, vyrez, vedle, out):
    """Výřez (u souborů ořízne) a připíše číslo snímku: pod sebou vlevo, vedle sebe nahoře."""
    args = [M, src + "[0]"]
    if vyrez:
        r = subprocess.run([M, src + "[0]", "-format", "%w %h", "info:"], capture_output=True, text=True)
        try:
            W, H = map(int, r.stdout.split())
        except ValueError:
            print(f"  {src}: není obrázek", file=sys.stderr)
            return False
        x0, y0, x1, y1 = vyrez
        args += ["-crop", f"{round((x1 - x0) * W)}x{round((y1 - y0) * H)}+{round(x0 * W)}+{round(y0 * H)}", "+repage"]
    args += ["-resize", "1600x>", "-background", "white", "-fill", "#B00000", "-pointsize", "40"]
    args += ["-font", PISMO] if PISMO else []
    if not PISMO:   # bez písma aspoň okraj; pořadí výřezů vypíše main()
        args += ["-gravity", "West", "-splice", "8x0"]
    elif vedle:
        args += ["-gravity", "North", "-splice", "0x56", "-annotate", "+0+6", f"sn. {n}"]
    else:
        args += ["-gravity", "West", "-splice", "170x0", "-annotate", "+12+0", f"sn. {n}"]
    args += ["-bordercolor", "#888", "-border", "2", out]
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode:
        print(f"  snímek {n}: ImageMagick selhal ({(r.stderr.strip().splitlines() or ['?'])[-1]})", file=sys.stderr)
    return r.returncode == 0


def main(a):
    if not a or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    vyrez, vedle, ostre, out, rest = None, "--vedle" in a, "--ostre" in a, None, []
    i = 0
    while i < len(a):
        if a[i] == "--vyrez" and i + 1 < len(a):
            try:
                vyrez = tuple(float(v) for v in a[i + 1].split(","))
            except ValueError:
                vyrez = ()
            if len(vyrez) != 4 or not (0 <= vyrez[0] < vyrez[2] <= 1 and 0 <= vyrez[1] < vyrez[3] <= 1):
                sys.exit(f"--vyrez „{a[i + 1]}“ zadej jako x0,y0,x1,y1 (zlomky 0–1, x0 < x1, y0 < y1), ne pixely")
            i += 2
        elif a[i] == "-o" and i + 1 < len(a):
            out, i = a[i + 1], i + 2
        elif a[i] in ("--vedle", "--ostre"):
            i += 1
        else:
            rest.append(a[i]); i += 1
    M = magick()
    tmp = tempfile.mkdtemp(prefix="mapa_")
    try:
        dily, cisla = [], []
        if rest[0] == "soubory":
            soubory = rest[1:]
            if not soubory:
                sys.exit("mapa_knihy.py soubory <obrázek> [<obrázek> …]")
            vyrez = vyrez or (0, 0, 1, 0.15)
            for j, f in enumerate(soubory):
                n = (re.findall(r"\d+", os.path.basename(f)) or [str(j + 1)])[-1]
                p = os.path.join(tmp, f"d{j:04d}.png")
                if oznac(M, f, n, vyrez, vedle, p):
                    dily.append(p); cisla.append(n)
            nazev = "soubory"
        else:
            if len(rest) < 4:
                sys.exit(__doc__)
            archiv, kniha = rest[0], rest[1]
            try:
                od, do = int(rest[2]), int(rest[3])
                krok = int(rest[4]) if len(rest) > 4 else 10
            except ValueError:
                sys.exit("od, do a krok jsou čísla snímků")
            if od > do or krok < 1:
                sys.exit("rozsah: od ≤ do, krok aspoň 1")
            snimky = list(range(od, do + 1, krok))
            if len(snimky) > 60:
                sys.exit(f"{len(snimky)} snímků je moc – zvětši krok nebo zuž rozsah (šetři archiv)")
            vyrez = vyrez or (0, 0, 1, 0.15)
            print(f"stahuji {len(snimky)} výřezů ({archiv} {kniha}, snímky {od}–{do} po {krok}) …", file=sys.stderr)
            for n in snimky:
                s = os.path.join(tmp, f"s{n:05d}.jpg")
                p = os.path.join(tmp, f"d{n:05d}.png")
                if stahni(archiv, kniha, n, vyrez, ostre, s) and oznac(M, s, n, None, vedle, p):
                    dily.append(p); cisla.append(n)
            nazev = f"{archiv}_{re.sub(r'[^A-Za-z0-9-]', '', kniha)[:24]}_{od}-{do}"
        if not dily:
            sys.exit("žádný výřez nevznikl")
        out = out or os.path.join(ROOT, "pracovni", f"mapa_{nazev}.jpg")
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        po = VEDLE if vedle else NA_OBRAZEK
        skupiny = [(dily[k:k + po], cisla[k:k + po]) for k in range(0, len(dily), po)]
        koren, pripona = os.path.splitext(out)
        for k, (sk, cs) in enumerate(skupiny):
            cil = out if len(skupiny) == 1 else f"{koren}_{k + 1}{pripona or '.jpg'}"
            subprocess.run([M, *sk, "-background", "white", "+append" if vedle else "-append", "-quality", "85", cil], check=True)
            print(cil, "– snímky", ", ".join(map(str, cs)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1:])
