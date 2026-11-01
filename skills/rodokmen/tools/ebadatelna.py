#!/usr/bin/env python3
"""Matriky a archiválie SOA Praha (eBadatelna, ebadatelna.soapraha.cz) bez prohlížeče a bez přihlášení.

Použití (z kořene projektu):
  ebadatelna.py hledat "Obec"              -> lokality z našeptávače portálu (celý název „Obec - obec X - okres Y“);
                                            portál nemá číselná id lokalit, do „matriky“ dávej celý název
  ebadatelna.py matriky <"Obec"|"celý název">
                                         -> matriky lokality: matrikaId | kniha | druh | roky | fara | snímků
                                            (u víc stejných jmen vypíše možnosti – zadej celý název s okresem)
  ebadatelna.py info <matrikaId>          -> kniha, fara (původce), okres, druhy a roky, obsah, lokality, počet snímků
  ebadatelna.py snimek <matrikaId> <snímek> <vystup.jpg> [nahled] [x0,y0,x1,y1]
                                         -> stáhne snímek v plném rozlišení (portál dává celý snímek jedním
                                            požadavkem, nedlaždicuje); "nahled" = 1/4 rozlišení; x0,y0,x1,y1 = výřez
                                            jako zlomky šířky/výšky (0–1), např. 0.5,0,1,0.5 = pravá horní čtvrtina
  ebadatelna.py link <matrikaId> <snímek> -> trvalý odkaz na snímek (pole "odkaz" v data/zaznamy.json)
  ebadatelna.py svazek <matrikaId>        -> zapíše svazek do data/svazky.json (klíč ebad_<matrikaId>)
  ebadatelna.py a-info <archivalieId>     -> totéž pro archiválie (urbáře, gruntovní knihy …)
  ebadatelna.py a-snimek <archivalieId> <snímek> <vystup.jpg> [nahled] [x0,y0,x1,y1]
  ebadatelna.py a-link <archivalieId> <snímek>
  ebadatelna.py a-svazek <archivalieId>   -> klíč ebad_a_<archivalieId>
Trvalé odkazy: matrika https://ebadatelna.soapraha.cz/d/<matrikaId>/<snímek>,
               archiválie https://ebadatelna.soapraha.cz/a/<archivalieId>/<snímek>
Snímky se číslují od 1 (jako v prohlížeči portálu). Na výřez a náhled je potřeba ImageMagick (magick).
Portál má denní údržbu kolem 4:44 (asi 2 minuty). Ber ohled na server: stahuj jen snímky, které čteš.
"""
import glob, html, http.client, http.cookiejar, json, os, re, shutil, subprocess, sys, tempfile, time, unicodedata
import urllib.error, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://ebadatelna.soapraha.cz"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_cj = http.cookiejar.CookieJar()
_op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj))
_op.addheaders = [("User-Agent", "Mozilla/5.0 (rodokmen)"), ("Accept-Language", "cs")]
NEEXISTUJE = "neexistující stránku"
PAUZA = 0.5   # s před každým požadavkem – ohled na server i při volání ve smyčce


class Chyba(Exception):
    pass


def udrzba():
    t = time.localtime()
    return " Teď je asi denní údržba portálu (kolem 4:44, ~2 min) – zkus to za pár minut." \
        if (t.tm_hour, t.tm_min) >= (4, 40) and (t.tm_hour, t.tm_min) <= (4, 52) else ""


