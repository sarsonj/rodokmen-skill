#!/usr/bin/env python3
"""Rekonstrukce rodin a rozhodování mezi kandidáty – malá databáze jednoho „případu“ v data/rodiny/<případ>.json.

Kdy: (1) skládáš celou rodinu předka ze křtů sourozenců (kmotři, dům, prarodiče se doplňují navzájem);
(2) na místo předka připadá víc lidí stejného jména (18. století: v jedné vsi dva páry „Václav × Kateřina“ křtí děti současně).
Postup jako hledání do šířky (BFS): kandidáty zapíšeš, ke každému čteš zápisy po vrstvách
(1 = jeho vlastní křest, svatba, úmrtí; 2 = jeho děti, kmotři, svědci, sourozenci; 3 = rodiče, tchán…)
a po každé vrstvě se díváš, kde se osoby nebo domy kandidáta potkají s tím, co je o předkovi doložené („kotvy“).

Použití (z kořene projektu; síť nepoužívá, čte jen soubory):
  rodiny.py novy <případ> "cíl" [--osoba N]       založí případ (N = Kekulého číslo předka, volitelné)
  rodiny.py kandidat <případ> <id> "popis"         přidá kandidáta (id krátké: A, B, syn_jana…)
  rodiny.py stav <případ> <id> otevreny|vyloucen|potvrzen "důvod"
  rodiny.py zapis <případ> <soubor.json>            přidá přečtený zápis (objekt nebo seznam objektů, formát níže)
  rodiny.py ukol <případ> <kandidát|vse> <vrstva> "co hledat" ["kde: svazek, snímky"]
  rodiny.py hotovo <případ> <úkol> "výsledek" [--nic]   --nic = prošel jsem, nic jsem nenašel (taky výsledek)
  rodiny.py prehled <případ>     kandidáti, zápisy, co je na řadě (nejnižší vrstva s otevřenými úkoly)
  rodiny.py prunik <případ>      shody osob a domů kandidátů s kotvami a s data/osoby.py
  rodiny.py rodiny <případ>      děti seskupené podle rodičů: pořadí, mezery, opakovaná jména, stálí kmotři
  rodiny.py seznam               všechny případy v projektu

Zápis (pracovni/x.json):
  {"patri": "kotva" | "<id kandidáta>" | "?",   kotva = doloženě o předkovi; "?" = zatím nevíme čí
   "druh": "N" | "O" | "Z" | "J", "datum": "3. 3. 1760", "obec": "Lhota", "dum": "5",
   "zdroj": "a1b2c3d4 sn. 10", "klic": "<klíč v data/zaznamy.json, když už tam je>", "pozn": "…",
   "osoby": [{"jmeno": "Václav Novák", "role": "otec", "dum": "5", "obec": "Lhota", "pozn": "sedlák"}, …]}
Role: dite, otec, matka, zenich, nevesta, otec_zenicha, matka_zenicha, otec_nevesty, matka_nevesty, kmotr, kmotra,
svedek, baba, zemrely, manzel, manzelka, rodic, jiny. Jména piš česky v 1. pádě (Wenceslaus → Václav), nejistá s „(?)“.

Nástroj jména porovnává volně (latinská a německá křestní jména, -ová, w/v, cz/č…), proto jsou shody jen NÁMĚTY:
každou ověř v zápisu. Rozhoduje doklad, ne počet shod. Do data/osoby.py jde až potvrzený kandidát.
"""
import json, os, re, sys, unicodedata
from collections import defaultdict
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.getcwd()
SLOZKA = os.path.join(ROOT, "data", "rodiny")   # stav výzkumu – patří do gitu, web ho nečte
ROLE = {"dite", "otec", "matka", "zenich", "nevesta", "otec_zenicha", "matka_zenicha", "otec_nevesty", "matka_nevesty",
        "kmotr", "kmotra", "svedek", "baba", "zemrely", "manzel", "manzelka", "rodic", "jiny"}
STAVY = ("otevreny", "vyloucen", "potvrzen")

