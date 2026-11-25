#!/usr/bin/env python3
"""Export rodokmenu do GEDCOM 5.5.1 (pro MyHeritage, Gramps, Ancestry a jiné rodokmenové programy).

Použití (z kořene projektu, na Windows `python -I -X utf8 tools/ged_export.py …`):
  python3 -I tools/ged_export.py                  -> pracovni/rodokmen.zip (rodokmen.ged + složka media/ s obrázky)
  python3 -I tools/ged_export.py --slozka         -> pracovni/rodokmen/ (rodokmen.ged + media/ rovnou rozbalené
                                                     – k importu ve Family Tree Builderu nebo Gramps; cesty
                                                     k obrázkům absolutní, FTB relativní nenačte; výřezy
                                                     zápisů i přímo u osoby a zdroj = jeden zápis s výřezem,
                                                     FTB obrázky z citací zahodí; obrázky v plném
                                                     rozlišení ze zdroje/, jako detail na webu)
  python3 -I tools/ged_export.py --bez-obrazku    -> pracovni/rodokmen.ged (jen text, bez odkazů na obrázky)
  … --plne-rozliseni   přidá k zápisům i výřezy v plném rozlišení (zdroje/); s --slozka zbytečné – ta bere
                       plné rozlišení rovnou
  … --cp-v-miste       číslo popisné i do místa události („Holice čp. 112, okres Pardubice, …“) – pro MyHeritage,
                       který adresu (ADDR) u narození, sňatku a úmrtí nezobrazí; ADDR zůstane pro jiné programy
  … --koren <číslo>    jen tato osoba a její předci (např. --koren 3 = maminčina strana); čísla osob zůstanou,
                       výchozí soubor pracovni/rodokmen_koren3.zip
  … --vystup <soubor>  jiný výstup (.zip, s --bez-obrazku .ged, s --slozka složka; ne ve složce web/)
  … --prepsat          přepsat existující výstup (jinak nástroj skončí a nic nezmění; ve složce jen rodokmen.ged
                       a media/ – složku s jinými soubory nepřepíše nikdy)
  … --zijici           i údaje žijících a nedávno zemřelých – jen na výslovné přání uživatele (Claude se předem
                       zeptá); do cizí služby jen s vědomím, že údaje dostane i ona; nikdy na web
  … --rozdil <strom.ged>  sloučení se stromem na MyHeritage: jen nové osoby (bez vazby ged) a kotvy (osoby ze
                       stromu, ke kterým se nové připojují; jméno a data ze stromu) + přehled pracovni/rozdil_zmeny.md
                       (výchozí výstup pracovni/rozdil…); vazbu ged dá ged_import.py --ged-id
  … --se-zmenenymi     s --rozdil i osoby ze stromu s novými zápisy a obrázky (každá = ruční spojení ve FTB)

Čte data/osoby.py, zaznamy.json, svazky.json, prepisy.json, mista.json, dokumenty.json a obrázky z vyrezy/ (zdroje/).
Rodiny odvozuje z Kekulého čísel, fakta (`* 14. 2. 1890 Holice čp. 112`) převádí na události GEDCOM.
Zápis z matriky cituje u události jen tehdy, když sedí druh i rok (křest syna v `r` otce není otcovo narození);
ostatní zápisy cituje u osoby. Žijící zůstanou ve stromu jen jako „Žijící osoba“, zemřelí do 30 let jako „Chráněná
osoba“ (bez údajů). Kotva v --rozdil má i u chráněné osoby jméno a data ze stromu (vrací jen to, co strom už má).
Na konci vypíše souhrn: co v exportu je, co vynechal a co se nepodařilo převést.
"""
import datetime, json, os, re, shutil, sys, unicodedata, zipfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
DATA = os.path.join(ROOT, "data")
VYREZY = os.path.join(ROOT, "vyrezy")
ZDROJE = os.path.join(ROOT, "zdroje")

MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
STATUS = {"doc": "doloženo matrikou", "prob": "pravděpodobné", "fam": "údaj od rodiny",
          "mh": "jen z cizího rodokmenu", "unk": "neznámé"}
QUAY = {"doc": "3", "prob": "2"}
KIND_EVENT = {"N": "BIRT", "O": "MARR", "Z": "DEAT"}
MARKERS = {"*": "BIRT", "†": "DEAT", "×": "MARR"}
DATE_TOKEN = re.compile(r"^(?:asi|≈\S*|cca|kolem|před|po|mezi|od|a|do|[\d./–-]+,?)$")
NOT_OCCU = ("dcera", "syn ", "vdova", "vdovec", "bratr", "sestra", "manžel", "nemanžel", "provd", "roz.", "žil",
            "bydl", "zemřel", "narozen", "pohřben", "křtěn", "táž osoba")
PROTECT_DEATH_YEARS = 30    # nedávno zemřelí (stejná lhůta jako u archivu pro úmrtí)
LIVING_BIRTH_YEARS = 100    # bez úmrtí a narozen v posledních 100 letech = žijící
RECENT_YEARS = 100          # poznámky a příčiny úmrtí jen u lidí starších než ~100 let
CLOUD = ("Google Drive", "Můj disk", "My Drive", "GoogleDrive", "OneDrive", "Dropbox", "iCloud", "Mobile Documents")


# ---------- pomocné ----------

def jload(name, default):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def load_people():
    ns = {}
    exec(open(os.path.join(DATA, "osoby.py"), encoding="utf-8-sig").read(), ns)
    for name, default in (("P", {}), ("SIDE", []), ("SAME", {})):
        ns.setdefault(name, default)
    return ns


def placeholder(p):
    return p["n"].startswith(("otec neuveden", "matka neuvedena")) or p["n"] in ("", "?")


def is_portrait(key):
    """Portrét osoby = dokument s „portret“ kdekoli v názvu (bez ohledu na diakritiku a velikost písmen) a jednou osobou."""
    name = unicodedata.normalize("NFD", os.path.basename(key))
    return "portret" in "".join(c for c in name if not unicodedata.combining(c)).casefold()


def year(text):
    m = re.search(r"\d{4}", text or "")
    return int(m.group()) if m else None


def chunks(s, n=240):
    """Dlouhý text na kusy pro CONC (GEDCOM 5.5.1 má řádek nejvýš 255 znaků); nedělí u mezery, aby se neztratila."""
    out = []
    while len(s) > n:
        i = n
        while i > n // 2 and (s[i - 1].isspace() or s[i].isspace()):
            i -= 1
        out.append(s[:i])
        s = s[i:]
    return out + [s]


def gtext(level, tag, value):
    out = []
    for k, line in enumerate((value or "").replace("\r", "").split("\n")):
        parts = chunks(line.rstrip())
        head = f"{level} {tag}" if k == 0 else f"{level + 1} CONT"
        out.append(f"{head} {parts[0]}" if parts[0] else head)
        out += [f"{level + 1} CONC {p}" for p in parts[1:]]
    return out


# ---------- data a místa ----------

def _one_date(t):
    t = t.strip().rstrip(",")
    m = re.fullmatch(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{3,4})", t)
    if m and 1 <= int(m[1]) <= 31 and 1 <= int(m[2]) <= 12:
        return f"{int(m[1])} {MONTHS[int(m[2]) - 1]} {m[3]}"
    m = re.fullmatch(r"(\d{1,2})\s*[./]\s*(\d{3,4})", t)     # „3/1867“, „8. 1945“ = měsíc a rok
    if m and 1 <= int(m[1]) <= 12:
        return f"{MONTHS[int(m[1]) - 1]} {m[2]}"
    if re.fullmatch(r"\d{3,4}", t):
        return t
    return None


def ged_date(text):
    """České datum → GEDCOM. Vrací (hodnota, převedeno); co nejde převést, je fráze v závorkách."""
    t = re.sub(r"\s+", " ", (text or "").strip())
    if not t:
        return "", True
    t = re.sub(r"^≈\s*", "asi ", t)
    m = re.fullmatch(r"(?:mezi|od) (.+?) (?:a|do|–|-) (.+)", t)
    if m and _one_date(m[1]) and _one_date(m[2]):
        return f"BET {_one_date(m[1])} AND {_one_date(m[2])}", True
    for pre, tag in (("asi ", "ABT"), ("cca ", "ABT"), ("kolem ", "ABT"), ("před ", "BEF"), ("po ", "AFT")):
        if t.startswith(pre) and _one_date(t[len(pre):]):
            return f"{tag} {_one_date(t[len(pre):])}", True
    v = _one_date(t)
    if v:
        return v, True
    return "(" + t.replace("(", "").replace(")", "") + ")", False


