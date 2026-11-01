#!/usr/bin/env python3
"""Export dat rodokmenu (data/*) do webu ve složce web/.

Čte data/osoby.py, data/zaznamy.json, data/svazky.json, data/prepisy.json, data/zvyrazneni.json,
data/mista.json, data/web.json, data/dokumenty.json a markdownové poznámky. Zapisuje
web/src/data/site.json, web/src/generated/*, web/public/{img,zdroje}, web/public/prihlaseni.html,
web/nginx.conf a web/netlify/edge-functions/brana.js.

Spouští se z web/ příkazem `npm run data` (nebo přímo `python3 -I tools/export_web.py`, na Windows `python -I -X utf8 …`).
"""
import hashlib, html, json, os, re, shutil, subprocess, sys, unicodedata
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
DATA = os.path.join(ROOT, "data")
WEB = os.path.join(ROOT, "web")
VYREZY = os.path.join(ROOT, "vyrezy")      # výřezy zápisů a dokumentů (asi 1800 px) – zobrazují se na webu
ZDROJE = os.path.join(ROOT, "zdroje")      # tytéž výřezy v plném rozlišení (proklik)

LINE_COLORS = {8: "#EFB45F", 9: "#F09A78", 10: "#E58AA6", 11: "#B99AE0",
               12: "#86B8E8", 13: "#6FCBB9", 14: "#9CD17A", 15: "#D3D46A"}
STATUS = {"doc": "doloženo matrikou", "prob": "pravděpodobné", "fam": "údaj od rodiny",
          "mh": "jen z cizího rodokmenu", "unk": "neznámé"}
KINDS = {"N": "křest / narození", "O": "sňatek", "Z": "úmrtí", "I": "rejstřík", "S": "sčítání lidu", "J": "jiný pramen"}


def jload(name, default):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_people():
    ns = {}
    exec(open(os.path.join(DATA, "osoby.py"), encoding="utf-8").read(), ns)
    for name, default in (("P", {}), ("SIDE", []), ("LINES", {}), ("ISSUES", []), ("HYPOTEZY", []), ("SAME", {})):
        ns.setdefault(name, default)
    return ns


def record_rows():
    svazky = jload("svazky.json", {})
    rows = []
    for z in jload("zaznamy.json", []):
        sv = svazky.get(z.get("svazek", ""), {})
        key = z["klic"]
        rows.append(dict(
            key=key, kind=z.get("druh", "J"), date=z.get("datum", ""), title=z.get("nazev", key),
            summary=z.get("shrnuti", ""), scan=z.get("snimek", ""),
            archive=sv.get("archiv", ""), volume=sv.get("svazek", ""), vdesc=sv.get("popis", ""),
            portal=sv.get("portal", "archivu"), url=z.get("odkaz") or sv.get("url", ""),
            img=os.path.exists(os.path.join(VYREZY, key + ".jpg")),
            full=os.path.exists(os.path.join(ZDROJE, key + ".jpg")),
        ))
    return rows


def strip_comments(md):
    """Poznámky <!-- … --> v markdownu jsou pro Clauda, ne pro web."""
    return re.sub(r"<!--.*?-->\n?", "", md, flags=re.S)


def story_frontmatter(path, slug, require_rod=True):
    """Načte omezené skalární frontmatter pro příběhy bez další Python závislosti."""
    text = open(path, encoding="utf-8").read()
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.S)
    if not match:
        sys.exit(f"CHYBA: {path}: chybí YAML frontmatter.")
    fields = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        item = re.fullmatch(r"(title|lead|rod):\s*(.*?)\s*", line)
        if not item:
            sys.exit(f"CHYBA: {path}: očekávám pouze skalární pole title, lead a rod.")
        key, value = item.groups()
        if key in fields:
            sys.exit(f"CHYBA: {path}: pole {key} je uvedené vícekrát.")
        if value.startswith('"'):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as ex:
                sys.exit(f"CHYBA: {path}: neplatná hodnota {key}: {ex}")
            if not isinstance(value, str):
                sys.exit(f"CHYBA: {path}: {key} musí být text.")
        elif value.startswith("'"):
            if len(value) < 2 or not value.endswith("'"):
                sys.exit(f"CHYBA: {path}: neuzavřená hodnota {key}.")
            value = value[1:-1].replace("''", "'")
        fields[key] = value
    for key in ("title", "lead") + (("rod",) if require_rod else ()):
        if key not in fields:
            sys.exit(f"CHYBA: {path}: ve frontmatter chybí pole {key}.")
    if not fields["title"].strip():
        sys.exit(f"CHYBA: {path}: title nesmí být prázdný.")
    rod = fields.get("rod")
    if require_rod and not re.fullmatch(r"(?:[8-9]|1[0-5])", rod or ""):
        sys.exit(f"CHYBA: {path}: rod musí být číslo 8 až 15.")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        sys.exit(f"CHYBA: {path}: název souboru musí být bezpečný slug z malých písmen, číslic a pomlček.")
    return dict(slug=slug, title=fields["title"], lead=fields["lead"],
                rod=int(rod) if require_rod else None, text=text)