# Křestní jména: latinské a německé tvary z matrik → český tvar (bez diakritiky, malá písmena).
KRESTNI = {
    "vaclav": "wenceslaus wenzel wenzl wentzel venceslaus wenceslai", "jan": "joannes johannes johann hans joanne joannis",
    "katerina": "catharina katharina katharine catherina", "ondrej": "andreas andre andreae", "jiri": "georgius georg georgii",
    "antonin": "antonius anton antoni", "frantisek": "franciscus franz francisci", "frantiska": "francisca franziska",
    "josef": "josephus joseph josephi", "josefa": "josepha", "rozalie": "rosalia rozalia", "anna": "anne", "marie": "maria",
    "terezie": "theresia teresia theresa terezia", "vavrinec": "laurentius lorenz laurenz", "mikulas": "nicolaus nikolaus nicolai",
    "martin": "martinus", "matej": "matthias mathias matthaeus", "petr": "petrus peter", "pavel": "paulus paul",
    "tomas": "thomas", "jakub": "jacobus jakob jacob", "vojtech": "adalbertus adalbert", "augustin": "augustinus",
    "dorota": "dorothea", "magdalena": "magdalene", "veronika": "veronica", "barbora": "barbara", "alzbeta": "elisabetha elisabeth",
    "ludmila": "ludmilla", "justina": "justine", "judita": "judith", "tobias": "tobiae", "karel": "carolus karl",
    "ignac": "ignatius ignaz", "alois": "aloysius aloys", "simon": "simeon", "stepan": "stephanus stephan",
    "vit": "vitus veit", "zuzana": "susanna susana zuzanna", "eva": "eva", "kristina": "christina", "jindrich": "henricus heinrich",
    "bartolomej": "bartholomaeus", "filip": "philippus philipp", "rehor": "gregorius gregor", "michal": "michael",
    "jakub_": "", "lukas": "lucas", "marek": "marcus", "daniel": "danielus", "adam": "adamus", "eliska": "",
}
_KR = {}
for cz, vs in KRESTNI.items():
    _KR[cz.rstrip("_")] = cz.rstrip("_")
    for v in vs.split():
        _KR[v] = cz.rstrip("_")


def bez_diakritiky(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


def krestni_klic(s):
    s = re.sub(r"[^a-z ]", " ", bez_diakritiky(s)).split()
    return _KR.get(s[0], s[0]) if s else ""


def prijmeni_klic(s):
    """Volný klíč příjmení: Novák, Nowak, Nowák, Nováková, Nováčka → novak; Petráček, Petráčková → petrak."""
    s = re.sub(r"[^a-z]", "", bez_diakritiky(s))
    s = s.replace("sch", "s").replace("cz", "c").replace("w", "v").replace("y", "i").replace("ia", "a")
    s = s.replace("tz", "c").replace("ch", "#").replace("c", "k").replace("#", "ch")
    for kon in ("ovich", "ova", "ovi", "ove", "a"):     # ženský tvar a koncovky → kmen
        if len(s) > 4 and s.endswith(kon):
            s = s[: -len(kon)]
            break
    if s.endswith("ek"):                                # pohyblivé e: Javůrek / Javůrková, Doleček / Dolečková
        s = s[:-2] + "k"
    s = re.sub(r"(.)\1+", r"\1", s)
    return s


def osoba_klic(jmeno):
    cast = [c for c in re.sub(r"\(\?\)|\[.*?\]|†|\+", " ", jmeno).split() if c]
    if not cast:
        return None
    if len(cast) == 1:
        return (krestni_klic(cast[0]), "")
    return (krestni_klic(cast[0]), prijmeni_klic(cast[-1]))


def dum_klic(obec, dum):
    if not dum:
        return None
    return (prijmeni_klic(obec or "")[:4], re.sub(r"\D", "", str(dum)))


def cesta(pripad):
    if not re.fullmatch(r"[a-z0-9_]+", pripad):
        sys.exit("CHYBA: název případu jen malá písmena bez diakritiky, číslice a _ (např. vaclav_512)")
    return os.path.join(SLOZKA, pripad + ".json")


def nacti(pripad):
    c = cesta(pripad)
    if not os.path.exists(c):
        sys.exit(f"CHYBA: případ {pripad} neexistuje ({c}); založ ho: rodiny.py novy {pripad} \"cíl\"")
    with open(c, encoding="utf-8") as f:
        return json.load(f)


def uloz(pripad, d):
    os.makedirs(SLOZKA, exist_ok=True)
    tmp = cesta(pripad) + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, cesta(pripad))


