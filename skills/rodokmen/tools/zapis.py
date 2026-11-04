#!/usr/bin/env python3
"""Přidá nebo nahradí jednu položku v datech projektu – formát souboru zůstane stejný (odsazení 1, české znaky, konce
řádků LF), takže změna v historii je jen ta jedna položka.

Použití (z kořene projektu):
  zapis.py <soubor> <klíč> <vstup.json> [--sloucit]
    soubor     zaznamy | svazky | prepisy | zvyrazneni | mista | dokumenty   (= data/<soubor>.json)
    klíč       zaznamy: „klic“ zápisu; dokumenty: „img“; ostatní: klíč ve slovníku (id svazku, klíč zápisu, obec)
    vstup.json soubor s jedním objektem JSON (napiš ho nástrojem Write do pracovni/), „-“ = ze vstupu
    --sloucit  jen změní / doplní uvedená pole, ostatní pole položky nechá
Položka se stejným klíčem se nahradí, jinak se přidá na konec. Python skripty ani `sed -i` na data nepoužívej.

  zapis.py --smazat <klíč zápisu>
    smaže zápis, který se ukázal jako omyl (cizí rodina): položku v zaznamy, prepisy a zvyrazneni (zbytek souborů beze
    změny) a výřezy vyrezy/<klíč>.jpg a zdroje/<klíč>.jpg přesune do pracovni/smazano_<datum>/ (jdou vrátit).
    Když zápis ještě cituje osoba, boční příbuzný nebo text na webu (osoby.py, pribeh.md, zajimavosti.md, web.json),
    nic nesmaže a vypíše kde; zmínky v deníku a dalších poznámkách jen ohlásí.
"""
import json, os, re, shutil, sys, time
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEZNAMY = {"zaznamy": "klic", "dokumenty": "img"}   # soubory se seznamem: pole, podle kterého se položka pozná
SLOVNIKY = {"svazky", "prepisy", "zvyrazneni", "mista"}
WS = re.compile(r"\s*")


def polozky(text):
    """Položky nejvyšší úrovně: [(klíč nebo None, začátek hodnoty, konec hodnoty)] – pozice v původním textu."""
    dec, i = json.JSONDecoder(), WS.match(text).end()
    otevreni, i, out = text[i], i + 1, []
    while True:
        i = WS.match(text, i).end()
        if text[i] in "]}":
            return out
        klic = None
        if otevreni == "{":
            klic, i = dec.raw_decode(text, i)
            i = WS.match(text, WS.match(text, i).end() + 1).end()   # za dvojtečku
        _, j = dec.raw_decode(text, i)
        out.append((klic, i, j))
        i = WS.match(text, j).end()
        if text[i] == ",":
            i += 1


def jako(text, s, e, v):
    """Hodnota v JSON ve stejném stylu jako text[s:e] (na jednom řádku, nebo odsazená po jedné mezeře)."""
    if "\n" not in text[s:e]:
        return json.dumps(v, ensure_ascii=False)
    odsazeni = text[text.rfind("\n", 0, s) + 1:s]
    odsazeni = odsazeni[:len(odsazeni) - len(odsazeni.lstrip())]
    return json.dumps(v, ensure_ascii=False, indent=1).replace("\n", "\n" + odsazeni)


def prepis_v_poradku(klic, v):
    """prepisy.json: web čte jen „orig“ (přepis) a „cs“ (překlad); jiné pole by na webu tiše chybělo (#74)."""
    jine = sorted(set(v) - {"orig", "cs"})
    chybi = [p for p in ("orig", "cs") if not isinstance(v.get(p), str) or not v[p].strip()]
    if jine or chybi:
        sys.exit(f"Přepis „{klic}“ nezapsán: má mít jen pole „orig“ (přepis originálu) a „cs“ (český překlad), "
                 "obě neprázdná." + (f" Chybí: {', '.join(chybi)}." if chybi else "")
                 + (f" Navíc: {', '.join(jine)} – web je nezobrazí (překlad patří do „cs“)." if jine else ""))


def bez_polozky(text, poz, idx):
    """Text JSON bez položky idx – zbytek souboru zůstane doslova (stejně jako při nahrazení)."""
    if len(poz) == 1:
        zacatek = WS.match(text).end()
        return text[:zacatek + 1] + text[text.rindex("]" if text[zacatek] == "[" else "}"):]
    if idx > 0:   # od konce předchozí hodnoty: „,\n <klíč>: hodnota“
        return text[:poz[idx - 1][2]] + text[poz[idx][2]:]
    zacatek = WS.match(text, WS.match(text).end() + 1).end()      # první položka (u slovníku i s klíčem)
    za = WS.match(text, poz[0][2]).end() + 1                      # za čárku
    return text[:zacatek] + text[WS.match(text, za).end():]


def kdo_cituje(klic):
    """Kde v datech je klíč zápisu ještě použitý (osoby.py, markdown, web.json)."""
    data = os.path.join(ROOT, "data")
    vzor = re.compile(r"(?<![\w-])" + re.escape(klic) + r"(?![\w-])")
    return [f for f in sorted(os.listdir(data)) if f.endswith((".py", ".md")) or f == "web.json"
            if vzor.search(open(os.path.join(data, f), encoding="utf-8-sig").read())]


BLOKUJE = ("osoby.py", "pribeh.md", "zajimavosti.md", "web.json")   # z nich vzniká obsah webu – citace musí pryč


