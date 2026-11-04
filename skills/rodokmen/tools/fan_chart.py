#!/usr/bin/env python3
"""Vějíř předků (360°) z data/osoby.py jako SVG.
Použití: fan_chart.py <out_dir>                         (plakát: SVG + HTML s nadpisem a legendou, PNG přes Chrome, je-li k dispozici)
         fan_chart.py <out_file.svg> --web <hrefs.json>  (holé klikací SVG pro web – volá ho export_web.py)"""
import html, json, math, os, re, subprocess, sys
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, "vystupy")
WEB = "--web" in sys.argv
HREFS = {int(k): v for k, v in json.load(open(sys.argv[sys.argv.index("--web") + 1])).items()} if WEB else {}
CHROME = next((c for c in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                           "C:/Program Files/Google/Chrome/Application/chrome.exe",
                           "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
                           "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
                           "google-chrome", "chromium", "chromium-browser")
               if os.path.exists(c) or __import__("shutil").which(c)), None)

ns = {}
exec(open(os.path.join(ROOT, "data", "osoby.py"), encoding="utf-8").read(), ns)
P, LINES = ns["P"], ns.get("LINES", {})
WEBCFG = json.load(open(os.path.join(ROOT, "data", "web.json"), encoding="utf-8")) if os.path.exists(os.path.join(ROOT, "data", "web.json")) else {}

W, H = (4520, 4520) if WEB else (4600, 5650)
CX, CY = (2260, 2260) if WEB else (W / 2, 2760)
RINGS = [(0, 240), (240, 440), (440, 650), (650, 880), (880, 1100), (1100, 1380),
         (1380, 1640), (1640, 1870), (1870, 2010), (2010, 2130), (2130, 2240)]
BASE = {8: "#EFB45F", 9: "#F09A78", 10: "#E58AA6", 11: "#B99AE0",
        12: "#86B8E8", 13: "#6FCBB9", 14: "#9CD17A", 15: "#D3D46A"}
LIGHT = {3: 0.0, 4: 0.18, 5: 0.32, 6: 0.44, 7: 0.55, 8: 0.64, 9: 0.72, 10: 0.78}
SIDE_COL = {0: "#E9DFCF", 1: "#D6E2EC"}          # father / mother half, generations 1–2
EMPTY, FONT = "#ECE8E0", "Helvetica Neue, Helvetica, Arial, sans-serif"
MINF = {5: 15, 6: 13, 7: 11, 8: 9.5, 9: 8.5, 10: 7.5}
MAXF = {5: 26, 6: 22, 7: 18, 8: 14, 9: 11, 10: 9}


def mix(hex_, t):
    r, g, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % tuple(round(c + (255 - c) * t) for c in (r, g, b))


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
        return approx + ys[0] + ("–?" if dash else "")
    second = "?" if "před" in tail else ("po " if re.search(r"\bpo\b", tail) else "") + \
        ("≈" if re.search(r"(asi|≈)", tail) else "") + ys[-1]
    return f"{approx}{ys[0]}–{second}"


def pt(r, a):
    t = math.radians(a)
    return CX + r * math.sin(t), CY - r * math.cos(t)


def sector(r0, r1, a0, a1):
    large = 1 if a1 - a0 > 180 else 0
    x0, y0 = pt(r1, a0); x1, y1 = pt(r1, a1); x2, y2 = pt(r0, a1); x3, y3 = pt(r0, a0)
    if r0 == 0:
        return f"M{CX},{CY} L{x0:.1f},{y0:.1f} A{r1},{r1} 0 {large} 1 {x1:.1f},{y1:.1f} Z"
    return (f"M{x0:.1f},{y0:.1f} A{r1},{r1} 0 {large} 1 {x1:.1f},{y1:.1f} "
            f"L{x2:.1f},{y2:.1f} A{r0},{r0} 0 {large} 0 {x3:.1f},{y3:.1f} Z")


def gen(k):
    return k.bit_length() - 1


