#!/usr/bin/env python3
"""Místa předků pro mapu na webu (data/mista.json).

Použití:
  mista.py pridej "Název" ["regulární výraz"] ["dotaz pro vyhledání"]
      přidá obec; výraz se hledá v údajích osob (výchozí = prvních 5 písmen názvu, aby sedělo i skloňování),
      dotaz pro OpenStreetMap (výchozí = "Název, Česko", když nic nenajde, zkusí Slovensko a další sousední země);
      historickou část obce, kterou mapa nezná, zadej jako celou obec; u víceznačných názvů (Podolí, Dub) přidej sousední obec:
      "Podolí, Odlochovice" – a ve výpisu vždy zkontroluj okres
  mista.py pridej "Název" --souradnice 49.6512,15.2031
      malá osada, kterou OpenStreetMap nenajde: souřadnice zadáš sám (zjistíš je na mapy.cz nebo openstreetmap.org)
  mista.py
      dohledá souřadnice u míst, která je ještě nemají (OpenStreetMap Nominatim, 1 dotaz za sekundu),
      a vypíše seznam. Když bod nesedí, opravte lat/lon v data/mista.json ručně.

Hledá jen sídla (featuretype=settlement); když žádné nenajde, vezme cokoli a pod seznamem napíše „POZOR: není obec“
(bar, ulice, ostrov, chráněné území). Pod seznamem varuje i u nového bodu dál než VZDALENE_KM od všech ostatních míst – nejspíš jiná obec
stejného jména. Vystěhovalci (Chicago, Vídeň) varování dostanou taky, jen jednou při přidání; stačí ověřit adresu.

Položka může mít "hypoteza": true a "rod": <Kekulé 8–15> – pak se na mapě ukáže jako hypotéza bez osob.
"""
import json, math, os, re, sys, time, urllib.error, urllib.parse, urllib.request
if sys.argv[1:2] in (["-h"], ["--help"]):   # nápověda místo pádu
    sys.exit(__doc__.strip())
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "mista.json")


VZDALENE_KM = 50   # nový bod dál než tohle od všech ostatních míst projektu = asi jiná obec stejného jména


class Nedostupny(Exception):
    """Geokodér nejde použít (chyba serveru, síť) ani po druhém pokusu."""


def nominatim(par):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(par)
    req = urllib.request.Request(url, headers={"User-Agent": "rodokmen-skill/1.0 (family genealogy map, occasional geocoding)"})
    for pokus in (1, 2):   # dočasná chyba serveru (5xx, 629 …) nebo sítě: jednou počkat a zkusit znovu
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                res = json.load(r)
            time.sleep(1.1)
            return res
        except urllib.error.HTTPError as e:
            if e.code == 429 or pokus == 2:   # 429 = příliš mnoho dotazů – znovu nezkoušet
                raise Nedostupny(f"HTTP {e.code}") from None
        except (urllib.error.URLError, OSError, ValueError) as e:
            if pokus == 2:
                raise Nedostupny(type(e).__name__) from None
        time.sleep(10)


SIDLA = {"city", "town", "village", "hamlet", "suburb", "quarter", "neighbourhood", "isolated_dwelling", "farm",
         "municipality", "borough", "cadastral_community"}   # typy ve třídě place; z boundary jen administrative (obce, katastry)
# place=locality chybí schválně: v OSM je to pojmenované neobydlené místo (pole, trať), ne sídlo


def je_sidlo(r):
    if r.get("class") == "place":
        return r.get("type") in SIDLA
    if (r.get("class"), r.get("type")) != ("boundary", "administrative"):
        return False
    if r.get("addresstype"):   # obec má „municipality“, „village“…; kraj „state“, okres „county“
        return r["addresstype"] in SIDLA | {"city_district"}
    return int(r.get("place_rank") or 0) >= 16


def vyber(res):
    """První sídlo jako (výsledek, True); bez sídla první výsledek (bar, ostrov, chráněné území…) s False."""
    obce = [r for r in res if je_sidlo(r)]
    return (obce[0], True) if obce else (res[0], False) if res else None


def geocode(q, zeme=None):
    """(lat, lon, adresa z OSM, je_obec); nejdřív jen sídla (featuretype=settlement), když nic, tak cokoli."""
    nalez = None
    for sidla in ({"featuretype": "settlement"}, {}):
        par = {"q": q, "format": "json", "limit": 5} | sidla | ({"countrycodes": zeme} if zeme else {})
        v = vyber(nominatim(par))
        if v and v[1]:
            nalez = v
            break
        nalez = nalez or v
    return (round(float(nalez[0]["lat"]), 4), round(float(nalez[0]["lon"]), 4), nalez[0]["display_name"], nalez[1]) if nalez else None