def slugify(text):
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def norm_answer(text):
    """Stejná normalizace jako v prihlaseni.html: bez diakritiky, malá písmena, jen a-z0-9."""
    t = unicodedata.normalize("NFD", text)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]", "", t)


def years(y):
    y = (y or "").strip()
    ys = re.findall(r"\d{4}", y)
    if not ys:
        return ""
    approx = "≈" if re.match(r"^(asi|≈)", y) else ""
    head, dash, tail = y.partition("–")
    if y.startswith(("?", "†")) or (dash and not re.search(r"\d", head)) or re.match(r"po\b", y):
        # neznámé narození: ukázat jen úmrtí („? – před 1743“ → „† před 1743“, „– po 1921“ → „žil 1921“)
        if re.search(r"\bpo\b", tail or y):
            return "žil " + ys[-1]
        return "† " + ("před " if "před" in y else "") + ys[-1]
    if y.startswith("*"):
        return "* " + ys[0]
    if len(ys) == 1:
        return approx + ys[0]
    second = "?" if "před" in tail else ("po " if re.search(r"\bpo\b", tail) else "") + \
        ("≈" if re.search(r"(asi|≈)", tail) else "") + ys[-1]
    return f"{approx}{ys[0]}–{second}"


def gen(k):
    return k.bit_length() - 1


def relation(k):
    g, male = gen(k), (k % 2 == 0)
    if g == 0:
        return "výchozí osoba rodokmenu"
    if g == 1:
        return "otec" if male else "matka"
    base = "dědeček" if male else "babička"
    if g <= 5:
        return "pra" * (g - 2) + base
    return f"{'předek' if male else 'předkyně'} v {g}. generaci ({'pra' * (g - 2)}{base})"


def placeholder(p):
    return p["n"].startswith(("otec neuveden", "matka neuvedena")) or p["n"] in ("", "?")


def magick_bin():   # ImageMagick 7 (magick), jinak 6 (convert) – ten ale ne na Windows, tam je convert.exe jiný program
    return shutil.which("magick") or (os.name != "nt" and shutil.which("convert")) or None


def size(path):
    w, h = subprocess.run([magick_bin(), path + "[0]", "-format", "%w %h", "info:"],
                          capture_output=True, text=True, check=True).stdout.split()
    return int(w), int(h)


