#!/usr/bin/env python3
"""Matriky SOA Plzeň na portálu Porta fontium (portafontium.eu) bez prohlížeče.

Použití (z kořene projektu `python3 -I tools/portafontium.py …`, na Windows `python -I -X utf8 tools/portafontium.py …`):
  portafontium.py fara <fara>                -> knihy fary: kniha | obce | roky a druhy (* N, oo O, + Z, i index) | popis
                                                <fara> = část adresy římskokatolické fary, např. „dolni-bela“
                                                (https://www.portafontium.eu/contents/register/soap-pn/cirkev-rimskokatolicka/dolni-bela);
                                                obec → fara nástroj nehledá – faru zjisti na portálu (vyhledávání matrik, pole Místo)
  portafontium.py info <kniha>               -> popis knihy (signatura, druh, text desky…) a počet snímků
                                                <kniha> = část adresy knihy, např. „dolni-bela-17“
  portafontium.py snimek <kniha> <snímek> <vystup.jpg> [nahled] [x0,y0,x1,y1]
                                             -> snímek v plném rozlišení (IIIF, jeden požadavek); „nahled“ = 1/4;
                                                x0,y0,x1,y1 = jen výřez (zlomky 0..1)
  portafontium.py link <kniha> <snímek>      -> trvalý odkaz na snímek (pole „odkaz“ v zaznamy.json)
  portafontium.py svazek <kniha>             -> zapíše svazek do data/svazky.json (klíč pf_<kniha>)
Snímek = pořadové číslo náhledu v prohlížeči portálu (1, 2, 3…). Stránky knih i celé snímky se ukládají do sdílené cache (tools/cache.py).
Ber ohled na server: stahuj jen snímky, které čteš.
"""
import html, http.client, json, os, re, ssl, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)
import cache  # noqa: E402 – sdílená cache stažených snímků (tools/cache.py)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://www.portafontium.eu"
ARCHIV = "soap-pn"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = cache.cesta("portafontium")   # stránky knih (seznam snímků) i celé snímky
UA = {"User-Agent": "Mozilla/5.0 (rodokmen)"}   # bez prohlížečového User-Agentu portál vrací 403
PAUZA = 0.5   # s před každým požadavkem – ohled na server i při volání ve smyčce

