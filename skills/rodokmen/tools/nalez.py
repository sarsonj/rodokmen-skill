#!/usr/bin/env python3
"""Zápis jednoho nálezu z matriky jedním příkazem: snímek → výřez → rámeček → zápis + přepis → osoby → deník → rejstřík snímků.

Proč: dřív to bylo 7–8 samostatných příkazů (aron_img, vyrez, ramecek, zapis zaznamy, zapis prepisy, zapis odkaz,
řádek deníku, snimky pridej) a snadno se na něco zapomnělo (přepis, rámeček, odkaz u osoby, rejstřík snímků).

Použití (z kořene projektu):
  nalez.py nahled <vstup.json>   stáhne snímek, udělá výřez a rámeček a vypíše kontrolní obrázek – data nemění
                                 (zdroje/, vyrezy/ a zvyrazneni.json přepíše; tak se ladí souřadnice)
  nalez.py zapis  <vstup.json>   totéž a k tomu zapíše zápis, přepis, odkazy u osob, řádek deníku a rejstřík snímků
      --prepsat   zápis se stejným klíčem už existuje a má se nahradit (jinak nástroj skončí)

Vstup (napiš ho nástrojem Write do pracovni/):
{
  "klic":    "chocen_umrti_tomas_prihoda_1791",          klíč zápisu (malá písmena, obec_druh_jmeno_rok)
  "apu":     "b156902e-891e-4932-8f96-4696953e68f5",     ARON: celé apu_id svazku (svazek i odkaz doplní nástroj sám)
  "snimek":  10,
      … nebo jiný archiv:  "obraz": "pracovni/x.jpg", "svazek": "<klíč v data/svazky.json>", "odkaz": "https://…",
                           "archiv": "mza|soa-praha|soa-trebon|matricula|jiny", "kniha": "<číslo knihy pro rejstřík snímků>"
  "vyrez":   [0, 0.25, 0.75, 0.40],                       zlomky celé stránky (velkoryse: hlavička sloupců, okraje)
  "kontrast": false,                                      vybledlý zápis
  "ramecek": [[0, 0.30, 1, 0.62]],                        zlomky VÝŘEZU – kde přesně je čtený zápis
  "ramecek_pozn": "Zápis 1. 2. 1791, č. 108",
  "zaznam":  {"druh": "N|O|Z|S", "datum": "1. 2. 1791", "nazev": "Úmrtí Tomáše Příhody (1791)", "shrnuti": "…"},
  "prepis":  {"orig": "[Datum] …", "cz": "…"},
  "osoby":   [928, "Isidor Jenisch"],                     Kekulého čísla nebo jednoznačná část jména bočního příbuzného
  "denik":   {"zdroj": "…", "rozsah": "…", "hledano": "…", "vysledek": "…", "citace": "…"},   nepovinné
  "snimky_co": "zemřelí 1791, fol. 14, Tomáš Příhoda"     popis do data/snimky.tsv (výchozí: název zápisu)
}
Po „zapis“ pusť tools/kontrola.py. Kontrolní obrázek rámečku si VŽDY prohlédni.
"""
import ast, json, os, re, subprocess, sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
PRAC = os.path.join(ROOT, "pracovni", "nalez")
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
DRUHY = {"N", "O", "Z", "S"}


def nastroj(*args, vystup=False):
    """Spustí jiný nástroj z tools/ stejným Pythonem; při chybě skončí s jeho hláškou."""
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(TOOLS, args[0]), *map(str, args[1:])],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        sys.exit(f"{args[0]} skončil chybou:\n{(r.stderr or r.stdout).strip()}")
    if not vystup and r.stdout.strip():
        print("  " + r.stdout.strip().splitlines()[-1])
    return r.stdout


def jload(nazev, vychozi):
    p = os.path.join(ROOT, "data", nazev)
    return json.load(open(p, encoding="utf-8-sig")) if os.path.exists(p) else vychozi


def ctverice(v, co):
    if not (isinstance(v, list) and len(v) == 4 and all(isinstance(x, (int, float)) for x in v)
            and 0 <= v[0] < v[2] <= 1 and 0 <= v[1] < v[3] <= 1):
        sys.exit(f"{co}: čekám [x0, y0, x1, y1] jako zlomky 0..1 (x0 < x1, y0 < y1), dostal jsem {v}.")
    return v