def nove_id(seznam, pismeno):
    n = max([int(x["id"][1:]) for x in seznam if re.fullmatch(pismeno + r"\d+", x.get("id", ""))] + [0])
    return f"{pismeno}{n + 1}"


def predci():
    """Osoby z data/osoby.py (P a SIDE) jako {klíč: [popis]} – kvůli shodám s rodokmenem."""
    p = os.path.join(ROOT, "data", "osoby.py")
    out = defaultdict(list)
    if not os.path.exists(p):
        return out
    ns = {}
    try:
        exec(open(p, encoding="utf-8").read(), ns)
    except Exception as e:
        print(f"upozornění: data/osoby.py nejde načíst ({e}), shody s rodokmenem vynechávám")
        return out
    for k, o in ns.get("P", {}).items():
        kl = osoba_klic(o.get("n", ""))
        if kl and kl[1]:
            out[kl].append((rok(o.get("y", "") + " " + " ".join(o.get("f", [])[:1])), f"č. {k} {o.get('n')}"))
    for o in ns.get("SIDE", []):
        kl = osoba_klic(re.sub(r"\(.*?\)", "", o.get("n", "")))
        if kl and kl[1]:
            out[kl].append((rok(o.get("n", "") + " " + o.get("t", "")), f"příbuzný u č. {o.get('k')}: {o.get('n')}"))
    return out


SOUCASNIK = 80   # rozdíl let, do kterého beru člověka z rodokmenu jako možnou shodu (jinak jen jmenovec)


def soucasnici(rod, kl, r):
    return [t for y, t in rod.get(kl, []) if not (y and r and abs(y - r) > SOUCASNIK)]


def popis_zapisu(z):
    return f"{z['id']} {z.get('druh', '?')} {z.get('datum', '')} {z.get('obec', '')}" + \
           (f" č. {z['dum']}" if z.get("dum") else "") + (f" ({z['zdroj']})" if z.get("zdroj") else "")


# ---------------------------------------------------------------- příkazy
def cmd_novy(a):
    if len(a) < 2:
        sys.exit("použití: rodiny.py novy <případ> \"cíl\" [--osoba N]")
    pripad, cil = a[0], a[1]
    if os.path.exists(cesta(pripad)):
        sys.exit(f"CHYBA: případ {pripad} už existuje")
    d = {"pripad": pripad, "cil": cil, "kandidati": {}, "zapisy": [], "ukoly": []}
    if "--osoba" in a:
        d["osoba"] = int(a[a.index("--osoba") + 1])
    uloz(pripad, d)
    print(f"založeno: {cesta(pripad)}\nDál: kotvy (doložené zápisy o předkovi) přes `zapis` s \"patri\": \"kotva\", "
          f"pak kandidáti (`kandidat`) a úkoly vrstvy 1 (`ukol`).")


def cmd_kandidat(a):
    if len(a) < 3:
        sys.exit("použití: rodiny.py kandidat <případ> <id> \"popis\"")
    d = nacti(a[0])
    if not re.fullmatch(r"[A-Za-z0-9_]+", a[1]) or a[1] in ("kotva", "vse"):
        sys.exit("CHYBA: id kandidáta jen písmena, číslice a _ (ne „kotva“ ani „vse“)")
    d["kandidati"].setdefault(a[1], {"stav": "otevreny", "duvod": ""})["popis"] = a[2]
    uloz(a[0], d)
    print(f"kandidát {a[1]}: {a[2]}")


def cmd_stav(a):
    if len(a) < 4 or a[2] not in STAVY:
        sys.exit("použití: rodiny.py stav <případ> <id> otevreny|vyloucen|potvrzen \"důvod\"")
    d = nacti(a[0])
    if a[1] not in d["kandidati"]:
        sys.exit(f"CHYBA: kandidát {a[1]} v případu není ({', '.join(d['kandidati'])})")
    d["kandidati"][a[1]].update(stav=a[2], duvod=a[3])
    if a[2] == "potvrzen":
        jini = [k for k, v in d["kandidati"].items() if k != a[1] and v["stav"] == "potvrzen"]
        if jini:
            print(f"POZOR: potvrzený je i {', '.join(jini)} – potvrzený má být jen jeden")
    uloz(a[0], d)
    print(f"{a[1]}: {a[2]} – {a[3]}")
    if a[2] == "potvrzen":
        print("Teď zapiš do data/osoby.py (st=\"doc\" jen když vazbu říká zápis přímo, jinak \"prob\" s poznámkou proč) "
              "a do deníku. Kandidáti, kteří zůstali otevření, ať mají v deníku důvod, proč odpadli.")