def draw_boxes(src, dst, boxes, small):
    """Kopie výřezu v plném rozlišení s nakreslenými rámečky (pokud má stejný poměr stran jako webový výřez,
    na kterém se rámečky měřily). Vrací False, pak se kopíruje bez rámečků."""
    if not os.path.exists(small) or not magick_bin():
        return False
    (W, H), (w, h) = size(src), size(small)
    if abs(W / H - w / h) > 0.015 * (w / h):
        return False
    sw = max(4, round(W / 450))
    cmd = [magick_bin(), src, "-fill", "none", "-stroke", "#d7302a", "-strokewidth", str(sw)]
    for x0, y0, x1, y1 in boxes:
        cmd += ["-draw", f"rectangle {x0 * W:.0f},{y0 * H:.0f},{x1 * W:.0f},{y1 * H:.0f}"]
    subprocess.run(cmd + ["-quality", "90", dst], check=True)
    return True


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def login_files(cfg):
    """Přihlašovací brána: otázka na webu, na serveru (nginx i Netlify) jen otisk odpovědi (SHA-256).
    Stejný otisk spočítá přihlašovací stránka a uloží ho do cookie – samotná odpověď se nikam neukládá."""
    login = cfg.get("prihlaseni") or {}
    answer = norm_answer(login.get("odpoved", ""))
    tpl = open(os.path.join(WEB, "prihlaseni.sablona.html"), encoding="utf-8").read()
    if "rodokmen:" not in tpl:   # stará šablona (do 0.4.0) ukládá do cookie odpověď – s novou bránou by se nikdo nepřihlásil
        sys.exit("CHYBA: web/ má starou šablonu přihlášení. Aktualizujte projekt: python3 -I <skill>/tools/novy_projekt.py <složka projektu>")
    contact = cfg.get("kontakt") or {}
    hint = ""
    if contact.get("email"):
        hint = (f'Neznáte odpověď? Napište {html.escape(contact.get("jmeno", ""))} na '
                f'<a href="mailto:{html.escape(contact["email"])}">{html.escape(contact["email"])}</a>.')
    page = (tpl.replace("{{NAZEV}}", html.escape(cfg.get("nazev", "Rodokmen")))
               .replace("{{UVOD}}", html.escape(login.get("uvod", "Tenhle web je jen pro rodinu a příbuzné.")))
               .replace("{{OTAZKA}}", html.escape(login.get("otazka", "Odpověď na rodinnou otázku")))
               .replace("{{NAPOVEDA}}", hint))
    write(os.path.join(WEB, "public", "prihlaseni.html"), page)

    edge = os.path.join(WEB, "netlify", "edge-functions", "brana.js")
    if answer:
        digest = hashlib.sha256(("rodokmen:" + answer).encode()).hexdigest()
        nginx_map = f'  "{digest}" 1;'
        write(edge, open(os.path.join(WEB, "netlify", "brana.sablona.js"), encoding="utf-8").read().replace("{{HASH}}", digest))
    else:   # bez přihlášení – web je otevřený
        nginx_map = "  default 1;"
        if os.path.exists(edge):
            os.remove(edge)
    nginx = open(os.path.join(WEB, "nginx.sablona.conf"), encoding="utf-8").read().replace("{{ODPOVED}}", nginx_map)
    write(os.path.join(WEB, "nginx.conf"), nginx)
    return bool(answer)


