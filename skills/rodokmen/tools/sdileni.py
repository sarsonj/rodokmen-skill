"""Komunitní sdílení přečteného: Mapa matrik (kde co v knize je) a index matrik (co v zápisu stojí). Viz reference/sdileni.md.

Použití (z kořene projektu `python3 -I tools/sdileni.py …`):
  sdileni.py najdi <obec> [rok] [N|O|Z]   -> knihy z Mapy matrik s odhadem snímku a kolik zápisů z knihy už je v indexu
  sdileni.py kniha <klíč svazku | url>     -> orientační body knihy z mapy a zápisy z knihy, které už někdo přečetl
  sdileni.py bod <klíč svazku> <snímek> [rok=1785] [rok_do=1787] [druh=N] [strana=fol. 12] [ves=Lhota] [rejstrik=A–C]
                                         -> orientační bod do fronty (rok, ves, začátek rejstříku na snímku, který čteš)
  sdileni.py prehled                     -> co je nového k nasdílení, souhlas uživatele (data/sdileni.json)
  sdileni.py souhlas <ano|ne> [jméno]    -> zapíše rozhodnutí uživatele (jméno nebo přezdívka v indexu; bez něj anonymně)
  sdileni.py navrh                       -> pracovni/sdileni/: body pro mapu a zápisy pro index (osoby a ostatní doplní Claude)
  sdileni.py odeslat [mapa|index]        -> pull request do mapy a/nebo indexu; s účtem GitHub (gh) pod ním,
                                            bez něj přes sběrnou schránku Mapy matrik; jen se souhlasem

Čtení jde přes brzdu (tools/slusne.py) a ukládá se na den do ~/.cache/rodokmen_sdileni/. Ven jde jen to, co uživatel
schválí: orientační body (bez jmen) a přepisy zápisů starších zákonných lhůt (narození 100 let, sňatky a úmrtí 75 let),
bez výřezů, fotek a závěrů rodokmenu. Podporované archivy: SOA Plzeň (Porta fontium) a SOA Praha (eBadatelna) pro mapu,
k tomu AHMP pro index; ostatní nástroj vynechá a řekne to.
"""
import datetime, json, os, re, shutil, subprocess, sys, tempfile, time, unicodedata, urllib.error, urllib.request
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda (tools/slusne.py)

MAPA = "https://ondrnovy.github.io/mapa-matrik/v1"
INDEX = "https://pe-pan.github.io/matriky-index"
REPO_MAPA, REPO_INDEX = "ondrnovy/mapa-matrik", "pe-pan/matriky-index"
SCHRANKA = os.environ.get("SDILENI_SCHRANKA", "https://mapa-matrik-schranka.schranka.workers.dev")   # sběrná schránka (bez účtu GitHub)
CACHE = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.cache"), "rodokmen_sdileni")
DEN = 24 * 3600
LHUTA = {"N": 100, "O": 75, "Z": 75}   # lhůty indexu matrik (jeho kontrola.py); úmrtí přísněji než archivy (30 let)
ROOT = os.getcwd()
DATA = os.path.join(ROOT, "data")
NASTAVENI = os.path.join(DATA, "sdileni.json")
FRONTA = os.path.join(ROOT, "pracovni", "sdileni", "body.jsonl")
NAVRH = os.path.join(ROOT, "pracovni", "sdileni")


# ---------- síť (přes brzdu) a mezipaměť ----------

