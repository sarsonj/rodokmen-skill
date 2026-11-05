#!/usr/bin/env python3
"""Arolsen Archives (collections.arolsen-archives.org): vězni a oběti nacismu, nucené práce, vysídlení – bez prohlížeče.

Dachau, Mauthausen, Osvětim (část), Buchenwald, Flossenbürg, Terezín, Gestapo, nuceně nasazení, DP (vysídlené osoby) po válce
a další – přes 30 milionů záznamů o osobách (kartotéky táborů, seznamy transportů, korespondence ITS).

Použití (z kořene projektu):
  arolsen.py souhlas    -> uživatel (ne Claude!) jednou za 30 dní potvrdí prohlášení, které portál ukazuje při vstupu (citlivé údaje,
                           osobní odpovědnost; v Claude Code `!python3 -I tools/arolsen.py souhlas`). Bez souhlasu nástroj nic nestahuje.
  arolsen.py hledat "Příjmení Jméno [rok]" [filtry] [--max N] [--od N] [--podrobne] [--jazyk en|de]
        -> osoby: id | příjmení | jméno | rodné | narozen | místo narození | č. vězně | národnost | část archivu | odkaz
           Slova jsou spojená „a zároveň“ (každé musí být v záznamu); rok narození přidej jako další slovo („Novák Josef 1905“).
           Hledá i hláskové varianty. Řazeno podle příjmení; výchozí výpis N = 40, portál dává po 1000 záznamech (`--od 1000` = další tisícovka).
        Filtry (zúží výsledek, volitelné, lze kombinovat):
           --misto-narozeni Praha   (obsahuje)       --rodne Nováková   (rodné jméno obsahuje)
           --cislo 103258           (číslo vězně)    --narodnost Czech  (jen přesný název z portálu, např. Czech, Czechoslovakian, Polish)
           --vyznani Jewish         (jen přesný název z portálu)
        --podrobne vypíše u každé osoby všechna vyplněná pole (otec, matka, vyznání, povolání, místo věznění, datum úmrtí, poslední bydliště…)
  arolsen.py karta <id> <vystup.jpg>
        -> stáhne obrázek kartotéční karty / dokumentu (víc obrázků dostane příponu _2, _3…) a vypíše odkaz do archivu
Datum narození v databázi je v pořadí měsíc/den/rok – nástroj ho převádí na „den. měsíc. rok“.
POZOR: shoda jména není ztotožnění. Jména se píší i s chybami (Novák/Nowak/Novak); ověř datum a místo narození na kartě
a v rodině. Údaje o obětech jsou citlivé – na web jen se souhlasem rodiny (soukromi.md). Podmínky užití sbírky jsou na
https://arolsen-archives.org (údaje jen pro osobní, vědecké a genealogické účely). Neprocházej databázi hromadně.
"""
import http.cookiejar, json, os, random, re, string, sys, time, urllib.parse, urllib.request
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)
import souhlas  # noqa: E402 – souhlas s podmínkami vstupu do online archivu (tools/souhlas.py)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

SOUHLAS_KLIC, SOUHLAS_PORTAL, SOUHLAS_PRIKAZ = "arolsen", "Arolsen Archives (online archiv)", "tools/arolsen.py souhlas"
SOUHLAS_ZNENI = ("Welcome to the Online Archive of the Arolsen Archives! Our Data Protection Rules and Terms of Use were established by the "
                 "International Commission as the governing body of the Arolsen Archives and do not correspond to German or other national "
                 "archival law. Please note that this portal on persons persecuted by the National Socialists includes sensitive personal data "
                 "on identified or identifiable persons. As a user of this portal, you are obliged to observe applicable data protection law "
                 "and to respect the legitimate concerns of third parties or victims. The Arolsen Archives cannot be held responsible for "
                 "third-party publications that appear as a result of the use made of the collections. Some of the documents held by the "
                 "Arolsen Archives are copies. Other archives hold the originals and the rights of use. Before publishing documents from our "
                 "archives, please always take note of our Terms of Use and, if necessary, obtain the rights from third parties.\n\n"
                 "Declaration of consent: I hereby declare my consent to using sensitive personal data in accordance with applicable national "
                 "laws and provisions. I am aware that any violation of these laws and/or provisions may result in criminal charges.")
SOUHLAS_URL = "https://arolsen-archives.org/en/materials/terms-of-use/ (pravidla ochrany údajů: https://aroa.to/data-processing-rules)"
API = "https://collections-server.arolsen-archives.org/ITS-WS.asmx/"
WEB = "https://collections.arolsen-archives.org/"
_op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))   # server drží dotaz v session
_op.addheaders = [("User-Agent", "Mozilla/5.0 (rodokmen)")]


