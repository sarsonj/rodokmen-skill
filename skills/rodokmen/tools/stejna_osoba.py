#!/usr/bin/env python3
"""Zapíše, že jeden předek je v rodokmenu podruhé (jiné Kekulého číslo): přidá ho do `SAME` v data/osoby.py.
Stránka „Dvakrát ve stromě“, vějíř i strom pak ukážou tutéž osobu, ne dvě různé. Zbytek souboru zůstane doslova.

Použití (z kořene projektu):
  stejna_osoba.py <další-číslo> <první-číslo> [--vynutit]
    další-číslo   Kekulého číslo, pod kterým je předek ve stromě PODRUHÉ (alias), např. 350
    první-číslo   číslo, pod kterým je veden poprvé (hlavní osoba), např. 140
    --vynutit     přes varování o jménu, letech nebo rodičích (písař psal jméno jinak) – použij, jen když jsi to ověřil v zápisech
  stejna_osoba.py --seznam      vypíše dosavadní SAME s jmény

Ohlídá: obě osoby jsou v `P`, nejde o tutéž ani o předka/potomka jedné druhé, alias ještě není v `SAME` (a hlavní osoba
není sama aliasem), jména (i rodičů, jsou-li v `P`) a roky narození sedí, nad aliasem nejsou ve stromě vlastní předci
(větev nad aliasem se bere z hlavní osoby), `SAME` je v souboru právě jednou a po zápisu přibyl právě jeden záznam a
nic jiného se nezměnilo (P, SIDE, LINES, ISSUES, HYPOTEZY). Opakované volání se stejnou dvojicí nic nemění.
Alias musí v `P` být (jméno, `f=["TÁŽ OSOBA jako 140"]`, `st`) – přidej ho před spuštěním; potom: `tools/kontrola.py`.
Příklad:
  python3 -I tools/stejna_osoba.py 350 140
"""
import ast, importlib.util, os, re, sys, unicodedata
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
PATH = os.path.join(ROOT, "data", "osoby.py")


