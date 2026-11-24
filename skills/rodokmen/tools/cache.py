#!/usr/bin/env python3
"""Sdílená mezipaměť obrázků z archivů – každý obrázek (snímek, dlaždice) se z archivu stáhne jen jednou.

Ukládá ji brzda tools/slusne.py: každý obrázek stažený přes brzdu (nástroje, vlastní skripty, pomocníci) se uloží
podle adresy a příště se vezme z disku bez dotazu na archiv. Z adresy se před uložením odstraní jen části, které
obsah nemění (;jsessionid=, PHPSESSID, pojistky proti mezipaměti typu _=1793… nebo &1793…, utm_…); neznámé
parametry zůstávají – raději stáhnout znovu, než vrátit cizí snímek. Ukládá se jen úspěšná odpověď, která je
opravdu celý obrázek: sedí délka ze serveru a soubor má značku konce (přerušené stažení se neuloží, zkrácený
uložený snímek se smaže a stáhne znovu). Porta fontium a eBadatelna dělají výřez a náhled z uloženého celého
snímku bez sítě.

Mezipaměť je společná pro všechny projekty na počítači: ~/.cache/rodokmen_snimky/ (Windows
%LOCALAPPDATA%\\rodokmen_snimky), jinou složku nastaví proměnná RODOKMEN_SNIMKY. Nejvýš 5 GB (RODOKMEN_SNIMKY_GB),
nejdéle nepoužité soubory se mažou samy. Celou složku lze kdykoli smazat, nástroje si obrázky stáhnou znovu.

Použití (z kořene projektu):
  cache.py stav                       -> kolik místa zabírá a kolik stažení z archivu ušetřila (podrobně slusne.py stav)
  cache.py uloz <soubor.json> [vystup.jpg] [--nahled nahled.jpg]
                                      -> uloží snímek z prohlížeče eBadatelny, FamilySearch nebo ZA Opava (výsledek
                                         úryvku v reference/portaly.md); soubor .json pak smaže
  cache.py najdi <adresa snímku> [--nahled nahled.jpg]
                                      -> cesta k uloženému snímku eBadatelny (/d/… nebo /a/…), FamilySearch
                                         (adresa $dist nebo /ark:/61903/3:1:…) nebo ZA Opava (adresa
                                         showZoomifySeparate…myImageUuid=…), jinak kód 1; vypíše i rozměr
                                         (nalezený snímek se počítá jako ušetřené otevření v prohlížeči)
  cache.py z-chromu "<adresa showZoomifySeparate…>" <Z.imagePath> <šířka>x<výška> [vystup.jpg] [--plne]
                                      -> ZA Opava, AHMP: složí snímek z dlaždic, které si prohlížeč snímků načetl do
                                         mezipaměti Chromu (Edge, Brave), a uloží ho; archiv nedostane žádný dotaz.
                                         Bez --plne poloviční rozlišení (na čtení stačí), s --plne plné
  --nahled nahled.jpg                 -> k tomu rovnou náhled široký 1600 px (k přečtení stránky, bez sítě)

Počítá se jen to, co by jinak opravdu šlo z archivu znovu: u nástrojů přes brzdu každý obrázek vrácený z disku,
u eBadatelny nalezení přes „najdi“ (ne výřezy a náhledy z ebadatelna.py, ty by se dělaly z disku i bez mezipaměti).
"""
import base64, glob, hashlib, json, os, re, shutil, subprocess, sys
from urllib.parse import parse_qsl, urlencode, urlsplit

KOREN = os.environ.get("RODOKMEN_SNIMKY") or os.path.join(
    os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".cache"), "rodokmen_snimky")
LIMIT = float(os.environ.get("RODOKMEN_SNIMKY_GB") or 5) * 1024 ** 3
PRIPONY = ((b"\xff\xd8\xff", ".jpg"), (b"\x89PNG\r\n\x1a\n", ".png"), (b"GIF8", ".gif"), (b"II*\x00", ".tif"),
           (b"MM\x00*", ".tif"), (b"\x00\x00\x00\x0cjP  ", ".jp2"), (b"\xffO\xffQ", ".j2k"))