def najdi_osobu(cil, ns):
    """Ověří, že osoba existuje (stejná pravidla jako zapis.py odkaz); vrátí popis."""
    if isinstance(cil, int) or (isinstance(cil, str) and cil.isdigit()):
        k = int(cil)
        if k not in ns["P"]:
            sys.exit(f"Osoba {k} v P (data/osoby.py) není.")
        return f"{k} {ns['P'][k].get('n')}"
    shody = [s.get("n") for s in ns.get("SIDE", []) if str(cil).lower() in str(s.get("n", "")).lower()]
    if len(shody) != 1:
        sys.exit(f"Bočního příbuzného „{cil}“ " + ("v SIDE není." if not shody else
                 "je víc: " + "; ".join(shody) + " – napiš delší část jména."))
    return shody[0]


def over(v, prepsat, zapis):
    """Všechno zkontrolovat dřív, než se cokoli stáhne nebo zapíše."""
    klic = v.get("klic", "")
    if not re.fullmatch(r"[a-z0-9_]+", klic):
        sys.exit(f"Klíč „{klic}“: jen malá písmena bez diakritiky, číslice a podtržítka (obec_druh_jmeno_rok).")
    if "apu" in v:
        if not UUID.fullmatch(str(v["apu"])):
            sys.exit(f"apu „{v['apu']}“ není celé apu_id ARONu (8-4-4-4-12 znaků).")
        if not isinstance(v.get("snimek"), int):
            sys.exit("U ARONu chybí číslo snímku „snimek“ (celé číslo).")
    else:
        for f in ("obraz", "svazek", "odkaz"):
            if not v.get(f):
                sys.exit(f"Bez „apu“ (jiný archiv než ARON) potřebuji „obraz“, „svazek“ a „odkaz“ – chybí „{f}“.")
        if not os.path.exists(os.path.join(ROOT, v["obraz"])):
            sys.exit(f"Obraz {v['obraz']} neexistuje.")
        if v["svazek"] not in jload("svazky.json", {}):
            sys.exit(f"Svazek „{v['svazek']}“ není v data/svazky.json – zapiš ho nejdřív (zapis.py svazky …).")
    if "vyrez" in v:
        ctverice(v["vyrez"], "vyrez")
    ramecky = v.get("ramecek") or []
    if not ramecky:
        sys.exit("Chybí „ramecek“ – seznam aspoň jednoho rámečku [[x0, y0, x1, y1]] ve zlomcích výřezu.")
    for r in ramecky:
        ctverice(r, "ramecek")
    if not zapis:
        return
    z = v.get("zaznam") or {}
    for f in ("druh", "datum", "nazev", "shrnuti"):
        if not str(z.get(f) or "").strip():
            sys.exit(f"V „zaznam“ chybí „{f}“.")
    if z["druh"] not in DRUHY:
        sys.exit(f"druh „{z['druh']}“ musí být jeden z {', '.join(sorted(DRUHY))} (narození, oddaní, zemřelí, sčítání).")
    p = v.get("prepis") or {}
    if not (str(p.get("orig") or "").strip() and str(p.get("cz") or "").strip()):
        sys.exit("V „prepis“ chybí „orig“ (doslovný přepis) nebo „cz“ (překlad) – každý zápis má mít obojí.")
    if any(x.get("klic") == klic for x in jload("zaznamy.json", [])) and not prepsat:
        sys.exit(f"Zápis „{klic}“ už v data/zaznamy.json je. Chceš-li ho nahradit, přidej --prepsat.")
    osoby = v.get("osoby") or []
    if not osoby:
        sys.exit("Chybí „osoby“ – komu zápis patří (Kekulého číslo nebo část jména bočního příbuzného). "
                 "Zápis, který nikdo necituje, kontrola hlásí.")
    src = open(os.path.join(ROOT, "data", "osoby.py"), encoding="utf-8-sig").read()
    ns = {}
    try:
        ast.parse(src)
        exec(compile(src, "data/osoby.py", "exec"), ns)
    except Exception as e:
        sys.exit(f"data/osoby.py nejde načíst ({e}) – oprav ho nejdřív.")
    for o in osoby:
        najdi_osobu(o, ns)
    d = v.get("denik")
    if d is not None:
        chybi = [k for k in ("zdroj", "rozsah", "hledano", "vysledek") if not str(d.get(k) or "").strip()]
        if chybi:
            sys.exit("V „denik“ chybí: " + ", ".join(chybi) + ".")