def zapis_modul():
    """zapis.py z téže složky (nacti_osoby, bajty_pozice); při `python -I` skriptová složka v sys.path není."""
    spec = importlib.util.spec_from_file_location("zapis", os.path.join(TOOLS, "zapis.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def kmeny(jmeno):
    """První 4 písmena slov bez diakritiky; text v závorce se nepočítá (stejně jako v kontrola.py)."""
    t = re.sub(r"\([^)]*\)", " ", jmeno or "")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return {w[:4] for w in re.findall(r"[a-z]+", t)}


def zastupna(p):
    return p["n"].startswith(("otec neuveden", "matka neuvedena")) or p["n"] in ("", "?")


def stejne_jmeno(a, b):
    ka, kb = kmeny(a), kmeny(b)
    return bool(ka and kb) and (ka <= kb or kb <= ka)


def rok_narozeni(p):
    y = (p.get("y") or "").strip()
    if y.startswith(("†",)):
        return None
    m = re.search(r"\d{4}", y)
    return int(m.group()) if m else None


def predci_v_P(k, P):
    """Čísla v P, která jsou předky k (k*2, k*2+1, …) a mají jméno."""
    out, fronta = [], [2 * k, 2 * k + 1]
    while fronta:
        q = fronta.pop()
        if q in P:
            if not zastupna(P[q]):
                out.append(q)
            fronta += [2 * q, 2 * q + 1]
    return sorted(out)


def je_predek(a, b):
    """True, když a je předek b (b se k a dostane půlením čísla)."""
    while b > 1:
        b //= 2
        if b == a:
            return True
    return False


def vlozit(src, same_uzel, a, c, pos):
    """Nový text souboru se záznamem a: c ve slovníku SAME (jen ta jedna změna, styl podle souboru)."""
    zaznam = f"{a}: {c}".encode()
    zacatek = pos(same_uzel.lineno, same_uzel.col_offset)
    konec = pos(same_uzel.end_lineno, same_uzel.end_col_offset)   # za „}“
    if not same_uzel.keys:
        if src[zacatek + 1:konec - 1].strip():
            sys.exit("SAME je prázdné, ale uvnitř jsou komentáře – přidej záznam ručně.")
        return src[:zacatek + 1] + zaznam + src[konec - 1:]
    posl = same_uzel.values[-1]
    konec_posl = pos(posl.end_lineno, posl.end_col_offset)
    carka = re.match(rb"[ \t]*,", src[konec_posl:])
    rozdel = src[konec_posl:konec - 1]
    if b"\n" not in rozdel:   # na jednom řádku: {350: 140} → {350: 140, 351: 141}
        return src[:konec_posl] + b", " + zaznam + src[konec_posl:]
    # na víc řádků: nový řádek se stejným odsazením pod poslední položkou (za čárkou a případným komentářem)
    radek_klice = pos(same_uzel.keys[-1].lineno, 0)
    odsazeni = re.match(rb"[ \t]*", src[radek_klice:]).group()
    nova_carka = b"" if carka else b","
    konec_radku = src.index(b"\n", konec_posl)
    return (src[:konec_posl] + nova_carka + src[konec_posl:konec_radku] + b"\n" + odsazeni + zaznam + b","
            + src[konec_radku:])


def main():
    zapis = zapis_modul()
    args = [x for x in sys.argv[1:] if x not in ("--vynutit", "--seznam")]
    vynutit, seznam = "--vynutit" in sys.argv, "--seznam" in sys.argv
    src = open(PATH, "rb").read() if os.path.exists(PATH) else sys.exit("data/osoby.py v projektu není.")
    try:
        strom = ast.parse(src)
        pred = zapis.nacti_osoby(src)
    except Exception as e:
        sys.exit(f"data/osoby.py nejde načíst ({e}) – oprav ho nejdřív (git diff ukáže poslední změnu).")
    P, SAME = pred.get("P", {}), pred.get("SAME", {})
    if seznam:
        for a, c in sorted(SAME.items()):
            print(f"{a} ({P.get(a, {}).get('n', '?')}) = {c} ({P.get(c, {}).get('n', '?')})")
        return print(f"SAME: {len(SAME)} záznamů") if SAME else print("SAME je prázdné.")
    if len(args) != 2 or not all(re.fullmatch(r"\d+", x) for x in args):
        sys.exit(__doc__)
    a, c = int(args[0]), int(args[1])

    # --- kontroly (chyby se nedají obejít, varování jde přes --vynutit) ---
    if a == c:
        sys.exit("Obě čísla jsou stejná.")
    for k, role in ((a, "další číslo"), (c, "první číslo")):
        if k not in P:
            sys.exit(f"Osoba {k} ({role}) v P (data/osoby.py) není." + (
                " Nejdřív ji tam přidej (jméno, roky, f=[\"TÁŽ OSOBA jako %d\"], st) a spusť nástroj znovu." % c if k == a else ""))
        if zastupna(P[k]):
            sys.exit(f"Osoba {k} je zástupná (bez jména) – SAME musí ukazovat na skutečné osoby.")
    if SAME.get(a) == c:
        return print(f"SAME už {a} -> {c} obsahuje, nic neměním.")
    if a in SAME:
        sys.exit(f"Osoba {a} už je v SAME jako alias osoby {SAME[a]} – nejdřív ověř, kterému číslu patří (ruční úprava).")
    if c in SAME:
        sys.exit(f"Osoba {c} je sama alias osoby {SAME[c]} – použij jako první číslo {SAME[c]} (alias aliasu nejde).")
    if a in SAME.values():
        sys.exit(f"Osoba {a} je už hlavní osobou pro {', '.join(str(x) for x, y in SAME.items() if y == a)} – "
                 f"zapiš místo toho tyto aliasy na {c} (nebo obráceně: jako další číslo dej {c} a jako první {a}).")
    if je_predek(a, c) or je_predek(c, a):
        sys.exit(f"Osoba {a} a {c} jsou ve stromě předek a potomek – nemůže jít o tutéž osobu (číslo předka je v rodokmenu špatně).")

    varovani = []
    if not stejne_jmeno(P[a]["n"], P[c]["n"]):
        varovani.append(f"jména nesedí: {a} „{P[a]['n']}“, {c} „{P[c]['n']}“")
    ra, rc = rok_narozeni(P[a]), rok_narozeni(P[c])
    if ra and rc and abs(ra - rc) > 3:
        varovani.append(f"roky narození se liší: {a} {ra}, {c} {rc}")
    if a % 2 != c % 2 and (a > 1 and c > 1):
        varovani.append(f"pohlaví nesedí: {a} je {'žena' if a % 2 else 'muž'}, {c} je {'žena' if c % 2 else 'muž'} (muži sudá čísla, ženy lichá)")
    for pa, pc in ((2 * a, 2 * c), (2 * a + 1, 2 * c + 1)):   # rodiče, jsou-li u obou známi
        if pa in P and pc in P and not zastupna(P[pa]) and not zastupna(P[pc]) and not stejne_jmeno(P[pa]["n"], P[pc]["n"]):
            varovani.append(f"rodiče nesedí: {pa} „{P[pa]['n']}“, {pc} „{P[pc]['n']}“")
    if varovani and not vynutit:
        sys.exit("Nezapsáno – " + "; ".join(varovani) + ".\nJe-li to přesto tatáž osoba (ověřeno v zápisech), spusť znovu s --vynutit.")
    predci = predci_v_P(a, P)
    if predci:
        jmena = ", ".join("%d %s" % (q, P[q]["n"]) for q in predci[:5]) + (" …" if len(predci) > 5 else "")
        sys.exit(f"Nad osobou {a} jsou ve stromě vlastní předci ({jmena}). U aliasu se předci berou z osoby {c} – porovnej je s jejími předky a duplicity "
                 f"z P smaž (ručně), pak nástroj spusť znovu. Nejsou-li to tytéž osoby, nejde o jednu osobu.")

    # --- zápis ---
    nalezy = [u for u in strom.body if isinstance(u, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SAME" for t in u.targets)]
    pos = zapis.bajty_pozice(src)
    if len(nalezy) > 1:
        sys.exit(f"SAME je v data/osoby.py přiřazeno {len(nalezy)}× – nechej jediné a spusť znovu.")
    if not nalezy:   # starší projekt bez SAME: připoj na konec souboru
        novy = src.rstrip(b"\n") + f"\n\n# Předek v rodokmenu vícekrát: {{alias: hlavní číslo}}\nSAME = {{{a}: {c}}}\n".encode()
    elif not isinstance(nalezy[0].value, ast.Dict) or any(not isinstance(k, ast.Constant) for k in nalezy[0].value.keys):
        sys.exit("SAME není prostý slovník { číslo: číslo } – uprav ručně.")
    else:
        novy = vlozit(src, nalezy[0].value, a, c, pos)

    try:   # pojistka: soubor jde načíst, SAME přibylo přesně o jeden záznam, nic jiného se nezměnilo
        po = zapis.nacti_osoby(novy)
    except Exception as e:
        sys.exit(f"Úprava by rozbila data/osoby.py ({e}) – nic jsem nezapsal, uprav ručně.")
    if po.get("SAME") != {**SAME, a: c}:
        sys.exit("Úprava by změnila SAME jinak, než má – nic jsem nezapsal, uprav ručně.")
    for jmeno in ("P", "SIDE", "LINES", "ISSUES", "HYPOTEZY"):
        if po.get(jmeno) != pred.get(jmeno):
            sys.exit(f"Úprava by změnila i {jmeno} – nic jsem nezapsal, uprav ručně.")
    tmp = PATH + ".tmp"
    with open(tmp, "wb") as f:
        f.write(novy)
    os.replace(tmp, PATH)
    pocet = 1 + sum(1 for x, y in po["SAME"].items() if y == c)
    print(f"data/osoby.py: SAME {a} -> {c} ({P[a]['n']} = {P[c]['n']}); osoba {c} je teď ve stromě {pocet}×.")
    if not any("TÁŽ OSOBA" in f for f in P[a].get("f", [])):
        print(f"Tip: osobě {a} dej do `f` řádek „TÁŽ OSOBA jako {c}“ (vidí ho kontrola i čtenář dat). Pak: python3 -I tools/kontrola.py")
    else:
        print("Dál: python3 -I tools/kontrola.py")


if __name__ == "__main__":
    main()