# Předek v rodokmenu vícekrát (SAME = {alias: hlavní číslo}): na místě aliasu kresli hlavní osobu i celou její větev
# předků (alias << d | (k − (hlavní << d))), jinak by sektory nad aliasem zůstaly prázdné (#31).
SAME = ns.get("SAME", {})
VLASTNI = set(P) - set(SAME)   # osoby bez zrcadlených kopií – pro statistiku
for _a, _c in sorted(SAME.items()):
    for _k in sorted(P):
        _d = gen(_k) - gen(_c)
        if _d >= 0 and _k >> _d == _c:
            _t = (_a << _d) | (_k - (_c << _d))
            if _d == 0 or _t not in P:
                P[_t] = P[_k]
            if _k in HREFS:
                HREFS.setdefault(_t, HREFS[_k])


def angles(k):
    g = gen(k); n = 2 ** g; i = k - n
    span = 360 / n
    return 180 + i * span, 180 + (i + 1) * span


def fill(k):
    g = gen(k); p = P.get(k)
    if p is None or p.get("st") == "unk":
        return EMPTY
    if g == 0:
        return "#5B4A3A"
    if g <= 2:
        return SIDE_COL[(k >> (g - 1)) & 1]
    c = mix(BASE[k >> (g - 3)], LIGHT[g])
    return mix(c, 0.45) if p.get("st") in ("prob", "mh") else c


def fit(text, avail, fmax, fmin):
    return max(fmin, min(fmax, avail / (0.56 * max(len(text), 1))))


paths, defs, texts, links = [], [], [], []
slots = sorted({k for k in P if gen(k) < len(RINGS)} |   # vějíř má 11 prstenců (generace 0–10); starší předky vynech
               {c for k in P for c in (2 * k, 2 * k + 1) if gen(c) <= 10 and k in P})
for k in slots:
    g = gen(k)
    r0, r1 = RINGS[g]
    a0, a1 = (0, 360) if g == 0 else angles(k)
    if g == 0:
        paths.append(f'<circle cx="{CX}" cy="{CY}" r="{r1}" fill="{fill(k)}" stroke="#fff" stroke-width="3"/>')
    else:
        paths.append(f'<path d="{sector(r0, r1, a0, a1)}" fill="{fill(k)}" stroke="#FBF8F2" stroke-width="{3 if g < 6 else 1.6}"/>')
    p = P.get(k)
    if not p:
        continue
    name = " / ".join(p["zap"]) if WEBCFG.get("puvodni_jmena") and p.get("zap") else p["n"]
    yrs, st = years(p.get("y")), p.get("st")
    if k in HREFS:
        shape = (f'<circle cx="{CX}" cy="{CY}" r="{r1}"/>' if g == 0 else f'<path d="{sector(r0, r1, a0, a1)}"/>')
        links.append(f'<a href="{HREFS[k]}"><title>{html.escape(name)} {html.escape(yrs)}</title>{shape}</a>')
    unknown = st == "unk"
    style = 'font-style="italic" fill="#8A8278"' if unknown else ('font-style="italic" fill="#2B2620"' if st in ("prob", "mh") else 'fill="#1F1A15"')
    if g == 0:
        texts.append(f'<text x="{CX}" y="{CY - 8}" text-anchor="middle" font-size="44" font-weight="700" fill="#FFF8EE">{html.escape(name)}</text>')
        texts.append(f'<text x="{CX}" y="{CY + 46}" text-anchor="middle" font-size="34" fill="#F1E3CF">{html.escape(yrs)}</text>')
        continue
    am = (a0 + a1) / 2
    if g <= 4:   # tangential text on arcs
        rm = (r0 + r1) / 2
        lines = []
        if g == 3 and k in LINES:
            lines.append((LINES[k][0].upper(), 21, 'font-weight="700" letter-spacing="4" fill="#5A4632"'))
        lines.append((name, {1: 40, 2: 34, 3: 30, 4: 27}[g], f'font-weight="600" {style}'))
        if yrs:
            lines.append((yrs, {1: 30, 2: 27, 3: 24, 4: 22}[g], f'{style}'))
        gap = [s * 1.25 for _, s, _ in lines]
        total = sum(gap)
        bottom = 90 < (am % 360) < 270
        # radii from outer to inner as read top-to-bottom
        cur = rm + total / 2
        order = []
        for (t, s, a), h in zip(lines, gap):
            cur -= h
            order.append((t, s, a, cur + h * 0.28))
        if bottom:   # read inner→outer, so reverse radii
            radii = [o[3] for o in order][::-1]
            order = [(t, s, a, r + s * 0.55) for (t, s, a, _), r in zip(order, radii)]
        for j, (t, s, a, r) in enumerate(order):
            pid = f"p{k}_{j}"
            pad = min(3.0, (a1 - a0) * 0.04)
            b0, b1 = a0 + pad, a1 - pad
            arc_len = math.radians(b1 - b0) * r
            s = min(s, arc_len / (0.56 * max(len(t), 1)))
            if bottom:
                xa, ya = pt(r, b1); xb, yb = pt(r, b0)
                d = f"M{xa:.1f},{ya:.1f} A{r:.1f},{r:.1f} 0 {1 if b1 - b0 > 180 else 0} 0 {xb:.1f},{yb:.1f}"
            else:
                xa, ya = pt(r, b0); xb, yb = pt(r, b1)
                d = f"M{xa:.1f},{ya:.1f} A{r:.1f},{r:.1f} 0 {1 if b1 - b0 > 180 else 0} 1 {xb:.1f},{yb:.1f}"
            defs.append(f'<path id="{pid}" d="{d}" fill="none"/>')
            texts.append(f'<text font-size="{s:.1f}" {a}><textPath href="#{pid}" startOffset="50%" text-anchor="middle">{html.escape(t)}</textPath></text>')
    else:        # radial text
        rm = (r0 + r1) / 2
        depth = (r1 - r0) - 22
        arc = math.radians(a1 - a0) * rm
        f1 = fit(name, depth, MAXF[g], MINF[g])
        f2 = fit(yrs, depth, MAXF[g] * 0.85, MINF[g] * 0.9) if yrs else 0
        two = yrs and arc >= (f1 + f2) * 1.15
        if not two:
            f1 = min(f1, arc / 1.25)
        rot = am - 90 if (am % 360) < 180 else am + 90
        x, y = pt(rm, am)
        tw = f'transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f})"'
        if two:
            h = (f1 + f2) * 1.08
            texts.append(f'<g {tw}><text y="{-h / 2 + f1 * 0.85:.1f}" text-anchor="middle" font-size="{f1:.1f}" font-weight="600" {style}>{html.escape(name)}</text>'
                         f'<text y="{h / 2 - f2 * 0.15:.1f}" text-anchor="middle" font-size="{f2:.1f}" {style}>{html.escape(yrs)}</text></g>')
        else:
            texts.append(f'<g {tw}><text y="{f1 * 0.35:.1f}" text-anchor="middle" font-size="{f1:.1f}" font-weight="600" {style}>{html.escape(name)}</text></g>')

