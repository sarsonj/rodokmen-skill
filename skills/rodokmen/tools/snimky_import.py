#!/usr/bin/env python3
"""Převezme snímky uložené rozšířením Snímkovač do sdílené mezipaměti a do rejstříku snímků.

Rozšíření ukládá do Stažené/rodokmen-snimky/<kniha>/<matrikaId>_<snímek>.jpg + .json (adresa, rozměry, čas).
Tenhle skript:
  1. každý snímek uloží do mezipaměti (tools/cache.py, klíč jako u eBadatelny: cache.py najdi <adresa> ho pak najde),
  2. do rejstříku data/snimky.tsv zapíše řádky (přes tools/snimky.py pridej, když ho projekt má): archiv podle webu
     (soa-praha, mza, soa-trebon, matricula, jiny), snímky za sebou v jednom úseku „10-12“, stav „nejisty“ = uloženo,
     ale zatím nepřečteno (po přečtení se doplní),
  3. zpracované soubory přesune do <složka>/_importovano/ (ať se neberou dvakrát; --nechat je nechá na místě).
Na síť nesahá, nic se nestahuje.

Použití (z kořene projektu):
  python3 -I tools/snimky_import.py [složka] [--nechat] [--nahled]
      složka   výchozí <složka Stažené>/rodokmen-snimky (na Windows i přesunutá, např. D:/Downloads)
      --nahled jen vypíše, co by se stalo (nic neuloží)
"""
import glob, json, os, subprocess, sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:   # python -I nepřidává složku skriptu do cesty
    sys.path.insert(0, HERE)
import cache  # noqa: E402

def slozka_stazene():
    """Složka Stažené: na Windows podle registru (uživatel ji mohl přesunout, např. na D:/Downloads), jinak ~/Downloads."""
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as k:
                cesta = os.path.expandvars(winreg.QueryValueEx(k, "{374DE290-123F-4565-9164-39C4925E467B}")[0])
                if os.path.isdir(cesta):
                    return cesta
        except OSError:
            pass
    return os.path.join(os.path.expanduser("~"), "Downloads")


VYCHOZI = os.path.join(slozka_stazene(), "rodokmen-snimky")
SNIMKY_PY = os.path.join(HERE, "snimky.py")


def do_rejstriku(archiv, kniha, snimky, co):
    """Řádek do rejstříku snímků (tools/snimky.py). Když ho projekt nemá, jen vypíše, co by zapsal."""
    if not os.path.exists(SNIMKY_PY):
        print(f"(rejstřík snímků v projektu není) {archiv} {kniha} sn. {snimky} – {co}")
        return
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", SNIMKY_PY, "pridej",
                        archiv, kniha, snimky, co, "--stav", "nejisty", "--cetl", "Snímkovač"],
                       capture_output=True, text=True, encoding="utf-8")
    print((r.stdout or r.stderr).strip())