def cmd_zapis(a):
    if len(a) < 2:
        sys.exit("použití: rodiny.py zapis <případ> <soubor.json>")
    d = nacti(a[0])
    with open(a[1], encoding="utf-8") as f:
        vstup = json.load(f)
    for z in vstup if isinstance(vstup, list) else [vstup]:
        patri = z.get("patri", "?")
        if patri not in ("kotva", "?") and patri not in d["kandidati"]:
            sys.exit(f"CHYBA: \"patri\": \"{patri}\" – kandidát neexistuje (založ ho příkazem kandidat)")
        if not z.get("osoby"):
            sys.exit("CHYBA: zápis bez \"osoby\" – vypiš všechny lidi ze zápisu i s rolí (kmotři a svědci jsou to nejcennější)")
        for o in z["osoby"]:
            if o.get("role") not in ROLE:
                print(f"upozornění: role „{o.get('role')}“ u {o.get('jmeno')} není v seznamu ({', '.join(sorted(ROLE))})")
        dupl = [x["id"] for x in d["zapisy"] if x.get("zdroj") and x.get("zdroj") == z.get("zdroj")
                and x.get("datum") == z.get("datum")]
        if dupl:
            print(f"upozornění: stejný zdroj a datum už má {', '.join(dupl)} – nezapisuješ ho podruhé?")
        z["id"] = nove_id(d["zapisy"], "z")
        z["patri"] = patri
        d["zapisy"].append(z)
        print(f"zapsáno {popis_zapisu(z)} → {patri}, {len(z['osoby'])} osob")
    uloz(a[0], d)


def cmd_ukol(a):
    if len(a) < 4:
        sys.exit("použití: rodiny.py ukol <případ> <kandidát|vse> <vrstva> \"co hledat\" [\"kde\"]")
    d = nacti(a[0])
    if a[1] != "vse" and a[1] not in d["kandidati"]:
        sys.exit(f"CHYBA: kandidát {a[1]} v případu není")
    u = {"id": nove_id(d["ukoly"], "u"), "kandidat": a[1], "vrstva": int(a[2]), "co": a[3],
         "kde": a[4] if len(a) > 4 else "", "stav": "ceka", "vysledek": ""}
    d["ukoly"].append(u)
    uloz(a[0], d)
    print(f"úkol {u['id']} (vrstva {u['vrstva']}, {u['kandidat']}): {u['co']}")


def cmd_hotovo(a):
    if len(a) < 3:
        sys.exit("použití: rodiny.py hotovo <případ> <úkol> \"výsledek\" [--nic]")
    d = nacti(a[0])
    for u in d["ukoly"]:
        if u["id"] == a[1]:
            u.update(stav="nic" if "--nic" in a else "hotovo", vysledek=a[2])
            uloz(a[0], d)
            print(f"{u['id']}: {u['stav']} – {a[2]}")
            return
    sys.exit(f"CHYBA: úkol {a[1]} v případu není")


def otevreni(d):
    return [k for k, v in d["kandidati"].items() if v["stav"] == "otevreny"]