# statistics
known = [k for k in VLASTNI if k > 1 and not P[k]["n"].startswith("otec neuveden")]
doc = [k for k in known if P[k].get("st") == "doc"]
zpath = os.path.join(ROOT, "data", "zaznamy.json")
recs = json.load(open(zpath, encoding="utf-8")) if os.path.exists(zpath) else []
maxg = max(gen(k) for k in P)

title = (f'<text x="{W / 2}" y="250" text-anchor="middle" font-family="Georgia, \'Times New Roman\', serif" font-size="128" fill="#3B2E22">{html.escape(WEBCFG.get("nazev", "Rodokmen"))}</text>'
         f'<text x="{W / 2}" y="370" text-anchor="middle" font-size="50" fill="#6B5A48">{len(known)} známých předků v {maxg + 1} generacích · {len(doc)} doloženo matrikou · {len(recs)} matričních zápisů</text>')

lx, ly = 300, CY + 2240 + 170
legend = []
items = [(k, LINES[k][0]) for k in range(8, 16) if k in LINES]


def popis_rodu(text, jmeno):
    """První věta popisu rodu, zkrácená na celé slovo, aby se vešla do sloupce legendy.
    Tečka končí větu jen před velkým písmenem nebo na konci a po slově s aspoň 4 znaky – „čp. 41“, „roz. Nová“,
    „sv. Jan“ ani „19. století“ větu neukončí."""
    t = text.split(";")[0].strip()
    for m in re.finditer(r"\.(\s+|$)", t):
        za, pred = t[m.end():m.end() + 1], t[:m.start()].split()[-1:]
        if (not za or za.isupper()) and pred and len(pred[0]) >= 4:
            t = t[:m.start()]
            break
    t = t.rstrip(". ")
    limit = max(30, 84 - len(jmeno))   # sloupec legendy pojme asi 85 znaků písmem 40 px
    if len(t) > limit:
        t = t[:limit].rsplit(" ", 1)[0].rstrip(",;:–- ") + "…"
    return t