class Places:
    """Obce z mista.json (výraz `re`) → název pro PLAC a souřadnice."""

    def __init__(self, mista):
        self.items = []
        for name, e in mista.items():
            if e.get("hypoteza"):
                continue
            try:
                rx = re.compile(e.get("re") or re.escape(name))
            except re.error:
                continue
            self.items.append((name, e, rx))

    def find(self, text):
        """Nejdřívější (při shodě nejdelší) nalezená obec → (název, záznam, text bez celých slov názvu)."""
        best = None
        for name, e, rx in self.items:
            m = rx.search(text)
            if m and (best is None or (m.start(), -(m.end() - m.start())) < (best[0], -best[1])):
                best = (m.start(), m.end() - m.start(), name, e)
        if not best:
            return None, None, text
        s, e = best[0], best[0] + best[1]
        while s > 0 and text[s - 1].isalnum():     # „Holic“ v „Holicích“ – odebrat celé slovo
            s -= 1
        while e < len(text) and text[e].isalnum():
            e += 1
        return best[2], best[3], re.sub(r"\s+", " ", text[:s] + " " + text[e:]).strip()

    @staticmethod
    def plac(name, e):
        """Plný název z OpenStreetMap (bez PSČ), když začíná názvem obce; jinak jen název."""
        parts = [p.strip() for p in (e.get("osm") or "").split(",") if p.strip()]
        parts = [p for p in parts if not re.fullmatch(r"\d{3} ?\d{2}", p)]
        return ", ".join(parts) if parts and parts[0] == name else name


def parse_fact(fact, places, partner_names=()):
    """„* 14. 2. 1890 Holice čp. 112 (pozn.)“ → událost. Vrací dict nebo None (fakt bez značky)."""
    fact = fact.strip()
    tag = MARKERS.get(fact[:1])
    if not tag:
        return None
    tokens = fact[1:].split()
    i = 0
    while i < len(tokens) and DATE_TOKEN.match(tokens[i]):
        i += 1
    date_text, rest = " ".join(tokens[:i]).rstrip(","), " ".join(tokens[i:])
    date, ok = ged_date(date_text)
    notes = [n.strip() for n in re.findall(r"\(([^)]*)\)", rest) if n.strip()]
    rest = re.sub(r"\s*\([^)]*\)", "", rest)
    head, _, extra = rest.partition(",")
    addr = None
    m = re.search(r"\b(?:čp\.|č\.\s?p\.)\s*(\d+\w*)", head)
    if m:
        addr = "čp. " + m[1]
        head = head[:m.start()] + " " + head[m.end():]
    if tag == "MARR":
        for pn in partner_names:
            if pn and pn in head:
                head = head.replace(pn, " ")
    head = re.sub(r"\s+", " ", head).strip()
    name, entry, left = places.find(head) if head else (None, None, "")
    if name:
        plac = Places.plac(name, entry)
        if left and tag != "MARR":              # u sňatku je zbytek jméno partnera
            notes.append(left)
    else:
        plac, entry = head, None
        if tag == "MARR" and len(head.split()) >= 3:   # „Holice Kateřina Ryšavá“ s neznámou obcí: konec je jméno partnera
            plac = " ".join(head.split()[:-2])
        if plac and not plac[:1].isupper():            # „v Holicích“ – nejde o název obce, jen poznámka
            notes.append(plac)
            plac = ""
    return dict(tag=tag, date=date, date_ok=ok, date_text=date_text, plac=plac, place=entry, addr=addr,
                notes=notes, extra=extra.strip(), raw=fact, year=year(date_text))


def coord(v, pos, neg):
    return f"{pos if v >= 0 else neg}{abs(v):.4f}"


# ---------- soukromí ----------

def life_years(p, events):
    by = next((e["year"] for e in events if e["tag"] == "BIRT" and e["year"]), None)
    dy = next((e["year"] for e in events if e["tag"] == "DEAT" and e["year"]), None)
    died = any(e["tag"] == "DEAT" for e in events)
    y = (p.get("y") or "").strip()
    head, dash, tail = y.partition("–")
    if y.startswith("†"):
        died, dy = True, dy or year(y)
    elif dash and year(tail) and not re.search(r"\bpo\b", tail):
        died, dy = True, dy or year(tail)
    if by is None and not y.startswith(("†", "?")) and year(head):
        by = year(head)
    return by, dy, died


def is_protected(p, events, now):
    if (p.get("note") or "").strip().lower().startswith("žijící"):
        return True
    by, dy, died = life_years(p, events)
    if died:
        return dy is not None and now - dy < PROTECT_DEATH_YEARS
    if by is None:
        return p.get("st") == "fam"
    return now - by < LIVING_BIRTH_YEARS


def side_protected(n, now):
    """Boční příbuzný „Josef Novák (1865–1920)“: chráněný, když může žít nebo zemřel nedávno."""
    ys = [int(x) for x in re.findall(r"\b\d{4}\b", n)]
    if not ys:
        return False
    if len(ys) == 1 and "†" not in n:
        return now - ys[0] < LIVING_BIRTH_YEARS
    return now - ys[-1] < RECENT_YEARS


# ---------- export ----------