def cmd_prehled(a):
    d = nacti(a[0])
    print(f"PŘÍPAD {d['pripad']}: {d['cil']}" + (f" (předek č. {d['osoba']})" if d.get("osoba") else ""))
    kotvy = [z for z in d["zapisy"] if z["patri"] == "kotva"]
    print(f"\nKotvy (doloženo o předkovi): {len(kotvy)}")
    for z in kotvy:
        print(f"  {popis_zapisu(z)}" + (f" – {z['pozn']}" if z.get("pozn") else ""))
    print("\nKandidáti:")
    for k, v in d["kandidati"].items():
        zz = [z for z in d["zapisy"] if z["patri"] == k]
        print(f"  [{v['stav']}] {k}: {v.get('popis', '')}" + (f" – {v['duvod']}" if v.get("duvod") else ""))
        for z in zz:
            print(f"      {popis_zapisu(z)}" + (f" – {z['pozn']}" if z.get("pozn") else ""))
    nez = [z for z in d["zapisy"] if z["patri"] == "?"]
    if nez:
        print(f"\nZápisy bez přiřazení (?): {len(nez)}")
        for z in nez:
            print(f"  {popis_zapisu(z)}" + (f" – {z['pozn']}" if z.get("pozn") else ""))
    ot = otevreni(d)
    potvrzeny = [k for k, v in d["kandidati"].items() if v["stav"] == "potvrzen"]
    if potvrzeny:
        print(f"\nROZHODNUTO: {', '.join(potvrzeny)}. Zbývající úkoly jen pro rekonstrukci rodiny.")
    cekaji = [u for u in d["ukoly"] if u["stav"] == "ceka" and (u["kandidat"] == "vse" or u["kandidat"] in ot or potvrzeny)]
    if cekaji:
        v = min(u["vrstva"] for u in cekaji)
        print(f"\nNA ŘADĚ – vrstva {v} (do šířky: dokonči vrstvu u všech otevřených kandidátů, než půjdeš hlouběji):")
        for u in cekaji:
            if u["vrstva"] == v:
                print(f"  {u['id']} [{u['kandidat']}] {u['co']}" + (f" – {u['kde']}" if u["kde"] else ""))
        dalsi = sorted({u["vrstva"] for u in cekaji if u["vrstva"] > v})
        if dalsi:
            print(f"  (čekají i vrstvy {', '.join(map(str, dalsi))})")
    elif len(ot) > 1:
        hl = max([u["vrstva"] for u in d["ukoly"]] + [0])
        print(f"\nVrstva {hl} je hotová a kandidáti {', '.join(ot)} jsou pořád otevření. Spusť `prunik`; když nerozhodne, "
              f"přidej úkoly vrstvy {hl + 1}: děti a jejich kmotři, svědci na svatbě, sourozenci, úmrtí s věkem, "
              f"rodina nevěsty – u každého kandidáta stejné druhy zápisů, ať je srovnání férové.")
    elif len(ot) == 1 and not potvrzeny:
        print(f"\nZbývá jediný otevřený kandidát ({ot[0]}). Než ho potvrdíš: má aspoň jednu přímou shodu s kotvou "
              f"(`prunik`)? Vyloučení ostatních samo nestačí, mohl být ještě někdo, koho jsme nenašli.")
    hot = [u for u in d["ukoly"] if u["stav"] != "ceka"]
    if hot:
        print(f"\nHotové úkoly: {len(hot)}")
        for u in hot:
            print(f"  {u['id']} v{u['vrstva']} [{u['kandidat']}] {u['co']} → {u['stav']}: {u['vysledek']}")


def osoby_zapisu(z):
    for o in z.get("osoby", []):
        kl = osoba_klic(o.get("jmeno", ""))
        if kl:
            yield kl, o, dum_klic(o.get("obec") or z.get("obec"), o.get("dum") or (z.get("dum") if o.get("role") in (
                "otec", "matka", "dite", "zemrely", "zenich") else ""))


