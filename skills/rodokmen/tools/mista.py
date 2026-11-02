#!/usr/bin/env python3
"""Místa předků pro mapu na webu (data/mista.json).

Použití:
  mista.py pridej "Název" ["regulární výraz"] ["dotaz pro vyhledání"]
      přidá obec; výraz se hledá v údajích osob (výchozí = prvních 5 písmen názvu, aby sedělo i skloňování),
      dotaz pro OpenStreetMap (výchozí = "Název, Česko", když nic nenajde, zkusí Slovensko a další sousední země);
      historickou část obce, kterou mapa nezná, zadej jako celou obec; u víceznačných názvů (Podolí, Dub) přidej sousední obec:
      "Podolí, Odlochovice" – a ve výpisu vždy zkontroluj okres
  mista.py
      dohledá souřadnice u míst, která je ještě nemají (OpenStreetMap Nominatim, 1 dotaz za sekundu),
      a vypíše seznam. Když bod nesedí, opravte lat/lon v data/mista.json ručně.

Položka může mít "hypoteza": true a "rod": <Kekulé 8–15> – pak se na mapě ukáže jako hypotéza bez osob.
"""
import json, os, re, sys, time, urllib.parse, urllib.request
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "mista.json")


def geocode(q, zeme=None):
    par = {"q": q, "format": "json", "limit": 1} | ({"countrycodes": zeme} if zeme else {})
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(par)
    req = urllib.request.Request(url, headers={"User-Agent": "rodokmen-skill/1.0 (family genealogy map, occasional geocoding)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)
    time.sleep(1.1)
    return (round(float(res[0]["lat"]), 4), round(float(res[0]["lon"]), 4), res[0]["display_name"]) if res else None


def main():
    cache = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    if len(sys.argv) > 2 and sys.argv[1] == "pridej":
        name = sys.argv[2]
        stem = re.escape(name.split()[0][:5]) if len(name.split()) == 1 else re.escape(name)
        cache[name] = dict(cache.get(name, {}), re=sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else stem,
                           dotaz=sys.argv[4] if len(sys.argv) > 4 else f"{name}, Česko")
    for name, e in cache.items():
        if "lat" not in e:
            g = geocode(e.get("dotaz") or f"{name}, Česko")
            if not g and e.get("dotaz", f"{name}, Česko") == f"{name}, Česko":   # výchozí dotaz: zkus sousední země
                g = geocode(name, "sk,pl,at,de,hu")
                if g:
                    print("MIMO ČESKO:", name, "→", g[2][:80], "– zkontroluj, že je to ono")
            if g:
                e["lat"], e["lon"], e["osm"] = g
            else:
                print("NENALEZENO:", name, "– upravte 'dotaz' nebo doplňte lat/lon ručně")
    json.dump(cache, open(OUT, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    for n, e in cache.items():
        print(f"{n:28} {e.get('lat', '?'):>8} {e.get('lon', '?'):>8}  hledá „{e.get('re')}“  {e.get('osm', '')[:60]}")


if __name__ == "__main__":
    main()
