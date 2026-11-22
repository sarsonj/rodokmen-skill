#!/usr/bin/env python3
"""Přidá, změní nebo smaže podpis či křížky předka (stránka Podpisy na webu): vystřihne obrázek ze snímku zápisu
do podpisy/<id>.jpg a zapíše položku do data/podpisy.json (formát souboru zůstane, viz zapis.py).

Použití (z kořene projektu):
  podpis.py <klíč zápisu> <osoba> <podpis|krizky> --text "Wáclaw Nowak" --vyrez x0,y0,x1,y1 [volby]
    klíč zápisu  „klic“ z data/zaznamy.json (zápis, pod kterým je podpis)
    osoba        Kekulého číslo, nebo část jména osoby z `P` v data/osoby.py (musí sedět na jedinou)
    druh         podpis = vlastnoruční podpis, krizky = dotyčný neuměl psát a udělal křížky
    --text       co je napsáno, jak to čteš (u křížků se „+++ “ doplní samo); uvozovky „ “ se doplní samy
    --vyrez      oblast podpisu jako zlomky 0..1 šířky a výšky obrázku zápisu (zdroje/<klíč>.jpg; není-li, vyrezy/<klíč>.jpg),
                 stejně jako u vyrez.py a ramecek.py; velkoryse, ať je vidět celý podpis. Bez --vyrez se ponechá
                 už uložený obrázek podpisy/<id>.jpg (úprava textu nebo popisu)
    --snimek     jiný zdrojový obrázek místo zdroje/<klíč>.jpg (např. celá stránka v pracovni/) – zlomky se pak vztahují k němu
    --rok        rok podpisu; bez něj se vezme poslední čtyřčíslí z „datum“ zápisu
    --popis      kdo, kde a kdy („podpis ženicha pod zápisem sňatku, Holice 1884“) – nepovinné
    --id         název obrázku a kotva na stránce (písmena bez diakritiky, číslice, _ a -); bez něj „<jméno>_<rok>“
  podpis.py --smazat <id>      smaže položku z data/podpisy.json i obrázek podpisy/<id>.*

Ohlídá, že zápis i osoba existují, že osoba má zápis v `r` (jinak nejdřív `zapis.py odkaz <osoba> <klíč>`) a že oblast
je zlomek 0..1. Stejné id položku nahradí (nástroj jde spustit znovu). Podpis lze přiřadit jen osobě z `P` (boční příbuzní
v `SIDE` vlastní stránku nemají); předek vedený vícekrát (`SAME`) se přiřadí hlavnímu číslu.
Potřebuje ImageMagick (příkaz `magick`). Příklad:
  python3 -I tools/podpis.py holice_snatek_vaclav_novak_barbora_mala_1884 "Václav Novák" podpis \\
      --text "Wáclaw Nowak" --vyrez 0.55,0.62,0.95,0.72 --popis "podpis ženicha pod zápisem sňatku, Holice 1884"
"""
import argparse, importlib.util, json, os, re, subprocess, sys, unicodedata
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
PRIPONY = (".jpg", ".jpeg", ".png", ".webp")