def get(path, referer=None, binary=False, data=None, ajax_base=None):
    """GET/POST s opakováním (2, 4, 8 s; při HTTP 429 déle). Vrací (obsah, konečná adresa)."""
    url = path if path.startswith("http") else BASE + path
    wait = 0
    for attempt in range(4):
        time.sleep(wait or PAUZA)
        wait = 2 ** (attempt + 1)
        req = urllib.request.Request(url, data=data)
        if referer:
            req.add_header("Referer", referer)
        if data is not None:
            req.add_header("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
        if ajax_base:
            req.add_header("Wicket-Ajax", "true")
            req.add_header("Wicket-Ajax-BaseURL", ajax_base)
            req.add_header("X-Requested-With", "XMLHttpRequest")
        try:
            with _op.open(req, timeout=90) as r:
                d = r.read()
                return (d if binary else d.decode("utf-8", "replace")), r.geturl()
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:   # moc požadavků – počkat (podle Retry-After) a zkusit znovu
                ra = e.headers.get("Retry-After", "")
                wait = min(int(ra), 120) if ra.isdigit() else 30 * (attempt + 1)
                print(f"eBadatelna: HTTP 429; další pokus za {wait or PAUZA} s "
                      f"({attempt + 2}/4).", file=sys.stderr, flush=True)
            elif e.code < 500 or attempt == 3:
                raise Chyba(f"portál vrátil chybu HTTP {e.code} ({url}).{udrzba()}")
            else:
                print(f"eBadatelna: HTTP {e.code}; další pokus za {wait} s "
                      f"({attempt + 2}/4).", file=sys.stderr, flush=True)
        except (OSError, http.client.HTTPException) as e:   # i useknutý přenos (IncompleteRead)
            if attempt == 3:
                raise Chyba(f"portál neodpovídá ({e}).{udrzba() or ' Zkus to za chvíli znovu.'}")
            print(f"eBadatelna: portál neodpovídá ({e}); další pokus za {wait} s "
                  f"({attempt + 2}/4).", file=sys.stderr, flush=True)


def text(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def roky(s):
    s = s.replace(" - ", "–").strip()
    return "" if s in ("---", "") else s


def bez_diakritiky(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if not unicodedata.combining(c))


# ---------- popis knihy / archiválie ----------

def radky(page):
    """Dvojice popisek -> hodnoty z tabulek „tableMatrikaBasicInfoRow“."""
    out = {}
    for row in page.split('class="tableMatrikaBasicInfoRow"')[1:]:
        cols = [text(c) for c in re.findall(r'<div class="tableMatrikaBasicInfoColumn[^"]*">\s*<div[^>]*>(.*?)</div>',
                                            row, re.S)]
        if cols and cols[0] and cols[0] not in out:
            out[cols[0]] = cols[1:]
    return out


def lokality(page):
    return [text(x).split(" / ")[0] for x in re.findall(r'<div class="obecCastLabel">(.*?)</div>', page, re.S)]


def stranka(path, co):
    page, url = get(path)
    if NEEXISTUJE in page:
        raise Chyba(f"{co} nenalezena – zkontroluj číslo.")
    if "obecCastLabel" not in page and "tableMatrikaBasicInfo" not in page:
        raise Chyba(f"stránka {url} nemá očekávaný obsah (údržba portálu?).{udrzba()}")
    return page


def info(mid):
    page = stranka(f"/pages/MatrikaPage/matrikaId/{mid}", f"matrika {mid}")
    h1 = re.search(r"<h1>(.*?)</h1>", page, re.S)
    r = radky(page)
    puv = re.search(r'class="puvodceLink"[^>]*>(.*?)</div>', page, re.S)
    druhy = []
    for k, v in r.items():
        for pref, zk in (("Naroz", "N"), ("Odda", "O"), ("Zem", "Z"), ("Birth", "N"), ("Marr", "O"), ("Death", "Z")):
            if k.startswith(pref):
                if v and roky(v[0]):
                    druhy.append(f"{zk} {roky(v[0])}")
                if len(v) > 1 and roky(v[1]):
                    druhy.append(f"{zk}i {roky(v[1])}")
    obsah = re.search(r'tableMatrikaDescriptionHeader1">\s*<span>(.*?)</span>.*?tableMatrikaDescriptionHeader1">\s*'
                      r'<span>(.*?)</span>', page, re.S)
    sn = next((v[0] for k, v in r.items() if k.startswith(("Počet snímků", "Number of scans")) and v), "")
    okres = next((v[0] for k, v in r.items() if k.startswith(("Okres", "District")) and v), "")
    return {"kniha": text(h1.group(1)) if h1 else f"matrika {mid}", "puvodce": text(puv.group(1)) if puv else "",
            "okres": okres, "druhy": druhy, "obsah": text(obsah.group(2)) if obsah else "",
            "lokality": lokality(page), "snimku": int(sn) if sn.isdigit() else None,
            "url": f"{BASE}/pages/MatrikaPage/matrikaId/{mid}"}


def a_info(aid):
    page = stranka(f"/pages/ArchivaliePage/archivalieId/{aid}", f"archiválie {aid}")
    h1 = re.search(r"<h1>(.*?)</h1>", page, re.S)
    r = radky(page)
    pole = {k: v[0] for k, v in r.items() if v and v[0] and v[0] != "---"}
    popis = re.search(r"<span>Popis archiválie</span>.*?<span>(.*?)</span>", page, re.S)
    sn = pole.get("Snímky", pole.get("Scans", ""))
    return {"nazev": text(h1.group(1)) if h1 else f"archiválie {aid}", "pole": pole,
            "popis": text(popis.group(1)) if popis and text(popis.group(1)) != "---" else "",
            "lokality": lokality(page), "snimku": int(sn) if sn.isdigit() else None,
            "url": f"{BASE}/pages/ArchivaliePage/archivalieId/{aid}"}


# ---------- vyhledávání lokalit a matrik ----------

def _hledaci_stranka():
    get("/pages/IndexPage")   # založí relaci (cookie) a české prostředí; bez toho portál nic nenajde
    page, url = get("/pages/SearchMatrikaPage")
    m = re.search(r"var availableTags1 = (\[.*?\]);", page, re.S)
    if not m:
        raise Chyba(f"seznam lokalit na stránce hledání nenalezen (údržba portálu?).{udrzba()}")
    return json.loads(m.group(1)), page, url


def _shoda(tag, token):
    t = bez_diakritiky(tag)
    jmeno, _, zbytek = t.partition(" - ")
    obec = zbytek.split(" - ")[0].removeprefix("obec ")
    return any(re.search(r"(^|\s)" + re.escape(token), w) for w in (jmeno, obec))


def hledat(nazev, tagy=None):
    tagy = tagy or _hledaci_stranka()[0]
    token = bez_diakritiky(nazev.strip())
    return list(dict.fromkeys(t for t in tagy if _shoda(t, token)))


def _vyber_lokalitu(arg, tagy):
    s, a = arg.strip().lower(), bez_diakritiky(arg.strip())
    # nejdřív přesně i s diakritikou: „Příbram“ a „Přibram“ jsou v našeptávači dvě různé položky
    presne = [t for t in tagy if t.lower() == s] or [t for t in tagy if bez_diakritiky(t) == a] or \
             [t for t in tagy if t.lower().partition(" - ")[0] == s] or \
             [t for t in tagy if bez_diakritiky(t).partition(" - ")[0] == a]
    kandidati = list(dict.fromkeys(presne)) or hledat(arg, tagy)   # našeptávač má i zdvojené položky
    if len(kandidati) == 1:
        return kandidati[0]
    if not kandidati:
        raise Chyba(f"lokalita „{arg}“ v eBadatelně není (zkus jiný tvar jména, např. bez „Dolní“, "
                    f"nebo `hledat`).")
    raise Chyba(f"„{arg}“ odpovídá víc lokalit – zadej celý název v uvozovkách:\n  " + "\n  ".join(kandidati[:40])
                + ("\n  …" if len(kandidati) > 40 else ""))


def _ajax(odkaz, page_url, base, data=None):
    xml, _ = get(urllib.parse.urljoin(page_url, odkaz), referer=page_url, ajax_base=base,
                 data=urllib.parse.urlencode(data).encode() if data is not None else None)
    if "<ajax-response>" not in xml:
        raise Chyba("portál nevrátil výsledky hledání (vypršela relace nebo údržba?)." + udrzba())
    return "".join(re.findall(r"<!\[CDATA\[(.*?)\]\]>", xml, re.S)), xml


def _handler(xml, nazev):
    m = re.search(r'"u":"([^"]*-' + re.escape(nazev) + r')"', xml)
    return m.group(1) if m else None


def matriky(arg):
    if arg.isdigit():
        raise Chyba("eBadatelna nemá číselná id lokalit – zadej název obce (případně celý název z `hledat`).")
    tagy, page, url = _hledaci_stranka()
    lok = _vyber_lokalitu(arg, tagy)
    base = re.search(r'Wicket\.Ajax\.baseUrl="([^"]*)"', page)
    tlacitko = _handler(page, "searchForm-searchButton")
    if not base or not tlacitko:
        raise Chyba("formulář hledání se změnil – nástroj je potřeba upravit.")
    obsah, xml = _ajax(tlacitko, url, base.group(1), {"searchType": "1", "keywordBox:searchTokenIn": "radio0",
                                             "keywordBox:searchToken": lok, "dateYearFrom": "1000",
                                             "dateYearTo": "2100", "searchButton": "1"})
    celkem = re.search(r"nalezeno (\d+)", obsah)
    celkem = int(celkem.group(1)) if celkem else 0
    out = {}

    def sber(obsah):
        nove = 0
        for m in re.finditer(r'<tr name="dataLink"[^>]*matrikaId/(\d+)"[^>]*>(.*?)</tr>', obsah, re.S):
            if m.group(1) not in out:
                out[m.group(1)] = [text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", m.group(2), re.S)]
                nove += 1
        return nove

    sber(obsah)
    if len(out) < celkem:   # víc než 50 výsledků: 100 na stránku a listovat dál
        h = _handler(xml, "resultsOnPagePanel-resultsOnPage")
        if h:
            obsah, xml = _ajax(h, url, base.group(1), {"tableContainer:resultsOnPagePanel:resultsOnPage": "100"})
            sber(obsah)
        while len(out) < celkem:
            h = _handler(xml, "pagination-results-nextPageUrl")
            if not h:
                break
            obsah, xml = _ajax(h, url, base.group(1))
            if not sber(obsah):
                break
    return lok, celkem, out


def radek_matriky(mid, c):
    # sloupce: kniha | typ původce | okres | počet lokalit | lokality | N | O | Z | index N | index O | index Z | snímky
    c = c + [""] * (12 - len(c))
    druh, rk = [], []
    for zk, v in zip(("N", "O", "Z", "Ni", "Oi", "Zi"), c[5:11]):
        if roky(v):
            rk.append(f"{zk} {roky(v)}")
            if zk[0] not in druh:
                druh.append(zk[0])
    if any(roky(v) for v in c[8:11]):
        druh.append("I")
    fara = re.sub(r"\s+\d+\w*$", "", c[0])
    if c[1] and not c[1].startswith("Římskokatol"):
        fara += f" ({c[1]})"
    return f"{mid} | {c[0]} | {'+'.join(druh) or '?'} | {', '.join(rk) or '?'} | {fara}, okres {c[2]} | {c[11]} snímků"


# ---------- snímky ----------

def magick():
    m = (shutil.which("magick") or next(iter(sorted(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe"))), None)
         or (os.name != "nt" and shutil.which("convert")))   # ImageMagick 6 bez magick; na Windows je convert.exe jiný program
    if not m:
        raise Chyba("chybí ImageMagick (magick) – je potřeba na náhled, výřez a zjištění rozměrů.")
    return m


def rozmer(path):
    try:
        m = magick()
    except Chyba:   # bez ImageMagicku se celý snímek uloží, jen rozměr nevypíšeme
        return "?"
    r = subprocess.run([m, path + "[0]", "-format", "%wx%h", "info:"], capture_output=True, text=True)
    return r.stdout.strip() or "?"


def odkaz(druh, xid, n):
    return f"{BASE}/{druh}/{xid}/{n}"


def snimek(druh, xid, n, out, volby):
    if not str(n).isdigit() or int(n) < 1:
        raise Chyba(f"číslo snímku musí být celé číslo od 1 (zadáno „{n}“).")
    nahled = "nahled" in volby
    vyrez = next((v for v in volby if v != "nahled"), None)
    if vyrez:
        try:
            x0, y0, x1, y1 = (float(v) for v in vyrez.split(","))
            assert 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1
        except (ValueError, AssertionError):
            raise Chyba(f"výřez „{vyrez}“ má být x0,y0,x1,y1 jako zlomky 0–1 (x0<x1, y0<y1), např. 0,0,0.5,0.5.")
    ref = odkaz(druh, xid, n)
    page, url = get(ref)
    co = "matrika" if druh == "d" else "archiválie"
    if NEEXISTUJE in page:
        raise Chyba(f"{co} {xid} nenalezena – zkontroluj číslo.")
    pc = re.search(r"var pageCount = (\d+);", page)
    src = re.search(r'<img id="scanImage"[^>]*src="([^"]+)"', page)
    if not pc or not src:
        raise Chyba(f"stránka snímku nemá očekávaný obsah ({ref}).{udrzba()}")
    if int(n) > int(pc.group(1)):
        raise Chyba(f"snímek {n} neexistuje – {co} {xid} má snímky 1–{pc.group(1)}.")
    data, _ = get(urllib.parse.urljoin(url, html.unescape(src.group(1))), referer=url, binary=True)
    if not (data[:3] == b"\xff\xd8\xff" or data[:8] == b"\x89PNG\r\n\x1a\n"):
        raise Chyba(f"portál místo obrázku vrátil něco jiného ({len(data)} B) – snímek chybí nebo údržba?{udrzba()}")
    d = os.path.dirname(os.path.abspath(out))
    os.makedirs(d, exist_ok=True)
    jpeg_ven = os.path.splitext(out)[1].lower() in (".jpg", ".jpeg")
    if not nahled and not vyrez and data[:3] == b"\xff\xd8\xff" and jpeg_ven:
        with open(out, "wb") as f:   # původní soubor beze změny (bez překódování)
            f.write(data)
    else:
        with tempfile.TemporaryDirectory(prefix="ebad_") as tmp:
            src_f = os.path.join(tmp, "snimek.jpg" if data[:3] == b"\xff\xd8\xff" else "snimek.png")
            with open(src_f, "wb") as f:
                f.write(data)
            cmd = [magick(), src_f]
            if vyrez:
                wh = rozmer(src_f)
                if not re.fullmatch(r"\d+x\d+", wh):
                    raise Chyba("ImageMagick stažený snímek nepřečetl (poškozený přenos?) – zkus to znovu.")
                w, h = (int(v) for v in wh.split("x"))
                cw, ch = round((x1 - x0) * w), round((y1 - y0) * h)
                cmd += ["-crop", f"{cw}x{ch}+{round(x0 * w)}+{round(y0 * h)}", "+repage"]
            if nahled:
                cmd += ["-resize", "25%"]
            r = subprocess.run(cmd + ["-quality", "92", out], capture_output=True, text=True)
            if r.returncode:
                raise Chyba(f"ImageMagick selhal: {r.stderr.strip()[:300]}")
    print(out, rozmer(out), "odkaz:", ref)


# ---------- svazky.json ----------

def zapis_svazek(klic, zaznam):
    path = os.path.join(ROOT, "data", "svazky.json")
    d = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    d[klic] = zaznam
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    print(f"{klic} -> {zaznam['svazek']}")


def zkrat(s, n=300):
    return s if len(s) <= n else s[:n - 1].rsplit(", ", 1)[0] + " …"


def svazek(mid):
    i = info(mid)
    zapis_svazek(f"ebad_{mid}", {
        "archiv": "SOA Praha – Sbírka matrik", "portal": "eBadatelna",
        "svazek": ", ".join([i["kniha"]] + i["druhy"]), "popis": zkrat(", ".join(i["lokality"])),
        "snimku": i["snimku"], "url": i["url"]})


def a_svazek(aid):
    i = a_info(aid)
    p = i["pole"]
    archiv = "SOA Praha" if p.get("Místo uložení", "Státní oblastní archiv v Praze") == "Státní oblastní archiv v Praze" \
        else p["Místo uložení"]
    if p.get("Archivní fond"):
        archiv += " – " + p["Archivní fond"]
    datace = roky(p.get("Datace od do", "")) or p.get("Datace rok", "")
    nazev = i["nazev"] + (f", {datace}" if datace and datace not in i["nazev"] else "") + \
        (f", inv. č. {p['Inventární číslo']}" if p.get("Inventární číslo") else "") + \
        (f", sign. {p['Signatura']}" if p.get("Signatura") else "")
    popis = " ".join(x for x in (i["popis"], "Lokality: " + ", ".join(i["lokality"]) if i["lokality"] else "") if x)
    zapis_svazek(f"ebad_a_{aid}", {"archiv": archiv, "portal": "eBadatelna", "svazek": nazev,
                                   "popis": zkrat(popis), "snimku": i["snimku"], "url": i["url"]})


def main(a):
    if not a or a[0] not in PRIKAZY or len(a) < PRIKAZY[a[0]]:
        sys.exit(__doc__)
    cmd = a[0]
    if cmd in ("info", "svazek", "snimek", "link", "a-info", "a-svazek", "a-snimek", "a-link") and not a[1].isdigit():
        raise Chyba(f"id musí být číslo (zadáno „{a[1]}“).")
    if cmd == "hledat":
        vysledky = hledat(a[1])
        if not vysledky:
            raise Chyba(f"nic nenalezeno pro „{a[1]}“ – zkus kratší tvar jména nebo název bez přívlastku.")
        for t in vysledky:
            print(t)
    elif cmd == "matriky":
        lok, celkem, out = matriky(a[1])
        print(f"# {lok}: {celkem} knih")
        for mid, c in out.items():
            print(radek_matriky(mid, c))
    elif cmd == "info":
        i = info(a[1])
        print(i["kniha"])
        print("fara (původce):", i["puvodce"], "| okres:", i["okres"])
        print("druhy a roky:", ", ".join(i["druhy"]) or "?")
        print("snímků:", i["snimku"])
        if i["obsah"] and i["obsah"] != "---":
            print("obsah:", i["obsah"])
        print("lokality:", ", ".join(i["lokality"]))
        print("odkaz:", i["url"])
    elif cmd in ("snimek", "a-snimek"):
        snimek("d" if cmd == "snimek" else "a", a[1], a[2], a[3], a[4:])
    elif cmd in ("link", "a-link"):
        if not a[2].isdigit() or int(a[2]) < 1:
            raise Chyba(f"číslo snímku musí být celé číslo od 1 (zadáno „{a[2]}“).")
        print(odkaz("d" if cmd == "link" else "a", a[1], a[2]))
    elif cmd == "svazek":
        svazek(a[1])
    elif cmd == "a-info":
        i = a_info(a[1])
        print(i["nazev"])
        for k, v in i["pole"].items():
            print(f"{k}: {v}")
        if i["popis"]:
            print("popis:", i["popis"])
        print("lokality:", ", ".join(i["lokality"]))
        print("odkaz:", i["url"])
    elif cmd == "a-svazek":
        a_svazek(a[1])


PRIKAZY = {"hledat": 2, "matriky": 2, "info": 2, "snimek": 4, "link": 3, "svazek": 2,
           "a-info": 2, "a-snimek": 4, "a-link": 3, "a-svazek": 2}

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Chyba as e:
        sys.exit(f"Chyba: {e}")
    except KeyboardInterrupt:
        sys.exit("přerušeno")
