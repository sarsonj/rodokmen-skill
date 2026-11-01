#!/usr/bin/env python3
"""Stažení snímku matriky z portálu ARON (SOA Zámrsk, aron.vychodoceskearchivy.cz).

Použití:
  aron_img.py <apu_id> <snimek> [uroven] [vystup.jpg] [x0,y0,x1,y1]
      uroven: 0 = plné rozlišení, 1 = polovina (výchozí), 2 = čtvrtina
      x0,y0,x1,y1: jen výřez (zlomky 0..1 celé stránky) – stahují se jen potřebné dlaždice
  aron_img.py <apu_id> info          -> název svazku a počet snímků
  aron_img.py <apu_id> link <n>      -> trvalý odkaz na snímek n v prohlížeči ARON (pole "odkaz" v zaznamy.json)
  aron_img.py <apu_id> svazek        -> zapíše svazek do data/svazky.json (klíč = prvních 8 znaků apu_id)
  aron_img.py odkazy [--opravit]     -> najde v data/ odkazy z dřívějšího `link`, které otevřou knihu na prvním
                                        snímku (id souboru PUBLISHED); s --opravit je přepíše na správný snímek (TILE)

Popis svazků se ukládá do pracovni/.cache_aron/<apu_id>.json (ve složce projektu).
"""
import glob, json, math, os, re, shutil, subprocess, sys, tempfile, time, urllib.request
import concurrent.futures as cf
import xml.etree.ElementTree as ET
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

API = "https://aron.vychodoceskearchivy.cz/api/aron"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "pracovni", ".cache_aron")


