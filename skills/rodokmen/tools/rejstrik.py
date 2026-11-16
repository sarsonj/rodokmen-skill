#!/usr/bin/env python3
"""Rejstřík projektu v SQLite – rychlé hledání napříč všemi daty bez načítání velkých souborů.

Zdrojem pravdy zůstávají textové soubory v data/, kontext/ (a kniha/podklady/, pokud je). Databáze
pracovni/rejstrik.sqlite se z nich vytváří automaticky (při každém dotazu, když se některý zdroj změnil) a do gitu nejde.
Nemá žádné závislosti (Python ≥ 3.9 se SQLite FTS5, který má běžný Python).

Použití (z kořene projektu; na Windows `python -I -X utf8 tools/rejstrik.py …`):
  rejstrik.py                         jen (znovu) vytvoří rejstřík a vypíše počty
  rejstrik.py hledej "Novák kovář"     fulltext bez ohledu na diakritiku (FTS5: AND, OR, NOT, "přesná fráze", předpona*)
        --zdroj denik,zajimavost      omezit na druhy zdrojů (seznam: rejstrik.py druhy)
        -n 30                         počet výsledků (výchozí 20); neověřené výstupy pomocníků jsou až na konci
  rejstrik.py osoba 8                 vše o osobě: fakta, zápisy, deník, otázky, zajímavosti, dotazy…
  rejstrik.py osoba "Dvořák"          totéž podle části jména (přímí předci i SIDE)
  rejstrik.py zapis <klíč|část>       zápis: datum, svazek a snímek, přepis s překladem, osoby, řádky deníku
  rejstrik.py svazek <id|"Název 05">  svazek: které snímky jsme už prošli (z deníku, s výsledkem) a zápisy z něj
  rejstrik.py denik 443-445           vypíše řádky deníku (zkráceně; --cele celé); denik --posledni 3 = konec deníku
  rejstrik.py misto Lhota             předci, zápisy a texty spojené s místem (regulární výraz z mista.json)
  rejstrik.py rod 15                  přehled rodu (číslo 8–15 z LINES): osoby po generacích se stavem
  rejstrik.py tema [vojáci]           témata zajímavostí (štítek téma:) a texty k jednomu tématu
  rejstrik.py podklady rod 15         podklad ke kapitole → pracovni/podklady/rod_15.md (také: osoba 8, misto Lhota,
        --do kniha/podklady/rejstrik  tema vojáci): osoby, fakta, zápisy s překladem, zajímavosti, deník, otázky, co chybí
  rejstrik.py chybi                   kontrolní seznamy pro knihu (bez přepisu, bez zajímavosti, nepropojené zápisy…)
  rejstrik.py sql "SELECT …"          libovolný dotaz (tabulky: rejstrik.py sql "SELECT name FROM sqlite_master")

Propojení textu s osobou: číslo osoby „č. 84“ / „#84“, klíč zápisu, štítek <!-- osoby: 84, 85 --> (zajímavosti).
Čísla „č. N“ v textu mohou být i čísla zápisu v knize a stejné jméno může mít jiný člověk – zmínky z textu
(jak='text' podle čísla, jak='jmeno' podle jména a příjmení, jak='jmeno_rok' / 'jmeno_vice' když stejné
jméno má víc předků a rok u jména rozhodl / nerozhodl, jak='side' zmínka bočního příbuzného z SIDE → jeho předek)
jsou vodítko, ne jistota; jisté je jen jak='citace'/'stitek'. Jména se hledají ve všech pádech (Pešek/Peška, Karel/Karla).
"""
import json, os, re, runpy, sqlite3, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
DB = os.path.join(ROOT, "pracovni", "rejstrik.sqlite")
DRUH_MD = {  # soubor v data/ → druh; ostatní data/*.md mají druh podle jména souboru (ukoly.md → ukoly)
    "zajimavosti.md": "zajimavost", "pribeh.md": "pribeh", "archivni_dotazy.md": "dotaz",
    "udaje_od_rodiny.md": "rodina", "historie_kol.md": "historie", "STAV.md": "stav",
}
NE_MD = ("research_log.md", "README.md")  # deník má vlastní tabulku
KONTEXT = ("kontext", os.path.join("kniha", "podklady"))  # ručně vedené podklady mimo data/ (jsou-li)
PODKLADY = os.path.join(ROOT, "pracovni", "podklady")  # výchozí složka výstupu `podklady` (přepínač --do)
VYSTUPY = {os.path.normcase(os.path.join(ROOT, "kniha", "podklady", "rejstrik")), os.path.normcase(PODKLADY)}


def zdroje_md():
    """Markdown soubory v data/ s druhem; dělí se podle nadpisů (##) nebo odrážek (historie, stav)."""
    if not os.path.isdir(DATA):
        return {}
    return {f: DRUH_MD.get(f, os.path.splitext(f)[0].lower()) for f in sorted(os.listdir(DATA))
            if f.endswith(".md") and f not in NE_MD}
VYGENEROVANO = "Vygenerováno nástrojem `tools/rejstrik.py podklady`"  # takové soubory se neindexují
RE_SEP = re.compile(r"(?<!\\)\|")
RE_CIS = re.compile(r"(?:\bč\.|#)\s*(\d{1,5}(?:\s*(?:,|a|–|-)\s*\d{1,5})*)")
RE_STITEK = re.compile(r"<!--\s*((?:osoby|rod|téma|tema|roky|místa):.*?)-->")


def zdroje():
    out = [os.path.join(DATA, f) for f in ("osoby.py", "zaznamy.json", "prepisy.json", "svazky.json",
                                           "mista.json", "dokumenty.json", "research_log.md", *zdroje_md())]
    for d, _, fs in kontext_walk():
        out += [os.path.join(d, f) for f in fs if f.endswith((".md", ".txt"))]
    out.append(os.path.abspath(__file__))  # změna nástroje = nové schéma rejstříku
    return [p for p in out if os.path.exists(p)]


def kontext_walk():
    """Složky s podklady mimo data/: kontext/ a ručně vedené kniha/podklady/ (bez vygenerovaných podkladů)."""
    for k in KONTEXT:
        for d, ds, fs in os.walk(os.path.join(ROOT, k)):
            ds[:] = [x for x in ds if os.path.normcase(os.path.join(d, x)) not in VYSTUPY]
            yield d, ds, fs