def post(metoda, data):
    err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(API + metoda, data=json.dumps(data).encode(),
                                         headers={"Content-Type": "application/json; charset=utf-8", "Origin": WEB.rstrip("/"), "Referer": WEB})
            with _op.open(req, timeout=90) as r:
                return json.load(r)["d"]
        except (OSError, ValueError, KeyError) as e:   # i neplatná odpověď (HTML chybová stránka, JSON bez „d“)
            err = e
            if getattr(e, "code", 0) in (400, 403, 404):
                break
            time.sleep(3 * (attempt + 1))
    sys.exit(f"Arolsen neodpověděl správně ({type(err).__name__}: {str(err)[:100]}). Zkus to později nebo hledej na collections.arolsen-archives.org.")


def datum(s):
    m = re.fullmatch(r"(\d\d)/(\d\d)/(\d{4})", s or "")
    return f"{int(m.group(2))}. {int(m.group(1))}. {m.group(3)}" if m else (s or "")


POLE_CS = {"Father": "otec", "Mother": "matka", "Religion": "vyznání", "Nationality": "národnost", "Occupaton": "povolání",
           "Place_of_incarceration": "místo věznění", "Date_of_decease": "úmrtí", "Last_residence": "poslední bydliště",
           "Last_residence_country": "země", "Last_residence_district": "okres", "Last_residence_province": "provincie",
           "Last_residence_town": "obec", "Last_residence_part_of_town": "část obce", "Last_residence_street": "ulice",
           "Last_residence_house_number": "číslo domu", "Signature": "část archivu"}


def nacti_tag(uid, jazyk, typ, hodnota):
    """Id položky filtru (národnost, vyznání) podle přesného názvu na portálu."""
    tagy = post("GetTagList", {"uniqueId": uid, "lang": jazyk, "type": typ, "filter": {}, "top": "", "orderBy": "t1.value", "filterType": "person"})
    shody = [t for t in tagy if (t.get("desc") or "").strip().lower() == hodnota.strip().lower()]
    if not shody:
        nabidka = ", ".join(f"{t['desc']} ({t['count']})" for t in tagy[:25])
        sys.exit(f"Hodnota „{hodnota}“ není ve filtru. V tomto hledání jsou např.: {nabidka}")
    return shody[0]["id"]


def hledat(dotaz, maxn, jazyk, filtry=None, od=0, podrobne=False):
    filtry = filtry or {}
    uid = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(20))
    post("BuildQueryGlobalForAngular", {"uniqueId": uid, "lang": jazyk, "archiveIds": [], "strSearch": dotaz, "synSearch": True})
    pouzit = False
    grid = [{"Field": pole, "Operator": op, "Value": filtry[k]} for k, (pole, op) in
            {"misto": ("PlaceBirth", "contains"), "rodne": ("MaidenName", "contains"), "cislo": ("PrisonerNumber", "eq")}.items() if k in filtry]
    if grid:
        post("BuildGridFilter", {"uniqueId": uid, "lang": jazyk, "type": "person", "filter": {"Operator": "and", "Field": "", "Filters": grid, "Value": ""}})
        pouzit = True
    cb = {}
    for klic, typ in (("narodnost", "per_nationality"), ("vyznani", "per_religion")):
        if klic in filtry:
            cb[typ] = [nacti_tag(uid, jazyk, typ, filtry[klic])]
    if cb:
        post("BuildFilter", {"uniqueId": uid, "lang": jazyk, "searchType": "person", "filter": cb})
        pouzit = True
    celkem = post("GetCount", {"uniqueId": uid, "lang": jazyk, "searchType": "person", "useFilter": pouzit})
    rows = post("GetPersonList", {"uniqueId": uid, "lang": jazyk, "rowNum": od, "orderBy": "LastName", "orderType": "asc"})
    for r in rows[:maxn]:
        print(" | ".join([str(r["ObjId"]), r.get("LastName") or "-", r.get("FirstName") or "-", r.get("MaidenName") or "-", datum(r.get("Dob")) or "-",
                          r.get("PlaceBirth") or "-", r.get("PrisonerNumber") or "-", r.get("Nationality") or "-",
                          (r.get("Signature") or "")[:70], f"{WEB}{jazyk}/document/{r['ObjId']}"]))
        if podrobne:
            extra = [f"{POLE_CS[k]}: {datum(v) if k == 'Date_of_decease' else v}" for k, v in r.items()
                     if k in POLE_CS and v not in ("", None) and k not in ("Signature", "Nationality")]
            if extra:
                print("    " + "; ".join(extra))
    if not rows:
        print("Nic nenalezeno (zkus jiný pravopis, jen příjmení, nebo bez roku / filtrů)." if not od else "Za tímto posunem už nic není.", file=sys.stderr)
    else:
        if len(rows) > maxn:
            print(f"… načteno {len(rows)} z {celkem} záznamů, zobrazeno {maxn}; víc ukáže --max {len(rows)}, užší výběr rok, křestní jméno nebo filtr", file=sys.stderr)
        try:
            vic = int(re.sub(r"\D", "", str(celkem)) or 0) > od + len(rows)
        except ValueError:
            vic = False
        if vic:
            print(f"… celkem {celkem} záznamů, načteno {len(rows)} (od {od}); další tisícovka: --od {od + len(rows)}, užší výběr rok, křestní jméno nebo filtr",
                  file=sys.stderr)