def vzdalenost_km(a, b):
    """Vzdušná vzdálenost dvou bodů (lat, lon) v km (haversine)."""
    (f1, l1), (f2, l2) = [(math.radians(x), math.radians(y)) for x, y in (a, b)]
    h = math.sin((f2 - f1) / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin((l2 - l1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def bod(e):
    """(lat, lon) jako čísla, nebo None, když souřadnice chybí, nejdou přečíst nebo jsou mimo rozsah ("50.1" projde)."""
    try:
        lat, lon = float(e["lat"]), float(e["lon"])
    except (KeyError, TypeError, ValueError):
        return None
    return (lat, lon) if -90 <= lat <= 90 and -180 <= lon <= 180 else None   # NaN i nekonečno rozsahem neprojdou


def nejblizsi(name, cache):
    """(km, název) nejbližšího jiného místa s použitelnými souřadnicemi, nebo None."""
    a = bod(cache[name])
    d = [(vzdalenost_km(a, b), n) for n, o in cache.items() if n != name and (b := bod(o))] if a else []
    return min(d) if d else None


def main():
    cache = json.load(open(OUT, encoding="utf-8-sig")) if os.path.exists(OUT) else {}
    argv = sys.argv
    souradnice = None
    if "--souradnice" in argv:
        i = argv.index("--souradnice")
        m = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*", argv[i + 1] if i + 1 < len(argv) else "")
        if not m or not (-90 <= float(m.group(1)) <= 90 and -180 <= float(m.group(2)) <= 180):
            sys.exit("--souradnice potřebuje zeměpisnou šířku a délku v desetinných stupních, např. --souradnice 49.6512,15.2031")
        souradnice = (round(float(m.group(1)), 4), round(float(m.group(2)), 4))
        sys.argv = argv = argv[:i] + argv[i + 2:]
    if souradnice and argv[1:2] != ["pridej"]:
        sys.exit('--souradnice jen s „pridej“: mista.py pridej "Název" --souradnice 49.6512,15.2031')
    if len(sys.argv) > 2 and sys.argv[1] == "pridej":
        name = sys.argv[2]
        stem = re.escape(name.split()[0][:5]) if len(name.split()) == 1 else re.escape(name)
        stare = cache.get(name, {})
        dotaz = sys.argv[4] if len(sys.argv) > 4 else stare.get("dotaz", f"{name}, Česko")
        cache[name] = dict(stare, re=sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else stare.get("re", stem),
                           dotaz=dotaz)
        if "lat" in stare and dotaz != stare.get("dotaz", f"{name}, Česko"):   # jiný dotaz = oprava místa → hledat znovu
            for k in ("lat", "lon", "osm"):
                cache[name].pop(k, None)
            print(f"přepočítávám: {name} (nový dotaz „{dotaz}“)")
        if souradnice:
            cache[name].update(lat=souradnice[0], lon=souradnice[1], osm="souřadnice zadané ručně")
    pozor, nove = [], []   # varování se vypíšou až pod seznamem, aby se v něm neztratila
    def uloz():
        json.dump(cache, open(OUT, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)

    for name, e in cache.items():
        if "lat" not in e:
            try:
                g = geocode(e.get("dotaz") or f"{name}, Česko")
                if not g and e.get("dotaz", f"{name}, Česko") == f"{name}, Česko":   # výchozí dotaz: zkus sousední země
                    g = geocode(name, "sk,pl,at,de,hu")
                    if g:
                        pozor.append(f"MIMO ČESKO: {name} → {g[2][:80]} – zkontroluj, že je to ono")
            except (Nedostupny, slusne.Zastaveno) as chyba:   # hotová místa neztratit, jedna srozumitelná věta
                uloz()
                duvod = f" ({chyba})" if isinstance(chyba, Nedostupny) else ""
                sys.exit(f"Geokodér OpenStreetMap teď neodpovídá{duvod} – místa dohledaná do teď jsem uložil, zbytek "
                         f"zkus za chvíli znovu (od „{name}“). Malou osadu přidáš i bez něj: "
                         f'mista.py pridej "{name}" --souradnice <šířka>,<délka>')
            if g:
                e["lat"], e["lon"], e["osm"] = g[:3]
                if not g[3]:
                    pozor.append(f"POZOR: není obec – zkontrolujte: {name} → {g[2][:80]}")
                nove.append(name)
            else:
                pozor.append(f"NENALEZENO: {name} – upravte 'dotaz' nebo doplňte lat/lon ručně")
    for name in nove:   # až po celé dávce, ať nezáleží na pořadí míst
        n = nejblizsi(name, cache)
        if n and n[0] > VZDALENE_KM:
            pozor.append(f"POZOR: {name} je {n[0]:.0f} km od nejbližšího místa ({n[1]}) – je to ono? {cache[name]['osm'][:80]}")
    uloz()
    for n, e in cache.items():
        print(f"{n:28} {str(e.get('lat', '?')):>8} {str(e.get('lon', '?')):>8}  hledá „{e.get('re')}“  {e.get('osm', '')[:60]}")
    for p in pozor:
        print(p)


if __name__ == "__main__":
    main()