def nacti_sidecar(jpg):
    try:
        with open(os.path.splitext(jpg)[0] + ".json", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def uloz_do_cache(jpg, meta):
    """Uloží jeden snímek do mezipaměti. Vrací 'ulozeno' | 'uz-bylo' | chybový text."""
    with open(jpg, "rb") as f:
        data = f.read()
    if not cache.cely(data):
        return "soubor není celý obrázek"
    if meta["druh"] == "osd":   # poskládáno z dlaždic (MZA aj.) – novější uložení je úplnější, přepíše starší
        p = f"osd/{meta.get('host', 'web')}/{meta['matrikaId']}/sn{int(meta['snimek']):04d}.jpg" if str(meta["snimek"]).isdigit()             else f"osd/{meta.get('host', 'web')}/{meta['matrikaId']}/{cache.hashlib.sha1(str(meta['snimek']).encode()).hexdigest()[:16]}.jpg"
        return "ulozeno" if cache.uloz(p, data) else "do mezipaměti nejde zapisovat"
    if meta["druh"] == "matricula":   # Matricula Online: celý snímek, klíč farnost/signatura/číslo snímku
        p = f"matricula/{meta.get('dieceze', 'x')}/{meta.get('farnost', 'x')}/{meta.get('signatura', meta['matrikaId'])}/sn{int(meta['snimek']):04d}.jpg"
        if os.path.exists(cache.cesta(p)) and cache.cely_soubor(cache.cesta(p)):
            return "uz-bylo"
        return "ulozeno" if cache.uloz(p, data) else "do mezipaměti nejde zapisovat"
    if meta["druh"] == "web":   # obecný web: mezipaměť podle adresy obrázku (jako u brzdy slusne.py)
        url = meta.get("obrazek") or ""
        if not url.startswith("http"):
            return "v .json chybí adresa obrázku"
        if cache.najdi_url(url):
            return "uz-bylo"
        return "ulozeno" if cache.uloz_url(url, data) else "do mezipaměti nejde zapisovat"
    klic = cache.klic_ebadatelna(meta["druh"], meta["matrikaId"], meta["snimek"])
    if os.path.exists(cache.cesta(klic)) and cache.cely_soubor(cache.cesta(klic)):
        return "uz-bylo"
    return "ulozeno" if cache.uloz(klic, data) else "do mezipaměti nejde zapisovat"


def useky(cisla):
    """[10, 11, 12, 20] -> ['10-12', '20']"""
    out, cisla = [], sorted(set(cisla))
    i = 0
    while i < len(cisla):
        j = i
        while j + 1 < len(cisla) and cisla[j + 1] == cisla[j] + 1:
            j += 1
        out.append(str(cisla[i]) if i == j else f"{cisla[i]}-{cisla[j]}")
        i = j + 1
    return out


def main(a):
    if "-h" in a or "--help" in a:
        sys.exit(__doc__)
    nechat = "--nechat" in a
    nahled = "--nahled" in a
    poz = [x for x in a if not x.startswith("--")]
    slozka = os.path.abspath(poz[0]) if poz else VYCHOZI
    if not os.path.isdir(slozka):
        sys.exit(f"složka neexistuje: {slozka}")

    knihy = {}   # (matrikaId, druh) -> {"kniha": název, "snimky": [čísla]}
    pocty = {"ulozeno": 0, "uz-bylo": 0, "chyba": 0}
    zpracovane = []
    for jpg in sorted(glob.glob(os.path.join(slozka, "**", "*.jpg"), recursive=True)):
        if any(c.startswith("_") for c in os.path.relpath(jpg, slozka).split(os.sep)[:-1]):
            continue   # podsložky na podtržítko (_importovano, _chybne …) se přeskakují
        meta = nacti_sidecar(jpg)
        if not meta or not all(k in meta for k in ("druh", "matrikaId", "snimek")):
            print(f"přeskakuji (chybí .json se základními údaji): {jpg}")
            pocty["chyba"] += 1
            continue
        if meta.get("vyrez"):   # výřez k osobě – zůstává ve složce, Claude ho přiřadí k zápisu ručně
            print(f"výřez ponechán: {jpg}")
            continue
        # pojistka: eBadatelna (druh d/a) jen s adresou eBadatelny; neznámý druh (novější verze rozšíření) přeskočit
        if meta["druh"] in ("d", "a") and "ebadatelna.soapraha.cz" not in str(meta.get("adresa", "ebadatelna.soapraha.cz")):
            print(f"přeskakuji (druh {meta['druh']}, ale adresa není eBadatelna): {jpg}")
            pocty["chyba"] += 1
            continue
        if meta["druh"] not in ("d", "a", "osd", "web", "matricula"):
            print(f"přeskakuji (neznámý druh „{meta['druh']}“ – aktualizuj tools/snimky_import.py): {jpg}")
            pocty["chyba"] += 1
            continue
        vysledek = "ulozeno" if nahled else uloz_do_cache(jpg, meta)
        if vysledek not in ("ulozeno", "uz-bylo"):
            print(f"CHYBA {jpg}: {vysledek}")
            pocty["chyba"] += 1
            continue
        pocty[vysledek] += 1
        k = knihy.setdefault((str(meta["matrikaId"]), meta["druh"]), {"kniha": meta.get("kniha") or "", "snimky": []})
        k["snimky"].append(meta["snimek"] if meta["druh"] == "web" or not str(meta["snimek"]).isdigit() else int(meta["snimek"]))
        if meta["druh"] == "matricula":
            k["matricula_id"] = f"{meta.get('dieceze', '')}/{meta.get('farnost', '')}/{meta.get('signatura', '')}".strip("/")
        if meta["druh"] == "osd":
            k["host"] = meta.get("host", "")
            pk = meta.get("pokryti") or {}
            k["pokryti"] = (f" (přehled {pk.get('prehled_procent', '?')} %, čtení {pk.get('ideal_procent', '?')} %"
                            + (f", záznam {pk['zapis_procent']} %" if 'zapis_procent' in pk else "") + " stránky)")
        if meta.get("kniha"):
            k["kniha"] = meta["kniha"]
        zpracovane.append(jpg)

    for (xid, druh), k in sorted(knihy.items()):
        if druh == "web":   # jeden řádek na obrázek: archiv „jiny“, kniha = web, snímek = otisk adresy obrázku
            for h in sorted(set(k["snimky"])):
                co = f"uloženo Snímkovačem z webu (zatím nepřečteno){': ' + k['kniha'] if k['kniha'] else ''}"
                if nahled:
                    print(f"rejstřík: jiny {xid} {h} – {co}")
                    continue
                do_rejstriku("jiny", xid, str(h), co)
            continue
        kniha_id = k.get("matricula_id") or xid if druh == "matricula" else (xid if druh in ("d", "osd") else f"a-{xid}")
        host = k.get("host", "")
        archiv = ("matricula" if druh == "matricula" else "soa-praha" if druh in ("d", "a") else "mza" if host.endswith("mza.cz")
                  else "soa-trebon" if host.endswith("ceskearchivy.cz") else "jiny")
        for us in useky([s for s in k["snimky"] if isinstance(s, int)]):
            co = f"uloženo Snímkovačem (zatím nepřečteno){': ' + k['kniha'] if k['kniha'] else ''}{k.get('pokryti', '')}"
            if nahled:
                print(f"rejstřík: {archiv} {kniha_id} sn. {us} – {co}")
                continue
            do_rejstriku(archiv, kniha_id, us, co)

    if not nahled and not nechat:
        for jpg in zpracovane:
            rel = os.path.relpath(jpg, slozka)
            for src in (jpg, os.path.splitext(jpg)[0] + ".json"):
                if os.path.exists(src):
                    cil = os.path.join(slozka, "_importovano", os.path.relpath(src, slozka))
                    os.makedirs(os.path.dirname(cil), exist_ok=True)
                    os.replace(src, cil)
    print(f"hotovo: nově v mezipaměti {pocty['ulozeno']}, už tam bylo {pocty['uz-bylo']}, chyb {pocty['chyba']}"
          + (" (nahled – nic se neuložilo)" if nahled else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