def modul(nazev):
    """Načte sousední nástroj (zapis.py, vyrez.py) – při `python -I` skriptová složka v sys.path není."""
    spec = importlib.util.spec_from_file_location(nazev, os.path.join(TOOLS, nazev + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def slugify(text):   # stejně jako v export_web.py
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def bez_diakritiky(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def nacti_json(soubor, default):
    path = os.path.join(ROOT, "data", soubor)
    if not os.path.exists(path):
        return default
    try:
        return json.load(open(path, encoding="utf-8-sig"))
    except ValueError as e:
        sys.exit(f"data/{soubor} nejde přečíst ({e}) – oprav ho nejdřív (git diff ukáže poslední změnu).")


def najdi_osobu(zapis, hledana):
    """(Kekulého číslo hlavní osoby, adresa na webu, množina klíčů zápisů osoby včetně aliasů SAME)."""
    try:
        ns = zapis.nacti_osoby(open(os.path.join(ROOT, "data", "osoby.py"), "rb").read())
    except Exception as e:
        sys.exit(f"data/osoby.py nejde načíst ({e}) – oprav ho nejdřív (git diff ukáže poslední změnu).")
    P, SIDE, SAME = ns.get("P", {}), ns.get("SIDE", []), ns.get("SAME", {})

    def zastupna(p):
        return p["n"].startswith(("otec neuveden", "matka neuvedena")) or p["n"] in ("", "?")

    if re.fullmatch(r"\d+", hledana):
        k = int(hledana)
        if k not in P:
            sys.exit(f"Osoba {k} v P (data/osoby.py) není.")
    else:
        kand = [kk for kk, p in P.items() if bez_diakritiky(hledana) in bez_diakritiky(p["n"]) and not zastupna(p)]
        kand = sorted({SAME.get(kk, kk) for kk in kand})
        if not kand:
            bocni = [s.get("n", "") for s in SIDE if bez_diakritiky(hledana) in bez_diakritiky(s.get("n", ""))]
            sys.exit(f"Osoba „{hledana}“ v P (data/osoby.py) není." + (
                f" Boční příbuzní ({', '.join(bocni)}) vlastní stránku nemají, podpis jim web nepřiřadí." if bocni else ""))
        if len(kand) > 1:
            sys.exit(f"Osob „{hledana}“ je víc: " + "; ".join(f"{kk} {P[kk]['n']}" for kk in kand)
                     + " – napiš číslo, nebo delší část jména.")
        k = kand[0]
    k = SAME.get(k, k)   # předek ve stromě vícekrát: podpis patří hlavní osobě
    if k not in P or zastupna(P[k]):
        sys.exit(f"Osoba {k} je zástupná (bez jména) – podpis jí nejde přiřadit.")
    slugs, used = {}, set()   # stejný výpočet adresy jako export_web.py
    for kk in sorted(P):
        p = P[kk]
        if zastupna(p) or kk in SAME:
            continue
        yv = (p.get("y") or "").strip()
        ys = [] if yv.startswith(("?", "†")) else re.findall(r"\d{4}", yv)
        s = slugify(p["n"] + (" " + ys[0] if ys else ""))
        if s in used or not s:
            s = f"{s}-{kk}"
        used.add(s)
        slugs[kk] = s
    zaznamy = set(P[k].get("r") or [])
    for a, c in SAME.items():
        if c == k:
            zaznamy |= set(P.get(a, {}).get("r") or [])
    return k, P[k], slugs[k], zaznamy


def vyrez_obrazku(zdroj, cil, box):
    """Výřez podle zlomků box do cil (JPEG, nejvýš 1200 px, EXIF pryč). Vrací (šířka, výška) výřezu v px."""
    magick = modul("vyrez").magick()
    w, h = (int(v) for v in subprocess.run([magick, zdroj + "[0]", "-auto-orient", "-format", "%w %h", "info:"],
                                            capture_output=True, text=True, check=True).stdout.split())
    sx, sy = round((box[2] - box[0]) * w), round((box[3] - box[1]) * h)
    if sx < 20 or sy < 10:
        sys.exit(f"Oblast {sx}×{sy} px je moc malá na podpis – zkontroluj zlomky (0..1 šířky a výšky obrázku {w}×{h} px).")
    subprocess.run([magick, zdroj, "-auto-orient", "-crop", f"{sx}x{sy}+{round(box[0] * w)}+{round(box[1] * h)}", "+repage",
                    "+profile", "!icc,*", "+set", "comment", "-resize", "1200x1200>", "-quality", "90", cil], check=True)
    return sx, sy


def smazat(zapis, iid):
    path = os.path.join(ROOT, "data", "podpisy.json")
    text = open(path, encoding="utf-8-sig").read() if os.path.exists(path) else ""
    data = nacti_json("podpisy.json", [])
    idx = next((n for n, x in enumerate(data) if isinstance(x, dict) and x.get("id") == iid), None)
    if idx is None:
        sys.exit(f"Podpis „{iid}“ v data/podpisy.json není.")
    poz = zapis.polozky(text)
    if len(poz) == 1:
        novy = "[]\n"
    elif idx == 0:   # od začátku položky po začátek další
        novy = text[:poz[0][1]] + text[poz[1][1]:]
    else:            # od konce předchozí položky (čárka) po konec této
        novy = text[:poz[idx - 1][2]] + text[poz[idx][2]:]
    json.loads(novy)   # pojistka
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(novy)
    os.replace(tmp, path)
    for e in PRIPONY:
        img = os.path.join(ROOT, "podpisy", iid + e)
        if os.path.exists(img):
            os.remove(img)
    print(f"data/podpisy.json: smazáno „{iid}“ (i obrázek podpisy/{iid}.*)")


def main():
    ap = argparse.ArgumentParser(add_help=True, usage="podpis.py <klíč zápisu> <osoba> <podpis|krizky> --text … --vyrez x0,y0,x1,y1 "
                                 "[--rok R] [--popis …] [--id …] [--snimek …] | --smazat <id>", description=__doc__.split("\n")[0])
    ap.add_argument("klic", nargs="?")
    ap.add_argument("osoba", nargs="?")
    ap.add_argument("druh", nargs="?", choices=["podpis", "krizky"])
    ap.add_argument("--text")
    ap.add_argument("--vyrez")
    ap.add_argument("--snimek")
    ap.add_argument("--rok", type=int)
    ap.add_argument("--popis", default="")
    ap.add_argument("--id")
    ap.add_argument("--smazat", metavar="ID")
    a = ap.parse_args()
    zapis = modul("zapis")
    if a.smazat:
        return smazat(zapis, a.smazat)
    if not (a.klic and a.osoba and a.druh and a.text):
        sys.exit(__doc__)

    zaz = {z.get("klic"): z for z in nacti_json("zaznamy.json", []) if isinstance(z, dict)}
    if a.klic not in zaz:
        sys.exit(f"Zápis „{a.klic}“ v data/zaznamy.json není – nejdřív ho zapiš (zapis.py zaznamy …).")
    k, osoba, slug, zaznamy_osoby = najdi_osobu(zapis, a.osoba)
    if a.klic not in zaznamy_osoby:
        sys.exit(f"Osoba {k} ({osoba['n']}) nemá zápis {a.klic} v `r` – podpis by na webu nebyl u zápisu. "
                 f"Nejdřív: python3 -I tools/zapis.py odkaz {k} {a.klic}")
    rok = a.rok
    if rok is None:
        m = re.findall(r"\d{4}", str(zaz[a.klic].get("datum", "")))
        if not m:
            sys.exit("Zápis nemá v „datum“ rok – napiš --rok.")
        rok = int(m[-1])
    if not 1400 <= rok <= 2100:
        sys.exit(f"Rok {rok} nevypadá správně.")
    iid = a.id or (slugify(osoba["n"]).replace("-", "_") + f"_{rok}")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", iid):
        sys.exit("--id smí mít jen písmena bez diakritiky, číslice, _ a -.")
    stare = next((x for x in nacti_json("podpisy.json", []) if isinstance(x, dict) and x.get("id") == iid), None)
    if stare and (stare.get("osoba") != slug or stare.get("zdroj") != a.klic):
        sys.exit(f"Podpis „{iid}“ už existuje u jiné osoby nebo zápisu ({stare.get('osoba')}, {stare.get('zdroj')}) – "
                 "zvol jiné --id, nebo ho nejdřív smaž (--smazat).")

    text = a.text.strip().strip("„“\"").strip()
    if a.druh == "krizky" and "+" not in text and "✠" not in text:
        text = "+++ " + text
    zaznam = {"id": iid, "rok": rok, "osoba": slug, "kruzky": a.druh == "krizky", "text": f"„{text}“"}
    if a.popis.strip():
        zaznam["popis"] = a.popis.strip()
    zaznam["zdroj"] = a.klic

    cil = os.path.join(ROOT, "podpisy", iid + ".jpg")
    existuje = [os.path.join(ROOT, "podpisy", iid + e) for e in PRIPONY if os.path.exists(os.path.join(ROOT, "podpisy", iid + e))]
    tmp = None
    if a.vyrez:
        try:
            box = [float(v) for v in a.vyrez.split(",")]
            assert len(box) == 4
        except (ValueError, AssertionError):
            sys.exit(f"--vyrez {a.vyrez} musí být x0,y0,x1,y1 (zlomky 0..1).")
        if not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
            sys.exit(f"Oblast {a.vyrez} musí být zlomky 0..1 (x0 < x1, y0 < y1), ne pixely.")
        zdroj = a.snimek or next((p for p in (os.path.join(ROOT, d, a.klic + ".jpg") for d in ("zdroje", "vyrezy")) if os.path.exists(p)), None)
        if not zdroj or not os.path.exists(zdroj):
            sys.exit(f"Chybí obrázek zápisu zdroje/{a.klic}.jpg ani vyrezy/{a.klic}.jpg – nejdřív vyrez.py, nebo dej --snimek.")
        os.makedirs(os.path.dirname(cil), exist_ok=True)
        tmp = os.path.join(ROOT, "podpisy", iid + ".tmp.jpg")
        sx, sy = vyrez_obrazku(zdroj, tmp, box)
        print(f"výřez {sx}×{sy} px ze {os.path.relpath(zdroj, ROOT)}")
    elif not existuje:
        sys.exit(f"Chybí --vyrez a obrázek podpisy/{iid}.jpg ještě není – napiš oblast podpisu (zlomky 0..1 obrázku zápisu).")

    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(TOOLS, "zapis.py"), "podpisy", iid, "-", "--prepsat"],
                       input=json.dumps(zaznam, ensure_ascii=False).encode("utf-8"), cwd=ROOT, capture_output=True)
    sys.stdout.write(r.stdout.decode("utf-8", "replace"))
    if r.returncode:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)
        sys.exit(r.stderr.decode("utf-8", "replace").strip() or "zápis do data/podpisy.json selhal")
    if tmp:
        for img in existuje:   # jiná přípona téhož id by na webu kolidovala s novým obrázkem
            os.remove(img)
        os.replace(tmp, cil)
        print(f"uloženo: podpisy/{iid}.jpg – prohlédni si ho, jestli je podpis celý")
    print(f"osoba {k} ({osoba['n']}), zápis {a.klic}. Na webu: npm run data (v web/).")


if __name__ == "__main__":
    main()