def cesta(klic):
    """Soubor v mezipaměti; klíč je relativní cesta s „/“."""
    return os.path.join(KOREN, *klic.split("/"))


def pripona(data):
    """Přípona podle prvních bajtů; None = není obrázek (chybová stránka, „zablokováno“ …)."""
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return next((p for z, p in PRIPONY if data.startswith(z)), None)


def _cely(hlava, konec, velikost):
    """Má obrázek konec? Přerušené stažení má hlavičku taky, jen mu chybí spodek snímku."""
    p = pripona(hlava)
    if p in (".jpg", ".jp2", ".j2k"):   # značka konce FF D9 (za ní bývá výplň); uvnitř dat se objevit nemůže
        return b"\xff\xd9" in konec
    if p == ".png":
        return b"IEND" in konec[-64:]
    if p == ".gif":
        return konec.rstrip(b"\x00")[-1:] == b";"
    if p == ".webp":
        return int.from_bytes(hlava[4:8], "little") + 8 <= velikost
    return p is not None   # TIFF konec nemá – ohlídá ho jen délka ze serveru


def cely(data, delka=None):
    """Úplný obrázek: sedí délka ze serveru (Content-Length), je-li, a má značku konce."""
    if delka is not None and len(data) != delka:
        return False
    return _cely(data[:16], data[-1024:], len(data))


def cely_soubor(path):
    """Totéž pro uložený soubor (čte jen začátek a konec)."""
    try:
        n = os.path.getsize(path)
        with open(path, "rb") as f:
            hlava = f.read(16)
            f.seek(max(0, n - 1024))
            return _cely(hlava, f.read(), n)
    except OSError:
        return False


# --- obrázky podle adresy (ukládá brzda slusne.py) ----------------------------------------------------------------
def klic_url(url):
    """Klíč podle adresy bez částí, které obsah nemění. Neznámé parametry zůstávají."""
    u = urlsplit(url)
    path = re.sub(r";jsessionid=[^/?#;]*", "", u.path, flags=re.I)
    q = []
    for k, v in parse_qsl(u.query, keep_blank_values=True):
        kl = k.lower()
        if kl in ("jsessionid", "phpsessid") or kl.startswith("utm_"):
            continue
        if (kl == "_" and v.isdigit()) or (not v and re.fullmatch(r"\d{10,}", k)):   # pojistka proti mezipaměti
            continue
        q.append((k, v))
    host = (u.hostname or "").lower()
    port = f":{u.port}" if u.port and u.port not in (80, 443) else ""   # http i https = týž obrázek
    norm = f"{host}{port}{path}?{urlencode(sorted(q))}"
    h = hashlib.sha1(norm.encode()).hexdigest()
    return f"web/{host}/{h[:2]}/{h}"


def najdi_url(url):
    """Uložený obrázek pro adresu, nebo None."""
    k = cesta(klic_url(url))
    for _, p in PRIPONY + ((None, ".webp"),):
        if os.path.exists(k + p):
            if not cely_soubor(k + p):   # zkrácený (uložený starší verzí) – smazat a stáhnout znovu
                try:
                    os.remove(k + p)
                except OSError:
                    pass
                return None
            _pouzito(k + p)
            return k + p
    return None


_ulozeno = [0]


def uloz_url(url, data, delka=None):
    """Uloží obrázek stažený z adresy (jen opravdový a úplný obrázek). Vrací cestu nebo None."""
    p = pripona(data)
    return uloz(klic_url(url) + p, data) if p and cely(data, delka) else None


# --- společné ---------------------------------------------------------------------------------------------------
def _pouzito(p):
    try:
        os.utime(p)   # naposledy použito – úklid maže nejdéle nepoužité
    except OSError:
        pass


