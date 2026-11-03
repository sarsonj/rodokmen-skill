#!/usr/bin/env python3
"""Kontrola konzistence dat rodokmenu. Spouštějte po každé větší změně a před stavbou webu.

Použití: kontrola.py
Vypíše CHYBY (rozbijí web nebo jsou věcně špatně) a UPOZORNĚNÍ (něco chybí, doplnit).
Návratový kód 1, pokud jsou chyby.
"""
import datetime, json, os, re, sys
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def jload(name, default):
    p = os.path.join(DATA, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def main():
    err, warn = [], []
    ns = {}
    try:
        exec(open(os.path.join(DATA, "osoby.py"), encoding="utf-8").read(), ns)
    except Exception as e:  # noqa: BLE001
        sys.exit(f"CHYBA: data/osoby.py nejde načíst: {e}")
    P, SIDE, LINES, SAME = ns.get("P", {}), ns.get("SIDE", []), ns.get("LINES", {}), ns.get("SAME", {})
    zaz = jload("zaznamy.json", [])
    svazky, prep, hl = jload("svazky.json", {}), jload("prepisy.json", {}), jload("zvyrazneni.json", {})
    keys = [z.get("klic") for z in zaz]
    dup = {k for k in keys if keys.count(k) > 1}
    if dup:
        err.append(f"zápisy se stejným klíčem: {sorted(dup)}")
    keys = set(keys)

    if 1 not in P:
        err.append("chybí osoba 1 (výchozí osoba rodokmenu)")
    for k, p in P.items():
        if not isinstance(k, int) or k < 1:
            err.append(f"osoba {k!r}: číslo musí být kladné celé číslo")
            continue
        if k > 1 and k // 2 not in P and k not in SAME:
            warn.append(f"osoba {k} ({p.get('n')}): v rodokmenu chybí její dítě {k // 2} – je číslo správně?")
        st = p.get("st", "unk")
        if st not in ("doc", "prob", "fam", "mh", "unk"):
            err.append(f"osoba {k}: neznámý stav '{st}'")
        for r in p.get("r", []):
            if r not in keys:
                err.append(f"osoba {k} ({p.get('n')}) cituje neexistující zápis '{r}'")
        if st == "doc" and not p.get("r"):
            warn.append(f"osoba {k} ({p.get('n')}) je 'doc' (doloženo), ale necituje žádný zápis")
    for s in SIDE:
        if s.get("k") not in P:
            err.append(f"boční příbuzný '{s.get('n')}' patří k neexistující osobě {s.get('k')}")
        for r in s.get("r", []):
            if r not in keys:
                err.append(f"boční příbuzný '{s.get('n')}' cituje neexistující zápis '{r}'")
    for a, c in SAME.items():
        if c not in P:
            err.append(f"SAME: {a} -> {c}, ale osoba {c} neexistuje")
    for k in LINES:
        if k not in range(8, 16):
            err.append(f"LINES: rod {k} – rody mají čísla 8 až 15 (pradědečci a prababičky)")

    cited = ({r for p in P.values() for r in p.get("r", [])} | {r for s in SIDE for r in s.get("r", [])}
             | {r for h in ns.get("HYPOTEZY", []) if isinstance(h, dict) for r in h.get("zaznamy", [])})
    for z in zaz:
        k = z.get("klic", "?")
        for f in ("klic", "druh", "datum", "nazev", "shrnuti"):
            if not z.get(f):
                err.append(f"zápis {k}: chybí pole '{f}'")
        if z.get("svazek") and z["svazek"] not in svazky:
            err.append(f"zápis {k}: svazek '{z['svazek']}' není v data/svazky.json")
        if z.get("ukazka"):   # vymyšlený zápis ukázkové rodiny – nemá snímek ani přepis
            continue
        if not z.get("odkaz") and not svazky.get(z.get("svazek", ""), {}).get("url"):
            warn.append(f"zápis {k}: chybí odkaz na snímek (pole 'odkaz')")
        if not os.path.exists(os.path.join(ROOT, "vyrezy", k + ".jpg")):
            warn.append(f"zápis {k}: chybí výřez vyrezy/{k}.jpg")
        elif k not in hl:
            warn.append(f"zápis {k}: chybí rámeček (tools/ramecek.py)")
        if k not in prep:
            warn.append(f"zápis {k}: chybí přepis a překlad v data/prepisy.json")
        if k not in cited:
            warn.append(f"zápis {k}: necituje ho žádná osoba (doplnit do 'r' u osoby nebo bočního příbuzného)")

    znamy = [k for k in range(8, 16) if P.get(k, {}).get("st") in ("doc", "prob")]
    chybi = [f"{k} ({P[k].get('n', '?')})" for k in znamy if k not in LINES]
    if chybi:   # bez LINES web neukáže rody ani barvy ve vějíři
        warn.append(f"LINES: chybí rod pro {', '.join(chybi)}"
                    " – jakmile znáš pradědečky a prababičky (8–15), vyplň v data/osoby.py LINES (reference/data.md)")

    mista = jload("mista.json", {})
    vzory = []
    for n, e in mista.items():
        try:
            vzory += [re.compile(e.get("re") or re.escape(n))] if "lat" in e else []
        except re.error:   # špatný výraz hlásí kontrola míst níž
            pass
    bez_mista = [k for k, p in sorted(P.items()) if isinstance(k, int) and p.get("st") == "doc" and p.get("f")
                 and not any(rx.search(" ".join(p["f"])) for rx in vzory)]
    if bez_mista:   # mapa na webu ukáže jen obce z data/mista.json
        ukazka = ", ".join(f"{k} {P[k].get('n', '?')}" for k in bez_mista[:3])
        warn.append(f"mapa: {len(bez_mista)} doložených předků nemá v údajích žádnou obec z data/mista.json (např. {ukazka})"
                    " – přidej jejich obce: tools/mista.py pridej \"Obec\", pak tools/mista.py")

    for name, e in mista.items():
        if "lat" not in e:
            warn.append(f"místo {name}: nemá souřadnice (spusťte tools/mista.py)")
        try:
            re.compile(e.get("re") or "")
        except re.error as ex:
            err.append(f"místo {name}: špatný výraz '{e.get('re')}': {ex}")

    cfg = jload("web.json", {})
    # Chybějící přihlašovací otázku nehlásit pořád – ohlídá ji až nasazení (export_web.py --nasazeni).
    ukazka = ("Rodokmen Novákových", "(ukázka", "vymyšlená rodina", "kovárnu v Holicích čp. 112")
    if any(u in json.dumps(cfg, ensure_ascii=False) for u in ukazka) and "Novák" not in P.get(1, {}).get("n", ""):
        warn.append("web.json: jsou v něm ještě ukázkové texty (Novákovi) – nastav název, příběh a kontakt")

    # Citlivé věci, které jdou na web: ISSUES („Co hledáme“), poznámky a fakta osob, boční příbuzní, texty.
    citlive = re.compile(r"sebevra|vzal[a]? si život|oběsil|zastřelil[a]? se|utopil[a]? se|alkohol|vězen|kriminál|"
                         r"rozvod|rozvedl|psychiatr|léčebn|duševn|rakovin|nemanželsk|cizoložst|dluh|exekuc|interrupc|potrat", re.I)

    hranice = datetime.date.today().year - 100   # posledních ~100 let; staré matriční údaje (nemanželské dítě v 18. stol.) nevadí

    def recent(text):   # datum v závorce („Dovětek (3. 11. 2026)“) je datum zápisu poznámky, ne události
        text = re.sub(r"\(\s*\d{1,2}\.\s*\d{1,2}\.\s*\d{4}\s*\)", "", text)
        return any(int(y) >= hranice for y in re.findall(r"\b(19\d\d|20\d\d)\b", text))

    def popreno(text, m):   # „nejsou dluhy“, „bez dluhů“, „nebyl rozveden“ – slovo je popřené
        return re.search(r"(?:^|\s)(?:bez|žádn\w*|nejsou|nebyl\w*|neměl\w*|nemá\w*|není)\s+(?:\w+\s+)?$",
                         text[max(0, m.start() - 30):m.start()], re.I)
    schvaleno = [s for s in (cfg.get("citlive_schvaleno") if isinstance(cfg.get("citlive_schvaleno"), list) else [])
                 if isinstance(s, str) and len(s.strip()) >= 3]

    def schvalene(text, m):   # uživatel to na web pustil: v web.json „citlive_schvaleno“ je úryvek textu s tímto slovem
        for s in schvaleno:
            i = text.find(s)
            while i >= 0:
                if i <= m.start() and m.end() <= i + len(s):
                    return True
                i = text.find(s, i + 1)
        return False
    texty = [("ISSUES", i if isinstance(i, str) else " ".join(i)) for i in ns.get("ISSUES", [])]
    for k, p in P.items():
        text = " ".join(p.get("f", [])) + " " + p.get("note", "")
        roky = [int(y) for y in re.findall(r"\b1[5-9]\d\d|20\d\d\b", p.get("y", "") + " " + text)]
        texty.append((f"osoba {k}", text + (f" {hranice}" if roky and min(roky) >= 1870 or k < 8 else "")))
    texty += [(f"boční příbuzný {s.get('n')}", s.get("n", "") + " " + s.get("t", "")) for s in SIDE]
    for f in ("zajimavosti.md", "pribeh.md"):
        if os.path.exists(os.path.join(DATA, f)):
            obsah = open(os.path.join(DATA, f), encoding="utf-8").read()
            texty += [(f, odst) for odst in re.split(r"\n\s*\n|\n(?=#)", obsah)]   # odstavce i oddíly „## …“
    for kde, text in texty:
        if not recent(text):
            continue
        m = next((m for m in citlive.finditer(text) if not schvalene(text, m) and not popreno(text, m)), None)
        if m:
            warn.append(f"CITLIVÉ ({kde}): „…{text[max(0, m.start() - 40):m.end() + 40].strip()}…“ – jde na web; "
                        f"zeptej se uživatele, jestli to tam smí být (reference/soukromi.md); když ano, "
                        f"přidej úryvek textu s tím slovem do web.json „citlive_schvaleno“")

    if not os.path.exists(os.path.join(DATA, "pribeh.md")):
        hlavni = min(LINES) if LINES else 8   # bez LINES rod po meči (otec otce otce)
        jmeno = (LINES[hlavni][0] if LINES else
                 (P.get(8) or P.get(1) or {}).get("n", "").split()[-1:] or ["po meči"])
        jmeno = jmeno if isinstance(jmeno, str) else jmeno[0]
        n = max((k.bit_length() for k in P if isinstance(k, int) and k >= 8 and k >> (k.bit_length() - 4) == hlavni),
                default=0)
        if n >= 6:
            warn.append(f"rod {jmeno} má už {n} generací – je čas napsat příběh rodu "
                        f"(data/pribeh.md, reference/pribehy.md); koncept nejdřív ukaž uživateli v chatu")

    log = os.path.join(DATA, "research_log.md")
    rows = sum(1 for l in open(log, encoding="utf-8") if re.match(r"^\| \d+ \|", l)) if os.path.exists(log) else 0
    print(f"{len(P)} osob, {len(zaz)} zápisů, {len(svazky)} svazků, {rows} řádků deníku")
    for e in err:
        print("CHYBA:", e)
    for w in warn:
        print("upozornění:", w)
    if not err and not warn:
        print("Vše v pořádku.")
    sys.exit(1 if err else 0)


if __name__ == "__main__":
    main()