def magick():
    """Cesta k ImageMagicku; když chybí, skončí hned (před stahováním) srozumitelnou hláškou."""
    m = (shutil.which("magick") or next(iter(sorted(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe"))), None)
         or (os.name != "nt" and shutil.which("convert")))   # ImageMagick 6 bez magick; na Windows je convert.exe jiný program
    if not m:
        sys.exit("Chybí ImageMagick (příkaz magick). Nainstaluj ho (macOS: brew install imagemagick, "
                 "Windows: winget install ImageMagick.ImageMagick a restart Claude Code) a spusť nástroj znovu.")
    return m


def get(url, binary=False, tries=4):
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                data = r.read()
            return data if binary else data.decode("utf-8")
        except OSError:
            if attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def volume(apu_id):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, apu_id + ".json")
    if not os.path.exists(path):
        data = get(f"{API}/apu/{apu_id}")
        tmp = f"{path}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(data)
        os.replace(tmp, path)  # atomic, safe when several processes fetch the same volume
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def tiles_by_order(vol):
    out = {}
    for dao in vol.get("digitalObjects", []):
        for f in dao["files"]:
            if f["type"] == "TILE":
                out[f["order"]] = f["referencedFile"]
    return out


def fetch_image(dzi_url, level_offset=1, out="page.jpg", crop=None):
    MAGICK = magick()
    dzi = ET.fromstring(get(dzi_url))
    ns = {"d": "http://schemas.microsoft.com/deepzoom/2009"}
    ts = int(dzi.get("TileSize"))
    ov = int(dzi.get("Overlap"))
    size = dzi.find("d:Size", ns)
    W, H = int(size.get("Width")), int(size.get("Height"))
    maxlevel = math.ceil(math.log2(max(W, H)))
    level = maxlevel - level_offset
    scale = 2 ** level_offset
    w, h = math.ceil(W / scale), math.ceil(H / scale)
    cols, rows = math.ceil(w / ts), math.ceil(h / ts)
    c0, r0, c1, r1 = 0, 0, cols - 1, rows - 1
    if crop:
        x0, y0, x1, y1 = crop
        c0, c1 = int(x0 * w // ts), min(cols - 1, int(x1 * w // ts))
        r0, r1 = int(y0 * h // ts), min(rows - 1, int(y1 * h // ts))
    base = dzi_url[: -len(".dzi")] + "_files"
    tmp = tempfile.mkdtemp(prefix="aron_")
    try:
        jobs = []
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                jobs.append((c, r, f"{base}/{level}/{c}_{r}.jpg", os.path.join(tmp, f"{c}_{r}.jpg")))

        def dl(job):
            c, r, url, p = job
            with open(p, "wb") as f:
                f.write(get(url, binary=True))
            return job

        with cf.ThreadPoolExecutor(8) as ex:
            list(ex.map(dl, jobs))
        # a tile with c > 0 (r > 0) carries `ov` extra pixels on its left (top) edge;
        # crop every tile to its own ts x ts cell, then append rows and columns
        # po řádcích: jeden příkaz na celou stránku by na Windows přesáhl limit délky příkazové řádky (32 767 znaků)
        row_files = []
        for r in range(r0, r1 + 1):
            args = [MAGICK]
            for c in range(c0, c1 + 1):
                p = os.path.join(tmp, f"{c}_{r}.jpg")
                cw, ch = min(ts, w - c * ts), min(ts, h - r * ts)
                ox, oy = (ov if c > 0 else 0), (ov if r > 0 else 0)
                args += ["(", p, "-crop", f"{cw}x{ch}+{ox}+{oy}", "+repage", ")"]
            row_files.append(os.path.join(tmp, f"row_{r}.miff"))   # MIFF zachová vlastnosti JPEG (podvzorkování barev)
            subprocess.run(args + ["+append", row_files[-1]], check=True)
        subprocess.run([MAGICK, *row_files, "-append", "-quality", "88", out], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)   # uklidit i při chybě stahování nebo magick
    return out, (W, H)


ODKAZ = re.compile(r"aron\.vychodoceskearchivy\.cz/apu/([0-9a-f-]{36})/dao/([0-9a-f-]{36})/file/([0-9a-f-]{36})")


def oprav_odkazy(opravit):
    """Odkazy na snímek v data/*.json a data/*.md s id souboru PUBLISHED (dřívější `link`) otevřou knihu na prvním
    snímku. Nahradí to id za id souboru TILE téhož snímku; zbytek souborů zůstane beze změny."""
    soubory = sorted(glob.glob(os.path.join(ROOT, "data", "*.json")) + glob.glob(os.path.join(ROOT, "data", "*.md")))
    texty = {}
    for p in soubory:
        with open(p, encoding="utf-8", newline="") as f:   # newline="": konce řádků zůstanou, jak jsou
            texty[p] = f.read()
    nahrady, nezname, dobre = {}, [], 0
    for apu, dao_id, file_id in sorted({m.groups() for t in texty.values() for m in ODKAZ.finditer(t)}):
        dao = next((d for d in volume(apu).get("digitalObjects", []) if d["id"] == dao_id), {})
        f = next((f for f in dao.get("files", []) if f["id"] == file_id), None)
        tile = f and next((t for t in dao["files"] if t["type"] == "TILE" and t["order"] == f["order"]), None)
        if f and f["type"] == "TILE":
            dobre += 1
        elif tile:
            nahrady[file_id] = tile["id"]
        else:
            nezname.append(f"…/apu/{apu}/dao/{dao_id}/file/{file_id}")
    zmenene = {}
    for p, t in texty.items():
        nove = t
        for stare, tile_id in nahrady.items():
            nove = nove.replace(stare, tile_id)
        if nove != t:
            zmenene[p] = (nove, sum(t.count(stare) for stare in nahrady))
    print(f"odkazy na snímky ARON: {dobre + len(nahrady) + len(nezname)} různých, správně {dobre}, "
          f"na první snímek {len(nahrady)}" + (f", nenalezeno ve svazku {len(nezname)}" if nezname else ""))
    for p, (_, kolik) in zmenene.items():
        print(f"  {os.path.relpath(p, ROOT)}: {kolik}× {'opraveno' if opravit else 'k opravě'}")
    for o in nezname:
        print("  nenalezeno:", o)
    if opravit:
        for p, (nove, _) in zmenene.items():
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(nove)
        if zmenene:
            print("Hotovo. Web: cd web && npm run data && npm run build")
    elif nahrady:
        print("Opravíš je: python3 -I tools/aron_img.py odkazy --opravit")


if __name__ == "__main__":
    if sys.argv[1:2] == ["odkazy"]:
        oprav_odkazy("--opravit" in sys.argv[2:])
        sys.exit(0)
    apu = sys.argv[1]
    vol = volume(apu)
    tiles = tiles_by_order(vol)
    if sys.argv[2] == "info":
        print(vol["name"], "|", vol.get("description"))
        print("scans:", len(tiles))
        sys.exit(0)
    if sys.argv[2] == "svazek":
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, "data", "svazky.json")
        sv = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
        fond, _, rest = vol["name"].partition(": ")
        sv[apu[:8]] = dict(archiv=fond if rest else "", portal="ARON", svazek=rest or vol["name"],
                           popis=(vol.get("description") or "")[:300], snimku=len(tiles),
                           url=f"https://aron.vychodoceskearchivy.cz/apu/{vol['id']}")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(sv, f, ensure_ascii=False, indent=1)
        print(apu[:8], "->", sv[apu[:8]]["svazek"])
        sys.exit(0)
    if sys.argv[2] == "link":
        n = int(sys.argv[3])
        dao = vol["digitalObjects"][0]
        # prohlížeč ARON pozná snímek podle id souboru TILE; s id souboru PUBLISHED otevře knihu vždy na prvním snímku
        tile = [f for f in dao["files"] if f["type"] == "TILE" and f["order"] == n][0]
        print(f"https://aron.vychodoceskearchivy.cz/apu/{apu}/dao/{dao['id']}/file/{tile['id']}")
        sys.exit(0)
    n = int(sys.argv[2])
    lo = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    out = sys.argv[4] if len(sys.argv) > 4 else f"{apu[:8]}_{n:04d}.jpg"
    crop = tuple(float(v) for v in sys.argv[5].split(",")) if len(sys.argv) > 5 else None
    path, dims = fetch_image(tiles[n], lo, out, crop)
    print(path, "full size", dims)