def jload(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def rod_of(k):
    if k < 8:
        return None
    return k >> (k.bit_length() - 4)


def gen_of(k):
    return k.bit_length() - 1  # 0 = výchozí osoba, 1 = rodiče, 2 = prarodiče …


def bez_diakritiky(t):
    return "".join(ch for ch in unicodedata.normalize("NFD", t) if not unicodedata.combining(ch)).lower()


def kmen(w):
    """Regulární kmen slova bez diakritiky pro všechny pády: Dvořáková → dvorak, Anna → ann,
    pohyblivé e: Pešek → pes(e)k (Peška), Karel → kar(e)l (Karla), Němec → nem(e)c (Němce)."""
    w = re.sub(r"ov[aá]$", "", bez_diakritiky(w))
    if len(w) > 3 and w[-1] in "aeiouy":
        w = w[:-1]
    if len(w) >= 4 and re.search(r"[^aeiouy]e[kclnr]$", w):
        return re.escape(w[:-2]) + "e?" + w[-1]
    return re.escape(w)


def jmenne_vzory(P):
    """Vzor „Křestní (+ jedno slovo) Příjmení“ bez diakritiky a s volnou koncovkou (Jana Nováka, Anně Dvořákové,
    Matěje Peška)."""
    out = []
    for k, p in P.items():
        if p.get("st") == "unk":
            continue
        n = p.get("n", "")
        slova = re.findall(r"[^\W\d_]+", re.sub(r"\(.*?\)", "", n))
        if len(slova) < 2:
            continue
        prijmeni = [slova[-1]] + [z for z in re.findall(r"\(([^\W\d_]{4,})\)", n)]  # Jan Malý (Novotný)
        alt = "|".join(kmen(x) for x in prijmeni if len(x) >= 4)
        if alt:
            out.append((k, re.compile(rf"\b{kmen(slova[0])}\w*\s+(?:\w+\s+)?(?:{alt})\w*")))
    return out


def volny_re(misto, vzor):
    """Vzor z mista.json + volnější tvar pro víceslovná jména (deník píše jen „Ústí“, „Brandýs“)."""
    prvni = re.split(r"[ ,]", misto)[0]
    if prvni != misto and len(prvni) >= 5:
        kmen = prvni[:-2] if len(prvni) >= 6 else prvni[:-1]   # Kostelec n. L. → Kostel (Kostelci), ne Kostelní
        vzor = f"(?:{vzor})|{re.escape(kmen)}(?!n[íi])"
    return re.compile(vzor)


def rozpeti(y):
    """Roky života (od, do) z pole y – velkoryse: „* 1839“ → 1839–1929, „† před 1728“ → 1638–1728."""
    roky = [int(x) for x in re.findall(r"\d{4}", y or "")]
    if not roky:
        return (0, 0)  # neznámé – rokem nejde rozhodnout
    if len(roky) >= 2:
        return (min(roky) - 2, max(roky) + 1)
    if "†" in y or "před" in y:
        return (roky[0] - 90, roky[0] + 1)
    return (roky[0] - 2, roky[0] + 90)


def kmeny_jmena(jmeno):
    """Kmeny křestního jména a příjmení jako regulární výrazy (Anna Dvořáková → ann, dvorak; Pešek → pes(e)k)."""
    out = []
    for w in re.findall(r"[^\W\d_]+", re.sub(r"\(.*?\)", "", jmeno or "")):
        if len(w) >= 3 and bez_diakritiky(w) not in ("otec", "neuveden", "starsi", "mladsi"):
            out.append(re.compile(kmen(w)))
    return out


def cisla(text, platna, jmena=None):
    """Čísla osob zmíněná v textu (č. 84, č. 164, 165, #84). Číslo platí, jen když před ním (do 150 znaků)
    stojí křestní jméno i příjmení té osoby (v libovolném tvaru); v závorce za jménem („Novák (č. 84)“) stačí jedno z nich – jinak jde nejspíš o číslo zápisu v knize („po sobě č. 6, č. 7“)."""
    found = set()
    holy = bez_diakritiky(text)
    for m in RE_CIS.finditer(text):
        okno = holy[max(0, m.start() - 150):m.end()]
        for n in re.findall(r"\d+", m.group(1)):
            n = int(n)
            kmeny_n = jmena.get(n, [re.compile(r"\?")]) if jmena else []
            v_zavorce = text[max(0, m.start() - 2):m.start()].strip().endswith("(")   # „Novák (č. 84)“
            if jmena is not None and not kmeny_n:
                continue  # osoba bez jména („otec neuveden“) – číslo nejde ověřit
            if n in platna and (jmena is None or (any(k.search(okno[-80:]) for k in kmeny_n) if v_zavorce
                                                 else all(k.search(okno) for k in kmeny_n))):
                found.add(n)
    return found


def oddily(text, druh):
    """Rozdělí markdown na (nadpis, text): podle ## / ### nadpisů, u historie/stavu po odrážkách."""
    if druh in ("historie", "stav"):
        parts, cur = [], None
        for line in text.splitlines():
            if line.startswith("- "):
                if cur:
                    parts.append(cur)
                m = re.match(r"- \*\*(.+?)\*\*", line)
                cur = [(m.group(1) if m else line[2:])[:100], line]
            elif line.startswith("#"):
                if cur:
                    parts.append(cur)
                cur = None
            elif cur:
                cur[1] += "\n" + line
        if cur:
            parts.append(cur)
        return [tuple(p) for p in parts]
    parts = re.split(r"(?m)^(#{2,3} .*)$", text)
    out = [("(úvod)", parts[0])] if parts[0].strip() else []
    for i in range(1, len(parts), 2):
        out.append((parts[i].lstrip("#").strip(), parts[i + 1]))
    return out


def postav():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    tmp = DB + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    c = sqlite3.connect(tmp)
    c.executescript("""
    CREATE TABLE osoby(cislo INTEGER PRIMARY KEY, jmeno, roky, st, rod INTEGER, generace INTEGER, note, druh);
    CREATE TABLE side(id INTEGER PRIMARY KEY, k INTEGER, jmeno, text);
    CREATE TABLE fakta(cislo INTEGER, fakt);
    CREATE TABLE osoba_zaznam(cislo INTEGER, klic, side_id INTEGER);
    CREATE TABLE hypoteza_zaznam(hypoteza INTEGER, klic);
    CREATE TABLE zaznamy(klic PRIMARY KEY, svazek, snimek, druh, datum, rok INTEGER, nazev, shrnuti, odkaz);
    CREATE TABLE prepisy(klic PRIMARY KEY, orig, cs);
    CREATE TABLE svazky(id PRIMARY KEY, archiv, portal, svazek, popis, url);
    CREATE TABLE mista(misto PRIMARY KEY, re, lat, lon);
    CREATE TABLE lines(rod INTEGER PRIMARY KEY, nazev, popis);
    CREATE TABLE otazky(druh, rod INTEGER, nadpis, text);
    CREATE TABLE denik(radek PRIMARY KEY, datum, zdroj, rozsah, hledano, vysledek, citace);
    CREATE TABLE texty(id INTEGER PRIMARY KEY, druh, soubor, nadpis, text);
    CREATE TABLE zminky(druh, ref, cislo INTEGER, jak);   -- ref = klíč zápisu / řádek deníku / id textu
    CREATE TABLE zminky_mist(druh, ref, misto);
    CREATE TABLE stitky(druh, ref, klic, hodnota);       -- štítky <!-- osoby: … · rod: … · téma: … -->
    CREATE VIRTUAL TABLE fts USING fts5(druh UNINDEXED, ref UNINDEXED, nadpis, text,
                                        tokenize='unicode61 remove_diacritics 2');
    """)
    d = runpy.run_path(os.path.join(DATA, "osoby.py"))
    P, SIDE = d.get("P", {}), d.get("SIDE", [])
    platna = set(P)
    mista = jload("mista.json") if os.path.exists(os.path.join(DATA, "mista.json")) else {}
    mre = [(m, volny_re(m, v["re"])) for m, v in mista.items() if v.get("re")]
    for m, v in mista.items():
        c.execute("INSERT INTO mista VALUES(?,?,?,?)", (m, v.get("re"), v.get("lat"), v.get("lon")))

    vzory = jmenne_vzory(P)
    # boční příbuzní (SIDE): zmínka jménem → vazba na předka, ke kterému patří (jak='side', vodítko)
    vzory_side = [(s["k"], v[0][1], rozpeti(" ".join(re.findall(r"\((.*?)\)", s.get("n", "")))))
                  for s in SIDE if s.get("k") in platna
                  for v in [jmenne_vzory({0: {"n": s.get("n", "")}})] if v]
    pocet_vzoru, skupiny = {}, {}
    for k, rx in vzory:  # stejné jméno u víc předků (Jan Novák č. 16, 64, 256) → zmínka je nejednoznačná
        pocet_vzoru[rx.pattern] = pocet_vzoru.get(rx.pattern, 0) + 1
        skupiny.setdefault(rx.pattern, []).append(k)
    zivot = {k: rozpeti(p.get("y", "")) for k, p in P.items()}
    kmeny = {k: kmeny_jmena(p.get("n")) for k, p in P.items()}

    def fts(druh, ref, nadpis, text, osoby_text=True):
        c.execute("INSERT INTO fts VALUES(?,?,?,?)", (druh, str(ref), nadpis or "", text or ""))
        for m, rx in mre:
            if rx.search(text or "") or rx.search(nadpis or ""):
                c.execute("INSERT INTO zminky_mist VALUES(?,?,?)", (druh, str(ref), m))
        if osoby_text:
            cel = (nadpis or "") + " " + (text or "")
            podle_cisla = cisla(cel, platna, kmeny)
            for n in podle_cisla:
                c.execute("INSERT INTO zminky VALUES(?,?,?,?)", (druh, str(ref), n, "text"))
            holy = bez_diakritiky(cel)
            for n, rx in vzory:
                if n in podle_cisla:
                    continue
                shody = list(rx.finditer(holy))
                if not shody:
                    continue
                if pocet_vzoru[rx.pattern] == 1:
                    jak = "jmeno"
                else:  # stejné jméno má víc předků: rozhodne rok u jména (± 80 znaků), jinak nejednoznačné
                    roky = {int(y) for m in shody for y in re.findall(r"\b1[5-9]\d\d\b", holy[max(0, m.start() - 80):m.end() + 80])}
                    sedi = [k for k in skupiny[rx.pattern] if any(zivot[k][0] <= y <= zivot[k][1] for y in roky)]
                    jak = "jmeno_rok" if sedi == [n] else "jmeno_vice"
                    if len(sedi) == 1 and sedi != [n]:
                        continue  # rok ukazuje na jiného stejnojmenného předka
                c.execute("INSERT INTO zminky VALUES(?,?,?,?)", (druh, str(ref), n, jak))
            side_k = set()
            for k, rx, (od, do) in vzory_side:
                for m in rx.finditer(holy):  # rok u jména (± 80 znaků) musí sedět na roky příbuzného, jsou-li známé
                    roky = [int(y) for y in re.findall(r"\b1[5-9]\d\d\b", holy[max(0, m.start() - 80):m.end() + 80])]
                    if not od or not roky or any(od <= y <= do for y in roky):
                        side_k.add(k)
                        break
            for n in side_k:
                c.execute("INSERT INTO zminky VALUES(?,?,?,'side')", (druh, str(ref), n))

    for k, p in P.items():
        f = p.get("f", [])
        c.execute("INSERT INTO osoby VALUES(?,?,?,?,?,?,?,?)",
                  (k, p.get("n"), p.get("y"), p.get("st"), rod_of(k), gen_of(k), p.get("note", ""), "P"))
        c.executemany("INSERT INTO fakta VALUES(?,?)", [(k, x) for x in f])
        c.executemany("INSERT INTO osoba_zaznam VALUES(?,?,NULL)", [(k, r) for r in p.get("r", [])])
        fts("osoba", k, f"č. {k} {p.get('n')} ({p.get('y', '')})", "\n".join(f) + "\n" + p.get("note", ""), False)
    for i, s in enumerate(SIDE):
        c.execute("INSERT INTO side VALUES(?,?,?,?)", (i, s.get("k"), s.get("n"), s.get("t", "")))
        c.executemany("INSERT INTO osoba_zaznam VALUES(?,?,?)", [(s.get("k"), r, i) for r in s.get("r", [])])
        fts("side", i, f"{s.get('n')} (k č. {s.get('k')})", s.get("t", ""), False)
    for rod, (nazev, popis) in d.get("LINES", {}).items():
        c.execute("INSERT INTO lines VALUES(?,?,?)", (rod, nazev, popis))
    for i, it in enumerate(d.get("ISSUES", [])):
        nad, txt = (it[0], it[1]) if isinstance(it, (list, tuple)) else (str(it)[:80], str(it))
        c.execute("INSERT INTO otazky VALUES('issue',NULL,?,?)", (nad, txt))
        fts("issue", i, nad, txt)
    for i, h in enumerate(d.get("HYPOTEZY", [])):
        c.execute("INSERT INTO otazky VALUES('hypoteza',?,?,?)", (h.get("rod"), h.get("nadpis"), h.get("text")))
        c.executemany("INSERT INTO hypoteza_zaznam VALUES(?,?)", [(i, z) for z in h.get("zaznamy", [])])
        fts("hypoteza", i, h.get("nadpis"), h.get("text"))

    for z in jload("zaznamy.json"):
        rok = re.findall(r"\d{4}", z.get("datum", "") or "")
        c.execute("INSERT INTO zaznamy VALUES(?,?,?,?,?,?,?,?,?)",
                  (z["klic"], z.get("svazek"), z.get("snimek"), z.get("druh"), z.get("datum"),
                   int(rok[-1]) if rok else None, z.get("nazev"), z.get("shrnuti"), z.get("odkaz")))
        fts("zaznam", z["klic"], z.get("nazev"), (z.get("shrnuti") or "") + " " + (z.get("datum") or ""), False)
    for k, v in jload("prepisy.json").items():
        c.execute("INSERT INTO prepisy VALUES(?,?,?)", (k, v.get("orig"), v.get("cs")))
        fts("prepis", k, k, (v.get("orig") or "") + "\n" + (v.get("cs") or ""), False)
    for k, v in jload("svazky.json").items():
        c.execute("INSERT INTO svazky VALUES(?,?,?,?,?,?)",
                  (k, v.get("archiv"), v.get("portal"), v.get("svazek"), v.get("popis"), v.get("url")))
        fts("svazek", k, v.get("svazek"), json.dumps(v, ensure_ascii=False), False)
    if os.path.exists(os.path.join(DATA, "dokumenty.json")):  # dokumenty od rodiny, mapy, fotky (popis + osoby)
        for d in jload("dokumenty.json"):
            fts("dokument", d.get("img"), d.get("img"), d.get("popis", ""), False)
            for n in d.get("osoby", []):
                if n in platna:
                    c.execute("INSERT INTO zminky VALUES('dokument',?,?,'citace')", (str(d.get("img")), n))

    klic_osoby = {}
    for cislo, klic in c.execute("SELECT cislo, klic FROM osoba_zaznam WHERE side_id IS NULL").fetchall():
        klic_osoby.setdefault(klic, set()).add(cislo)

    # deník: tabulka | # | datum | zdroj | rozsah | hledáno | výsledek | citace |
    videne = set()  # číslo řádku omylem dvakrát → druhý výskyt „12b“, ať se neztratí
    with open(os.path.join(DATA, "research_log.md"), encoding="utf-8") as f:
        for line in f:
            if not re.match(r"\|\s*\d+[a-z]?\s*\|", line):  # i dodatečně vložené řádky „53b“
                continue
            # svislítko v textu buňky je escapované „\|“ (tools/denik.py) – dělit jen na neescapovaných
            cells = [x.strip().replace("\\|", "|") for x in RE_SEP.split(line.strip().strip("|"))]
            # Deník má řádky ve třech tvarech: 7 sloupců (# datum zdroj rozsah hledáno výsledek citace),
            # 6 sloupců (rozsah je součástí zdroje) a 5 sloupců (navíc bez citace). Sjednotit na 7.
            if len(cells) == 6:
                cells.insert(3, "")
            elif len(cells) == 5:
                cells.insert(3, "")
                cells.append("")
            elif len(cells) > 7:  # svislítko v textu – zbytek patří do výsledku
                vys = 4 if cells[4].startswith("**") and not cells[5].startswith("**") else 5  # 6sloupcový tvar?
                cells = cells[:vys] + [" | ".join(cells[vys:-1]), cells[-1]]
                if vys == 4:
                    cells.insert(3, "")
            cells += [""] * (7 - len(cells))
            n = int(cells[0]) if cells[0].isdigit() else cells[0]
            while n in videne:
                n = f"{n}b" if isinstance(n, int) else n + "b"
            videne.add(n)
            c.execute("INSERT OR REPLACE INTO denik VALUES(?,?,?,?,?,?,?)", tuple([n] + cells[1:7]))
            fts("denik", n, f"ř. {n} {cells[1]} – {cells[4][:120]}", " | ".join(cells[2:7]))
            for klic in re.findall(r"[a-z0-9_]{12,}", cells[6]):
                for cislo in klic_osoby.get(klic, ()):
                    c.execute("INSERT INTO zminky VALUES('denik',?,?,'citace')", (str(n), cislo))

    tid = 0
    for soubor, druh in zdroje_md().items():
        p = os.path.join(DATA, soubor)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            txt = f.read()
        for nad, body in oddily(txt, druh):
            tid += 1
            c.execute("INSERT INTO texty VALUES(?,?,?,?,?)", (tid, druh, "data/" + soubor, nad, body))
            fts(druh, tid, nad, body)
            for m in RE_STITEK.finditer(body):  # <!-- osoby: 6, 13 · rod: 8 · téma: víra, svatba -->
                for cast in m.group(1).split("·"):
                    if ":" not in cast:
                        continue
                    klic, hodn = (x.strip() for x in cast.split(":", 1))
                    for h in (x.strip() for x in hodn.split(",") if x.strip()):
                        c.execute("INSERT INTO stitky VALUES(?,?,?,?)", (druh, str(tid), klic, h))
                        if klic == "osoby" and h.isdigit() and int(h) in platna:
                            c.execute("INSERT INTO zminky VALUES(?,?,?,'stitek')", (druh, str(tid), int(h)))
    for d_, _, fs in kontext_walk():
        for fn in sorted(fs):
            if not fn.endswith((".md", ".txt")):
                continue
            p = os.path.join(d_, fn)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            druh = "pomocnik" if "/pomocnici/" in rel else "kontext"
            with open(p, encoding="utf-8", errors="replace") as f:
                txt = f.read()
            if VYGENEROVANO in txt[:400]:  # starší výstup `podklady` uložený mezi ručními podklady
                continue
            for nad, body in (oddily(txt, druh) if fn.endswith(".md") else [(fn, txt)]):
                tid += 1
                c.execute("INSERT INTO texty VALUES(?,?,?,?,?)", (tid, druh, rel, nad, body))
                fts(druh, tid, f"{rel}: {nad}", body)
    c.commit()
    c.close()
    os.replace(tmp, DB)


def otevri():
    if not os.path.exists(DB) or max(os.path.getmtime(p) for p in zdroje()) > os.path.getmtime(DB):
        postav()
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def jr(jmeno, roky):
    """„Jan Novák (1801–1860)“, bez prázdných závorek, když roky nejsou známé."""
    return f"{jmeno} ({roky})" if (roky or "").strip() else f"{jmeno}"


def kratce(t, n=300):
    t = re.sub(r"\s+", " ", t or "").strip()
    return t if len(t) <= n else t[:n] + "…"


def popis_ref(c, druh, ref):
    if druh in ("denik",):
        return f"deník ř. {ref}"
    if druh in ("osoba",):
        return f"osoba č. {ref}"
    if druh in ("zaznam", "prepis", "svazek", "dokument"):
        return f"{druh} {ref}"
    r = c.execute("SELECT soubor, nadpis FROM texty WHERE id=?", (ref,)).fetchone()
    return f"{r['soubor']} › {kratce(r['nadpis'], 70)}" if r else f"{druh} {ref}"


def hledej(c, dotaz, zdroj=None, n=20):
    sql = ("SELECT druh, ref, snippet(fts, 3, '»', '«', ' … ', 24) s FROM fts WHERE fts MATCH ?"
           + (" AND druh IN (%s)" % ",".join("?" * len(zdroj)) if zdroj else "") + " ORDER BY druh='pomocnik', rank LIMIT ?")
    try:
        rows = c.execute(sql, [dotaz] + (zdroj or []) + [n]).fetchall()
    except sqlite3.OperationalError:  # neplatná syntaxe FTS → hledej jako frázi
        rows = c.execute(sql, ['"' + dotaz.replace('"', '') + '"'] + (zdroj or []) + [n]).fetchall()
    for r in rows:
        znacka = "[NEOVĚŘENO – pomocník] " if r["druh"] == "pomocnik" else ""
        print(f"- {znacka}{popis_ref(c, r['druh'], r['ref'])}: {kratce(r['s'], 260)}")
    if not rows:
        print("Nic nenalezeno.")


def najdi_osobu(c, q):
    if q.isdigit():
        return [int(q)], []
    like = f"%{q}%"
    return ([r[0] for r in c.execute("SELECT cislo FROM osoby WHERE jmeno LIKE ?", (like,))],
            [r[0] for r in c.execute("SELECT id FROM side WHERE jmeno LIKE ?", (like,))])


def osoba(c, q):
    cisla_, sides = najdi_osobu(c, q)
    for k in cisla_:
        o = c.execute("SELECT * FROM osoby WHERE cislo=?", (k,)).fetchone()
        if not o:
            print(f"Osoba č. {k} v osoby.py není.")
            continue
        rod = c.execute("SELECT nazev FROM lines WHERE rod=?", (o["rod"],)).fetchone()
        print(f"## č. {k} {jr(o['jmeno'], o['roky'])} – stav {o['st']}, generace {o['generace']}"
              + (f", rod {o['rod']} {rod[0]}" if rod else ""))
        rodice = c.execute("SELECT cislo, jmeno, st FROM osoby WHERE cislo IN (?,?)", (2 * k, 2 * k + 1)).fetchall()
        if rodice:
            print("Rodiče: " + "; ".join(f"č. {r[0]} {r[1]} ({r[2]})" for r in rodice))
        for (f,) in c.execute("SELECT fakt FROM fakta WHERE cislo=?", (k,)):
            print(f"  · {f}")
        if o["note"]:
            print(f"Poznámka: {kratce(o['note'], 600)}")
        print("Zápisy:")
        for z in c.execute("SELECT z.klic, z.datum, z.nazev, (p.klic IS NOT NULL) ma_prepis FROM osoba_zaznam oz "
                           "JOIN zaznamy z ON z.klic=oz.klic LEFT JOIN prepisy p ON p.klic=z.klic "
                           "WHERE oz.cislo=? AND oz.side_id IS NULL", (k,)):
            print(f"  - {z['klic']} ({z['datum']}): {z['nazev']}" + ("" if z["ma_prepis"] else "  [BEZ PŘEPISU]"))
        s = c.execute("SELECT jmeno FROM side WHERE k=?", (k,)).fetchall()
        if s:
            print(f"Boční příbuzní (SIDE k č. {k}): " + "; ".join(r[0] for r in s))
        zm = c.execute("SELECT druh, ref, group_concat(DISTINCT jak) jak FROM zminky WHERE cislo=? "
                       "GROUP BY druh, ref ORDER BY druh, CAST(ref AS INTEGER)", (k,)).fetchall()
        for jak, popis in (("citace", "cituje jeho zápis"), ("text", "zmíněn číslem"), ("jmeno", "jen shoda jména – ověř"),
                           ("jmeno_rok", "jméno má i jiný předek, rozhodl rok u jména – ověř"),
                           ("jmeno_vice", "shoda jména, které má i jiný předek – NEJEDNOZNAČNÉ"),
                           ("side", "zmínka o bočním příbuzném z SIDE – ověř")):
            slabe = {"jmeno", "jmeno_vice", "jmeno_rok", "side"}
            den = [r["ref"] for r in zm if r["druh"] == "denik" and jak in r["jak"].split(",")
                   and not (jak in slabe and set(r["jak"].split(",")) - slabe)]
            if den:
                print(f"Deník ({popis}): ř. {', '.join(den)}")
        for r in zm:
            if r["druh"] != "denik":
                print(f"  ~ {popis_ref(c, r['druh'], r['ref'])} ({r['jak']})")
        print()
    for i in sides:
        s = c.execute("SELECT * FROM side WHERE id=?", (i,)).fetchone()
        print(f"## SIDE {s['jmeno']} – k č. {s['k']}\n  {kratce(s['text'], 600)}\n")
    if not cisla_ and not sides:
        print("Nenalezeno.")


def zapis(c, q):
    rows = c.execute("SELECT * FROM zaznamy WHERE klic=?", (q,)).fetchall() or \
        c.execute("SELECT * FROM zaznamy WHERE klic LIKE ? ORDER BY rok", (f"%{q}%",)).fetchall()
    if not rows:
        print("Zápis nenalezen (zkus `hledej`).")
        return
    if len(rows) > 5:
        for z in rows:
            print(f"- {z['klic']} ({z['datum']}): {z['nazev']}")
        print(f"({len(rows)} zápisů – upřesni klíč)")
        return
    for z in rows:
        sv = c.execute("SELECT svazek, archiv FROM svazky WHERE id=?", (z["svazek"],)).fetchone()
        print(f"## {z['klic']} – {z['nazev']} ({z['datum']}, {z['druh']})")
        print(f"Svazek: {z['svazek']}" + (f" = {sv['svazek']} ({sv['archiv']})" if sv else " [NENÍ v svazky.json]")
              + f", snímek {z['snimek']}" + (f"\nOdkaz: {z['odkaz']}" if z["odkaz"] else ""))
        if z["shrnuti"]:
            print(f"Shrnutí: {z['shrnuti']}")
        p = c.execute("SELECT orig, cs FROM prepisy WHERE klic=?", (z["klic"],)).fetchone()
        print(f"Přepis: {p['orig']}\nPřeklad: {p['cs']}" if p else "[BEZ PŘEPISU]")
        os_ = c.execute("SELECT oz.cislo, oz.side_id, o.jmeno, s.jmeno sj FROM osoba_zaznam oz LEFT JOIN osoby o "
                        "ON o.cislo=oz.cislo AND oz.side_id IS NULL LEFT JOIN side s ON s.id=oz.side_id WHERE oz.klic=?",
                        (z["klic"],)).fetchall()
        print("Osoby: " + ("; ".join(f"SIDE {r['sj']} (k č. {r['cislo']})" if r["side_id"] is not None
                                     else f"č. {r['cislo']} {r['jmeno']}" for r in os_) or "žádné"))
        den = [str(r[0]) for r in c.execute("SELECT radek FROM denik WHERE citace LIKE ? OR vysledek LIKE ?",
                                            (f"%{z['klic']}%", f"%{z['klic']}%"))]
        if den:
            print("Deník: ř. " + ", ".join(den))
        print()


RE_SN = re.compile(r"sn\.\s*\d+(?:\s*[–-]\s*\d+)?(?:\s*(?:,|a)\s*\d+(?:\s*[–-]\s*\d+)?)*")


def svazek(c, q):
    """Svazek: co z něj už máme a které snímky jsme prošli – odpověď na „nehledali jsme to už?“."""
    sv = c.execute("SELECT * FROM svazky WHERE id=?", (q,)).fetchall() or \
        c.execute("SELECT * FROM svazky WHERE svazek LIKE ? OR id LIKE ?", (f"%{q}%", f"%{q}%")).fetchall()
    if len(sv) > 8:
        for r in sv:
            print(f"- {r['id']}: {kratce(r['svazek'], 120)}")
        print(f"({len(sv)} svazků – upřesni)")
        return
    vzory = [] if sv else [re.escape(q)]
    for r in sv:
        print(f"## {r['id']} – {r['svazek']} ({r['archiv']})" + (f"\n{r['url']}" if r["url"] else ""))
        vzory.append(re.escape(r["id"]))
        m = re.match(r"ebad_(?:a_)?(\d+)$", r["id"])
        if m:
            vzory.append(rf"\bid\s*{m.group(1)}\b")
        nazev = re.split(r",| – ", r["svazek"] or "")[0].strip()
        if re.search(r"\d", nazev) and len(nazev) >= 5:   # „Poděbrady 05“, ne obecný název
            vzory.append(r"\s+".join(re.escape(w) for w in nazev.split()) + r"(?!\d)")
        zz = c.execute("SELECT klic, snimek FROM zaznamy WHERE svazek=? ORDER BY CAST(snimek AS INTEGER)",
                       (r["id"],)).fetchall()
        if zz:
            print(f"Zápisy z něj ({len(zz)}): " + "; ".join(f"sn. {z['snimek']} {z['klic']}" for z in zz))
    rx = re.compile("|".join(vzory))
    print("Deník (rozsahy snímků hned za zmínkou svazku – ověř v řádku, co přesně se četlo):")
    nic = True
    for d in c.execute("SELECT * FROM denik ORDER BY CAST(radek AS INTEGER), radek"):
        cel = " | ".join(x or "" for x in (d["zdroj"], d["rozsah"], d["hledano"], d["vysledek"]))
        ms = list(rx.finditer(cel))
        if not ms:
            continue
        nic = False
        sn = []
        for m in ms:
            for x in RE_SN.findall(cel[m.end():m.end() + 160]):
                if x not in sn:
                    sn.append(x)
        print(f"  ř. {d['radek']} ({d['datum']}) {'; '.join(sn) or '(bez čísla snímku)'} – hledáno: "
              f"{kratce(d['hledano'], 110)} → {kratce(d['vysledek'].replace('*', ''), 160)}")
    if nic:
        print("  nic – svazek v deníku není (nebo je zapsán jinak; zkus `hledej`)")


def denik(c, rest):
    cele = "--cele" in rest
    rest = [x for x in rest if x != "--cele"]
    if rest and rest[0] == "--posledni":
        n = int(rest[1]) if len(rest) > 1 else 3
        rows = c.execute("SELECT * FROM denik ORDER BY CAST(radek AS INTEGER) DESC, radek DESC LIMIT ?",
                         (n,)).fetchall()[::-1]
    else:
        chtene = set()
        for cast in " ".join(rest).replace(",", " ").split():
            a, _, b = cast.replace("–", "-").partition("-")
            chtene |= set(range(int(a), int(b or a) + 1))
        rows = [r for r in c.execute("SELECT * FROM denik ORDER BY CAST(radek AS INTEGER), radek")
                if int(re.match(r"\d+", str(r["radek"])).group()) in chtene]
    f = (lambda t, n: t or "") if cele else kratce
    for r in rows:
        print(f"ř. {r['radek']} ({r['datum']}) {f((r['zdroj'] or '') + ' ' + (r['rozsah'] or ''), 400)}\n"
              f"  hledáno: {f(r['hledano'], 200)}\n  výsledek: {f(r['vysledek'], 900)}"
              + (f"\n  citace: {r['citace']}" if r["citace"] and r["citace"] not in ("–", "-") else ""))
    if not rows:
        print("Žádné takové řádky.")


def misto(c, q):
    m = c.execute("SELECT misto, re FROM mista WHERE misto LIKE ?", (f"%{q}%",)).fetchall()
    if not m:
        print("Místo není v mista.json – zkus `hledej`.")
        return
    for mm in m:
        rx = volny_re(mm["misto"], mm["re"])
        print(f"## {mm['misto']}")
        os_ = [(k, j, y, st) for k, j, y, st, f in c.execute(
            "SELECT o.cislo, o.jmeno, o.roky, o.st, group_concat(f.fakt, ' ') FROM osoby o "
            "LEFT JOIN fakta f ON f.cislo=o.cislo GROUP BY o.cislo") if rx.search(f or "")]
        print("Předci s údajem v místě: " + "; ".join(f"č. {k} {j} ({y + ', ' if y else ''}{st})" for k, j, y, st in os_))
        zz = [r for r in c.execute("SELECT klic, datum FROM zaznamy ORDER BY rok") ]
        zz = [r for r in zz if rx.search(c.execute("SELECT coalesce(nazev,'')||' '||coalesce(shrnuti,'') FROM zaznamy WHERE klic=?",
                                                   (r[0],)).fetchone()[0])]
        print(f"Zápisy ({len(zz)}): " + ", ".join(f"{k} ({d})" for k, d in zz))
        for druh, n in c.execute("SELECT druh, count(*) FROM zminky_mist WHERE misto=? GROUP BY druh", (mm["misto"],)):
            print(f"  zmínky – {druh}: {n}")
        print(f"(Texty: rejstrik.py hledej \"{mm['misto']}\" --zdroj zajimavost,kontext,dotaz)\n")


def rod(c, r):
    r = int(r)
    l = c.execute("SELECT * FROM lines WHERE rod=?", (r,)).fetchone()
    print(f"## Rod {r}: {l['nazev'] if l else '?'} – {l['popis'] if l else ''}")
    for g, k, j, y, st in c.execute("SELECT generace, cislo, jmeno, roky, st FROM osoby WHERE rod=? OR cislo=? "
                                    "ORDER BY generace, cislo", (r, r)):
        nz = c.execute("SELECT count(*) FROM osoba_zaznam WHERE cislo=? AND side_id IS NULL", (k,)).fetchone()[0]
        print(f"  {'  ' * (g - 3)}g{g} č. {k} {jr(j, y)} {st}, zápisů {nz}")
    for h in c.execute("SELECT nadpis FROM otazky WHERE druh='hypoteza' AND rod=?", (r,)):
        print(f"  Hypotéza: {h[0]}")
    zaj = c.execute("SELECT DISTINCT t.nadpis FROM texty t WHERE t.druh='zajimavost' AND CAST(t.id AS TEXT) IN "
                    "(SELECT ref FROM stitky WHERE druh='zajimavost' AND klic='rod' AND hodnota=? UNION "
                    " SELECT z.ref FROM zminky z JOIN osoby o ON o.cislo=z.cislo WHERE z.druh='zajimavost' "
                    " AND z.jak='stitek' AND (o.rod=? OR o.cislo=?)) ORDER BY t.id", (str(r), r, r)).fetchall()
    print(f"  Zajímavosti ({len(zaj)}): " + "; ".join(z[0] for z in zaj))


def tema(c, q):
    if not q:
        for h, n in c.execute("SELECT hodnota, count(*) FROM stitky WHERE klic IN ('téma','tema') "
                              "GROUP BY hodnota ORDER BY count(*) DESC"):
            print(f"{h}: {n}")
        return
    for t in c.execute("SELECT t.soubor, t.nadpis FROM stitky s JOIN texty t ON CAST(t.id AS TEXT)=s.ref "
                       "WHERE s.klic IN ('téma','tema') AND s.hodnota LIKE ? ORDER BY t.id", (f"%{q}%",)):
        print(f"- {t[0]} › {t[1]}")
    print(f"(Další výskyty v datech: rejstrik.py hledej \"{q}\")")


def podklady(c, druh, q):
    """Podklad ke kapitole: všechno o vybraných osobách v jednom souboru <PODKLADY>/<druh>_<q>.md."""
    if druh == "osoba":
        cis, _ = najdi_osobu(c, q)
    elif druh == "rod":
        cis = [r[0] for r in c.execute("SELECT cislo FROM osoby WHERE rod=? OR cislo=? ORDER BY cislo", (int(q), int(q)))]
    elif druh == "misto":
        m = c.execute("SELECT misto, re FROM mista WHERE misto LIKE ?", (f"%{q}%",)).fetchone()
        if not m:
            sys.exit("Místo není v mista.json.")
        rx = volny_re(m[0], m[1])
        cis = [k for k, f in c.execute("SELECT o.cislo, group_concat(f.fakt, ' ') FROM osoby o LEFT JOIN fakta f "
                                       "ON f.cislo=o.cislo GROUP BY o.cislo ORDER BY o.cislo") if rx.search(f or "")]
    elif druh == "tema":
        cis = [r[0] for r in c.execute(
            "SELECT DISTINCT z.cislo FROM stitky s JOIN zminky z ON z.druh=s.druh AND z.ref=s.ref AND z.jak='stitek' "
            "WHERE s.klic IN ('téma','tema') AND s.hodnota LIKE ? ORDER BY z.cislo", (f"%{q}%",))]
    else:
        sys.exit("podklady osoba|rod|misto|tema <hodnota>")
    cis = [k for k in cis if c.execute("SELECT 1 FROM osoby WHERE cislo=? AND st!='unk'", (k,)).fetchone()]
    ph = ",".join("?" * len(cis)) or "NULL"
    out = [f"# Podklady: {druh} {q}", "",
           f"{VYGENEROVANO} z dat projektu – neupravovat, vytvořit znovu. "
           "Stav: doc = doloženo matrikou, prob = pravděpodobné, fam = jen od rodiny/rodinné knihy (jen vodítko).", ""]
    # zajímavosti a texty podle štítků / témat
    zaj_ids = [r[0] for r in c.execute(
        f"SELECT DISTINCT ref FROM zminky WHERE druh='zajimavost' AND jak='stitek' AND cislo IN ({ph})", cis)]
    if druh == "rod":
        zaj_ids += [r[0] for r in c.execute("SELECT ref FROM stitky WHERE druh='zajimavost' AND klic='rod' AND hodnota=?", (q,))]
    if druh == "tema":
        zaj_ids += [r[0] for r in c.execute("SELECT ref FROM stitky WHERE druh='zajimavost' AND klic IN ('téma','tema') "
                                            "AND hodnota LIKE ?", (f"%{q}%",))]
    if druh == "misto":
        zaj_ids += [r[0] for r in c.execute("SELECT ref FROM zminky_mist WHERE druh='zajimavost' AND misto LIKE ?", (f"%{q}%",))]
    zaj_ids = sorted(set(zaj_ids), key=int)
    out.append(f"## Osoby ({len(cis)})")
    out += [f"- č. {k} {jr(j, y)} – {st}" for k, j, y, st in
            c.execute(f"SELECT cislo, jmeno, roky, st FROM osoby WHERE cislo IN ({ph}) ORDER BY cislo", cis)]
    out += ["", f"## Zajímavosti ({len(zaj_ids)})", ""]
    for i in zaj_ids:
        t = c.execute("SELECT nadpis, text FROM texty WHERE id=?", (int(i),)).fetchone()
        out += [f"### {t[0]}", re.sub(r"<!--.*?-->\n?", "", t[1]).strip(), ""]
    for k in cis:
        o = c.execute("SELECT * FROM osoby WHERE cislo=?", (k,)).fetchone()
        out += [f"## č. {k} {jr(o['jmeno'], o['roky'])} – {o['st']}, generace {o['generace']}"]
        rod_ = c.execute("SELECT nazev FROM lines WHERE rod=?", (o["rod"],)).fetchone()
        rodice = c.execute("SELECT cislo, jmeno FROM osoby WHERE cislo IN (?,?)", (2 * k, 2 * k + 1)).fetchall()
        dite = c.execute("SELECT cislo, jmeno FROM osoby WHERE cislo=?", (k // 2,)).fetchone() if k > 1 else None
        out.append("Rod: " + (rod_[0] if rod_ else "–") + " · rodiče: " + ("; ".join(f"č. {a} {b}" for a, b in rodice) or "–")
                   + (f" · dítě v linii: č. {dite[0]} {dite[1]}" if dite else ""))
        out += [f"- {f[0]}" for f in c.execute("SELECT fakt FROM fakta WHERE cislo=?", (k,))]
        if o["note"]:
            out += ["", f"Poznámka: {o['note']}"]
        for z in c.execute("SELECT z.*, p.cs FROM osoba_zaznam oz JOIN zaznamy z ON z.klic=oz.klic "
                           "LEFT JOIN prepisy p ON p.klic=z.klic WHERE oz.cislo=? AND oz.side_id IS NULL ORDER BY z.rok", (k,)):
            out += ["", f"**Zápis {z['klic']}** – {z['nazev']} ({z['datum']}), {z['odkaz']}", f"{z['shrnuti']}"]
            if z["cs"]:
                out.append(f"> Překlad: {kratce(z['cs'], 1500)}")
        side = c.execute("SELECT jmeno, text FROM side WHERE k=?", (k,)).fetchall()
        if side:
            out += ["", "Boční příbuzní:"] + [f"- {a}: {kratce(b, 400)}" for a, b in side]
        for d_, nad, txt in c.execute("SELECT druh, nadpis, text FROM otazky WHERE text LIKE ? OR text LIKE ?",
                                      (f"%č. {k})%", f"%č. {k},%")):
            out += ["", f"Otevřená otázka ({d_}): **{nad}** – {kratce(txt, 800)}"]
        den = c.execute("SELECT d.radek, d.datum, d.hledano, d.vysledek, group_concat(DISTINCT z.jak) jak FROM zminky z "
                        "JOIN denik d ON CAST(d.radek AS TEXT)=z.ref WHERE z.druh='denik' AND z.cislo=? "
                        "GROUP BY d.radek ORDER BY CAST(d.radek AS INTEGER), d.radek", (k,)).fetchall()
        if den:
            out += ["", "Hledání v deníku (i neúspěšná):"]
            for r in den:
                jaky = set(r["jak"].split(","))
                jist = ("" if jaky - {"jmeno", "jmeno_vice", "jmeno_rok", "side"} else
                        " _(NEJEDNOZNAČNÉ – stejné jméno má i jiný předek)_" if "jmeno_vice" in jaky else
                        " _(zmínka o bočním příbuzném – ověř)_" if jaky == {"side"} else
                        " _(jen shoda jména – ověř, zda jde o tutéž osobu)_")
                out.append(f"- ř. {r['radek']} ({r['datum']}) {kratce(r['hledano'], 150)} → {kratce(r['vysledek'], 500)}{jist}")
        dot = c.execute("SELECT DISTINCT t.nadpis FROM zminky z JOIN texty t ON CAST(t.id AS TEXT)=z.ref "
                        "WHERE z.druh='dotaz' AND z.cislo=?", (k,)).fetchall()
        if dot:
            out += ["", "Archivní dotazy: " + "; ".join(d[0] for d in dot)]
        out.append("")
    mista_ = sorted({m for (m,) in c.execute(f"SELECT DISTINCT zm.misto FROM zminky_mist zm WHERE zm.druh='osoba' "
                                               f"AND CAST(zm.ref AS INTEGER) IN ({ph})", cis)})
    out += ["## Místa a historické souvislosti", "Místa osob: " + ", ".join(mista_), ""]
    for m in mista_:
        kt = c.execute("SELECT DISTINCT t.soubor, t.nadpis FROM zminky_mist zm JOIN texty t ON CAST(t.id AS TEXT)=zm.ref "
                       "WHERE zm.druh='kontext' AND zm.misto=?", (m,)).fetchall()
        if kt:
            out.append(f"- {m}: " + "; ".join(f"{a} › {kratce(b, 60)}" for a, b in kt))
    out += ["", "## Kontrolní seznam (co chybí)"]
    bez = [f"č. {k}" for k in cis if not c.execute("SELECT 1 FROM zminky WHERE druh='zajimavost' AND jak='stitek' AND cislo=?",
                                                    (k,)).fetchone()]
    out.append("- Osoby bez zajímavosti: " + (", ".join(bez) or "žádné"))
    out.append("- Jen pravděpodobné nebo od rodiny (v textu tak označit): " + ", ".join(
        f"č. {k}" for (k,) in c.execute(f"SELECT cislo FROM osoby WHERE cislo IN ({ph}) AND st IN ('prob','fam','mh')", cis)))
    out.append("- Chybějící rodiče (konec linie): " + ", ".join(
        f"č. {k}" for k in cis if not c.execute("SELECT 1 FROM osoby WHERE cislo IN (?,?) AND st!='unk'", (2 * k, 2 * k + 1)).fetchone()))
    cil = os.path.join(PODKLADY, f"{druh}_{re.sub(r'[^a-z0-9]+', '_', bez_diakritiky(q)).strip('_')}.md")
    os.makedirs(os.path.dirname(cil), exist_ok=True)
    with open(cil, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    print(f"{os.path.relpath(cil, ROOT)}: {len(cis)} osob, {len(zaj_ids)} zajímavostí, {os.path.getsize(cil) // 1024} kB")


def chybi(c):
    def vypis(nadpis, rows, fmt):
        print(f"## {nadpis} ({len(rows)})")
        for r in rows[:60]:
            print("  - " + fmt(r))
        if len(rows) > 60:
            print(f"  … a dalších {len(rows) - 60}")
        print()
    vypis("Zápisy bez přepisu", c.execute("SELECT z.klic, z.datum FROM zaznamy z LEFT JOIN prepisy p ON p.klic=z.klic "
                                          "WHERE p.klic IS NULL").fetchall(), lambda r: f"{r[0]} ({r[1]})")
    vypis("Zápisy nepropojené s žádnou osobou, SIDE ani hypotézou",
          c.execute("SELECT klic, nazev FROM zaznamy WHERE klic NOT IN (SELECT klic FROM osoba_zaznam) "
                    "AND klic NOT IN (SELECT klic FROM hypoteza_zaznam)").fetchall(),
          lambda r: f"{r[0]}: {r[1]}")
    vypis("Odkazy osob na neexistující zápis",
          c.execute("SELECT cislo, klic FROM osoba_zaznam WHERE klic NOT IN (SELECT klic FROM zaznamy)").fetchall(),
          lambda r: f"č. {r[0]} → {r[1]}")
    vypis("Doložení předci (doc) bez zajímavosti (podle štítků <!-- osoby: … -->)",
          c.execute("SELECT cislo, jmeno, roky FROM osoby WHERE st='doc' AND cislo NOT IN "
                    "(SELECT cislo FROM zminky WHERE druh='zajimavost' AND jak='stitek') ORDER BY cislo").fetchall(),
          lambda r: f"č. {r[0]} {jr(r[1], r[2])}")
    vypis("Zajímavosti bez štítku osob",
          c.execute("SELECT nadpis FROM texty WHERE druh='zajimavost' AND nadpis!='(úvod)' AND CAST(id AS TEXT) NOT IN "
                    "(SELECT ref FROM stitky WHERE druh='zajimavost')").fetchall(),
          lambda r: r[0])
    vypis("Řádky deníku bez propojené osoby",
          c.execute("SELECT radek, substr(hledano,1,90) FROM denik WHERE CAST(radek AS TEXT) NOT IN "
                    "(SELECT ref FROM zminky WHERE druh='denik')").fetchall(), lambda r: f"ř. {r[0]}: {r[1]}")


def main(a):
    if not a:
        postav()
        c = otevri()
        for t in ("osoby", "side", "zaznamy", "prepisy", "svazky", "denik", "texty", "zminky", "zminky_mist"):
            print(f"{t}: {c.execute(f'SELECT count(*) FROM {t}').fetchone()[0]}")
        print(f"→ {os.path.relpath(DB, ROOT)}")
        return
    cmd, rest = a[0], a[1:]
    c = otevri()
    if cmd == "hledej":
        zdroj, n, q = None, 20, []
        i = 0
        while i < len(rest):
            if rest[i] == "--zdroj":
                zdroj = rest[i + 1].split(","); i += 2
            elif rest[i] == "-n":
                n = int(rest[i + 1]); i += 2
            else:
                q.append(rest[i]); i += 1
        hledej(c, " ".join(q), zdroj, n)
    elif cmd == "osoba":
        osoba(c, " ".join(rest))
    elif cmd == "zapis":
        zapis(c, " ".join(rest))
    elif cmd == "svazek":
        svazek(c, " ".join(rest))
    elif cmd == "denik":
        denik(c, rest)
    elif cmd == "misto":
        misto(c, " ".join(rest))
    elif cmd == "rod":
        rod(c, rest[0])
    elif cmd == "chybi":
        chybi(c)
    elif cmd == "tema":
        tema(c, " ".join(rest))
    elif cmd == "podklady":
        global PODKLADY
        if "--do" in rest:
            i = rest.index("--do")
            PODKLADY = os.path.join(ROOT, rest[i + 1])
            rest = rest[:i] + rest[i + 2:]
        podklady(c, rest[0], " ".join(rest[1:]))
    elif cmd == "druhy":
        for r in c.execute("SELECT druh, count(*) FROM fts GROUP BY druh"):
            print(f"{r[0]}: {r[1]}")
    elif cmd == "sql":
        for r in c.execute(" ".join(rest)):
            print(" | ".join(kratce(str(x), 200) for x in r))
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
