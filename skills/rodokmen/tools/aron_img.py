#!/usr/bin/env python3
"""Stažení snímku matriky z portálu ARON (SOA Zámrsk, aron.vychodoceskearchivy.cz).

Použití:
  aron_img.py <apu_id> <snimek> [uroven] [vystup.jpg] [x0,y0,x1,y1]
      uroven: 0 = plné rozlišení, 1 = polovina (výchozí), 2 = čtvrtina
      x0,y0,x1,y1: jen výřez (zlomky 0..1 celé stránky) – stahují se jen potřebné dlaždice
  aron_img.py <apu_id> info          -> název svazku a počet snímků
  aron_img.py <apu_id> link <n>      -> trvalý odkaz na snímek n v prohlížeči ARON (pole "odkaz" v zaznamy.json)
  aron_img.py <apu_id> svazek        -> zapíše svazek do data/svazky.json (klíč = prvních 8 znaků apu_id)
  aron_img.py opravit-odkazy [--zapsat]
                                     -> odkazy v data/zaznamy.json z verzí do 0.7.0 vedly na první snímek knihy
                                        (soubor PUBLISHED místo TILE, #18); vypíše, které opraví, s --zapsat je opraví
                                        (přes zapis.py, formát souboru zůstane). Popis svazku bere z mezipaměti,
                                        chybějící stáhne – jeden dotaz na svazek, přes brzdu.

Popis svazků se ukládá do pracovni/.cache_aron/<apu_id>.json (ve složce projektu).
"""
import glob, json, math, os, re, shutil, ssl, subprocess, sys, tempfile, time, urllib.error, urllib.request
import concurrent.futures as cf
import xml.etree.ElementTree as ET
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)
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
                f.write(get(url, binary=True, tries=6))
            return job

        # 4 vlákna: brzda pustí 10 obrázků za s i tak a víc souběžných dotazů na macOS shazuje překlad adres
        # (URLError [Errno 8] nodename nor servname) u plného rozlišení
        with cf.ThreadPoolExecutor(4) as ex:
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


def bez_snimku(vol, tiles, n):
    """Snímek n ve svazku není: srozumitelná hláška místo KeyError."""
    if not tiles:
        sys.exit(f"Svazek „{vol.get('name', '')}“ nemá v ARONu zveřejněné snímky (scans: 0) – zkus jiný svazek fary "
                 "(bývá i samostatný rejstřík nebo druhopis), nebo ho najdi v prohlížeči ARON.")
    sys.exit(f"Snímek {n} ve svazku není – svazek má snímky {min(tiles)}–{max(tiles)} (aron_img.py <apu_id> info).")


SIT = (urllib.error.URLError, ssl.SSLError, ConnectionError, TimeoutError)   # chyby sítě (ne místních souborů)


def chyba_archivu(e):
    """Výpadek na straně ARONu (certifikát, jiná stránka místo snímku, server neodpovídá): hláška místo tracebacku."""
    duvod = getattr(e, "reason", e)
    if isinstance(duvod, ssl.SSLError) or isinstance(e, ET.ParseError):
        sys.exit("ARON: obrázkový server má neplatný certifikát nebo místo snímku vrací jinou stránku – chyba na straně "
                 f"archivu ({type(duvod).__name__}). Zkus to později; info a link fungují dál, svazky jde plánovat. "
                 "Kontrolu certifikátu nevypínej.")
    if isinstance(e, urllib.error.HTTPError):
        sys.exit(f"ARON vrátil chybu HTTP {e.code} – chyba na straně archivu, zkus to později.")
    sys.exit(f"ARON neodpovídá ({duvod}) – zkus to později.")


ODKAZ = re.compile(r"https://aron\.vychodoceskearchivy\.cz/apu/([^/\s]+)/dao/([^/\s]+)/file/([^/?#\s]+)")