# Server portálu posílá jen svůj certifikát bez mezilehlého (prohlížeče a curl si ho dohledají, Python ne →
# CERTIFICATE_VERIFY_FAILED). Mezilehlý certifikát GEANT TLS RSA 1 (vydal HARICA TLS RSA Root CA 2021, platí do 2039,
# SHA-256 5B:67:8D:C4:…:A5:FB:8C:79, z http://crt.harica.gr/HARICA-GEANT-TLS-R1.cer) přidáme jen jako článek řetězce:
# bez PARTIAL_CHAIN se z něj kotva důvěry nestane, ověření pořád musí skončit u systémového kořenového certifikátu.
GEANT_TLS_RSA_1 = """
-----BEGIN CERTIFICATE-----
MIIGBTCCA+2gAwIBAgIQFNV782kiKCGaVWf6kWUbIjANBgkqhkiG9w0BAQsFADBs
MQswCQYDVQQGEwJHUjE3MDUGA1UECgwuSGVsbGVuaWMgQWNhZGVtaWMgYW5kIFJl
c2VhcmNoIEluc3RpdHV0aW9ucyBDQTEkMCIGA1UEAwwbSEFSSUNBIFRMUyBSU0Eg
Um9vdCBDQSAyMDIxMB4XDTI1MDEwMzExMTUwMFoXDTM5MTIzMTExMTQ1OVowYDEL
MAkGA1UEBhMCR1IxNzA1BgNVBAoMLkhlbGxlbmljIEFjYWRlbWljIGFuZCBSZXNl
YXJjaCBJbnN0aXR1dGlvbnMgQ0ExGDAWBgNVBAMMD0dFQU5UIFRMUyBSU0EgMTCC
AaIwDQYJKoZIhvcNAQEBBQADggGPADCCAYoCggGBAKEEaZSzEzznAPk8IEa17GSG
yJzPTj4cwRY7/vcq2BPT5+IRGxQtaCdgLXIEl2cdPdIkj2eyakFmgMjAtyeju8V8
dRayQCD/bWjJ7thDlowgLljQaXirxnYbT8bzRHAhCZqBakYgi5KWw9dANLyDHGpX
UdY259ab0lWEaFE5Uu6IzQSMJOAy4l/Twym8GUiy0qMDEBFSlm31C9BXpdHKKAlh
vIjMiKoDeTWl5vZaLB2MMRGY1yW2ftPgIP0/MkX1uFITlvHmmMTngxplH1nybEIJ
FiwHg1KiLk1TprcZgeO2gxE5Lz3wTFWrsUlAzrh5xWmscWkjNi/4BpeuiT5+NExF
czboLnXOfjuci/7bsnPi1/aZN/iKNbJRnngFoLaKVMmqCS7Xo34f+BITatryQZFE
u2oDKExQGlxDBCfYMLgLucX/onpLzUSgeQITNLx6i5tGGbUYH+9Dy3GI66L/5tPj
qzlOsydki8ZYGE5SBJeWCZ2IrhUe0WzZ2b6Zhk6JAQIDAQABo4IBLTCCASkwEgYD
VR0TAQH/BAgwBgEB/wIBADAfBgNVHSMEGDAWgBQKSCOmYKSSCjPqk1vFV+olTb0S
7jBNBggrBgEFBQcBAQRBMD8wPQYIKwYBBQUHMAKGMWh0dHA6Ly9jcnQuaGFyaWNh
LmdyL0hBUklDQS1UTFMtUm9vdC0yMDIxLVJTQS5jZXIwEQYDVR0gBAowCDAGBgRV
HSAAMB0GA1UdJQQWMBQGCCsGAQUFBwMCBggrBgEFBQcDATBCBgNVHR8EOzA5MDeg
NaAzhjFodHRwOi8vY3JsLmhhcmljYS5nci9IQVJJQ0EtVExTLVJvb3QtMjAyMS1S
U0EuY3JsMB0GA1UdDgQWBBSGAXI/jKlw4jEGUxbOAV9becg8OzAOBgNVHQ8BAf8E
BAMCAYYwDQYJKoZIhvcNAQELBQADggIBABkssjQzYrOo4GMsKegaChP16yNe6Sck
cWBymM455R2rMeuQ3zlxUNOEt+KUfgueOA2urp4j6TlPbs/XxpwuN3I1f09Luk5b
+ZgRXM7obE6ZLTerVQWKoTShyl34R2XlK8pEy7+67Ht4lcJzt+K6K5gEuoPSGQDP
ef+fUfmXrFcgBMcMbtfDb9dubFKNZZxo5nAXiqhFMOIyByag3H+tOTuH8zuId9pH
RDsUpAIHJ9/W2WBfLcKav7IKRlNBRD/sPBy903J9WHPKwl8kQSDA+aa7XCYk7bJt
Eyf+7GM9F5cZ7+YyknXqnv/rtQEkTKZdQo5Us18VFe9qqj94tXbLdk7PejJYNB4O
Zlli44Ld7rtqfFlUych7gIxFOmiyxMQQYrYmUi+74lEZvfoNhuref0CupuKpz6O3
dLv6kO9T10uNdDBoBQTkge3UzHafTIe3R2o3ujXKUGPwyc9m7/FETyKLUCwSU/5O
AVOeBCU8QtkKKjM8AmbpKpe3pHWcyq3R7B3LmIALkMPTydyDfxen65IDqREbVq8N
xjhkJThUz40JqOlN6uqKqeDISj/IoucYwsqW24AlO7ZzNmohQmMi8ep23H4hBSh0
GBTe2XvkuzaNf92syK8l2HzO+13GLCjzYLTPvXTO9UpK8DGyfGZOuamuwbAnbNpE
3RfjV9IaUQGJ
-----END CERTIFICATE-----
"""
SSL_CTX = ssl.create_default_context()
SSL_CTX.verify_flags &= ~getattr(ssl, "VERIFY_X509_PARTIAL_CHAIN", 0)
SSL_CTX.load_verify_locations(cadata=GEANT_TLS_RSA_1)