def main():
    ns = load_people()
    P, LINES, SIDE, ISSUES = ns["P"], ns["LINES"], ns["SIDE"], ns["ISSUES"]
    if 1 not in P:
        sys.exit("V data/osoby.py chybí výchozí osoba (číslo 1).")
    SAME = ns["SAME"]                       # alias Kekulé → kanonické Kekulé (předek v rodokmenu vícekrát)
    cfg = jload("web.json", {})
    login = cfg.get("prihlaseni") or {}
    if "--nasazeni" in sys.argv and not norm_answer(login.get("odpoved", "")) and not login.get("otevreny"):
        sys.exit("CHYBA: v data/web.json není odpověď na přihlašovací otázku – web by byl otevřený komukoli.\n"
                 "Nastavte prihlaseni.odpoved, nebo (jen když to opravdu chcete) prihlaseni.otevreny: true.")
    docs_cfg = jload("dokumenty.json", [])
    recs = {r["key"]: r for r in record_rows()}

    slugs, used = {}, set()
    for k in sorted(P):
        p = P[k]
        if placeholder(p) or k in SAME:
            continue
        yv = (p.get("y") or "").strip()
        ys = [] if yv.startswith(("?", "†")) else re.findall(r"\d{4}", yv)   # rok úmrtí do adresy nedávat
        s = slugify(p["n"] + (" " + ys[0] if ys else ""))
        if s in used or not s:
            s = f"{s}-{k}"
        used.add(s)
        slugs[k] = s
    for a, c in SAME.items():
        slugs[a] = slugs[c]
    aliases_of = {}
    for a, c in SAME.items():
        aliases_of.setdefault(c, []).append(a)

    def line_of(k):
        g = gen(k)
        return k >> (g - 3) if g >= 3 else None

    people = {}
    for k, p in sorted(P.items()):
        if k not in slugs or k in SAME:
            continue
        path, c = [], k
        while c >= 1:
            path.append(slugs.get(c))
            c //= 2
        people[slugs[k]] = dict(
            k=k, slug=slugs[k], name=p["n"], y=p.get("y", ""), years=years(p.get("y")), st=p.get("st", "unk"),
            status=STATUS.get(p.get("st"), ""), gen=gen(k), sex="M" if k == 1 and p.get("sex", "M") == "M" or k > 1 and k % 2 == 0 else "F",
            rel=relation(k), line=line_of(k), facts=p.get("f", []), note=p.get("note", ""), records=[r for r in p.get("r", []) if r in recs],
            father=slugs.get(2 * k), mother=slugs.get(2 * k + 1),
            fatherUnknown=(2 * k in P and placeholder(P[2 * k])), motherUnknown=(2 * k + 1 in P and placeholder(P[2 * k + 1])),
            child=slugs.get(k // 2) if k > 1 else None, spouse=slugs.get(k ^ 1) if k > 1 else None,
            family=None, ownFamily=None, path=path,
            side=[dict(name=s["n"], text=s["t"], records=[r for r in s.get("r", []) if r in recs]) for s in SIDE if s["k"] == k],
            docs=[dict(img=d["img"], caption=d["popis"]) for d in docs_cfg if k in d.get("osoby", [])],
            children=[slugs[c] for c in [k // 2] + [a // 2 for a in aliases_of.get(k, [])] if k > 1 and c in slugs],
            also=[dict(k=a, rel=relation(a), line=line_of(a), child=slugs.get(a // 2)) for a in aliases_of.get(k, [])],
        )
        if aliases_of.get(k):
            for a in aliases_of[k]:
                people[slugs[k]]["records"] = list(dict.fromkeys(people[slugs[k]]["records"] + [r for r in P[a].get("r", []) if r in recs]))
            people[slugs[k]]["facts"] = [f for f in people[slugs[k]]["facts"] if not f.startswith("TÁŽ OSOBA")]

    families = {}
    for k in sorted(P):
        f, m = 2 * k, 2 * k + 1
        if k not in slugs or k in SAME or (f not in slugs and m not in slugs):
            continue
        fs, ms = slugs.get(f), slugs.get(m)
        fid = "-a-".join(x for x in (fs, ms) if x) if fs and ms else (fs or ms) + "-rodina"
        surname = (P[m]["n"].split()[-1] if m in P else "").strip("()?")
        mfacts = [x for x in P.get(f, {}).get("f", []) + P.get(m, {}).get("f", []) if x.startswith("×")]
        marriage = [x for x in mfacts if surname and surname[:5] in x] or mfacts
        frec = P.get(f, {}).get("r", []) + P.get(m, {}).get("r", [])
        child_rec = [r for r in P[k].get("r", []) if r in recs and recs[r]["kind"] == "N"]
        rlist = [r for r in dict.fromkeys(frec) if r in recs and recs[r]["kind"] == "O"] + child_rec
        if fid in families:   # stejný pár potkán dvakrát (předek v rodokmenu vícekrát) – jedna rodina, víc dětí
            fam = families[fid]
            fam["children"].append(slugs[k])
            fam["records"] = list(dict.fromkeys(fam["records"] + rlist))
            fam["side"] += people[slugs[k]]["side"]
        else:
            families[fid] = dict(id=fid, father=fs, mother=ms, fatherUnknown=f in P and placeholder(P[f]),
                                 child=slugs[k], children=[slugs[k]], marriage=marriage, records=rlist,
                                 line=line_of(f) if f in P else line_of(m), gen=gen(f), side=list(people[slugs[k]]["side"]))
        people[slugs[k]]["family"] = fid
        for x in (fs, ms):
            if x:
                people[x]["ownFamily"] = fid

    refs = {}
    for s, p in people.items():
        for r in p["records"] + [r for e in p["side"] for r in e["records"]]:
            refs.setdefault(r, []).append(s)
    hl = jload("zvyrazneni.json", {})
    prep = jload("prepisy.json", {})
    records = []
    for key, r in recs.items():
        r = dict(r)
        r["boxes"] = hl.get(key, {}).get("boxes", [])
        tr = prep.get(key, {})
        r["orig"], r["cs"] = tr.get("orig", ""), tr.get("cs", "")
        r["kindName"] = KINDS.get(r["kind"], r["kind"])
        r["people"] = list(dict.fromkeys(refs.get(key, [])))
        records.append(r)

    lines = {}
    for k, (name, desc) in sorted(LINES.items()):
        if k not in LINE_COLORS:
            continue
        members = [(p["k"], p) for p in people.values() if p["line"] == k]
        members += [(a["k"], p) for p in people.values() for a in p["also"] if a["line"] == k]
        members.sort(key=lambda x: x[0])
        lines[slugify(name)] = dict(k=k, slug=slugify(name), name=name, desc=desc, color=LINE_COLORS[k],
                                    root=slugs.get(k), people=[p["slug"] for _, p in members],
                                    gens={p["slug"]: gen(kk) for kk, p in members})
    lines = {s: l for s, l in lines.items() if l["root"]}
    for p in people.values():
        p["lineSlug"] = next((l["slug"] for l in lines.values() if l["k"] == p["line"]), None)

    places = []
    for name, e in jload("mista.json", {}).items():
        if "lat" not in e:
            continue
        rx = re.compile(e.get("re") or re.escape(name))
        hits = [p for p in people.values() if rx.search(" ".join(p["facts"]))]
        byline = {}
        for p in sorted(hits, key=lambda p: p["k"]):
            byline.setdefault(p["line"] or 0, []).append(p["slug"])
        if e.get("hypoteza"):
            byline = {e.get("rod", 0): []}
        if not byline:
            continue
        yrs = [int(y) for p in hits for y in re.findall(r"\b1[4-9]\d\d\b", p["y"] or "")]
        places.append(dict(name=name, lat=e["lat"], lon=e["lon"], lines=[dict(k=k, people=v) for k, v in sorted(byline.items())],
                           years=[min(yrs), max(yrs)] if yrs else None, hypothesis=bool(e.get("hypoteza"))))

    known = [p for p in people.values() if p["k"] > 1]
    stats = dict(ancestors=len(known), documented=sum(p["st"] == "doc" for p in known), records=len(records),
                 generations=max(p["gen"] for p in people.values()) + 1)
    hypotheses = [dict(line=h.get("rod"), title=h.get("nadpis", "Hypotéza"), text=h.get("text", ""),
                       items=[dict(name=a, text=b) for a, b in h.get("polozky", [])],
                       records=[r for r in h.get("zaznamy", []) if r in recs]) for h in ns["HYPOTEZY"]]

    story_dir = os.path.join(DATA, "pribehy")
    story_files = sorted(
        os.path.join(story_dir, name) for name in os.listdir(story_dir)
        if name.endswith(".md")
    ) if os.path.isdir(story_dir) else []
    stories = [story_frontmatter(path, os.path.splitext(os.path.basename(path))[0])
               for path in story_files]
    multi_stories = bool(stories)
    configured_order = cfg.get("pribehy", [])
    if not isinstance(configured_order, list) or any(not isinstance(slug, str) for slug in configured_order):
        sys.exit("CHYBA: web.json → pribehy musí být seznam slugů příběhů.")
    if multi_stories:
        slugs_in_files = [story["slug"] for story in stories]
        if len(set(slugs_in_files)) != len(slugs_in_files):
            sys.exit("CHYBA: názvy souborů příběhů se po převodu na slug opakují.")
        if configured_order:
            if len(set(configured_order)) != len(configured_order) or set(configured_order) != set(slugs_in_files):
                sys.exit("CHYBA: web.json → pribehy musí obsahovat každý slug v data/pribehy/ právě jednou.")
            by_slug = {story["slug"]: story for story in stories}
            stories = [by_slug[slug] for slug in configured_order]
    elif configured_order:
        sys.exit("CHYBA: web.json → pribehy odkazuje na příběhy, ale data/pribehy/ neobsahuje žádné Markdown soubory.")
    legacy_story = os.path.join(DATA, "pribeh.md")
    if not multi_stories and os.path.exists(legacy_story):
        legacy_text = open(legacy_story, encoding="utf-8").read()
        legacy_match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", legacy_text, re.S)
        legacy_fields = {}
        if legacy_match:
            for line in legacy_match.group(1).splitlines():
                item = re.fullmatch(r"(title|lead):\s*(.*?)\s*", line)
                if item:
                    legacy_fields[item.group(1)] = item.group(2)
        stories = [dict(slug="", title=legacy_fields.get("title", "Příběh"),
                        lead=legacy_fields.get("lead", ""), rod=cfg.get("pribeh", {}).get("rod"),
                        text=legacy_text)]
    has_story = bool(stories)
    public_cfg = {k: v for k, v in cfg.items() if k != "prihlaseni"}
    public_cfg["maPribeh"] = has_story
    public_cfg["maVicePribehu"] = multi_stories
    public_cfg["pribehy"] = [story["slug"] for story in stories] if multi_stories else []
    site = dict(config=public_cfg, places=places, root=slugs[1], aliases={a: slugs[a] for a in SAME}, people=people,
                families=families, records=records, lines=lines,
                issues=[dict(title=i, text="") if isinstance(i, str) else dict(title=i[0], text=i[1]) for i in ISSUES], stats=stats, hypotheses=hypotheses,
                docs=[dict(img=d["img"], caption=d["popis"], people=[slugs[k] for k in d.get("osoby", []) if k in slugs])
                      for d in docs_cfg if os.path.exists(os.path.join(VYREZY, d["img"] + ".jpg"))])

    write(os.path.join(WEB, "src", "data", "site.json"), json.dumps(site, ensure_ascii=False, indent=1))
    gen_dir = os.path.join(WEB, "src", "generated")
    for src, dst in (("archivni_dotazy.md", "dotazy.md"), ("research_log.md", "denik.md"), ("zajimavosti.md", "zajimavosti.md")):
        path = os.path.join(DATA, src)
        text = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        write(os.path.join(gen_dir, dst), strip_comments(re.sub(r"^# .*\n", "", text, count=1)))
    shutil.rmtree(os.path.join(gen_dir, "pribehy"), ignore_errors=True)
    if multi_stories:
        for story in stories:
            write(os.path.join(gen_dir, "pribehy", story["slug"] + ".md"), strip_comments(story["text"]))
    write(os.path.join(gen_dir, "pribehy.json"), json.dumps(
        [{key: story[key] for key in ("slug", "title", "lead", "rod")} for story in stories if story["slug"]],
        ensure_ascii=False, indent=1))
    story = stories[0]["text"] if stories else "---\ntitle: Příběh\nlead: ''\n---\n"
    write(os.path.join(gen_dir, "pribeh.md"), strip_comments(story))

    hrefs = os.path.join(gen_dir, "fan_hrefs.json")
    json.dump({k: f"/osoba/{s}/" for k, s in slugs.items()}, open(hrefs, "w", encoding="utf-8", newline="\n"))
    subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(TOOLS, "fan_chart.py"),
                    os.path.join(gen_dir, "fan.svg"), "--web", hrefs], check=True, capture_output=True)

    gated = login_files(cfg)

    copied = 0
    zv = os.path.join(DATA, "zvyrazneni.json")
    hl_mtime = os.path.getmtime(zv) if os.path.exists(zv) else 0
    for sub, src_dir in (("img", VYREZY), ("zdroje", ZDROJE)):
        dst_dir = os.path.join(WEB, "public", sub)
        os.makedirs(dst_dir, exist_ok=True)
        for key in list(recs) + [d["img"] for d in docs_cfg] + ([cfg["uvod"]["foto"]] if cfg.get("uvod", {}).get("foto") else []):
            src = os.path.join(src_dir, key + ".jpg")
            dst = os.path.join(dst_dir, key + ".jpg")
            if not os.path.exists(src):
                continue
            boxes = hl.get(key, {}).get("boxes", [])
            stale = not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst) \
                or (sub == "zdroje" and boxes and hl_mtime > os.path.getmtime(dst))
            if not stale:
                continue
            if sub == "zdroje" and boxes and draw_boxes(src, dst, boxes, os.path.join(VYREZY, key + ".jpg")):
                copied += 1
                continue
            shutil.copy2(src, dst)
            copied += 1
    print(f"{len(people)} osob, {len(families)} rodin, {len(records)} zápisů, {len(lines)} rodů, {len(places)} míst; "
          f"zkopírováno {copied} obrázků; přihlášení {'zapnuté' if gated else 'VYPNUTÉ (web je otevřený)'}")

    # odkazy v textech, které nikam nevedou (adresa osoby se změní třeba doplněním roku narození: jan-novak → jan-novak-1798)
    targets = dict(osoba=people, zdroj=recs, rod=lines, rodina=families)
    texts = {f: open(os.path.join(gen_dir, f), encoding="utf-8").read() for f in ("pribeh.md", "zajimavosti.md")}
    if multi_stories:
        texts.update({f"pribehy/{story['slug']}.md": story["text"] for story in stories})
    texts["web.json"] = json.dumps(cfg, ensure_ascii=False)
    texts["osoby.py (hypotézy)"] = json.dumps(hypotheses, ensure_ascii=False)
    targets["pribehy"] = {story["slug"] for story in stories if story["slug"]}
    broken = [(f, m.group(0)) for f, t in texts.items()
              for m in re.finditer(r"/(osoba|zdroj|rod|rodina|pribehy)/([^/\s)\"'#?<>\]]+)", t)
              if m.group(2) not in targets[m.group(1)]]
    for f, link in dict.fromkeys(broken):
        print(f"POZOR: nefunkční odkaz {link}/ v {f} – oprav ho (adresy stránek jsou ve web/src/data/site.json)")


if __name__ == "__main__":
    main()