def opravit_odkazy(zapsat):
    """Odkazy na soubor PUBLISHED → TILE téhož snímku (#18)."""
    path = os.path.join(ROOT, "data", "zaznamy.json")
    zaz = json.load(open(path, encoding="utf-8-sig")) if os.path.exists(path) else []
    podle_apu = {}
    for z in zaz:
        m = ODKAZ.fullmatch((z.get("odkaz") or "").strip())
        if m:
            podle_apu.setdefault(m.group(1), []).append((z["klic"], m.group(3)))
    oprava, dobre, nevim = [], 0, []
    for apu, zaznamy in podle_apu.items():
        try:
            vol = volume(apu)
        except SIT + (ValueError, urllib.error.HTTPError) as e:
            nevim += [f"{k} (svazek {apu} se nepodařilo načíst: {e})" for k, _ in zaznamy]
            continue
        soubory = {f["id"]: (dao, f) for dao in vol.get("digitalObjects") or [] for f in dao.get("files", [])}
        for klic, fid in zaznamy:
            dao, f = soubory.get(fid, (None, None))
            if not f:
                nevim.append(f"{klic} (soubor {fid} ve svazku není)")
            elif f["type"] == "TILE":
                dobre += 1
            else:
                tile = [(d, x) for d in vol.get("digitalObjects") or [] for x in d.get("files", [])
                        if x["type"] == "TILE" and x["order"] == f["order"]]
                if tile:
                    d, x = tile[0]
                    oprava.append((klic, f["order"], f"https://aron.vychodoceskearchivy.cz/apu/{apu}/dao/{d['id']}/file/{x['id']}"))
                else:
                    nevim.append(f"{klic} (snímek {f['order']} nemá dlaždice)")
    for klic, n, url in oprava:
        print(f"{'opravuji' if zapsat else 'opravit'}: {klic} (snímek {n}) → {url}")
        if zapsat:
            r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "zapis.py"), "zaznamy", klic, "-", "--sloucit"],
                               input=json.dumps({"odkaz": url}), text=True, encoding="utf-8", capture_output=True)
            if r.returncode:
                sys.exit(f"zapis.py selhal u {klic}: {r.stderr or r.stdout}")
    for x in nevim:
        print("nevím:", x)
    print(f"odkazů na ARON: {dobre + len(oprava) + len(nevim)}, v pořádku {dobre}, "
          f"{'opraveno' if zapsat else 'k opravě'} {len(oprava)}, nejasné {len(nevim)}"
          + ("" if zapsat or not oprava else " – opravíš je: aron_img.py opravit-odkazy --zapsat"))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "opravit-odkazy":
        opravit_odkazy("--zapsat" in sys.argv)
        sys.exit(0)
    if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    apu = sys.argv[1]
    try:
        vol = volume(apu)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            sys.exit(f"Svazek {apu} v ARONu není (HTTP 404) – zkontroluj apu_id (celé id z aron_search.py); "
                     "některé svazky z hledání ARON samotný nezveřejňuje, zkus jiný svazek fary.")
        chyba_archivu(e)
    except SIT + (ValueError,) as e:
        chyba_archivu(e)
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
        # prohlížeč ARONu najde snímek jen podle souboru typu TILE (dlaždice); s id varianty PUBLISHED
        # otevře knihu vždy na prvním snímku (#18)
        tile = [(dao, f) for dao in vol.get("digitalObjects") or [] for f in dao.get("files", [])
                if f["type"] == "TILE" and f["order"] == n]
        if not tile:
            bez_snimku(vol, tiles, n)
        dao, f = tile[0]
        print(f"https://aron.vychodoceskearchivy.cz/apu/{apu}/dao/{dao['id']}/file/{f['id']}")
        sys.exit(0)
    n = int(sys.argv[2])
    lo = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    out = sys.argv[4] if len(sys.argv) > 4 else f"{apu[:8]}_{n:04d}.jpg"
    crop = tuple(float(v) for v in sys.argv[5].split(",")) if len(sys.argv) > 5 else None
    if n not in tiles:
        bez_snimku(vol, tiles, n)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    try:
        path, dims = fetch_image(tiles[n], lo, out, crop)
    except SIT + (ET.ParseError,) as e:
        chyba_archivu(e)
    print(path, "full size", dims)