def cmd_prunik(a):
    d = nacti(a[0])
    rod = predci()
    kotvy_o, kotvy_d = defaultdict(list), defaultdict(list)
    for z in d["zapisy"]:
        if z["patri"] == "kotva":
            for kl, o, dk in osoby_zapisu(z):
                if kl[1]:
                    kotvy_o[kl].append(f"{o.get('role')} v {z['id']}")
                if dk:
                    kotvy_d[dk].append(f"{o.get('jmeno')} ({o.get('role')}) v {z['id']}")
    print(f"PRŮNIK – případ {d['pripad']}. Shody jsou podle volného porovnání jmen: každou ověř v zápisu.\n")
    nalezy = {}   # kandidát -> {(typ, klíč): [řádky]}
    for k, v in d["kandidati"].items():
        nalezy[k] = defaultdict(list)
        for z in (z for z in d["zapisy"] if z["patri"] == k):
            r = rok(z.get("datum", ""))
            for kl, o, dk in osoby_zapisu(z):
                kdo = f"{o.get('jmeno')} ({o.get('role')} v {z['id']}, {z.get('datum', '')})"
                if kl[1] and kl in kotvy_o:
                    nalezy[k][("osoba", kl)].append(f"OSOBA    {kdo} ~ kotvy: {'; '.join(kotvy_o[kl])}")
                sr = soucasnici(rod, kl, r) if kl[1] else []
                if sr:
                    nalezy[k][("rod", kl)].append(f"RODOKMEN {kdo} ~ {'; '.join(sr[:3])}")
                if dk and dk in kotvy_d:
                    nalezy[k][("dum", dk)].append(f"DŮM      č. {dk[1]}: {kdo} ~ kotvy: {'; '.join(kotvy_d[dk])}")
    ot = otevreni(d)
    spolecne = set.intersection(*(set(nalezy[k]) for k in ot)) if len(ot) > 1 else set()
    for k, v in d["kandidati"].items():
        n = sum(1 for z in d["zapisy"] if z["patri"] == k)
        print(f"[{v['stav']}] {k}: {v.get('popis', '')}  ({n} zápisů)")
        vlastni = [kl for kl in nalezy[k] if kl not in spolecne]
        for kl in vlastni:
            for radek in nalezy[k][kl]:
                print("   " + radek)
        if not vlastni:
            print("   žádná vlastní shoda" + (" – zatím žádné zápisy" if not n else ""))
    if spolecne:
        print("\nNEROZLIŠUJE (shoda u všech otevřených kandidátů – obvykle kandidát sám nebo celá ves): " +
              ", ".join(f"{t} {' '.join(x for x in kl if x)}" for t, kl in sorted(spolecne)))
    if len(ot) > 1:
        print("\nVlastní shody: " + ", ".join(f"{k} {len([x for x in nalezy[k] if x not in spolecne])}" for k in ot))
        print("Rozhoduje doklad, ne počet: shoda domu nebo kmotra je stopa, přímá věta „syn X“ je důkaz.")