def get(url, binary=False):
    url = url if url.startswith("http") else BASE + url
    err = None
    wait = 0
    for attempt in range(4):
        time.sleep(wait or PAUZA)
        wait = 2 * (attempt + 1)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120, context=SSL_CTX) as r:
                data = r.read()
            return data if binary else data.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                sys.exit(f"Porta fontium: stránka nenalezena (404): {url}")
            if e.code == 429:   # moc požadavků – počkat (podle Retry-After) a zkusit znovu
                ra = e.headers.get("Retry-After", "")
                wait = min(int(ra), 120) if ra.isdigit() else 30 * (attempt + 1)
                err = e
                continue
            if e.code < 500:   # 4xx se opakováním nespraví
                sys.exit(f"Porta fontium odmítl požadavek ({e.code}): {url}")
            err = e
        except (OSError, http.client.HTTPException) as e:   # i useknutý přenos (IncompleteRead)
            err = e
    sys.exit(f"Porta fontium neodpovídá ({err}): {url}")


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ")).strip()


def kniha_page(kniha):
    kniha = kniha.strip("/").split("/")[-1]
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, kniha + ".html")
    if os.path.exists(path):
        return kniha, open(path, encoding="utf-8").read()
    page = get(f"/register/{ARCHIV}/{kniha}")
    if "data-iip-path" in page:   # kešuj jen opravdovou stránku knihy se snímky
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(page)
    return kniha, page


def info(kniha):
    kniha, page = kniha_page(kniha)
    fields = {}
    for m in re.finditer(r'<div class="field-label">(.*?)</div>\s*<div class="field-items">(.*?)</div>\s*</div>', page, re.S):
        lab, val = text(m.group(1)).rstrip(":"), text(m.group(2))
        if val and lab not in fields:
            fields[lab] = val
    scans = re.findall(r'data-iip-path="([^"]+)"', page)
    # odkaz patří ke snímku, jehož náhled obaluje (<a href="/iipimage/…"><img data-iip-path="…">) – ne podle pořadí,
    # jinak by jiný odkaz na stránce posunul párování a citace by vedla na vedlejší snímek
    pary = dict((s, a) for a, s in re.findall(
        r'<a\s[^>]*?href="(/iipimage/\d+/[^"]+)"[^>]*>\s*<img\s[^>]*?data-iip-path="([^"]+)"', page))
    links = [pary.get(s, "") for s in scans]
    return kniha, fields, scans, links


def scan(kniha, n):
    kniha, fields, scans, links = info(kniha)
    if not str(n).isdigit():
        sys.exit(f"číslo snímku musí být celé číslo od 1 (zadáno „{n}“)")
    n = int(n)
    if not 1 <= n <= len(scans):
        sys.exit(f"{kniha}: snímek {n} neexistuje (kniha má {len(scans)} snímků)")
    path, link = scans[n - 1], links[n - 1]
    stem = os.path.splitext(os.path.basename(path))[0]
    if not link or link.rsplit("/", 1)[-1] != stem:   # odkaz musí nést stejné jméno souboru jako snímek
        sys.exit(f"{kniha}: k snímku {n} ({stem}) se nepodařilo najít jeho odkaz – portál asi změnil stránku. "
                 "Odkaz neuváděj, nahlas to (poznamky_pro_skill.md).")
    return kniha, fields, path, link