def smazat(klic):
    zminky = kdo_cituje(klic)
    cituje = [f for f in zminky if f in BLOKUJE]
    if cituje:
        sys.exit(f"Zápis „{klic}“ nesmazán: ještě ho cituje {', '.join('data/' + f for f in cituje)}. "
                 "Nejdřív ho odeber z „r“ osob a z textů, pak smaž znovu.")
    smazano = []
    for nazev in ("zaznamy", "prepisy", "zvyrazneni"):
        path = os.path.join(ROOT, "data", nazev + ".json")
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8-sig").read()
        data = json.loads(text) if text.strip() else None
        if not data:
            continue
        poz = polozky(text)
        if nazev in SEZNAMY:
            idx = next((n for n, x in enumerate(data) if isinstance(x, dict) and x.get(SEZNAMY[nazev]) == klic), None)
        else:
            idx = next((n for n, (k, _, _) in enumerate(poz) if k == klic), None)
        if idx is None:
            continue
        novy = bez_polozky(text, poz, idx)
        ocekavano = [x for n, x in enumerate(data) if n != idx] if nazev in SEZNAMY else \
            {k: v for k, v in data.items() if k != klic}
        if json.loads(novy) != ocekavano:   # pojistka: smazala se právě ta jedna položka
            sys.exit(f"data/{nazev}.json: smazání by změnilo víc než jednu položku – nic jsem nezměnil.")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(novy)
        os.replace(tmp, path)
        smazano.append(f"data/{nazev}.json")
    kam = os.path.join(ROOT, "pracovni", "smazano_" + time.strftime("%Y%m%d"))
    for slozka in ("vyrezy", "zdroje"):
        obr = os.path.join(ROOT, slozka, klic + ".jpg")
        if os.path.exists(obr):
            os.makedirs(os.path.join(kam, slozka), exist_ok=True)
            shutil.move(obr, os.path.join(kam, slozka, klic + ".jpg"))
            smazano.append(f"{slozka}/{klic}.jpg → {os.path.relpath(kam, ROOT)}/{slozka}/")
    if not smazano:
        sys.exit(f"Zápis „{klic}“ v datech není.")
    print(f"smazán zápis „{klic}“: " + "; ".join(smazano))
    jinde = [f for f in zminky if f not in BLOKUJE]
    if jinde:
        print(f"Zmiňuje ho i {', '.join('data/' + f for f in jinde)} – text nech, odkaz na web („/zdroj/{klic}/“) "
              "případně uprav (npm run data ho ohlásí jako nefunkční).")
    print("Do deníku (research_log.md) zapiš, proč zápis nepatří k rodině – ať ho příště nikdo nenajde „znovu“.")


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--smazat":
        return smazat(sys.argv[2])
    args = [a for a in sys.argv[1:] if a != "--sloucit"]
    sloucit = "--sloucit" in sys.argv
    if len(args) != 3 or args[0] not in {*SEZNAMY, *SLOVNIKY}:
        sys.exit(__doc__)
    nazev, klic, vstup = args
    path = os.path.join(ROOT, "data", nazev + ".json")
    try:
        obj = json.load(sys.stdin if vstup == "-" else open(vstup, encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        sys.exit(f"Vstup {vstup} není platný JSON: {e}")
    if not isinstance(obj, dict):
        sys.exit("Vstup musí být jeden objekt JSON ({…}).")
    seznam = nazev in SEZNAMY
    if seznam and obj.setdefault(SEZNAMY[nazev], klic) != klic:
        sys.exit(f"Klíč „{klic}“ nesedí s „{SEZNAMY[nazev]}“ ve vstupu („{obj[SEZNAMY[nazev]]}“).")
    text = open(path, encoding="utf-8-sig").read() if os.path.exists(path) else ""
    try:
        data = json.loads(text) if text.strip() else ([] if seznam else {})
        if not isinstance(data, list if seznam else dict):
            raise ValueError("čekal jsem " + ("seznam [ … ]" if seznam else "slovník { … }"))
    except ValueError as e:
        sys.exit(f"data/{nazev}.json nejde přečíst ({e}) – oprav ho nejdřív (git diff ukáže poslední změnu).")

    poz = polozky(text) if data else []
    if seznam:
        idx = next((n for n, x in enumerate(data) if isinstance(x, dict) and x.get(SEZNAMY[nazev]) == klic), None)
    else:
        idx = next((n for n, (k, _, _) in enumerate(poz) if k == klic), None)
    stare = None if idx is None else (data[idx] if seznam else data[klic])
    nove = {**stare, **obj} if sloucit and isinstance(stare, dict) else obj
    if not poz:   # prázdný nebo nový soubor
        text = json.dumps([nove] if seznam else {klic: nove}, ensure_ascii=False, indent=1) + "\n"
    elif idx is not None:   # nahradit jen text té jedné položky, zbytek souboru zůstane doslova
        _, s, e = poz[idx]
        text = text[:s] + jako(text, s, e, nove) + text[e:]
    else:   # přidat za poslední položku ve stejném stylu
        _, s, e = poz[-1]
        radek = text[text.rfind("\n", 0, s) + 1:s]
        odsazeni = radek[:len(radek) - len(radek.lstrip())]
        text = (text[:e] + ",\n" + odsazeni + ("" if seznam else json.dumps(klic, ensure_ascii=False) + ": ")
                + jako(text, s, e, nove) + text[e:])
    if nazev == "prepisy":
        prepis_v_poradku(klic, nove)
    json.loads(text)   # pojistka: výsledek musí být platný JSON

    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)   # celý soubor naráz – při chybě nezůstane rozepsaný
    print(f"data/{nazev}.json: {'přidáno' if idx is None else 'změněno'} „{klic}“")


if __name__ == "__main__":
    main()