def cmd_rodiny(a):
    d = nacti(a[0])
    pary = defaultdict(list)
    for z in d["zapisy"]:
        if z.get("druh") != "N":
            continue
        role = defaultdict(list)
        for o in z.get("osoby", []):
            role[o.get("role")].append(o)
        if not role.get("dite"):
            continue
        ot = role["otec"][0]["jmeno"] if role.get("otec") else "otec neuveden"
        ma = role["matka"][0]["jmeno"] if role.get("matka") else "?"
        klic = (osoba_klic(ot) or ("", ""), krestni_klic(ma), z["patri"])
        pary[klic].append((z, role, ot, ma))
    if not pary:
        print("Žádné křty (druh N s rolí dite) – zapiš křty sourozenců příkazem zapis.")
        return
    kmotri_paru = {}
    for klic, deti in sorted(pary.items(), key=lambda x: rok(x[1][0][0].get("datum", ""))):
        deti.sort(key=lambda x: den(x[0].get("datum", "")) or (rok(x[0].get("datum", "")), 0, 0))
        z0, _, ot, ma = deti[0]
        print(f"\n{ot} × {ma}: {len(deti)} dětí  (patří: {', '.join(sorted({x[0]['patri'] for x in deti}))})")
        jmena, predchozi, km, posledni_den = {}, None, defaultdict(int), None
        for z, role, _, _ in deti:
            r = rok(z.get("datum", ""))
            dite = role["dite"][0]["jmeno"]
            kk = [o["jmeno"] for x in ("kmotr", "kmotra") for o in role.get(x, [])]
            # stálí kmotři: v 18. století se tíž lidé střídají v roli kmotra a svědka – počítej obě
            for o in kk + [o["jmeno"] for o in role.get("svedek", [])]:
                km[osoba_klic(o)] += 1
            pozn = []
            kj = krestni_klic(dite)
            if kj in jmena:
                pozn.append(f"jméno už má dítě z {jmena[kj]} – to nejspíš zemřelo")
            jmena[kj] = z.get("datum", "")
            dd = den(z.get("datum", ""))
            if dd and posledni_den:
                dni = dny(dd) - dny(posledni_den)
                if 2 < dni < 270:
                    pozn.append(f"jen {dni // 30} měs. po předchozím dítěti – jedna matka nestihne: dva stejnojmenné "
                                "páry, nebo špatně čtené datum (měsíc/rok bývá v nadpisu sloupce)")
                elif 0 <= dni <= 2:
                    pozn.append("stejný den jako předchozí dítě – dvojčata?")
            posledni_den = dd or posledni_den
            if predchozi and r and predchozi and r - predchozi >= 4:
                pozn.append(f"mezera {r - predchozi} let – chybí dítě, nebo je zapsané jinde")
            predchozi = r or predchozi
            print(f"  {z.get('datum', ''):<14} {dite:<22} č. {z.get('dum') or '–':<5} kmotři: {', '.join(kk) or '–'}"
                  f"  [{z['id']}]" + (f"  ← {'; '.join(pozn)}" if pozn else ""))
        stali = [k for k, n in km.items() if n >= 2 and k]
        kmotri_paru[klic] = set(km)
        if stali:
            print(f"  stálí kmotři: {', '.join(' '.join(x for x in k if x) for k in stali)}")
    # kmotři společní dvěma párům – obě rodiny se znaly / jsou příbuzné
    kl = list(kmotri_paru)
    for i in range(len(kl)):
        for j in range(i + 1, len(kl)):
            sp = {k for k in kmotri_paru[kl[i]] & kmotri_paru[kl[j]] if k and k[1]}
            if sp:
                print(f"\nSpolečný kmotr párů {pary[kl[i]][0][2]} × {pary[kl[i]][0][3]} a {pary[kl[j]][0][2]} × "
                      f"{pary[kl[j]][0][3]}: {', '.join(' '.join(k) for k in sp)}")
    stejna = defaultdict(list)
    for kl in pary:
        stejna[kl[:2]].append(kl[2])
    for kl, kam in stejna.items():
        if len(kam) > 1:
            print(f"\nPár {pary[(*kl, kam[0])][0][2]} × {pary[(*kl, kam[0])][0][3]} má děti u: {', '.join(kam)}. "
                  "Jestli jde o jeden pár, nebo víc stejnojmenných, rozhodni podle domu a kmotrů výše.")
    if any(kl[2] == "?" for kl in pary):
        print("\nDěti s \"patri\": \"?\" přiřaď ke kandidátovi, jakmile je rozhodneš (opravíš v souboru případu).")


def den(datum):
    """„18. 1. 1764“ → (1764, 1, 18); neúplné datum → None."""
    m = re.search(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})", datum or "")
    return (int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else None


def dny(d):
    """Přibližný počet dní od začátku letopočtu – stačí na rozdíl porodů."""
    return int(d[0] * 365 + d[0] // 4 + (d[1] - 1) * 30.44 + d[2])


def rok(datum):
    m = re.search(r"\d{4}", datum or "")
    return int(m.group()) if m else 0


def cmd_seznam(a):
    if not os.path.isdir(SLOZKA):
        print("Žádné případy (data/rodiny/ neexistuje).")
        return
    for f in sorted(os.listdir(SLOZKA)):
        if f.endswith(".json"):
            try:
                d = json.load(open(os.path.join(SLOZKA, f), encoding="utf-8"))
                ot = otevreni(d)
                ck = sum(1 for u in d.get("ukoly", []) if u["stav"] == "ceka")
                print(f"{d['pripad']}: {d['cil']} – kandidátů {len(d['kandidati'])} (otevřených {len(ot)}), "
                      f"zápisů {len(d['zapisy'])}, čeká úkolů {ck}")
            except (ValueError, KeyError):
                pass   # jiný soubor ve složce (pracovní poznámky), ne případ


PRIKAZY = {"novy": cmd_novy, "kandidat": cmd_kandidat, "stav": cmd_stav, "zapis": cmd_zapis, "ukol": cmd_ukol,
           "hotovo": cmd_hotovo, "prehled": cmd_prehled, "prunik": cmd_prunik, "rodiny": cmd_rodiny, "seznam": cmd_seznam}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in PRIKAZY:
        print(__doc__)
        sys.exit(0 if len(sys.argv) < 2 else 2)
    PRIKAZY[sys.argv[1]](sys.argv[2:])