def uklid():
    """Nad limitem smaže nejdéle nepoužité soubory (na 90 % limitu)."""
    soubory = []
    for d, _, fs in os.walk(KOREN):
        for f in fs:
            if ".tmp" not in f:
                p = os.path.join(d, f)
                try:
                    st = os.stat(p)
                    soubory.append((st.st_mtime, st.st_size, p))
                except OSError:
                    pass
    celkem = sum(s for _, s, _ in soubory)
    if celkem <= LIMIT:
        return
    for _, s, p in sorted(soubory):
        try:
            os.remove(p)
            celkem -= s
        except OSError:
            continue
        if celkem <= LIMIT * 0.9:
            break


def uloz(klic, data):
    """Atomicky zapíše bajty do mezipaměti (souběžné stahování téhož obrázku si nepřekáží)."""
    p = cesta(klic)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        tmp = f"{p}.{os.getpid()}.{id(data)}.tmp"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, p)
    except OSError:   # plný disk, sandbox bez zápisu – mezipaměť je jen úspora, práci nezastaví
        return None
    _ulozeno[0] += 1
    if _ulozeno[0] % 200 == 1:   # úklid jen občas (prochází celou složku)
        uklid()
    return p


def _magick():
    return (shutil.which("magick") or next(iter(sorted(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe"))), None)
            or (os.name != "nt" and shutil.which("convert")))


def odvod(src, out, crop=None, zmenseni=1):
    """Výřez (zlomky 0–1) a zmenšení (1, 2, 4 …) z uloženého snímku bez sítě. True = povedlo se."""
    M = _magick()
    if not M:
        return False
    args = [M, src + "[0]"]
    if crop:
        r = subprocess.run([M, src + "[0]", "-format", "%w %h", "info:"], capture_output=True, text=True)
        try:
            W, H = map(int, r.stdout.split())
        except ValueError:
            return False
        x0, y0, x1, y1 = crop
        args += ["-crop", f"{round((x1 - x0) * W)}x{round((y1 - y0) * H)}+{round(x0 * W)}+{round(y0 * H)}", "+repage"]
    if zmenseni > 1:
        args += ["-resize", f"{100 / zmenseni:g}%"]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    return subprocess.run(args + ["-quality", "90", out], capture_output=True).returncode == 0


# --- snímky z prohlížeče (eBadatelna, FamilySearch, ZA Opava) -------------------------------------------------------------------------------
EBAD = re.compile(r"ebadatelna\.soapraha\.cz/(d|a)/(\d+)/(\d+)")


EBAD_WEB = "ebadatelna.soapraha.cz"


def _slusne():
    """Brzda tools/slusne.py ze stejné složky (python -I nepřidává složku skriptu do cesty)."""
    d = os.path.dirname(os.path.abspath(__file__))
    if d not in sys.path:
        sys.path.insert(0, d)
    import slusne
    return slusne


def _zapocti(host, velikost, z_disku=True):
    """Statistika pro slusne.py stav (stažené z archivu / vzaté z disku). Bez brzdy se nic nepočítá."""
    try:
        slusne = _slusne()
        slusne.zapocti(host, velikost, z_disku)
    except Exception:   # noqa: BLE001 – statistika nesmí zastavit práci
        pass


def klic_ebadatelna(druh, xid, n):
    return f"ebadatelna/{druh}/{xid}/sn{int(n):04d}.jpg"


# FamilySearch: snímek určuje ARK „3:1:XXXX-XXXX-XXX“ – stejný v adrese $dist i v trvalém odkazu /ark:/61903/3:1:…
FS = re.compile(r"familysearch\.org/.*?\b3:1:([0-9A-Z]{4}-[0-9A-Z-]{4,})")
FS_WEB = "www.familysearch.org"

# ZA Opava: snímek určuje myImageUuid v adrese prohlížeče snímků (showZoomifySeparate), dá se zjistit bez otevření snímku
ZAO = re.compile(r"archives\.cz/da/showZoomifySeparate\?.*?\bmyImageUuid=([0-9A-Fa-f-]{32,36})")
ZAO_WEB = "images.archives.cz"
# AHMP (nový Archivní katalog digi.ahmp.cz od 30. 11. 2026): stejný software jako ZA Opava
AHMP = re.compile(r"digi\.ahmp\.cz/pragapublica/showZoomifySeparate\?.*?\bmyImageUuid=([0-9A-Fa-f-]{32,36})")
AHMP_WEB = "digi-images.ahmp.cz"


def z_prohlizece(adresa):
    """(klíč v mezipaměti, web) pro adresu snímku z prohlížeče (eBadatelna, FamilySearch), jinak None."""
    m = EBAD.search(adresa or "")
    if m:
        return klic_ebadatelna(*m.groups()), EBAD_WEB
    m = FS.search(adresa or "")
    if m:
        return f"familysearch/3_1_{m.group(1)}.jpg", FS_WEB   # bez dvojteček – Windows je v názvu souboru neumí
    m = ZAO.search(adresa or "")
    if m:
        return f"zaopava/{m.group(1).replace('-', '').lower()}.jpg", ZAO_WEB
    m = AHMP.search(adresa or "")
    if m:
        return f"ahmp/{m.group(1).replace('-', '').lower()}.jpg", AHMP_WEB
    return None


def _sirka(p):
    """Šířka a výška uloženého snímku (ImageMagick), jinak None."""
    M = _magick()
    r = subprocess.run([M, p + "[0]", "-format", "%w %h", "info:"], capture_output=True, text=True) if M else None
    return tuple(map(int, r.stdout.split())) if r and re.fullmatch(r"\d+ \d+", r.stdout.strip()) else None


# --- ZA Opava a AHMP: dlaždice z mezipaměti prohlížeče ---------------------------------------------------------------
# Archivy posílají dlaždice s „Cache-Control: … public“ (ZA Opava 10 hodin, AHMP 1 hodinu), Chrome je drží na disku. Čteme jen
# soubory na disku – žádný dotaz na archiv. Chrome má dva formáty mezipaměti: „simple“ (soubory <hash>_0; macOS,
# Linux) a „blockfile“ (index, data_0–3, f_XXXXXX; Windows).
TILE = re.compile(r"(/ximage/\S+?\.jpg)/TileGroup\d+/(\d+)-(\d+)-(\d+)\.jpg$", re.I)


def _slozky_prohlizece():
    """Složky Cache_Data všech profilů Chromu, Edge, Brave a Chromia."""
    home = os.path.expanduser("~")
    lad = os.environ.get("LOCALAPPDATA") or ""
    zaklady = [os.path.join(home, "Library", "Caches", *p) for p in
               (("Google", "Chrome"), ("Microsoft Edge",), ("BraveSoftware", "Brave-Browser"), ("Chromium",))]
    zaklady += [os.path.join(home, ".cache", p) for p in
                ("google-chrome", "microsoft-edge", "BraveSoftware/Brave-Browser", "chromium")]
    zaklady += [os.path.join(lad, *p, "User Data") for p in
                (("Google", "Chrome"), ("Microsoft", "Edge"), ("BraveSoftware", "Brave-Browser"), ("Chromium",))] if lad else []
    return [d for z in zaklady for d in glob.glob(os.path.join(z, "*", "Cache", "Cache_Data"))]


def _simple(slozka, hledej):
    eof = (0xf4fa6f45970d41d8).to_bytes(8, "little")
    for f in glob.glob(os.path.join(slozka, "*_0")):
        try:
            b = open(f, "rb").read()
        except OSError:
            continue
        if len(b) < 24 or b[:8] != (0xfcfb6d1ba7725c30).to_bytes(8, "little"):
            continue
        n = int.from_bytes(b[12:16], "little")
        klic = b[24:24 + n].decode("utf-8", "replace")
        if hledej in klic:
            konec = b.find(eof, 24 + n)
            yield klic, b[24 + n:konec if konec > 0 else None]


def _blockfile(slozka, hledej):
    """Formát blockfile (net/disk_cache/blockfile/disk_format.h): záznamy po 256 B v data_1, klíč v záznamu,
    tělo odpovědi (proud 1) v data_N nebo v samostatném f_XXXXXX."""
    soubory = {}

    def blok(adresa, velikost):
        if not adresa >> 31:
            return None
        typ = (adresa >> 28) & 7
        if typ == 0:   # samostatný soubor f_XXXXXX
            try:
                return open(os.path.join(slozka, f"f_{adresa & 0x0FFFFFFF:06x}"), "rb").read(velikost)
            except OSError:
                return None
        bs = {1: 36, 2: 256, 3: 1024, 4: 4096}.get(typ)
        if not bs:
            return None
        n = (adresa >> 16) & 0xFF
        if n not in soubory:
            try:
                soubory[n] = open(os.path.join(slozka, f"data_{n}"), "rb").read()
            except OSError:
                return None
        start = 8192 + (adresa & 0xFFFF) * bs
        return soubory[n][start:start + velikost]

    try:
        d1 = open(os.path.join(slozka, "data_1"), "rb").read()
    except OSError:
        return
    for o in range(8192, len(d1) - 256, 256):
        n = int.from_bytes(d1[o + 32:o + 36], "little")
        if not 0 < n <= 928:   # klíč přímo v záznamu (až 4 bloky)
            continue
        klic = d1[o + 96:o + 96 + n].decode("utf-8", "replace")
        if hledej not in klic:
            continue
        velikost = int.from_bytes(d1[o + 44:o + 48], "little")
        adresa = int.from_bytes(d1[o + 60:o + 64], "little")
        data = blok(adresa, velikost) if 0 < velikost < 2 ** 24 else None
        if data:
            yield klic, data


def dlazdice_z_prohlizece(cesta_obrazku):
    """{(úroveň, x, y): bajty} pro snímek podle Z.imagePath ze všech mezipamětí prohlížečů; (dlaždice, formáty)."""
    hledej = urlsplit(cesta_obrazku).path if "://" in cesta_obrazku else cesta_obrazku
    t, formaty = {}, set()
    for slozka in _slozky_prohlizece():
        if os.path.exists(os.path.join(slozka, "data_1")):
            formaty.add("blockfile")
            zdroj = _blockfile(slozka, hledej)
        else:
            formaty.add("simple")
            zdroj = _simple(slozka, hledej)
        for klic, data in zdroj:
            m = TILE.search(klic)
            if m and data[:2] == b"\xff\xd8" and cely(data):
                t[tuple(map(int, m.group(2, 3, 4)))] = data
    return t, formaty


def urovne(W, H, T=256):
    """Rozměry úrovní Zoomify od nejmenší (0) po plné rozlišení."""
    d = []
    while True:
        d.insert(0, (W, H))
        if W <= T and H <= T:
            return d
        W, H = (W + 1) // 2, (H + 1) // 2


def sloz_z_prohlizece(cesta_obrazku, W, H, out, plne=False):
    """Složí snímek z dlaždic v mezipaměti prohlížeče. Vrací (w, h, chybějící [(x, y)], formáty)."""
    t, formaty = dlazdice_z_prohlizece(cesta_obrazku)
    d = urovne(W, H)
    L = len(d) - 1 if plne else len(d) - 2
    w, h = d[L]
    nx, ny = -(-w // 256), -(-h // 256)
    chybi = [(x, y) for y in range(ny) for x in range(nx) if (L, x, y) not in t]
    if chybi:
        return w, h, chybi, formaty
    M = _magick()
    if not M:
        sys.exit("chybí ImageMagick (magick) – bez něj snímek nesložím")
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rodokmen_dlazdice_")
    try:
        args = [M, "-size", f"{w}x{h}", "xc:white"]
        for (l, x, y), data in t.items():
            if l == L:
                f = os.path.join(tmp, f"{x}-{y}.jpg")
                open(f, "wb").write(data)
                args += [f, "-geometry", f"+{x * 256}+{y * 256}", "-composite"]
        if subprocess.run(args + ["-quality", "92", out], capture_output=True).returncode:
            sys.exit("ImageMagick snímek nesložil")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return w, h, [], formaty


def _ze_souboru(path):
    d = json.loads(open(path, encoding="utf-8").read())
    if isinstance(d, str):   # Playwright ukládá výsledek jako řetězec JSON
        d = json.loads(d)
    return d


NAHLED_PX = 1600


def _nahled(src, out, sirka=None):
    """Náhled široký NAHLED_PX (menší snímek se jen zkopíruje)."""
    if not out:
        return
    if not sirka:
        M = _magick()
        r = subprocess.run([M, src + "[0]", "-format", "%w", "info:"], capture_output=True, text=True) if M else None
        sirka = int(r.stdout) if r and r.stdout.strip().isdigit() else NAHLED_PX
    if odvod(src, out, zmenseni=max(1, int(sirka) / NAHLED_PX)):
        print("náhled:", out)
    else:
        print("náhled se nepovedl (chybí ImageMagick?) – snímek je uložený, náhled udělej přes ebadatelna.py snimek … nahled")


def main(a):
    for s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")
    if not a or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    nahled = None
    if "--nahled" in a:
        i = a.index("--nahled")
        if i + 1 >= len(a):
            sys.exit("--nahled potřebuje soubor, např. --nahled pracovni/nahled.jpg")
        nahled = a[i + 1]
        a = a[:i] + a[i + 2:]
    if a[0] == "stav":
        n = s = 0
        for d, _, fs in os.walk(KOREN):
            for f in fs:
                n += 1
                s += os.path.getsize(os.path.join(d, f))
        print(f"{KOREN}: {n} souborů, {s / 1024 ** 2:.0f} MB z {LIMIT / 1024 ** 3:g} GB "
              "(nejdéle nepoužité se nad limitem mažou samy)")
        try:
            slusne = _slusne()
            slusne._stav_mezipameti(slusne._slozka())
        except Exception:   # noqa: BLE001
            pass
    elif a[0] == "uloz" and len(a) > 1:
        d = _ze_souboru(a[1])
        zdroj = z_prohlizece(d.get("adresa", ""))
        if d.get("chybi"):
            sys.exit(f"chybějící dlaždice: {d['chybi']} – prohlížeč je nenačetl; spusť úryvek pro dlaždice znovu "
                     "(doplní jen chybějící) a pak skládání")
        if not zdroj or not str(d.get("data", "")).startswith("data:image/"):
            sys.exit("soubor není výsledek úryvku pro eBadatelnu, FamilySearch ani ZA Opava (chybí adresa snímku "
                     "nebo obrázek)")
        klic, web = zdroj
        znovu = os.path.exists(cesta(klic))   # snímek už byl uložený – prohlížeč ho načetl z archivu zbytečně
        data = base64.b64decode(d["data"].split(",", 1)[1])
        if not cely(data):
            sys.exit("snímek z prohlížeče není celý (chybí konec obrázku) – počkej na načtení a ulož ho znovu")
        stary = _sirka(cesta(klic)) if znovu and web in (ZAO_WEB, AHMP_WEB) else None
        if stary and d.get("w") and stary[0] > int(d["w"]):   # ZA Opava: menší rozlišení nepřepíše větší
            print(f"v mezipaměti už je větší snímek ({stary[0]} × {stary[1]}) – nechávám ho:", cesta(klic))
            os.remove(a[1])
            _nahled(cesta(klic), nahled, stary[0])
            return
        p = uloz(klic, data)
        _zapocti(web, len(data), z_disku=False)
        if not p:
            sys.exit(f"do {KOREN} nejde zapisovat")
        os.remove(a[1])
        print("uloženo:", p, f"({d.get('w')} × {d.get('h')})")
        if znovu:
            print("pozor: tenhle snímek už v mezipaměti byl – příště se nejdřív zeptej „cache.py najdi <adresa>“")
        if len(a) > 2:
            os.makedirs(os.path.dirname(os.path.abspath(a[2])), exist_ok=True)
            shutil.copyfile(p, a[2])
            print(a[2])
        _nahled(p, nahled, d.get("w"))
    elif a[0] == "z-chromu" and len(a) > 3:
        plne = "--plne" in a
        a = [x for x in a if x != "--plne"]
        zdroj = z_prohlizece(a[1])
        rozmer = re.fullmatch(r"(\d+)[x×](\d+)", a[3])
        if not zdroj or zdroj[1] not in (ZAO_WEB, AHMP_WEB) or not rozmer:
            sys.exit('použití: cache.py z-chromu "<adresa showZoomifySeparate…myImageUuid=…>" <Z.imagePath> '
                     "<Z.imageW>x<Z.imageH> [vystup.jpg] [--plne] [--nahled nahled.jpg]")
        if not _slozky_prohlizece():
            sys.exit("nenašel jsem mezipaměť Chromu, Edge ani Brave – snímek čti ze snímků obrazovky (portaly.md)")
        W, H = map(int, rozmer.groups())
        klic = zdroj[0]
        stary = _sirka(cesta(klic)) if os.path.exists(cesta(klic)) else None
        cil = cesta(klic) + f".{os.getpid()}.tmp.jpg"
        os.makedirs(os.path.dirname(cil), exist_ok=True)
        w, h, chybi, formaty = sloz_z_prohlizece(a[2], W, H, cil, plne)
        if chybi:
            z = 1 if plne else 0.5
            radky = sorted({y for _, y in chybi})
            sys.exit(f"v mezipaměti prohlížeče chybí {len(chybi)} dlaždic (řádky {radky[0]}–{radky[-1]} z "
                     f"{-(-h // 256)}; formát {', '.join(sorted(formaty))}). Prohlížeč snímků je nenačetl: projdi "
                     f"stránku po pohledech (Z.Viewport.zoomAndPanToView(x, y, {z}), pauza 2,5 s) a spusť znovu. "
                     "Když nepřibudou ani potom, mezipaměť prohlížeče se nedá číst – čti ze snímků obrazovky.")
        if stary and stary[0] > w:
            os.remove(cil)
            print(f"v mezipaměti už je větší snímek ({stary[0]} × {stary[1]}) – nechávám ho:", cesta(klic))
            p = cesta(klic)
        else:
            os.replace(cil, cesta(klic))
            p = cesta(klic)
            print("uloženo:", p, f"({w} × {h})")
        _pouzito(p)
        if len(a) > 4:
            os.makedirs(os.path.dirname(os.path.abspath(a[4])), exist_ok=True)
            shutil.copyfile(p, a[4])
            print(a[4])
        _nahled(p, nahled, w)
    elif a[0] == "najdi" and len(a) > 1:
        zdroj = z_prohlizece(a[1])
        p = cesta(zdroj[0]) if zdroj else None
        if not p or not os.path.exists(p):
            sys.exit(1)
        if not cely_soubor(p):   # zkrácený – smazat, snímek se uloží znovu z prohlížeče
            os.remove(p)
            sys.exit(1)
        _pouzito(p)
        _zapocti(zdroj[1], os.path.getsize(p))   # snímek se nemusí znovu otevírat v prohlížeči
        r = _sirka(p)
        print(p, f"({r[0]} × {r[1]})" if r else "")
        _nahled(p, nahled)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