class Export:
    def __init__(self, with_images=True, full_res=False, living=False, now=None, root=None, cp_in_place=False):
        self.with_images, self.full_res, self.living, self.root = with_images, full_res, living, root
        self.cp_in_place = cp_in_place
        self.now = now or datetime.date.today().year
        self.media = {}            # cesta v ZIP → zdrojový soubor
        self.file_base = None      # s --slozka: FILE jako absolutní cesta do této složky (FTB relativní nenačte)
        self.cutouts_on_person = False  # s --slozka: výřezy zápisů i přímo u osoby (FTB obrázky z citací zahodí)
        self._cited = None         # výřezy zapsané v citacích právě zpracovávané osoby
        self.personal_photo = False  # s --slozka: portrét i jako osobní fotka FTB (okénko osoby ve stromu)
        self.photo_rin = 500000    # čísla fotek jako FTB (MH:P500001…); malá čísla kolidují s čísly, která FTB dá
                                   # ostatním obrázkům při importu – osobní fotka pak ukáže prázdný soubor
        self.prefer_full = False   # s --slozka: obrázek v plném rozlišení ze zdroje/, je-li (jinak vyrezy/)
        self.source_per_record = False  # s --slozka: zdroj = jeden zápis s výřezem (FTB dá obrázek ke zdroji, ne k citaci)
        self.diff_path = None      # --rozdil <strom.ged>: jen nové osoby, kotvy (a se --se-zmenenymi změněné)
        self.with_changed = False
        self.warn, self.unparsed, self.missing = [], [], set()
        self.stats = dict(protected=0, notes_skipped=0, side_skipped=0, docs_skipped=0,
                          rec_protected=set(), causes_skipped=0)

    # --- načtení ---
    def load(self):
        ns = load_people()
        self.P, self.SAME, self.SIDE = ns["P"], dict(ns["SAME"]), ns["SIDE"]
        if 1 not in self.P:
            sys.exit("V data/osoby.py chybí výchozí osoba (číslo 1).")
        self.places = Places(jload("mista.json", {}))
        self.recs = {z["klic"]: z for z in jload("zaznamy.json", []) if z.get("klic")}
        self.svazky = jload("svazky.json", {})
        self.prepisy = jload("prepisy.json", {})
        self.docs = jload("dokumenty.json", [])
        P, SAME = self.P, self.SAME
        for a, c in list(SAME.items()):
            if c not in P or placeholder(P[c]):
                self.warn.append(f"SAME {a} -> {c}: osoba {c} je zástupná nebo chybí, alias vynechán")
                del SAME[a]
        self.persons = [k for k in sorted(P) if k not in SAME and not placeholder(P[k])]
        if self.root is not None:
            r = SAME.get(self.root, self.root)
            if r not in P or placeholder(P[r]):
                sys.exit(f"--koren {self.root}: osoba s tímto číslem v data/osoby.py není (nebo je zástupná).")
            self.root = r
            inc = self.subtree(r)
            self.persons = [k for k in self.persons if k in inc]
        self.pset = set(self.persons)
        self.aliases = {}
        for a, c in SAME.items():
            self.aliases.setdefault(c, []).append(a)

    def subtree(self, r):
        """Čísla osoby r a všech jejích předků (k >> d == r). Alias SAME uvnitř, jehož hlavní osoba leží v jiné
        větvi, přidá i ji a její předky – je to tatáž osoba."""
        def under(k, c):
            d = k.bit_length() - c.bit_length()
            return d >= 0 and k >> d == c
        inc = {k for k in self.P if under(k, r)}
        changed = True
        while changed:
            changed = False
            for a, c in self.SAME.items():
                if a in inc and c not in inc:
                    inc |= {k for k in self.P if under(k, c)}
                    changed = True
        return inc

    def canon(self, k):
        k = self.SAME.get(k, k)
        return k if k in self.pset else None

    def sex(self, k):
        if k == 1:
            return "F" if self.P[1].get("sex") == "F" else "M"
        return "M" if k % 2 == 0 else "F"

    def partner_names(self, k):
        out = []
        for c in {k ^ 1} | {a ^ 1 for a in self.aliases.get(k, [])}:
            c = self.canon(c)
            if c:
                out.append(self.P[c]["n"])
        return out

    def records_of(self, k):
        rs = list(self.P[k].get("r", []))
        for a in self.aliases.get(k, []):
            rs += self.P[a].get("r", [])
        return [r for r in dict.fromkeys(rs) if r in self.recs]

    def rec_year(self, key):
        z = self.recs[key]
        m = re.search(r"_(\d{4})$", key)
        return year(z.get("datum")) or (int(m[1]) if m else None)

    # --- příprava osob ---
    def prepare(self):
        self.info = {}
        for k in self.persons:
            p = self.P[k]
            facts = [f for f in p.get("f", []) if not f.startswith("TÁŽ OSOBA")]
            events, free, marr = [], [], []
            for f in facts:
                e = parse_fact(f, self.places, self.partner_names(k))
                if e is None:
                    free.append(f.strip())
                elif e["tag"] == "MARR":
                    marr.append(e)
                else:
                    events.append(e)
                if e is not None and not e["date_ok"]:
                    self.unparsed.append(f"{k} {p['n']}: datum „{e['date_text']}“ ve faktu „{f}“")
            prot = not self.living and is_protected(p, events, self.now)
            by, dy, died = life_years(p, events)
            recent = not self.living and (dy or by or 0) > self.now - RECENT_YEARS
            self.info[k] = dict(events=events, free=free, marr=marr, protected=prot, recent=recent, died=died)
            if prot:
                self.stats["protected"] += 1
                self.stats["rec_protected"].update(self.records_of(k))

    # --- rodiny ---
    def families(self):
        fams = {}
        for k in self.persons:
            fa = self.canon(2 * k) if 2 * k in self.P else None
            mo = self.canon(2 * k + 1) if 2 * k + 1 in self.P else None
            if not fa and not mo:
                continue
            fams.setdefault((fa, mo), []).append(k)
        self.fams = []
        for n, ((fa, mo), kids) in enumerate(sorted(fams.items(), key=lambda x: min(x[1])), 1):
            self.fams.append(dict(id=f"@F{n}@", h=fa, w=mo, c=sorted(set(kids))))
        self.famc, self.fams_of = {}, {}
        for f in self.fams:
            for c in f["c"]:
                self.famc.setdefault(c, []).append(f["id"])
            for x in (f["h"], f["w"]):
                if x:
                    self.fams_of.setdefault(x, []).append(f["id"])

    def marriage(self, f):
        """Sňatek páru: fakt „×“ jmenující partnera; z obou vezme nejpřesnější datum a místo."""
        h, w = f["h"], f["w"]
        if not h or not w:
            return None, []
        cands = []
        for k, other in ((h, w), (w, h)):
            surname = (self.P[other]["n"].split() or [""])[-1].strip("()?")
            for e in self.info[k]["marr"]:
                if surname and surname[:5] in e["raw"]:
                    e["used"] = True
                    cands.append(e)
        if not cands:
            return None, []
        best = max(cands, key=lambda e: (e["date_ok"] and bool(e["date"]), len(e["date"]), bool(e["plac"])))
        if not best["plac"]:
            with_place = [e for e in cands if e["plac"]]
            if with_place:
                best = dict(best, plac=with_place[0]["plac"], place=with_place[0]["place"], addr=with_place[0]["addr"])
        y = best["year"]
        recs = [r for r in dict.fromkeys(self.records_of(h) + self.records_of(w))
                if self.recs[r].get("druh") == "O" and y and self.rec_year(r) == y]
        return best, recs

    # --- zápisy ---
    def match_records(self, k):
        """Zápis → událost jen při shodě druhu a roku (±1 u narození a úmrtí: křest či pohřeb až další rok)."""
        rs = self.records_of(k)
        used, by_event = set(), {}
        for e in self.info[k]["events"]:
            kind = {"BIRT": "N", "DEAT": "Z"}[e["tag"]]
            for r in rs:
                ry = self.rec_year(r)
                if r not in used and self.recs[r].get("druh") == kind and e["year"] and ry and abs(ry - e["year"]) <= 1:
                    by_event.setdefault(id(e), []).append(r)
                    used.add(r)
        return by_event, used

    def obje(self, level, key, title, src_dir=None, sub="", prim=False):
        src = os.path.join(src_dir or VYREZY, key + ".jpg")
        if self.prefer_full and src_dir is None and os.path.isfile(os.path.join(ZDROJE, key + ".jpg")):
            src = os.path.join(ZDROJE, key + ".jpg")   # plné rozlišení jako detail na webu (vyrezy/ ~1800 px)
        if not self.with_images:
            return []
        if not os.path.isfile(src):
            self.missing.add(os.path.relpath(src, ROOT).replace(os.sep, "/"))
            return []
        path = f"media/{sub}{key}.jpg"
        self.media[path] = src
        file = os.path.join(self.file_base, *path.split("/")) if self.file_base else path
        out = [f"{level} OBJE", f"{level + 1} FILE {file}", f"{level + 2} FORM jpeg"]
        out += gtext(level + 1, "TITL", title)
        if self.personal_photo and not prim:
            # Jako export FTB: číslo fotky a velikost u každého obrázku. Když je má jen dvojice portrétu, FTB ostatní
            # obrázky nenačte (zkoušky T12/T15, plán-myheritage-obrázky.md).
            self.photo_rin += 1
            out += [f"{level + 1} _PHOTO_RIN MH:P{self.photo_rin}", f"{level + 1} _FILESIZE {os.path.getsize(src)}"]
        if prim:
            out.append(f"{level + 1} _PRIM Y")
            if self.personal_photo:
                # Jako export Family Tree Builderu: původní fotka (_PRIM_CUTOUT) + osobní fotka (_CUTOUT) jako samostatný
                # soubor s odkazem _PARENTRIN. Bez _POSITION je osobní fotka celý obrázek. Jen tak ji FTB ukáže
                # v okénku osoby ve stromu – samotné _PRIM (ani _PRIM_CUTOUT) nestačí. Ověřeno zkouškami ve FTB
                # 24. 11. 2026 (plán-myheritage-obrázky.md): nutné i RIN osoby a čísla fotek od 500001.
                self.photo_rin += 2
                parent, cut = self.photo_rin - 1, self.photo_rin
                size = os.path.getsize(src)
                cpath = f"media/{sub}{key}_osobni.jpg"
                self.media[cpath] = src
                cfile = os.path.join(self.file_base, *cpath.split("/")) if self.file_base else cpath
                out += [f"{level + 1} _PRIM_CUTOUT Y", f"{level + 1} _PHOTO_RIN MH:P{parent}",
                        f"{level + 1} _FILESIZE {size}",
                        f"{level} OBJE", f"{level + 1} FILE {cfile}", f"{level + 2} FORM jpeg"]
                out += gtext(level + 1, "TITL", title)
                out += [f"{level + 1} _PRIM Y", f"{level + 1} _CUTOUT Y", f"{level + 1} _PHOTO_RIN MH:P{cut}",
                        f"{level + 1} _FILESIZE {size}", f"{level + 1} _PARENTRIN @P{parent}@"]
        return out

    def citation(self, level, key, st, note=""):
        z = self.recs[key]
        out = [f"{level} SOUR {self.sour_id(key)}"]
        page = f"snímek {z['snimek']} – {z.get('nazev', key)}" if z.get("snimek") not in (None, "") else z.get("nazev", key)
        out += gtext(level + 1, "PAGE", page)
        hidden = key in self.stats["rec_protected"] and not self.living
        date, ok = ged_date(z.get("datum", ""))
        text = "" if hidden else z.get("shrnuti", "")
        tr = {} if hidden else self.prepisy.get(key, {})
        if tr.get("orig"):
            text += ("\n\n" if text else "") + "Přepis:\n" + tr["orig"]
        if tr.get("cs"):
            text += ("\n\n" if text else "") + "Překlad:\n" + tr["cs"]
        if (date and ok) or text:
            out.append(f"{level + 1} DATA")
            if date and ok:
                out.append(f"{level + 2} DATE {date}")
            if text:
                out += gtext(level + 2, "TEXT", text)
        if not hidden:
            img = self.obje(level + 1, key, z.get("nazev", key))
            if img and self._cited is not None:
                self._cited.append(key)
            out += img
            if self.full_res and not self.prefer_full and os.path.isfile(os.path.join(ZDROJE, key + ".jpg")):
                out += self.obje(level + 1, key, z.get("nazev", key) + " (plné rozlišení)", ZDROJE, "plne/")
        if z.get("odkaz"):
            out += gtext(level + 1, "NOTE", "Odkaz na snímek: " + z["odkaz"])
        if note:
            out += gtext(level + 1, "NOTE", note)
        if st in QUAY:
            out.append(f"{level + 1} QUAY {QUAY[st]}")
        return out

    def sour_id(self, key):
        z = self.recs[key]
        sv = z.get("svazek") or ""
        sk = sv if sv in self.svazky and not self.source_per_record else "zapis:" + key
        if sk not in self.sources:
            self.sources[sk] = f"@S{len(self.sources) + 1}@"
        return self.sources[sk]

    # --- výstup ---
    def event_lines(self, e, recs, st, level=1):
        out = [f"{level} {e['tag']}"]
        if e["date"]:
            out.append(f"{level + 1} DATE {e['date']}")
        if e["plac"]:
            plac = e["plac"]
            if self.cp_in_place and e["addr"]:   # MyHeritage adresu u události nezobrazí – číslo domu do místa
                obec, sep, rest = plac.partition(", ")
                plac = f"{obec} {e['addr']}{sep}{rest}"
            out += gtext(level + 1, "PLAC", plac)
            pl = e.get("place") or {}
            if "lat" in pl and "lon" in pl:
                out += [f"{level + 2} MAP", f"{level + 3} LATI {coord(pl['lat'], 'N', 'S')}",
                        f"{level + 3} LONG {coord(pl['lon'], 'E', 'W')}"]
        if e["addr"]:
            out.append(f"{level + 1} ADDR {e['addr']}")
        return out, recs

    def person_lines(self, k):
        p, inf = self.P[k], self.info[k]
        L = [f"0 @I{k}@ INDI"]
        if self.personal_photo:
            L.append(f"1 RIN MH:I{k}")   # bez RIN osoby FTB osobní fotku (_PARENTRIN) nepřiřadí
        if inf["protected"]:   # zemřelí do 30 let nejsou „žijící“ – jen chránění
            L += [f"1 NAME {'Chráněná osoba' if inf['died'] else 'Žijící osoba'}", f"1 SEX {self.sex(k)}", "1 RESN privacy"]
            L += [f"1 FAMC {x}" for x in self.famc.get(k, [])] + [f"1 FAMS {x}" for x in self.fams_of.get(k, [])]
            return L
        clean = re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", "", p["n"]).replace("?", "")).strip()
        parts = clean.split()
        given, surname = " ".join(parts[:-1]), parts[-1] if parts else ""
        if len(parts) == 1:
            given, surname = parts[0], ""
        L += [f"1 NAME {given} /{surname}/".replace("  ", " ")]
        if given:
            L.append(f"2 GIVN {given}")
        if surname:
            L.append(f"2 SURN {surname}")
        st = p.get("st", "unk")
        self._cited = []
        by_event, used = self.match_records(k)
        free_out = []
        for f in inf["free"]:
            m = re.match(r"provd\.\s+(\S+)", f)
            if m:
                L += [f"1 NAME {given} /{m[1]}/", "2 TYPE married"]
                continue
            free_out.append(f)
        L.append(f"1 SEX {self.sex(k)}")
        for e in inf["events"]:
            ev, _ = self.event_lines(e, [], st)
            L += ev
            if e["tag"] == "DEAT" and e["extra"]:
                if inf["recent"]:
                    self.stats["causes_skipped"] += 1
                else:
                    L += gtext(2, "CAUS", e["extra"])
            elif e["extra"]:
                e["notes"].append(e["extra"])
            for n in e["notes"]:
                L += gtext(2, "NOTE", n)
            for r in by_event.get(id(e), []):
                L += self.citation(2, r, st)
        for f in free_out:
            low = f.lower()
            if len(f) <= 60 and not re.search(r"\d", f) and not low.startswith(NOT_OCCU):
                L += gtext(1, "OCCU", f)
            else:
                L += gtext(1, "NOTE", f)
        for e in inf["marr"]:
            if not e.get("used"):
                L += gtext(1, "NOTE", "Sňatek: " + e["raw"].lstrip("× ").strip())
        if st != "doc":
            L += gtext(1, "NOTE", "Původ údajů: " + STATUS.get(st, st))
        if p.get("note"):
            if inf["recent"]:
                self.stats["notes_skipped"] += 1
            else:
                L += gtext(1, "NOTE", p["note"])
        for s in self.SIDE:
            if self.canon(s.get("k")) != k:
                continue
            if not self.living and side_protected(s.get("n", ""), self.now):
                self.stats["side_skipped"] += 1
                continue
            L += gtext(1, "NOTE", "Příbuzný: " + s.get("n", "") + (" – " + s["t"] if s.get("t") else ""))
        marr_recs = {r for f in self.fams for r in f.get("mrecs", []) if k in (f["h"], f["w"])}
        for r in self.records_of(k):
            if r in used or r in marr_recs:
                continue
            kind = self.recs[r].get("druh")
            note = "Osoba je v zápisu jiné události (např. dítěte nebo rodičů)." if kind in KIND_EVENT else ""
            L += self.citation(1, r, st, note)
        cited, self._cited = self._cited, None
        if self.cutouts_on_person:
            # Family Tree Builder obrázky z citací zahodí (formulář citace pole pro obrázek nemá) a MyHeritage
            # ukazuje u osoby jen její fotky – výřez zápisu proto i přímo u osoby, každý jednou (i výřez sňatku).
            own_marr = [r for f in self.fams if k in (f["h"], f["w"]) for r in f.get("mrecs", [])
                        if not (r in self.stats["rec_protected"] and not self.living)]
            for r in dict.fromkeys(cited + own_marr):
                L += self.obje(1, r, self.recs[r].get("nazev", r))
        L += self.portrait.get(k, [])
        L += self.doc_links.get(k, [])
        L += [f"1 FAMC {x}" for x in self.famc.get(k, [])] + [f"1 FAMS {x}" for x in self.fams_of.get(k, [])]
        return L

    def family_lines(self, f):
        L = [f"0 {f['id']} FAM"]
        if f["h"]:
            L.append(f"1 HUSB @I{f['h']}@")
        if f["w"]:
            L.append(f"1 WIFE @I{f['w']}@")
        L += [f"1 CHIL @I{c}@" for c in f["c"]]
        prot = any(x and self.info[x]["protected"] for x in (f["h"], f["w"]))
        if prot:
            L.append("1 RESN privacy")
        elif f.get("marr"):
            e = f["marr"]
            st = "doc" if all(self.P[x].get("st") == "doc" for x in (f["h"], f["w"])) else "prob"
            ev, _ = self.event_lines(e, [], st)
            L += ev
            for n in e["notes"] + ([e["extra"]] if e["extra"] else []):
                L += gtext(2, "NOTE", n)
            for r in f["mrecs"]:
                L += self.citation(2, r, st)
        return L

    def documents(self):
        """Rodinné fotky a dokumenty (dokumenty.json) → OBJE u osob; portrét s _PRIM Y."""
        self.portrait, self.doc_links = {}, {}
        seen = set()
        for d in self.docs:
            key = d.get("img")
            if not key or key in seen:
                continue
            seen.add(key)
            persons = list(dict.fromkeys(c for c in (self.canon(k) for k in d.get("osoby", [])) if c))
            if not persons:
                continue
            if not self.living and any(self.info[c]["protected"] for c in persons):
                self.stats["docs_skipped"] += 1
                continue
            if is_portrait(key):
                if len(persons) != 1:
                    self.warn.append(f"portrét {key} musí mít právě jednu osobu – vynechán")
                    continue
                if persons[0] in self.portrait:
                    self.warn.append(f"více portrétů pro osobu {persons[0]} – ponechán první, {key} vynechán")
                    continue
                lines = self.obje(1, key, d.get("popis", "") or "Portrét", prim=True)
                if lines:
                    self.portrait[persons[0]] = lines
                continue
            for c in persons:
                self.doc_links.setdefault(c, []).extend(self.obje(1, key, d.get("popis", "") or key))

    def sources_lines(self):
        L, repos = [], {}
        for sk, sid in self.sources.items():
            L.append(f"0 {sid} SOUR")
            if sk.startswith("zapis:"):
                key = sk[len("zapis:"):]
                z = self.recs[key]
                sv = self.svazky.get(z.get("svazek") or "")
                title = z.get("nazev", key)
                if sv:
                    title += ", " + (sv.get("svazek") or z["svazek"])
                    if z.get("snimek") not in (None, ""):
                        title += f", snímek {z['snimek']}"
                L += gtext(1, "TITL", title)
                if sv:
                    L += self.volume_lines(sv, repos)
                if self.source_per_record and not (key in self.stats["rec_protected"] and not self.living):
                    L += self.obje(1, key, z.get("nazev", key))
                continue
            sv = self.svazky[sk]
            L += gtext(1, "TITL", sv.get("svazek") or sk)
            L += self.volume_lines(sv, repos)
        for name, rid in repos.items():
            L.append(f"0 {rid} REPO")
            L += gtext(1, "NAME", name)
        return L

    def volume_lines(self, sv, repos):
        """Archiv (REPO, signatura) a popis svazku – u zdroje-svazku i u zdroje-zápisu."""
        L = []
        if sv.get("archiv"):
            rid = repos.setdefault(sv["archiv"], f"@R{len(repos) + 1}@")
            L.append(f"1 REPO {rid}")
            m = re.search(r"sign\.\s*([^,;]+)", sv.get("svazek", ""))
            if m and m[1].strip(" .…"):
                L.append(f"2 CALN {m[1].strip()}")
        note = "; ".join(x for x in (sv.get("popis", ""), ("portál " + sv["portal"]) if sv.get("portal") else "",
                                     ("odkaz: " + sv["url"]) if sv.get("url") else "") if x)
        if note:
            L += gtext(1, "NOTE", note)
        return L

    # --- rozdílový export (fáze 2: sloučení se stromem na MyHeritage přes FTB) ---
    def has_new(self, k):
        """Má osoba ve stromu od skillu něco nového: zápis z matriky nebo obrázek (dokument, portrét)?"""
        return bool(self.records_of(k)) or any(
            k in {self.canon(x) for x in d.get("osoby", [])} for d in self.docs if d.get("img"))

    def diff_classify(self):
        """Roztřídí osoby podle vazby `ged` na původní strom: nové (ve stromu nejsou), kotvy (jsou ve stromu a nová
        osoba se k nim připojuje – rodiče/dítě/partner v rodině s novou osobou), změněné (jsou ve stromu a mají nový
        zápis či obrázek). Do GEDCOM jdou nové a kotvy, se --se-zmenenymi i změněné (bez rodinných vazeb)."""
        sys.path.insert(0, TOOLS)
        import ged_import
        self.tree = ged_import.read(self.diff_path)
        self.tree_date = datetime.date.fromtimestamp(os.path.getmtime(self.diff_path))
        self.tree_age_days = (datetime.date.today() - self.tree_date).days
        self.tree_ind = {r["_id"]: r for r in self.tree.values() if r["_type"] == "INDI"}
        in_tree = set()
        for k in self.persons:
            g = self.P[k].get("ged")
            if g and g in self.tree_ind:
                in_tree.add(k)
            elif g:
                self.warn.append(f"osoba {k} ({self.P[k]['n']}) má ged {g}, které ve stromu {os.path.basename(self.diff_path)} "
                                 "není – exportuji ji jako novou (jiný strom, nebo osoba ve stromu smazána?)")
        new = set(self.persons) - in_tree
        members = lambda f: [x for x in (f["h"], f["w"], *f["c"]) if x]
        fams = [f for f in self.fams if any(m in new for m in members(f))]
        anchors = {m for f in fams for m in members(f) if m in in_tree}
        changed = {k for k in in_tree - anchors if self.has_new(k)}
        sel = new | anchors | (changed if self.with_changed else set())
        self.persons = [k for k in self.persons if k in sel]
        self.fams = fams
        self.famc, self.fams_of = {}, {}
        for f in self.fams:
            for c in f["c"]:
                self.famc.setdefault(c, []).append(f["id"])
            for x in (f["h"], f["w"]):
                if x:
                    self.fams_of.setdefault(x, []).append(f["id"])
        # nová osoba na místě, kde strom už někoho má (rodič osoby ze stromu): jiný předek, nebo nespárovaná tatáž osoba
        occupied = {}
        for k in new:
            c = self.canon(k // 2) if k > 1 else None
            if c in in_tree:
                fa, mo = ged_import.parents(self.tree_ind[self.P[c]["ged"]], self.tree)
                there = fa if k % 2 == 0 else mo
                if there:
                    occupied[k] = there
        # nová osoba, která už ve stromu je jinde (strom ji má, jen ne na tomto místě): stejné jméno, rok ±2 nebo neznámý
        linked = {self.P[k].get("ged") for k in in_tree}
        similar = {}
        def tyear(ind, tags):
            return next((ged_import.year(d) for t, d, pl, x in ged_import.events(ind, self.tree)
                         if t in tags and ged_import.year(d)), None)

        for k in new:
            ev = self.info[k]["events"]
            nb = next((e["year"] for e in ev if e["tag"] == "BIRT" and e.get("year")), None)
            nd = next((e["year"] for e in ev if e["tag"] == "DEAT" and e.get("year")), None)
            married = [m for f in self.P[k].get("f", []) for m in re.findall(r"provd\.\s+(\S+)", str(f))]
            one_word = len(ged_import.tokens(self.P[k]["n"])) < 2   # „Kateřina“, „Markéta“ – jen se shodou roku
            hits, occ = [], occupied.get(k)
            for gid, ind in self.tree_ind.items():
                if gid in linked or (occ and gid == occ["_id"]):
                    continue
                if not ged_import.same_name(self.P[k]["n"], ged_import.name(ind), married):
                    continue
                sx = ged_import.first(ind, "SEX")
                if sx in ("M", "F") and sx != self.sex(k):
                    continue
                tb, td = tyear(ind, ("BIRT", "CHR")), tyear(ind, ("DEAT", "BURI"))
                if (nb and tb and abs(nb - tb) > 2) or (nd and td and abs(nd - td) > 2) \
                        or (nd and tb and tb > nd) or (nb and td and td < nb):
                    continue   # roky se k sobě nehodí (narozen po smrti, zemřel před narozením…)
                if one_word and not ((nb and tb) or (nd and td)):
                    continue
                hits.append(ind)
            if hits:
                similar[k] = hits
        self.diff = dict(new=sorted(new), anchors=sorted(anchors), changed=sorted(changed), in_tree=in_tree,
                         occupied=occupied, similar=similar)
        self.stats["protected"] = sum(1 for k in sel if self.info[k]["protected"])

    def tree_name_lines(self, ind):
        """NAME osoby ze stromu i s podřízenými (GIVN, SURN, _MARNM – FTB ukazuje příjmení po sňatku)."""
        L = []
        for n in self.tree_sub(ind, "NAME")[:1]:
            L.append(f"1 NAME {n['val'].strip()}")
            L += [f"2 {s['tag']} {s['val'].strip()}" for s in n["_sub"] if s["tag"] in ("GIVN", "SURN", "_MARNM")]
        return L

    @staticmethod
    def tree_sub(node, tag):
        return [n for n in node["_sub"] if n["tag"] == tag]

    def anchor_lines(self, k):
        """Kotva: osoba ze stromu jen tak, jak ji strom zná (jméno, pohlaví, narození, úmrtí) – po importu ji Kontrola
        duplicit ve FTB najde a spojí s originálem; nové osoby se připojí přes ni."""
        ind = self.tree_ind[self.P[k]["ged"]]
        L = [f"0 @I{k}@ INDI"]
        if self.personal_photo:
            L.append(f"1 RIN MH:I{k}")
        # I u chráněné osoby: kotva jen vrací do stromu, co v něm už je (jméno, data ze stromu) – nic z projektu.
        L += self.tree_name_lines(ind) or [f"1 NAME {self.P[k]['n']}"]
        sx = [n["val"].strip() for n in self.tree_sub(ind, "SEX")]
        L.append(f"1 SEX {sx[0] if sx else self.sex(k)}")
        for tag in ("BIRT", "DEAT"):
            for e in self.tree_sub(ind, tag)[:1]:
                L.append(f"1 {tag}" + (f" {e['val'].strip()}" if e["val"].strip() else ""))
                L += [f"2 {s['tag']} {s['val'].strip()}" for s in e["_sub"] if s["tag"] in ("DATE", "PLAC")]
        L += gtext(1, "NOTE", f"KOTVA pro sloučení: tato osoba už je ve stromu ({self.P[k]['ged']}). Po importu ji "
                              "spojte s originálem (Nástroje → Kontrola duplicit, nebo Osoba → Sloučit osoby).")
        L += [f"1 FAMC {x}" for x in self.famc.get(k, [])] + [f"1 FAMS {x}" for x in self.fams_of.get(k, [])]
        return L

    def changed_lines(self, k):
        """Změněná osoba (--se-zmenenymi) nebo kotva se změnami: plné údaje projektu, ale jméno jako ve stromu."""
        L = self.person_lines(k)
        ind = self.tree_ind[self.P[k]["ged"]]
        if not self.info[k]["protected"] and self.tree_name_lines(ind):
            i = next(i for i, l in enumerate(L) if l.startswith("1 NAME "))
            j = i + 1
            while j < len(L) and L[j].startswith(("2 GIVN", "2 SURN")):
                j += 1
            L[i:j] = self.tree_name_lines(ind)
        note = gtext(1, "NOTE", f"ZMĚNA pro sloučení: osoba už je ve stromu ({self.P[k]['ged']}); po importu ji spojte "
                                "s originálem (Kontrola duplicit) – přenesou se nové zápisy a obrázky.")
        at = next((i for i, l in enumerate(L) if l.startswith(("1 FAMC", "1 FAMS"))), len(L))
        return L[:at] + note + L[at:]

    def diff_report(self, ged_out):
        """Přehled změn pro uživatele (Markdown): kotvy ke spojení, nové osoby, změny u osob ve stromu."""
        d, tree_name = self.diff, os.path.basename(self.diff_path)

        def tname(k):
            ind = self.tree_ind[self.P[k]["ged"]]
            n = next((x for x in self.tree_sub(ind, "NAME")), None)
            nm = re.sub(r"\s+", " ", n["val"].replace("/", " ")).strip() if n else self.P[k]["n"]
            mar = next((s["val"].strip() for s in (n["_sub"] if n else []) if s["tag"] == "_MARNM"), "")
            return nm + (f" ({mar})" if mar else "")

        def life(k):
            return self.P[k].get("y") or "?"

        order = {k: i for i, k in enumerate(self.persons, 1)}
        fid = lambda k: order.get(k, "?")   # FTB dá importovaným osobám ID podle pořadí v souboru (strom má 500…)
        tid = lambda g: re.sub(r"\D", "", g) or g

        def oname(ind):   # osoba ze stromu podle záznamu
            n = next((x for x in self.tree_sub(ind, "NAME")), None)
            by = next((year(s["val"]) for e in self.tree_sub(ind, "BIRT") for s in e["_sub"] if s["tag"] == "DATE"), None)
            return (re.sub(r"\s+", " ", n["val"].replace("/", " ")).strip() if n else "?") + (f" (* {by})" if by else "")

        def rel(k):   # vztah nové osoby k osobám v exportu
            out = []
            for f in self.fams:
                if k in (f["h"], f["w"]):
                    out += [f"rodič osoby {self.P[c]['n']} ({c})" for c in f["c"]]
                if k in f["c"]:
                    out += [f"dítě osoby {self.P[x]['n']} ({x})" for x in (f["h"], f["w"]) if x]
            return "; ".join(dict.fromkeys(out))

        def conflicts(k):
            ind, out = self.tree_ind[self.P[k]["ged"]], []
            for tag, label in (("BIRT", "narození"), ("DEAT", "úmrtí")):
                ty = next((year(s["val"]) for e in self.tree_sub(ind, tag) for s in e["_sub"] if s["tag"] == "DATE"), None)
                oy = next((e["year"] for e in self.info[k]["events"] if e["tag"] == tag and e.get("year")), None)
                if ty and oy and ty != oy:
                    out.append(f"{label}: strom {ty} × projekt {oy}" + (" (doloženo zápisem)" if self.P[k].get("st") == "doc" else ""))
            return out

        anchors = [k for k in d["anchors"] if k in self.persons]
        L = [f"# Změny pro MyHeritage – {datetime.date.today():%d. %m. %Y}", "",
             f"Původní strom: `{tree_name}` (stažen {self.tree_date:%d. %m. %Y}). Soubor k importu: `{ged_out}`.", "",
             *(["**POZOR: strom je starší než týden** – osoby, které do něj mezitím přibyly, tady nejsou vidět a po importu "
                "by vznikly duplicity. Stáhněte čerstvý GEDCOM a export zopakujte.", ""] if self.tree_age_days > 7 else []),
             "Postup ve Family Tree Builderu (na projektu synchronizovaném s MyHeritage; předtím Soubor → Záloha):",
             "1. Soubor → Import GEDCOM → tento soubor → **Merge into project**; pak FTB restartujte (obrázky).",
             "2. Spojte kotvy (oddíl 1) – dvojice ID: importovaná osoba dostane ve FTB ID podle pořadí v souboru (1, 2, 3…),",
             "   originál má ID ze stromu (500…). Nástroje → **Kontrola duplicit** se sníženou citlivostí (kolem 40 %) najde",
             "   většinu kotev (ověřeno 8 z 10); spojujte **jen dvojice z oddílu 1**, ostatní nálezy nechte (starší podobnosti",
             "   ve stromu, nebo jiné osoby – u nových osob s upozorněním „nespojujte“). Co Kontrola nenajde, spojte ručně.",
             "3. Zkontrolujte nové osoby (jsou připojené ke kotvám), pak **Sync**.",
             "4. Po Sync ve FTB znovu Soubor → Export GEDCOM do `dokumenty/` (`strom_<datum>.ged`) a spusťte "
             "`ged_import.py <nový strom> \"Výchozí osoba\" --ged-id --zapsat` – jinak by se nové osoby příště tvářily jako nové.",
             "", f"## 1. Kotvy – spojit s originálem ({len(anchors)})", ""]
        if not anchors:
            L.append("Žádné – nové osoby se nepřipojují k nikomu ze stromu.")
        for k in anchors:
            novi = sorted({m for f in self.fams if k in (f["h"], f["w"], *f["c"]) for m in (f["h"], f["w"], *f["c"])
                           if m and m in d["new"]})
            L.append(f"- **{self.P[k]['n']}** ({life(k)}): spojit **ID {fid(k)} × ID {tid(self.P[k]['ged'])}** "
                     f"({tname(k)} ve stromu); připojují se: {', '.join(self.P[m]['n'] for m in novi)}")
            jini = [f"{'otce' if m % 2 == 0 else 'matku'} {oname(d['occupied'][m])} ({d['occupied'][m]['_id']})"
                    for m in novi if m in d["occupied"] and m // 2 == k]
            if jini:
                L.append(f"  - **POZOR: ve stromu už má {' a '.join(jini)}** – po spojení by měl dvoje rodiče. Rozhodněte "
                         "podle přehledu nových osob níže (jiný předek → původní rodiče ve stromu odpojit/smazat; tatáž "
                         "osoba → zapsat vazbu a export zopakovat).")
        L += ["", f"## 2. Nové osoby ({len(d['new'])})", ""]
        for k in d["new"]:
            L.append(f"- {k} **{self.P[k]['n']}** ({life(k)}), ve FTB ID {fid(k)}" + (f" – {rel(k)}" if rel(k) else ""))
            for o in d["similar"].get(k, []):
                L.append(f"  - **Možná už ve stromu jinde: {oname(o)} (ID {tid(o['_id'])}).** Tatáž osoba? Pak `zapis.py ged {k} "
                         f"{o['_id']}` a export zopakujte (jinak duplicita); jiná – v Kontrole duplicit dvojici ID {fid(k)} × "
                         f"{tid(o['_id'])} **nespojujte**.")
            if k in d["occupied"]:
                o = d["occupied"][k]
                L.append(f"  - **Ve stromu je na tomto místě {oname(o)} ({o['_id']}).** Jiná osoba (výzkum našel jiného "
                         f"předka)? Pak ve FTB rozhodněte, koho ponechat. Tatáž osoba (jiný pravopis, chyba ve stromu)? Pak "
                         f"`zapis.py ged {k} {o['_id']}` a export zopakujte – jinak vznikne duplicita.")
        ch = [k for k in d["changed"]]
        L += ["", f"## 3. Osoby ve stromu s novými údaji ({len(ch)})" +
              (" – v souboru, spojit v Kontrole duplicit" if self.with_changed else
               " – v souboru nejsou (doplňte ručně, nebo export s --se-zmenenymi)"), ""]
        for k in ch:
            bits = []
            recs = self.records_of(k)
            if recs:
                bits.append("zápisy: " + "; ".join(f"{self.recs[r].get('nazev', r)}" for r in recs))
            docs = [d_.get("popis") or d_["img"] for d_ in self.docs if d_.get("img")
                    and k in {self.canon(x) for x in d_.get("osoby", [])}]
            if docs:
                bits.append(f"obrázky: {len(docs)}")
            bits += conflicts(k)
            L.append(f"- {k} **{self.P[k]['n']}** ({life(k)}) = {tname(k)} ({self.P[k]['ged']}): " + " | ".join(bits))
        rozpory = [(k, c) for k in sorted(d["in_tree"]) if k not in ch for c in conflicts(k)]
        if rozpory:
            L += ["", "## 4. Rozpory údajů u ostatních osob ve stromu", ""]
            L += [f"- {k} {self.P[k]['n']}: {c}" for k, c in rozpory]
        return "\n".join(L) + "\n"

    def build(self):
        self.load()
        self.prepare()
        self.families()
        if self.diff_path:
            self.diff_classify()
        self.sources = {}
        for f in self.fams:
            e, recs = self.marriage(f)   # i u chráněného páru – fakty „×“ se tím označí jako použité (nejdou do poznámek)
            if any(x and self.info[x]["protected"] for x in (f["h"], f["w"])):
                e, recs = None, []
            f["marr"], f["mrecs"] = e, recs if e else []
        self.documents()
        verze = ""
        vf = os.path.join(ROOT, ".skill_verze")
        if os.path.isfile(vf):
            verze = open(vf, encoding="utf-8").read().strip()
        today = datetime.date.today()
        L = ["0 HEAD", "1 SOUR RODOKMEN", "2 NAME Rodokmen (skill pro Claude Code)"]
        if verze:
            L.append(f"2 VERS {verze}")
        L += [f"1 DATE {today.day} {MONTHS[today.month - 1]} {today.year}", "1 SUBM @U1@",
              "1 GEDC", "2 VERS 5.5.1", "2 FORM LINEAGE-LINKED", "1 CHAR UTF-8", "1 LANG Czech",
              "0 @U1@ SUBM", "1 NAME Rodokmen"]
        for k in self.persons:
            if self.diff_path and k in self.diff["in_tree"]:
                anchor_only = k in self.diff["anchors"] and not (self.with_changed and self.has_new(k))
                L += self.anchor_lines(k) if anchor_only else self.changed_lines(k)
            else:
                L += self.person_lines(k)
        for f in self.fams:
            L += self.family_lines(f)
        L += self.sources_lines()
        L.append("0 TRLR")
        return "\n".join(L) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] in (["-h"], ["--help"]):
        sys.exit(__doc__.strip())
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")
    known = {"--bez-obrazku", "--plne-rozliseni", "--zijici", "--vystup", "--koren", "--prepsat", "--slozka",
             "--cp-v-miste", "--rozdil", "--se-zmenenymi"}
    out, root = None, None
    if "--vystup" in argv:
        i = argv.index("--vystup")
        if i + 1 >= len(argv):
            sys.exit("--vystup potřebuje cestu k souboru.")
        out = argv[i + 1]
    if "--koren" in argv:
        i = argv.index("--koren")
        if i + 1 >= len(argv) or not argv[i + 1].isdigit() or int(argv[i + 1]) < 1:
            sys.exit("--koren potřebuje číslo osoby z data/osoby.py (např. --koren 3).")
        root = int(argv[i + 1])
    diff = None
    if "--rozdil" in argv:
        i = argv.index("--rozdil")
        if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
            sys.exit("--rozdil potřebuje původní strom, např. --rozdil dokumenty/strom.ged (GEDCOM z MyHeritage).")
        diff = os.path.abspath(argv[i + 1])
        if not os.path.isfile(diff):
            sys.exit(f"--rozdil: soubor {argv[i + 1]} neexistuje.")
    elif "--se-zmenenymi" in argv:
        sys.exit("--se-zmenenymi patří k --rozdil <strom.ged>.")
    bad = [a for a in argv if a.startswith("--") and a not in known]
    if bad:
        sys.exit(f"Neznámá volba {bad[0]}. Nápověda: --help")
    folder = "--slozka" in argv
    if folder and "--bez-obrazku" in argv:
        sys.exit("--slozka a --bez-obrazku nejdou spolu: složka je pro obrázky; samotný .ged dá --bez-obrazku.")
    ex = Export(with_images="--bez-obrazku" not in argv, full_res="--plne-rozliseni" in argv, living="--zijici" in argv,
                root=root, cp_in_place="--cp-v-miste" in argv)
    if diff:
        ex.diff_path, ex.with_changed = diff, "--se-zmenenymi" in argv
        if not any(p.get("ged") for p in load_people()["P"].values()):
            sys.exit("--rozdil: žádná osoba v data/osoby.py nemá vazbu na strom (ged). Nejdřív "
                     "python3 -I tools/ged_import.py <strom.ged> \"Výchozí osoba\" --ged-id --zapsat.")
    ext = "" if folder else ".zip" if ex.with_images else ".ged"
    if out is None:
        out = os.path.join(ROOT, "pracovni", ("rozdil" if diff else "rodokmen") + (f"_koren{root}" if root else "") + ext)
    out = os.path.abspath(out)
    if folder and out.lower().endswith((".zip", ".ged")):
        sys.exit(f"--vystup {out}: s --slozka je výstup složka (bez přípony .zip/.ged).")
    if not folder and not out.lower().endswith(ext):
        why = "s obrázky je výstup ZIP; samotný .ged dá --bez-obrazku, rozbalenou složku --slozka" if ex.with_images \
            else "--bez-obrazku zapisuje samotný GEDCOM"
        sys.exit(f"--vystup {out}: soubor musí mít příponu {ext} ({why}).")
    web = os.path.abspath(os.path.join(ROOT, "web"))
    if os.path.normcase(out + os.sep).startswith(os.path.normcase(web + os.sep)):
        sys.exit(f"Výstup {out} je ve složce web/ – odtud by soubor šel s webem ven. Zvolte jiné místo "
                 "(výchozí je pracovni/).")
    if folder:
        if os.path.exists(out) and not os.path.isdir(out):
            sys.exit(f"{out} je soubor, ne složka. Zvolte jiný název přes --vystup.")
        taken = os.path.isdir(out) and os.listdir(out)
        if taken and "--prepsat" not in argv:
            sys.exit(f"Složka {out} už existuje a není prázdná. Přepsat export v ní jde volbou --prepsat "
                     "(nahradí se jen rodokmen.ged a media/), nebo zvolte jiný název přes --vystup.")
        if taken and set(os.listdir(out)) - {"rodokmen.ged", "media"}:
            sys.exit(f"Složka {out} obsahuje i jiné soubory než předchozí export – nic nepřepisuji. "
                     "Zvolte jinou složku přes --vystup.")
    elif os.path.exists(out) and "--prepsat" not in argv:
        sys.exit(f"Soubor {out} už existuje. Přepsat ho jde volbou --prepsat, nebo zvolte jiný název přes --vystup.")
    if folder:
        ex.file_base, ex.cutouts_on_person, ex.source_per_record, ex.prefer_full = out, True, True, True
        ex.personal_photo = True
    report = (out if folder else os.path.splitext(out)[0]) + "_zmeny.md" if diff else None
    if report and os.path.exists(report) and "--prepsat" not in argv:
        sys.exit(f"Přehled změn {report} už existuje. Přepsat ho (i s exportem) jde volbou --prepsat.")
    ged = ex.build()
    os.makedirs(out if folder else os.path.dirname(out), exist_ok=True)
    if folder:
        media = os.path.join(out, "media")
        if os.path.isdir(media):
            shutil.rmtree(media)
        # Jako export MyHeritage: UTF-8 s BOM a konce řádků CRLF. Bez BOM Family Tree Builder špatně přečte cestu
        # s diakritikou („Můj disk“) a obrázek nenačte („Failed to Load Image“), i když hlavička uvádí CHAR UTF-8.
        with open(os.path.join(out, "rodokmen.ged"), "w", encoding="utf-8-sig", newline="\r\n") as f:
            f.write(ged)
        for path, src in sorted(ex.media.items()):
            dst = os.path.join(out, *path.split("/"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    elif ex.with_images:
        with zipfile.ZipFile(out, "w") as z:
            z.writestr("rodokmen.ged", ged.encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED)
            for path, src in sorted(ex.media.items()):
                z.write(src, path, compress_type=zipfile.ZIP_STORED)
    else:
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(ged)
    if report:
        with open(report, "w", encoding="utf-8", newline="\n") as f:
            f.write(ex.diff_report(os.path.join(out, "rodokmen.ged") if folder else out))
    st = ex.stats
    n_rec = sum(1 for line in ged.splitlines() if re.match(r"\d+ SOUR @S", line))
    print(f"GEDCOM: {out}")
    if ex.root is not None:
        print(f"  jen osoba č. {ex.root} ({ex.P[ex.root]['n']}) a její předci")
    if diff:
        dd = ex.diff
        print(f"  ROZDÍL proti {os.path.basename(diff)}: nových osob {len(dd['new'])}, kotev ke spojení "
              f"{sum(1 for k in dd['anchors'] if k in ex.persons)}, osob ve stromu s novými údaji {len(dd['changed'])} "
              + ("(v souboru)" if ex.with_changed else "(jen v přehledu; do souboru --se-zmenenymi)"))
        print(f"  Přehled změn a postup: {report}")
        if ex.tree_age_days > 7:
            print(f"  POZOR: strom {os.path.basename(diff)} je z {ex.tree_date:%d. %m. %Y} ({ex.tree_age_days} dní) – mezitím "
                  "mohly ve stromu přibýt osoby (Smart Match, ruční úpravy) a vznikly by duplicity. Stáhněte čerstvý GEDCOM "
                  "(FTB: synchronizovaný projekt → Sync → Soubor → Export GEDCOM), --ged-id --zapsat a export zopakujte.")
        if dd["similar"]:
            print(f"  POZOR: {len(dd['similar'])} nových osob možná už ve stromu je jinde (stejné jméno a rok): "
                  f"{', '.join(map(str, sorted(dd['similar'])))} – ověřte v přehledu změn.")
        if dd["occupied"]:
            print(f"  POZOR: {len(dd['occupied'])} nových osob je na místě, kde strom už někoho má (jiný předek, nebo "
                  f"nespárovaná tatáž osoba): {', '.join(map(str, sorted(dd['occupied'])))} – projděte s uživatelem "
                  "v přehledu změn, než soubor naimportuje.")
    print(f"  {len(ex.persons)} osob, {len(ex.fams)} rodin, {len(ex.sources)} pramenů ({'zápisů' if ex.source_per_record else 'svazků'}), {n_rec} citací zápisů, "
          f"{len(ex.media)} obrázků")
    if folder:
        print(f"  Jak dál: ve Family Tree Builderu importujte {os.path.join(out, 'rodokmen.ged')}, program restartujte "
              "(fotky jsou vidět až po restartu) a pak Sync "
              "(web MyHeritage bere jen .ged a obrázky z něj nenačte). Gramps: importujte týž .ged. Cesty k obrázkům jsou "
              "absolutní (Family Tree Builder relativní nenačte) – složku před importem nepřesouvejte ani "
              "nepřejmenovávejte; po přesunu export zopakujte.")
    elif ex.with_images:
        print("  Jak dál: ZIP rozbalte (rodokmen.ged a media/ vedle sebe), nebo exportujte rovnou s --slozka. Web "
              "MyHeritage bere jen .ged a obrázky z něj nenačte – s obrázky importujte rodokmen.ged ve Family Tree "
              "Builderu a pak Sync. Gramps: importujte .ged.")
    if ex.living:
        print("  POZOR: včetně žijících a nedávno zemřelých (--zijici) – jejich údaje dostane každá služba, kam soubor "
              "nahrajete; na web nepatří.")
        cloud = next((c for c in CLOUD if c.lower() in out.lower()), None)
        print("  Soubor leží " + (f"ve složce synchronizované do cloudu ({cloud}) – " if cloud else
                                  "ve složce projektu; synchronizuje-li ji cloud (Google Disk, OneDrive, Dropbox…), ")
              + "dostane ho i cloud. Po nahrání ho můžete smazat.")
    else:
        print(f"  chránění (žijící / zemřelí do {PROTECT_DEATH_YEARS} let): {st['protected']} osob jen jako „Žijící / Chráněná osoba“; "
              f"vynechané poznámky {st['notes_skipped']}, příčiny úmrtí {st['causes_skipped']}, "
              f"boční příbuzní {st['side_skipped']}, dokumenty s chráněnou osobou {st['docs_skipped']}")
        shared = sorted(r for r in st["rec_protected"]
                        if any(r in ex.records_of(k) for k in ex.persons if not ex.info[k]["protected"]))
        if shared:
            print("  Zápisy, ve kterých je i chráněná osoba (exportovány bez obrázku a přepisu) – zkontrolujte:")
            for r in shared:
                print("    -", r)
    for w in dict.fromkeys(ex.warn):
        print("  POZOR:", w)
    if ex.missing:
        miss = sorted(ex.missing)
        print(f"  Chybí {len(miss)} obrázků (zápis či dokument je v exportu bez obrázku), např.: "
              + ", ".join(miss[:5]) + (" …" if len(miss) > 5 else ""))
    if ex.unparsed:
        print("  Data, která nešla převést (jsou v GEDCOM jako text v závorkách):")
        for u in ex.unparsed:
            print("    -", u)


if __name__ == "__main__":
    main()