def snimek(kniha, n, out, nahled=False, crop=None):
    kniha, _, path, link = scan(kniha, n)
    region = "full"
    if crop:
        x0, y0, x1, y1 = crop
        if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
            sys.exit("výřez x0,y0,x1,y1 musí být zlomky 0–1 a x0 < x1, y0 < y1")
        region = "pct:" + ",".join(f"{v * 100:.3f}" for v in (x0, y0, x1 - x0, y1 - y0))
    size = "pct:25" if nahled else "full"

    def stahni(cil):
        data = get(f"/fcgi-bin/iipsrv.fcgi?IIIF={urllib.parse.quote(path)}/{region}/{size}/0/default.jpg", binary=True)
        if not data.startswith(b"\xff\xd8"):
            sys.exit("Porta fontium nevrátil obrázek JPEG (zkus to později)")
        os.makedirs(os.path.dirname(os.path.abspath(cil)), exist_ok=True)
        with open(cil, "wb") as f:
            f.write(data)

    if crop:
        stahni(out)
    else:
        cache.soubor(f"portafontium/{kniha}/sn{int(n):04d}{'-nahled' if nahled else ''}.jpg", out, stahni)
    print(out, f"{os.path.getsize(out) // 1024} kB", "odkaz:", BASE + link)


def fara(slug):
    slug = slug.strip("/").split("/")[-1]
    # „Mýto“ → „myto“, „Dolní Bělá“ → „dolni-bela“ (adresa fary na portálu je bez diakritiky)
    slug = unicodedata.normalize("NFKD", slug).encode("ascii", "ignore").decode().lower().replace(" ", "-")
    url = f"/contents/register/{ARCHIV}/cirkev-rimskokatolicka/{slug}"
    out, n = [], 0
    while True:   # seznam knih je po 40 na stránku
        page = get(url + (f"?page={n}" if n else ""))
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
            m = re.search(r'href="/register/[^/]+/([^"]+)"[^>]*>([^<]+)</a>', row)
            if not m:
                continue
            cells = [text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
            out.append((m.group(1), [c for c in cells if c and c != ">"]))
        n += 1
        if f'{slug}?page={n}"' not in page:
            return out


def zkrat(s, n=300):
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + " …"


def svazek(kniha):
    kniha, fields, scans, _ = info(kniha)
    path = os.path.join(ROOT, "data", "svazky.json")
    d = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    sig = fields.get("Signatura", kniha)
    popis = "; ".join(x for x in (fields.get("Místo", ""), fields.get("Text desky", "")) if x)
    d[f"pf_{kniha}"] = {"archiv": "SOA Plzeň – Sbírka matrik západních Čech", "portal": "Porta fontium",
                        "svazek": f"{sig}, {fields.get('Typ', '')}".strip(", "), "popis": popis[:300],
                        "snimku": len(scans), "url": f"{BASE}/register/{ARCHIV}/{kniha}"}
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    print(f"pf_{kniha} ->", d[f"pf_{kniha}"]["svazek"])


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "fara" and len(a) > 1:
        knihy = fara(a[1])
        if not knihy:
            sys.exit(f"Fara „{a[1]}“ nenalezena nebo nemá knihy – zkontroluj část adresy (např. dolni-bela).")
        for k, c in knihy:
            print(k, "|", " | ".join(zkrat(x) for x in c[1:]))
    elif a[0] == "info" and len(a) > 1:
        k, f, s, _ = info(a[1])
        for lab, val in f.items():
            print(f"{lab}: {val}")
        print("snímků:", len(s))
    elif a[0] == "snimek" and len(a) > 3:
        rest = a[4:]
        crop = None
        for x in rest:
            if "," in x:
                try:
                    crop = tuple(float(v) for v in x.split(","))
                except ValueError:
                    crop = ()
                if len(crop) != 4:   # špatný výřez nesmí potichu stáhnout celou stránku
                    sys.exit(f"výřez „{x}“ zadej jako čtyři čísla x0,y0,x1,y1 (zlomky 0–1)")
        snimek(a[1], a[2], a[3], "nahled" in rest, crop)
    elif a[0] == "link" and len(a) > 2:
        print(BASE + scan(a[1], a[2])[3])
    elif a[0] == "svazek" and len(a) > 1:
        svazek(a[1])
    else:
        sys.exit(__doc__)