def stahni(url, max_stari=DEN):
    """Text z url; uloží se na den. Bez sítě vrátí starší uloženou kopii, jinak None (404 = None)."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9._-]+", "_", url.split("://", 1)[-1])[-180:])
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < max_stari:
        return open(path, encoding="utf-8").read()
    try:
        slusne.pockej(url, obrazek=False)
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": slusne.UA}), timeout=60) as r:
            text = r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        print(f"sdileni: {url} odpověděl {e.code}", file=sys.stderr)
        return open(path, encoding="utf-8").read() if os.path.exists(path) else None
    except OSError as e:
        print(f"sdileni: {url} neodpovídá ({e})", file=sys.stderr)
        return open(path, encoding="utf-8").read() if os.path.exists(path) else None
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return text


def json_z(url):
    t = stahni(url)
    return json.loads(t) if t else None


def norm(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", norm(text)).strip("-")


# ---------- kniha v projektu -> mapa a index ----------

def kniha_z_url(url):
    """(archiv mapy, archiv indexu, kniha) z adresy svazku; None pro archivy, které zatím nepodporujeme."""
    url = url or ""
    if m := re.search(r"portafontium\.eu/register/soap-pn/([a-z0-9-]+)", url) or re.search(r"portafontium\.eu/iipimage/\d+/([a-z0-9-]+)_\d", url):
        return "soa-plzen", "portafontium", m.group(1)
    if m := re.search(r"ebadatelna\.soapraha\.cz/(?:d/|pages/MatrikaPage/matrikaId/)(\d+)", url):
        return "soa-praha", "soapraha", m.group(1)
    if m := re.search(r"ahmp\.cz/.*?xid=([0-9A-Fa-f]{8})", url):
        return None, "ahmp", m.group(1).lower()
    return None


def svazky():
    p = os.path.join(DATA, "svazky.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def kniha_svazku(klic_nebo_url):
    if "://" in klic_nebo_url:
        return kniha_z_url(klic_nebo_url), None
    s = svazky().get(klic_nebo_url)
    if not s:
        sys.exit(f"Svazek {klic_nebo_url} v data/svazky.json není.")
    return kniha_z_url(s.get("url")), s


def index_knihy():
    return {k["id"]: k for k in (json_z(f"{INDEX}/data/knihy.json") or [])}


def precteno_knihy(archiv, kniha):
    t = stahni(f"{INDEX}/knihy/{archiv}/{kniha}/precteno.tsv")
    if not t:
        return []
    radky = [r.split("\t") for r in t.splitlines() if r.strip()]
    return [dict(zip(radky[0], r)) for r in radky[1:]]


# ---------- čtení ----------

def odhad(body, rok):
    body = [b for b in body if b.get("year")]
    presne = [b for b in body if b["year"] <= rok <= b.get("year_to", b["year"])]
    if presne:
        return min(b["scan"] for b in presne), "přímo z bodu"
    pred = [b for b in body if b["year"] <= rok]
    po = [b for b in body if b.get("year_to", b["year"]) >= rok]
    if pred and po:
        a = max(pred, key=lambda b: (b["year"], b["scan"]))
        b = min(po, key=lambda b: (b["year"], b["scan"]))
        if a["year"] != b["year"]:
            return round(a["scan"] + (rok - a["year"]) * (b["scan"] - a["scan"]) / (b["year"] - a["year"])), \
                f"odhad mezi sn. {a['scan']} ({a['year']}) a {b['scan']} ({b['year']})"
    return None


def pokryva(ref, rok, druh):
    for k, rozsah in (ref.get("records") or {}).items():
        if druh and k != druh:
            continue
        roky = [int(r) for r in re.findall(r"\d{4}", rozsah)]
        if not rok or (roky and min(roky) <= rok <= max(roky)):
            return True
    return False


def najdi(obec, rok=None, druh=None):
    refs = json_z(f"{MAPA}/obce/{slug(obec)}.json")
    if refs is None:
        print(f"Mapa matrik obec „{obec}“ nezná (zatím). Najdi knihu obvyklou cestou a po přečtení zapiš body "
              f"(sdileni.py bod) – příště už ji mapa ukáže.")
        return 0
    idx = index_knihy()
    nic = True
    for ref in refs:
        if not pokryva(ref, rok, druh):
            continue
        nic = False
        rec = ", ".join(f"{k} {v}" for k, v in (ref.get("records") or {}).items())
        print(f"\n{ref['signature']} ({ref['archive']}/{ref['portal_id']}) – {rec}; uspořádání {ref.get('order', '?')}, "
              f"bodů v mapě {ref.get('points', 0)}")
        vol = json_z(f"{MAPA}/{ref['path']}") or {}
        body = [b for b in vol.get("points") or [] if not druh or b.get("type") in (druh, None)]
        if vol.get("order", "").startswith("by_village"):
            vlastni = [b for b in body if norm(b.get("place") or "") == norm(obec)]
            body = vlastni or []
            if not vlastni:
                print(f"  kniha je po vsích a oddíl {obec} v mapě zatím není – hledej podle sekcí a poznámek knihy")
        if rok and (o := odhad(body, rok)):
            print(f"  → začni na sn. {o[0]} ({o[1]})")
        for n in vol.get("notes") or []:
            print(f"  pozn.: {n}")
        archiv_idx = {"soa-plzen": "portafontium", "soa-praha": "soapraha"}.get(ref["archive"])
        k = idx.get(f"{archiv_idx}/{ref['portal_id']}")
        if k:
            print(f"  v indexu matrik: {k.get('precteno', '?')} přečtených zápisů{', OCR ' + str(k['ocr_stran']) + ' stran' if k.get('ocr_stran') else ''} "
                  f"(sdileni.py kniha {vol.get('url') or ref['portal_id']})")
    if nic:
        print(f"Pro {obec} {rok or ''} {druh or ''} mapa žádnou knihu nemá.")
    return 0


def kniha(klic_nebo_url):
    k, s = kniha_svazku(klic_nebo_url)
    if not k:
        print("Tenhle archiv zatím sdílení nepodporuje (reference/sdileni.md).")
        return 0
    archiv_mapy, archiv_idx, kn = k
    if archiv_mapy and (vol := json_z(f"{MAPA}/svazky/{archiv_mapy}/{kn}.json")):
        print(f"Mapa matrik: {vol['signature']}, uspořádání {vol.get('order', '?')}")
        for b in sorted(vol.get("points") or [], key=lambda b: b["scan"]):
            co = " ".join(str(x) for x in (b.get("type"), b.get("year"), b.get("place"), b.get("page") and f"str. {b['page']}",
                                            b.get("letters") and f"rejstřík {b['letters']}", b.get("note")) if x)
            print(f"  sn. {b['scan']}: {co}")
    else:
        print("Mapa matrik knihu zatím nemá.")
    radky = precteno_knihy(archiv_idx, kn)
    print(f"Index matrik: {len(radky)} přečtených zápisů" + (":" if radky else " – po přečtení je nasdílej (sdileni.py prehled)."))
    for r in radky:
        print(f"  sn. {r.get('snimek')}: {r.get('typ')} {r.get('datum')} {r.get('obec')} – {r.get('osoby')}")
    return 0


# ---------- fronta, souhlas, návrh ----------

def nastaveni():
    if os.path.exists(NASTAVENI):
        return json.load(open(NASTAVENI, encoding="utf-8"))
    return {"souhlas": None, "jmeno": "", "odeslano": {"body": [], "zapisy": []}}


def uloz_nastaveni(n):
    with open(NASTAVENI, "w", encoding="utf-8") as f:
        json.dump(n, f, ensure_ascii=False, indent=1)
        f.write("\n")


def bod(klic, snimek, *pole):
    zn = {"rok": "year", "rok_do": "year_to", "druh": "type", "strana": "page", "ves": "place", "rejstrik": "letters",
          "mesice": "months", "pozn": "note"}
    b = {"svazek": klic, "scan": int(snimek)}
    for p in pole:
        k, _, v = p.partition("=")
        if k not in zn:
            sys.exit(f"Neznámé pole {k} (zná: {', '.join(zn)}).")
        b[zn[k]] = int(v) if k in ("rok", "rok_do") else v
    if "letters" in b and "type" in b and not b["type"].startswith("i"):
        b["type"] = "i" + b["type"]
    os.makedirs(os.path.dirname(FRONTA), exist_ok=True)
    with open(FRONTA, "a", encoding="utf-8") as f:
        f.write(json.dumps(b, ensure_ascii=False) + "\n")
    print(f"bod zapsán ({sum(1 for _ in open(FRONTA, encoding='utf-8'))} ve frontě)")
    return 0


def rok_z(datum):
    roky = re.findall(r"(?<!\d)(1[0-9]{3})(?!\d)", datum or "")
    return int(roky[-1]) if roky else None


def nove(n=None):
    """Body (z fronty i ze zápisů) a zápisy, které ještě neodešly."""
    n = n or nastaveni()
    sv = svazky()
    zaznamy = json.load(open(os.path.join(DATA, "zaznamy.json"), encoding="utf-8")) if os.path.exists(os.path.join(DATA, "zaznamy.json")) else []
    prepisy = json.load(open(os.path.join(DATA, "prepisy.json"), encoding="utf-8")) if os.path.exists(os.path.join(DATA, "prepisy.json")) else {}
    body, zapisy, mimo = [], [], set()
    for z in zaznamy:
        k = kniha_z_url((sv.get(z.get("svazek")) or {}).get("url"))
        if not k:
            mimo.add(z.get("svazek"))
            continue
        rok = rok_z(z.get("datum"))
        if k[0] and rok and z.get("snimek"):
            body.append({"svazek": z["svazek"], "scan": int(z["snimek"]), "type": z.get("druh"), "year": rok})
        if z["klic"] in prepisy and rok and rok <= datetime.date.today().year - LHUTA.get(z.get("druh"), 100):
            zapisy.append(z)
    if os.path.exists(FRONTA):
        body += [json.loads(l) for l in open(FRONTA, encoding="utf-8") if l.strip()]
    klic = lambda b: f"{b['svazek']}:{b['scan']}:{b.get('type')}:{b.get('year')}:{b.get('place')}:{b.get('letters')}"
    hotove = set(n["odeslano"]["body"])
    body = list({klic(b): b for b in body if klic(b) not in hotove}.values())
    zapisy = [z for z in zapisy if z["klic"] not in set(n["odeslano"]["zapisy"])]
    return body, zapisy, mimo, klic


def prehled():
    n = nastaveni()
    body, zapisy, mimo, _ = nove(n)
    print(f"K nasdílení: {len(body)} orientačních bodů do Mapy matrik, {len(zapisy)} zápisů do indexu matrik.")
    if mimo:
        print(f"  (svazky z archivů, které zatím nepodporujeme: {', '.join(sorted(x for x in mimo if x))})")
    stav = {None: "NEROZHODNUTO – zeptej se uživatele jednou (reference/sdileni.md → Jak se zeptat)",
            "ano": "ANO – odešli na konci kola (sdileni.py navrh, odeslat) a řekni jednou větou co",
            "ne": "NE – neodesílej a znovu se neptej"}
    kdo = f"; uvádět jako „{n['jmeno']}“" if n.get("jmeno") else ("; v indexu anonymně" if n.get("souhlas") == "ano" else "")
    print(f"Souhlas: {stav.get(n.get('souhlas'), n.get('souhlas'))}{kdo}")
    return 0


def souhlas(odpoved, jmeno=""):
    if odpoved not in ("ano", "ne"):
        sys.exit("souhlas ano | ne")
    n = nastaveni()
    n["souhlas"] = odpoved
    if odpoved == "ano":
        n["jmeno"] = jmeno   # prázdné = anonymně
    uloz_nastaveni(n)
    print(f"Zapsáno do data/sdileni.json: {odpoved}")
    return 0


def navrh():
    body, zapisy, _, _ = nove()
    os.makedirs(NAVRH, exist_ok=True)
    prepisy = json.load(open(os.path.join(DATA, "prepisy.json"), encoding="utf-8")) if os.path.exists(os.path.join(DATA, "prepisy.json")) else {}
    with open(os.path.join(NAVRH, "zapisy.jsonl"), "w", encoding="utf-8") as f:
        for z in zapisy:
            k = kniha_z_url((svazky().get(z["svazek"]) or {}).get("url"))
            f.write(json.dumps({"klic": z["klic"], "archiv": k[1], "kniha": k[2], "snimek": str(z["snimek"]), "typ": z.get("druh"),
                                "datum": "", "obec": "", "osoby": "", "ostatni": "", "jistota": "",
                                "_shrnuti": z.get("shrnuti"), "_orig": prepisy[z["klic"]].get("orig"), "_datum": z.get("datum")},
                               ensure_ascii=False) + "\n")
    print(f"pracovni/sdileni/zapisy.jsonl: {len(zapisy)} zápisů. Doplň u každého datum (ISO), obec (ves a číslo domu), "
          f"osoby (role: jméno, …), ostatni (kmotři, svědci, kněz, věk, příčina), jistota (vysoká/střední/nízká) – jen z "
          f"_orig a _shrnuti, nejisté místo [?], žádné závěry rodokmenu (kdo je kdo). Body ({len(body)}) jsou hotové.")
    return 0


# ---------- odeslání (pull request) ----------

def gh(*a, cwd=None, vstup=None):
    r = subprocess.run(["gh", *a], cwd=cwd, input=vstup, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        sys.exit(f"gh {' '.join(a[:3])}: {r.stderr.strip()[-400:]}")
    return r.stdout.strip()


def git(*a, cwd):
    r = subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        sys.exit(f"git {' '.join(a[:3])}: {r.stderr.strip()[-400:]}")
    return r.stdout.strip()


def klon(repo):
    """Fork repa pod účtem uživatele, čerstvý klon v dočasné složce, větev od upstream/main."""
    if not shutil.which("gh"):
        sys.exit("Chybí GitHub CLI (gh). Sdílení vynech, nebo ho uživatel nainstaluje (reference/sdileni.md).")
    login = gh("api", "user", "--jq", ".login")
    if repo.split("/")[0] != login:
        gh("repo", "fork", repo, "--clone=false")
    d = tempfile.mkdtemp(prefix="sdileni_")
    git("clone", "-q", "--depth", "50", f"https://github.com/{login}/{repo.split('/')[1]}.git", d, cwd=ROOT)
    git("remote", "add", "upstream", f"https://github.com/{repo}.git", cwd=d)
    git("fetch", "-q", "upstream", "main", cwd=d)
    vetev = f"rodokmen-{datetime.datetime.now():%Y%m%d-%H%M}"
    git("switch", "-q", "-c", vetev, "upstream/main", cwd=d)
    return d, vetev, login


def pr(d, vetev, login, repo, titulek, telo, soubory):
    git("add", *soubory, cwd=d)
    git("-c", f"user.name={login}", "-c", f"user.email={login}@users.noreply.github.com", "commit", "-q", "-m", titulek, cwd=d)
    git("push", "-q", "-u", "origin", vetev, cwd=d)
    return gh("pr", "create", "--repo", repo, "--base", "main", "--head", f"{login}:{vetev}", "--title", titulek, "--body", telo, cwd=d)


def odeslat_mapu(body, klic):
    sv = svazky()
    d, vetev, login = klon(REPO_MAPA)
    zmenene, odeslane = set(), []
    for b in body:
        s = sv.get(b["svazek"]) or {}
        k = kniha_z_url(s.get("url"))
        if not k or not k[0]:
            continue
        path = os.path.join(d, "data", k[0], f"{k[2]}.json")
        if os.path.exists(path):
            vol = json.load(open(path, encoding="utf-8"))
        else:
            podpis = (s.get("svazek") or k[2]).split(",")[0].strip()
            vol = {"schema": 1, "archive": k[0], "portal": {"soa-plzen": "portafontium", "soa-praha": "ebadatelna"}[k[0]],
                   "portal_id": k[2], "url": s.get("url"), "signature": podpis,
                   "parish": re.sub(r"\s+\d+\w*$", "", podpis) or podpis, "records": {}, "points": [],
                   "sources": [{"by": login, "date": datetime.date.today().isoformat()}]}
            if s.get("snimku"):
                vol["scans"] = int(s["snimku"])
        p = {x: b[x] for x in ("scan", "type", "year", "year_to", "months", "page", "place", "letters", "note") if b.get(x) not in (None, "")}
        p["by"] = login
        if any(all(q.get(x) == p.get(x) for x in ("scan", "type", "year", "place", "letters")) for q in vol["points"]):
            odeslane.append(klic(b))
            continue
        vol["points"].append(p)
        vol["points"].sort(key=lambda q: q["scan"])
        if p.get("type") in ("N", "O", "Z") and p.get("year"):   # rozsah knihy aspoň podle přečtených bodů
            roky = [int(r) for r in re.findall(r"\d{4}", vol["records"].get(p["type"], ""))] + [p["year"]]
            vol["records"][p["type"]] = f"{min(roky)}–{max(roky)}" if min(roky) != max(roky) else str(min(roky))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(vol, f, ensure_ascii=False, indent=1)
            f.write("\n")
        zmenene.add(os.path.relpath(path, d))
        odeslane.append(klic(b))
    if not zmenene:
        print("Mapa: nic nového (body už v mapě jsou).")
        return odeslane
    url = pr(d, vetev, login, REPO_MAPA, f"Body od {login}: {len(odeslane)}",
             f"Orientační body přečtené při práci na rodokmenu (skill rodokmen, tools/sdileni.py). Knih: {len(zmenene)}.", sorted(zmenene))
    print(f"Mapa matrik: {url}")
    return odeslane


def pripravene_zapisy(n):
    """Zápisy z pracovni/sdileni/zapisy.jsonl s doplněnými poli, sloupec cetl a model."""
    path = os.path.join(NAVRH, "zapisy.jsonl")
    if not os.path.exists(path):
        sys.exit("Nejdřív sdileni.py navrh a doplň osoby/ostatni.")
    zapisy = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    chybi = [z["klic"] for z in zapisy if not (z.get("datum") and z.get("osoby") and z.get("jistota"))]
    if chybi:
        sys.exit(f"V pracovni/sdileni/zapisy.jsonl chybí datum/osoby/jistota u: {', '.join(chybi[:5])}…")
    model = os.environ.get("SDILENI_MODEL", "")   # např. claude-opus-5-5/high – index ho vyžaduje (README indexu, Kdo četl)
    if not re.match(r"^[a-z][a-z0-9.-]+/[a-z0-9]+$", model):
        sys.exit("Nastav SDILENI_MODEL=<id modelu>/<effort> (např. claude-opus-5-5/high) – index chce, čím se četlo.")
    kdo = f"{n['jmeno']} + " if n.get("jmeno") else ""   # bez jména = anonymně (jen model a datum)
    return zapisy, f"{kdo}{model} (z rodokmenu, přeneseno {datetime.date.today().isoformat()})", model


def odeslat_index(n):
    zapisy, cetl, model = pripravene_zapisy(n)
    d, vetev, login = klon(REPO_INDEX)
    hlav = ["snimek", "datum", "typ", "obec", "osoby", "ostatni", "jistota", "cetl", "odkaz"]
    sv = {kniha_z_url(s.get("url")): s for s in svazky().values() if kniha_z_url(s.get("url"))}
    zmenene = set()
    for z in zapisy:
        kd = os.path.join(d, "knihy", z["archiv"], z["kniha"])
        os.makedirs(kd, exist_ok=True)
        ky = os.path.join(kd, "kniha.yaml")
        if not os.path.exists(ky):
            s = next((v for k, v in sv.items() if k[1] == z["archiv"] and k[2] == z["kniha"]), {})
            nazev = (s.get("svazek") or z["kniha"]).replace('"', "'")
            with open(ky, "w", encoding="utf-8") as f:
                f.write(f'archiv: "{z["archiv"]}"\nkniha: "{z["kniha"]}"\nnazev: "{nazev}"\nurl: "{s.get("url", "")}"\n'
                        f'obsah: "snímek = číslo snímku na portálu; zatím jen jednotlivé zápisy"\n'
                        f'poznamka: "zápisy přečtené při práci na rodokmenu; jen vybrané zápisy, ne celá kniha"\n')
            zmenene.add(os.path.relpath(ky, d))
        tsv = os.path.join(kd, "precteno.tsv")
        nova = not os.path.exists(tsv)
        if not nova and any(r.split("\t")[:3] == [z["snimek"], z["datum"], z["typ"]] for r in open(tsv, encoding="utf-8")):
            continue   # stejný zápis (snímek, datum, druh) už v indexu je – nepřidávat podruhé
        with open(tsv, "a", encoding="utf-8", newline="") as f:
            if nova:
                f.write("\t".join(hlav) + "\n")
            vals = [z["snimek"], z["datum"], z["typ"], z["obec"], z["osoby"], z["ostatni"], z["jistota"], cetl, ""]
            f.write("\t".join(re.sub(r"[\t\r\n]+", " ", v or "") for v in vals) + "\n")
        zmenene.add(os.path.relpath(tsv, d))
    if os.path.exists(os.path.join(d, "tools", "kontrola.py")):
        r = subprocess.run([sys.executable, "tools/kontrola.py", "--zmeny", "upstream/main"], cwd=d, capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"Kontrola indexu neprošla – nic neodesláno:\n{r.stdout[-1500:]}{r.stderr[-500:]}")
    url = pr(d, vetev, login, REPO_INDEX, f"Zápisy z rodokmenu: {len(zapisy)} zápisů z {len({(z['archiv'], z['kniha']) for z in zapisy})} knih",
             f"Zápisy přečtené při práci na rodokmenu (skill rodokmen, tools/sdileni.py); čteno {model} ze snímků, "
             f"jistota a nejistá místa [?] u řádků. Jen zápisy starší zákonných lhůt, bez závěrů rodokmenu.\n\n"
             f"- [x] `python tools/kontrola.py` prošla bez chyb\n- [x] přidávám jen nové řádky, cizí jsem neměnil(a)\n"
             f"- [x] žádné zápisy mladší než 100 let (narození) / 75 let (sňatky, úmrtí)\n- [x] souhlasím se zveřejněním dat pod CC BY 4.0",
             sorted(zmenene))
    print(f"Index matrik: {url}")
    return [z["klic"] for z in zapisy]


def ma_github():
    if not shutil.which("gh"):
        return False
    return subprocess.run(["gh", "auth", "status"], capture_output=True).returncode == 0


def odeslat_schrankou(n, body, klic, se_zapisy):
    """Bez účtu GitHub: body a zápisy jedním požadavkem do sběrné schránky Mapy matrik, ta založí PR."""
    sv = svazky()
    data = {"nastroj": "rodokmen/sdileni.py", "body": [], "zapisy": []}
    poslane_body = []
    for b in body:
        s = sv.get(b["svazek"]) or {}
        k = kniha_z_url(s.get("url"))
        if not k or not k[0]:
            continue
        p = {x: b[x] for x in ("scan", "type", "year", "year_to", "months", "page", "place", "letters", "note") if b.get(x) not in (None, "")}
        p.update(archive=k[0], portal_id=k[2], signature=(s.get("svazek") or k[2]).split(",")[0].strip()[:120], url=s.get("url"))
        if str(s.get("snimku", "")).isdigit():
            p["scans"] = int(s["snimku"])
        data["body"].append(p)
        poslane_body.append(klic(b))
    poslane_zapisy = []
    if se_zapisy:
        zapisy, cetl, _ = pripravene_zapisy(n)
        nazvy = {kniha_z_url(s.get("url")): s for s in sv.values() if kniha_z_url(s.get("url"))}
        for z in zapisy:
            s = next((v for k, v in nazvy.items() if k[1] == z["archiv"] and k[2] == z["kniha"]), {})
            data["zapisy"].append({**{k: z[k] for k in ("archiv", "kniha", "snimek", "datum", "typ", "obec", "osoby", "ostatni", "jistota")},
                                   "cetl": cetl, "nazev": (s.get("svazek") or "")[:200], "url": s.get("url", "")})
            poslane_zapisy.append(z["klic"])
    if not data["body"] and not data["zapisy"]:
        return [], []
    slusne.pockej(SCHRANKA, obrazek=False)
    req = urllib.request.Request(f"{SCHRANKA}/v1/prispevek", data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json", "User-Agent": slusne.UA}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            vysledek = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"Schránka odmítla příspěvek ({e.code}): {e.read().decode('utf-8', 'replace')[:300]}")
    except OSError as e:
        sys.exit(f"Schránka neodpovídá ({e}) – zkus to příště, nic se neztratilo.")
    for k, url in vysledek.items():
        if url:
            print(f"{'Mapa matrik' if k == 'mapa' else 'Index matrik'}: {url}")
    return poslane_body, poslane_zapisy


def odeslat(co=None):
    n = nastaveni()
    if n.get("souhlas") != "ano":
        sys.exit("Bez souhlasu uživatele nic neodesílám (sdileni.py prehled, reference/sdileni.md).")
    body, _, _, klic = nove(n)
    if not ma_github():   # bez účtu GitHub (nebo bez gh) přes sběrnou schránku
        zapisy_jsou = co in (None, "index") and os.path.exists(os.path.join(NAVRH, "zapisy.jsonl"))
        b, z = odeslat_schrankou(n, body if co in (None, "mapa") else [], klic, zapisy_jsou)
        n["odeslano"]["body"] += b
        n["odeslano"]["zapisy"] += z
        uloz_nastaveni(n)
        if zapisy_jsou:
            os.remove(os.path.join(NAVRH, "zapisy.jsonl"))
        if co is None and os.path.exists(FRONTA):
            os.remove(FRONTA)
        return 0
    if co in (None, "mapa") and body:
        n["odeslano"]["body"] += odeslat_mapu(body, klic)
        uloz_nastaveni(n)
    if co in (None, "index") and os.path.exists(os.path.join(NAVRH, "zapisy.jsonl")):
        n["odeslano"]["zapisy"] += odeslat_index(n)
        uloz_nastaveni(n)
        os.remove(os.path.join(NAVRH, "zapisy.jsonl"))
    if co is None and os.path.exists(FRONTA):
        os.remove(FRONTA)
    return 0


def main(a):
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    prikaz, args = a[0], a[1:]
    try:
        if prikaz == "najdi" and args:
            rok = next((int(x) for x in args[1:] if x.isdigit()), None)
            druh = next((x.upper() for x in args[1:] if x.upper() in ("N", "O", "Z")), None)
            return najdi(args[0], rok, druh)
        if prikaz == "kniha" and args:
            return kniha(args[0])
        if prikaz == "bod" and len(args) >= 2:
            return bod(*args)
        if prikaz == "prehled":
            return prehled()
        if prikaz == "souhlas" and args:
            return souhlas(args[0], " ".join(args[1:]))
        if prikaz == "navrh":
            return navrh()
        if prikaz == "odeslat":
            return odeslat(args[0] if args else None)
    except slusne.Zastaveno:
        return slusne.KOD
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
