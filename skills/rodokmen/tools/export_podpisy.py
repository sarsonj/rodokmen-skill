#!/usr/bin/env python3
"""Doplněk webu: stránka Podpisy (podpisy a křížky předků vystřižené ze zápisů).

Čte data/podpisy.json a obrázky podpisy/<id>.jpg (nebo .png, .webp), ověří je proti web/src/data/site.json
a zapíše web/src/data/podpisy.json (vždy, i prázdný seznam) a zkopíruje obrázky do web/public/podpisy/.
Bez podpisů stránka ani položka v menu nevzniknou. Volá se z konce tools/export_web.py (po zápisu site.json);
formát dat/podpisy.json je popsán v reference/web.md.
"""
import json, os, shutil, sys

for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
if sys.argv[1:2] in (["-h"], ["--help"]):
    sys.exit(__doc__.strip())

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIPONY = (".jpg", ".jpeg", ".png", ".webp")


def main():
    src = os.path.join(ROOT, "data", "podpisy.json")
    out = os.path.join(ROOT, "web", "src", "data", "podpisy.json")
    pub = os.path.join(ROOT, "web", "public", "podpisy")
    site = json.load(open(os.path.join(ROOT, "web", "src", "data", "site.json"), encoding="utf-8"))
    people = site["people"]
    recs = {r["key"]: r for r in site["records"]}
    items = json.load(open(src, encoding="utf-8-sig")) if os.path.exists(src) else []
    shutil.rmtree(pub, ignore_errors=True)   # staré obrázky z vyřazených podpisů nezůstanou na webu
    ok, ids = [], set()
    for it in items:
        iid = it.get("id", "?")
        if not all(it.get(k) not in (None, "") for k in ("id", "rok", "osoba", "text", "zdroj")):
            print(f"POZOR: podpis {iid} – chybí některé z polí id, rok, osoba, text, zdroj, vynechávám")
            continue
        if iid in ids or not all(c.isalnum() or c in "_-" for c in iid):
            print(f"POZOR: podpis {iid} – id je duplicitní nebo obsahuje jiné znaky než písmena a číslice, _ a -, vynechávám")
            continue
        s, z = it["osoba"], it["zdroj"]
        if s not in people or z not in recs:
            print(f"POZOR: podpis {iid} – osoba {s} nebo zápis {z} není v datech, vynechávám")
            continue
        if s not in recs[z]["people"]:
            print(f"POZOR: podpis {iid} – osoba {s} není mezi lidmi zápisu {z}")
        img = next((os.path.join(ROOT, "podpisy", iid + e) for e in PRIPONY if os.path.exists(os.path.join(ROOT, "podpisy", iid + e))), None)
        if not img:
            print(f"POZOR: podpis {iid} – chybí obrázek podpisy/{iid}.jpg (nebo .png, .webp), vynechávám")
            continue
        os.makedirs(pub, exist_ok=True)
        shutil.copy2(img, os.path.join(pub, os.path.basename(img)))
        ids.add(iid)
        ok.append({**it, "popis": it.get("popis", ""), "kruzky": bool(it.get("kruzky")), "soubor": os.path.basename(img)})
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(ok, f, ensure_ascii=False, indent=1)
    if items or ok:
        print(f"podpisy: {len(ok)} z {len(items)}")


main()   # volá se přes runpy z konce export_web.py