desc = {k: popis_rodu(LINES[k][1], nm) for k, nm in items}
for idx, (k, nm) in enumerate(items):
    col, row = idx // 4, idx % 4
    x, y = lx + col * 1950, ly + row * 78
    legend.append(f'<rect x="{x}" y="{y - 40}" width="52" height="52" rx="8" fill="{BASE[k]}"/>'
                  f'<text x="{x + 76}" y="{y}" font-size="40"><tspan font-weight="700" fill="#3B2E22">{html.escape(nm)}</tspan>'
                  f'<tspan fill="#5E5245"> – {html.escape(desc[k])}</tspan></text>')
sy = ly + 4 * 78 + 50
legend.append(f'<rect x="{lx}" y="{sy - 34}" width="44" height="44" rx="6" fill="{mix(BASE[8], 0.2)}"/>'
              f'<text x="{lx + 64}" y="{sy}" font-size="36" fill="#3B2E22">doloženo matrikou</text>'
              f'<rect x="{lx + 520}" y="{sy - 34}" width="44" height="44" rx="6" fill="{mix(mix(BASE[8], 0.2), 0.45)}"/>'
              f'<text x="{lx + 584}" y="{sy}" font-size="36" font-style="italic" fill="#3B2E22">pravděpodobné</text>'
              f'<rect x="{lx + 1000}" y="{sy - 34}" width="44" height="44" rx="6" fill="{EMPTY}"/>'
              f'<text x="{lx + 1064}" y="{sy}" font-size="36" fill="#3B2E22">zatím neznámé</text>'
              f'<text x="{lx + 1500}" y="{sy}" font-size="36" fill="#5E5245">uprostřed {html.escape(P[1]["n"].split()[0])}, každý prstenec = o generaci starší; vlevo otcova, vpravo matčina strana</text>')
footer = (f'<text x="{W / 2}" y="{H - 50}" text-anchor="middle" font-size="36" fill="#7A6B5B">'
          f'{html.escape(WEBCFG.get("zapati", ""))}</text>')

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">'
       f'<rect width="{W}" height="{H}" fill="#FBF8F2"/><defs>{"".join(defs)}</defs>'
       f'{title}{"".join(paths)}{"".join(texts)}{"".join(legend)}{footer}</svg>')
if WEB:
    open(OUT, "w", encoding="utf-8", newline="\n").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{FONT}" class="fan">'
        f'<defs>{"".join(defs)}</defs>{"".join(paths)}{"".join(texts)}<g class="fan-links">{"".join(links)}</g></svg>')
    print(OUT, len(links), "odkazů")
    sys.exit(0)
os.makedirs(OUT, exist_ok=True)
svg_path = os.path.join(OUT, "rodokmen_vejir.svg")
html_path = os.path.join(OUT, "rodokmen_vejir.html")
png_path = os.path.join(OUT, "rodokmen_vejir.png")
open(svg_path, "w", encoding="utf-8", newline="\n").write(svg)
open(html_path, "w", encoding="utf-8", newline="\n").write(f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:#FBF8F2}}</style>{svg}')
import shutil, tempfile
if not CHROME:
    print(svg_path, "(PNG nevytvořen – chybí Google Chrome; HTML otevřete v prohlížeči a vytiskněte do PDF)")
    sys.exit(0)
prof = tempfile.mkdtemp(prefix="fanchart-")
before = os.path.getmtime(png_path) if os.path.exists(png_path) else 0
try:   # velký plakát na pomalejším stroji: Chrome PNG dopíše, ale skončí až po limitu – rozhoduje, zda PNG vznikl
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={prof}",
                    "--force-device-scale-factor=1", f"--window-size={W},{H}", f"--screenshot={png_path}",
                    __import__("pathlib").Path(html_path).as_uri()], check=True, capture_output=True, timeout=300)
except subprocess.TimeoutExpired:
    pass
shutil.rmtree(prof, ignore_errors=True)
if not os.path.exists(png_path) or os.path.getmtime(png_path) <= before:
    sys.exit(f"PNG se nevygeneroval (Chrome) – plakát je v {html_path}, otevřete ho v prohlížeči a vytiskněte do PDF")
print(png_path, len(known), "předků", len(doc), "doc", len(recs), "zápisů", maxg + 1, "generací")
