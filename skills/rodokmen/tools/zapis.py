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

  zapis.py odkaz <osoba> <klíč zápisu> [<klíč> …]
    Přidá klíč(e) do seznamu `r` v data/osoby.py: osoba = Kekulého číslo (P), nebo část jména bočního příbuzného
    (SIDE, musí sedět na jediného). Zbytek souboru zůstane doslova, klíč musí být v zaznamy.json.
"""
import ast, json, os, re, sys
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdin, "reconfigure"):   # vstup „-“ (roura, heredoc) je UTF-8; na Windows by se jinak četl v cp1250
    sys.stdin.reconfigure(encoding="utf-8-sig")

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


def bajty_pozice(src):
    """(řádek, sloupec v bajtech UTF-8) z ast → pozice v bajtech celého souboru."""
    starts, n = [0], 0
    for radek in src.split(b"\n"):
        n += len(radek) + 1
        starts.append(n)
    return lambda line, col: starts[line - 1] + col


def nacti_osoby(src):
    ns = {}
    exec(compile(src, "data/osoby.py", "exec"), ns)
    return ns


def odkaz(osoba, klice):
    path = os.path.join(ROOT, "data", "osoby.py")
    src = open(path, "rb").read()
    try:
        strom = ast.parse(src)
        pred = nacti_osoby(src)
    except Exception as e:
        sys.exit(f"data/osoby.py nejde načíst ({e}) – oprav ho nejdřív (git diff ukáže poslední změnu).")
    try:
        zaznamy = {z.get("klic") for z in json.load(open(os.path.join(ROOT, "data", "zaznamy.json"), encoding="utf-8-sig"))}
    except (OSError, ValueError) as e:
        sys.exit(f"data/zaznamy.json nejde přečíst ({e}).")
    chybi = [k for k in klice if k not in zaznamy]
    if chybi:
        sys.exit(f"Zápis {', '.join(chybi)} v data/zaznamy.json není – nejdřív ho zapiš (zapis.py zaznamy …).")

    def hodnota(jmeno):   # P = {…} / SIDE = […] na nejvyšší úrovni
        for uzel in strom.body:
            if isinstance(uzel, ast.Assign) and any(isinstance(t, ast.Name) and t.id == jmeno for t in uzel.targets):
                return uzel.value
        return None

    if re.fullmatch(r"\d+", osoba):
        P, k = hodnota("P"), int(osoba)
        volani = None
        if isinstance(P, ast.Dict):
            volani = next((v for kl, v in zip(P.keys, P.values) if isinstance(kl, ast.Constant) and kl.value == k), None)
        if volani is None:
            sys.exit(f"Osoba {k} v P (data/osoby.py) není.")
        popis, stare = f"osoba {k} ({pred['P'][k].get('n')})", pred["P"][k]
    else:
        side = hodnota("SIDE")
        kandidati = []
        for i, v in enumerate(side.elts if isinstance(side, ast.List) else []):
            n = next((kw.value.value for kw in getattr(v, "keywords", []) if kw.arg == "n" and isinstance(kw.value, ast.Constant)), "")
            if osoba.lower() in str(n).lower():
                kandidati.append((i, v, n))
        if len(kandidati) != 1:
            sys.exit(f"Bočního příbuzného „{osoba}“ " + ("v SIDE není." if not kandidati else
                     "je víc: " + "; ".join(n for _, _, n in kandidati) + " – napiš delší část jména."))
        i, volani, n = kandidati[0]
        popis, stare = f"boční příbuzný {n}", pred["SIDE"][i]
    jako_dict = isinstance(volani, ast.Call) and getattr(volani.func, "id", "") == "dict" and not volani.args
    if not (jako_dict or isinstance(volani, ast.Dict)):
        sys.exit(f"{popis}: čekal jsem dict(…) nebo {{…}} – uprav ručně.")

    nove = [k for k in klice if k not in (stare.get("r") or [])]
    if not nove:
        print(f"{popis}: zápis už má, nic neměním.")
        return
    pos = bajty_pozice(src)
    if jako_dict:
        r = next((kw.value for kw in volani.keywords if kw.arg == "r"), None)
    else:
        r = next((v for kl, v in zip(volani.keys, volani.values) if isinstance(kl, ast.Constant) and kl.value == "r"), None)
    # styl uvozovek podle souboru: první řetězec v položce (v ukázce a z importu bývají apostrofy)
    prvni = next((n for n in ast.walk(volani) if isinstance(n, ast.Constant) and isinstance(n.value, str)), None)
    apostrof = prvni is not None and src[pos(prvni.lineno, prvni.col_offset):][:1] == b"'"
    retez = lambda k: (repr(k) if apostrof else json.dumps(k, ensure_ascii=False))
    vlozit = ", ".join(retez(k) for k in nove).encode("utf-8")
    if r is not None:
        if not isinstance(r, ast.List):
            sys.exit(f"{popis}: r není seznam [ … ] – uprav ručně.")
        konec = pos(r.end_lineno, r.end_col_offset) - 1          # pozice „]“
        pred_z = src[:konec].rstrip()
        oddel = b"" if not r.elts else (b" " if pred_z.endswith(b",") else b", ")
    else:
        konec = pos(volani.end_lineno, volani.end_col_offset) - 1   # pozice „)“ nebo „}“
        pred_z = src[:konec].rstrip()
        klic_r = b"r=[" if jako_dict else (retez("r") + ": [").encode()
        oddel = (b" " if pred_z.endswith(b",") else b", ") + klic_r
        vlozit += b"]"
    if r is not None and not r.elts:   # r=[] → r=["klíč"]
        novy = src[:konec] + vlozit + src[konec:]
    else:   # za poslední prvek / argument; mezery a konec řádku před „]“ či „)“ zůstanou
        novy = pred_z + oddel + vlozit + src[len(pred_z):]

    # pojistka: soubor jde načíst, u osoby přibyly jen ty klíče a nic jiného se nezměnilo
    try:
        po = nacti_osoby(novy)
    except Exception as e:
        sys.exit(f"Úprava by rozbila data/osoby.py ({e}) – nic jsem nezapsal, uprav ručně.")
    ocekavane = dict(pred)
    if popis.startswith("osoba"):
        ocekavane["P"] = {**pred["P"], k: {**stare, "r": (stare.get("r") or []) + nove}}
    else:
        ocekavane["SIDE"] = [*pred["SIDE"][:i], {**stare, "r": (stare.get("r") or []) + nove}, *pred["SIDE"][i + 1:]]
    for jmeno in ("P", "SIDE", "LINES", "ISSUES", "HYPOTEZY", "SAME"):
        if po.get(jmeno) != ocekavane.get(jmeno):
            sys.exit(f"Úprava by změnila i {jmeno} – nic jsem nezapsal, uprav ručně.")

    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(novy)
    os.replace(tmp, path)
    print(f"data/osoby.py: {popis} – přidán zápis {', '.join(nove)}")


def main():
    if sys.argv[1:2] == ["odkaz"]:
        if len(sys.argv) < 4:
            sys.exit(__doc__)
        return odkaz(sys.argv[2], sys.argv[3:])
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
    json.loads(text)   # pojistka: výsledek musí být platný JSON

    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)   # celý soubor naráz – při chybě nezůstane rozepsaný
    print(f"data/{nazev}.json: {'přidáno' if idx is None else 'změněno'} „{klic}“")


if __name__ == "__main__":
    main()