def karta(objid, out):
    if not objid.isdigit():
        sys.exit("id je číslo z prvního sloupce výpisu `hledat`.")
    obrazky = post("GetFileByObj", {"objId": int(objid), "lang": "en"})
    if not obrazky:
        sys.exit("K záznamu není obrázek (jen údaj v kartotéce).")
    base, ext = os.path.splitext(out)
    for i, o in enumerate(obrazky, 1):
        url = (o.get("image") or "").replace("\\\\", "//").replace("\\", "/")
        if urllib.parse.urlsplit(url).hostname != "collections-server.arolsen-archives.org":
            sys.exit(f"Neočekávaný server obrázku: {url[:80]}")
        cil = out if i == 1 else f"{base}_{i}{ext}"
        os.makedirs(os.path.dirname(os.path.abspath(cil)), exist_ok=True)
        req = urllib.request.Request(url, headers={"Referer": WEB, "User-Agent": "Mozilla/5.0 (rodokmen)"})
        with _op.open(req, timeout=90) as r:
            if urllib.parse.urlsplit(r.geturl()).hostname != "collections-server.arolsen-archives.org":
                sys.exit(f"Přesměrování na neočekávaný server: {r.geturl()[:80]}")
            if not (r.headers.get("Content-Type") or "").startswith("image/"):
                sys.exit(f"Server nevrátil obrázek ({r.headers.get('Content-Type')}).")
            data = r.read()
        with open(cil, "wb") as fh:
            fh.write(data)
        print(cil, "|", o.get("title", ""), "|", WEB + o.get("relatedLink", ""))
        time.sleep(0.5)


if __name__ == "__main__":
    a = sys.argv[1:]
    maxn, jazyk, od, podrobne, filtry = 40, "en", 0, False, {}
    if "--podrobne" in a:
        a.remove("--podrobne")
        podrobne = True
    FILTRY = {"--misto-narozeni": "misto", "--rodne": "rodne", "--cislo": "cislo", "--narodnost": "narodnost", "--vyznani": "vyznani"}
    for volba in ("--max", "--od", "--jazyk", *FILTRY):
        if volba in a:
            i = a.index(volba)
            if i + 1 >= len(a) or a[i + 1].startswith("--") or not a[i + 1].strip() \
                    or (volba in ("--max", "--od") and not (a[i + 1].isascii() and a[i + 1].isdigit())) or (volba == "--max" and int(a[i + 1]) < 1) \
                    or (volba == "--jazyk" and a[i + 1] not in ("en", "de")):
                sys.exit(f"{volba}: chybí nebo neplatná hodnota (--max kladné číslo, --od číslo, --jazyk en|de, ostatní filtry text).")
            if volba == "--max":
                maxn = int(a[i + 1])
            elif volba == "--od":
                od = int(a[i + 1])
            elif volba == "--jazyk":
                jazyk = a[i + 1]
            else:
                filtry[FILTRY[volba]] = a[i + 1]
            del a[i:i + 2]
    if not a:
        sys.exit(__doc__)
    if a[0] == "souhlas" and len(a) == 1:
        souhlas.potvrd(SOUHLAS_KLIC, SOUHLAS_PORTAL, SOUHLAS_ZNENI, SOUHLAS_URL, SOUHLAS_PRIKAZ)
    elif a[0] == "hledat" and len(a) == 2 and a[1].strip():
        souhlas.vyzaduj(SOUHLAS_KLIC, SOUHLAS_PORTAL, SOUHLAS_ZNENI, SOUHLAS_PRIKAZ)
        hledat(a[1], maxn, jazyk, filtry, od, podrobne)
    elif a[0] == "karta" and len(a) == 3:
        souhlas.vyzaduj(SOUHLAS_KLIC, SOUHLAS_PORTAL, SOUHLAS_ZNENI, SOUHLAS_PRIKAZ)
        karta(a[1], a[2])
    else:
        sys.exit(__doc__)
