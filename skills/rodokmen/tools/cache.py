#!/usr/bin/env python3
"""Sdílená mezipaměť obrázků z archivů – každý obrázek (snímek, dlaždice) se z archivu stáhne jen jednou.

Ukládá ji brzda tools/slusne.py: každý obrázek stažený přes brzdu (nástroje, vlastní skripty, pomocníci) se uloží
podle adresy a příště se vezme z disku bez dotazu na archiv. Z adresy se před uložením odstraní jen části, které
obsah nemění (;jsessionid=, PHPSESSID, pojistky proti mezipaměti typu _=1793… nebo &1793…, utm_…); neznámé
parametry zůstávají – raději stáhnout znovu, než vrátit cizí snímek. Ukládá se jen úspěšná odpověď, která je
opravdu obrázek. Porta fontium a eBadatelna dělají výřez a náhled z uloženého celého snímku bez sítě.

Mezipaměť je společná pro všechny projekty na počítači: ~/.cache/rodokmen_snimky/ (Windows
%LOCALAPPDATA%\\rodokmen_snimky), jinou složku nastaví proměnná RODOKMEN_SNIMKY. Nejvýš 5 GB (RODOKMEN_SNIMKY_GB),
nejdéle nepoužité soubory se mažou samy. Celou složku lze kdykoli smazat, nástroje si obrázky stáhnou znovu.

Použití (z kořene projektu):
  cache.py stav                       -> kolik místa zabírá (ušetřené dotazy vypíše slusne.py stav)
  cache.py uloz <soubor.json> [vystup.jpg]
                                      -> uloží snímek z prohlížeče eBadatelny (výsledek úryvku v reference/portaly.md,
                                         SOA Praha); soubor .json pak smaže
  cache.py najdi <adresa snímku>      -> cesta k uloženému snímku eBadatelny (/d/… nebo /a/…), jinak kód 1
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
            _pouzito(k + p)
            return k + p
    return None


_ulozeno = [0]


def uloz_url(url, data):
    """Uloží obrázek stažený z adresy (jen opravdový obrázek). Vrací cestu nebo None."""
    p = pripona(data)
    return uloz(klic_url(url) + p, data) if p else None


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


# --- snímky z prohlížeče (eBadatelna) -------------------------------------------------------------------------------
EBAD = re.compile(r"ebadatelna\.soapraha\.cz/(d|a)/(\d+)/(\d+)")


def klic_ebadatelna(druh, xid, n):
    return f"ebadatelna/{druh}/{xid}/sn{int(n):04d}.jpg"


def _ze_souboru(path):
    d = json.loads(open(path, encoding="utf-8").read())
    if isinstance(d, str):   # Playwright ukládá výsledek jako řetězec JSON
        d = json.loads(d)
    return d


def main(a):
    for s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")
    if not a or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    if a[0] == "stav":
        n = s = 0
        for d, _, fs in os.walk(KOREN):
            for f in fs:
                n += 1
                s += os.path.getsize(os.path.join(d, f))
        print(f"{KOREN}: {n} souborů, {s / 1024 ** 2:.0f} MB z {LIMIT / 1024 ** 3:g} GB "
              "(nejdéle nepoužité se nad limitem mažou samy)")
    elif a[0] == "uloz" and len(a) > 1:
        d = _ze_souboru(a[1])
        m = EBAD.search(d.get("adresa", ""))
        if not m or not str(d.get("data", "")).startswith("data:image/"):
            sys.exit("soubor není výsledek úryvku pro eBadatelnu (chybí adresa snímku nebo obrázek)")
        p = uloz(klic_ebadatelna(*m.groups()), base64.b64decode(d["data"].split(",", 1)[1]))
        if not p:
            sys.exit(f"do {KOREN} nejde zapisovat")
        os.remove(a[1])
        print("uloženo:", p, f"({d.get('w')} × {d.get('h')})")
        if len(a) > 2:
            os.makedirs(os.path.dirname(os.path.abspath(a[2])), exist_ok=True)
            shutil.copyfile(p, a[2])
            print(a[2])
    elif a[0] == "najdi" and len(a) > 1:
        m = EBAD.search(a[1])
        p = cesta(klic_ebadatelna(*m.groups())) if m else None
        if not p or not os.path.exists(p):
            sys.exit(1)
        print(p)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