def obrazky(v):
    klic = v["klic"]
    os.makedirs(PRAC, exist_ok=True)
    if "apu" in v:
        obraz = os.path.join(PRAC, f"{v['apu'][:8]}_{v['snimek']:04d}.jpg")
        print(f"1/3 snímek {v['snimek']} z ARONu …")
        nastroj("aron_img.py", v["apu"], v["snimek"], 0, obraz)
    else:
        obraz = os.path.join(ROOT, v["obraz"])
    print("2/3 výřez …")
    args = ["vyrez.py", obraz, klic]
    if "vyrez" in v:
        args.append(",".join(str(x) for x in v["vyrez"]))
    if v.get("kontrast"):
        args.append("--kontrast")
    nastroj(*args)
    print("3/3 rámeček …")
    args = ["ramecek.py", klic, *(",".join(str(x) for x in r) for r in v["ramecek"])]
    if v.get("ramecek_pozn"):
        args += ["--pozn", v["ramecek_pozn"]]
    nastroj(*args, vystup=True)
    return os.path.join(ROOT, "pracovni", f"ramecek_{klic}.jpg")


def zapis_json(soubor, klic, obj):
    p = os.path.join(PRAC, f"{klic}.{soubor}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    nastroj("zapis.py", soubor, klic, p)


def data(v):
    klic = v["klic"]
    if "apu" in v:
        svazek = v["apu"][:8]
        if svazek not in jload("svazky.json", {}):
            print("svazek …")
            nastroj("aron_img.py", v["apu"], "svazek")
        odkaz = nastroj("aron_img.py", v["apu"], "link", v["snimek"], vystup=True).strip().splitlines()[-1]
        archiv, kniha = "aron", v["apu"]
    else:
        svazek, odkaz = v["svazek"], v["odkaz"]
        archiv, kniha = v.get("archiv", "jiny"), v.get("kniha", svazek)
    z = v["zaznam"]
    print("zápis, přepis …")
    zapis_json("zaznamy", klic, {"klic": klic, "svazek": svazek, "snimek": v.get("snimek", ""), "druh": z["druh"],
                                 "datum": z["datum"], "nazev": z["nazev"], "shrnuti": z["shrnuti"], "odkaz": odkaz})
    zapis_json("prepisy", klic, {"orig": v["prepis"]["orig"], "cz": v["prepis"]["cz"]})
    print("osoby …")
    for o in v["osoby"]:
        nastroj("zapis.py", "odkaz", o, klic)
    cislo = ""
    if v.get("denik"):
        sys.path.insert(0, TOOLS)
        import denik
        cislo = denik.pridej(v["denik"])
        print(f"  deník: řádek #{cislo}")
    nastroj("snimky.py", "pridej", archiv, kniha, v.get("snimek", "?"), v.get("snimky_co") or z["nazev"],
            *(["--denik", cislo] if cislo else []), "--stav", "zapsano")
    return cislo


def main():
    a = sys.argv[1:]
    prepsat = "--prepsat" in a
    a = [x for x in a if x != "--prepsat"]
    if len(a) != 2 or a[0] not in ("nahled", "zapis"):
        sys.exit(__doc__)
    try:
        v = json.load(open(a[1], encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        sys.exit(f"Vstup {a[1]} není platný JSON: {e}")
    zapis = a[0] == "zapis"
    over(v, prepsat, zapis)
    kontrolni = obrazky(v)
    if zapis:
        cislo = data(v)
        print(f"Hotovo: {v['klic']}" + (f", deník #{cislo}" if cislo else " (řádek deníku nebyl ve vstupu – přidej ho přes tools/denik.py)") + ".")
        print("Teď: python -I -X utf8 tools/kontrola.py")
    print(f"Prohlédni kontrolní obrázek rámečku: {kontrolni}")


if __name__ == "__main__":
    main()
