#!/usr/bin/env python3
"""Navrhne (a na požádání zapíše) větu „děti: Jan 1820, Marie 1822“ pro rodiče – ze sourozenců a dítěte v přímé linii,
které už jsou v data/osoby.py (`P` a `SIDE`, tj. z přečtených křtů). Stránka Statistiky (část „Děti v rodině“) čte
právě tento fakt; tvar viz reference/data.md.

Použití (z kořene projektu):
  deti.py <osoba>             Kekulého číslo (manžel i manželka), nebo část jména z `P`: ukáže děti páru a navržený fakt
  deti.py --vse               totéž pro všechny páry, které mají aspoň dvě děti s rokem a ještě fakt „děti“ nemají (ty s faktem přeskočí)
  deti.py <osoba> --zapsat    navržený fakt zapíše rodiči (otci; chybí-li, matce) přes `zapis.py fakt` – jen když tam
                              fakt „děti“ ještě není (existující ukáže; změň ho ručně jednou náhradou řetězce)
  deti.py --vse --zapsat      zapíše všechny navržené věty
Děti: dítě v přímé linii (číslo = číslo rodiče ÷ 2) a boční příbuzní z `SIDE` s `k` = toto číslo. Rok se bere ze závorky
za jménem v `SIDE` / z pole `y` osoby, jinak z data křtu v zápisu (`r`, druh N). Děti bez roku do věty nepřijdou (stránka
je nepočítá) a žijící děti (poznámka „Žijící“, nebo narozené před méně než 110 lety bez úmrtí) taky ne – jména a roky
žijících se nezveřejňují. Příklad:
  python3 -I tools/deti.py "Václav Novák"
"""
import importlib.util, json, os, re, subprocess, sys, unicodedata
from datetime import date
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
DETI = re.compile(r"^děti(\s|:|$)", re.I)
ROK = re.compile(r"\d{4}")


def zapis_modul():
    spec = importlib.util.spec_from_file_location("zapis", os.path.join(TOOLS, "zapis.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def bez_diakritiky(t):
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()


def zastupna(p):
    return p["n"].startswith(("otec neuveden", "matka neuvedena")) or p["n"] in ("", "?")


def kresni(n):
    """Křestní jméno z „Marie Nováková (1892–1970)“ → Marie (u šlechty a dvojích jmen první slovo)."""
    return re.sub(r"\([^)]*\)", "", n).split()[0] if re.sub(r"\([^)]*\)", "", n).split() else ""


def pocet_let(y):
    """(rok narození, žije/mohl žít) z textu v závorce nebo z pole y: „1892–1970“, „* 1990“, „asi 1720“, „† 1830“."""
    y = (y or "").strip()
    rok = None if y.startswith("†") else (ROK.search(y).group() if ROK.search(y) else None)
    umrti = "–" in y or "†" in y or "-" in y
    zije = rok is not None and not umrti and int(rok) > date.today().year - 110
    return (int(rok) if rok else None), zije


def main():
    zapsat, vse = "--zapsat" in sys.argv, "--vse" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if bool(args) == vse or len(args) > 1:
        sys.exit(__doc__)
    zapis = zapis_modul()
    try:
        ns = zapis.nacti_osoby(open(os.path.join(ROOT, "data", "osoby.py"), "rb").read())
        zaz = {z.get("klic"): z for z in json.load(open(os.path.join(ROOT, "data", "zaznamy.json"), encoding="utf-8-sig"))}
    except (OSError, ValueError) as e:
        sys.exit(f"Data nejdou načíst ({e}) – oprav je nejdřív (git diff ukáže poslední změnu).")
    P, SIDE = ns.get("P", {}), ns.get("SIDE", [])

    def rok_krtu(klice):
        for kl in klice or []:
            z = zaz.get(kl) or {}
            if z.get("druh") == "N" and ROK.findall(str(z.get("datum", ""))):
                return int(ROK.findall(z["datum"])[-1])
        return None

    def deti_paru(c):
        """[(jméno, rok, zdroj)], [(jméno, důvod)] pro děti rodičů 2c a 2c+1."""
        ok, vynech = [], []
        kandidati = []
        if c in P and not zastupna(P[c]):
            kandidati.append((P[c]["n"], P[c].get("y"), P[c].get("r"), f"osoba {c}", (P[c].get("note") or "").startswith("Žijící")))
        for s in SIDE:
            if s.get("k") == c:
                zavorka = re.search(r"\(([^)]*)\)", s.get("n", ""))
                kandidati.append((s["n"], zavorka.group(1) if zavorka else "", s.get("r"), "SIDE", (s.get("t") or "").startswith("Žijící")))
        for n, y, r, zdroj, zije_pozn in kandidati:
            rok, zije = pocet_let(y)
            if zije_pozn or zije:
                vynech.append((kresni(n), "žijící – neuvádí se"))
                continue
            if rok is None:
                rok = rok_krtu(r)
            if rok is None or not kresni(n):
                vynech.append((kresni(n) or n, "bez roku narození"))
                continue
            ok.append((kresni(n), rok, zdroj))
        return sorted(ok, key=lambda x: x[1]), vynech

    def cil(otec):
        """Komu fakt patří: otci (sudé číslo), chybí-li v P nebo je zástupný, matce."""
        for k in (otec, otec + 1):
            if k in P and not zastupna(P[k]):
                return k
        return None

    navrhy = []   # (číslo otce, děti, vynechané)
    if vse:
        cisla = sorted({c for c in P if c >= 1} | {s.get("k") for s in SIDE if isinstance(s.get("k"), int)})
        for c in cisla:   # c = dítě páru (2c, 2c+1); pár musí být v P
            if 2 * c in P or 2 * c + 1 in P:
                d, v = deti_paru(c)
                if len(d) >= 2:
                    navrhy.append((2 * c, d, v))
    else:
        h = args[0]
        if re.fullmatch(r"\d+", h):
            k = int(h)
        else:
            kand = sorted(kk for kk, p in P.items() if bez_diakritiky(h) in bez_diakritiky(p["n"]) and not zastupna(p))
            if len(kand) != 1:
                sys.exit(f"Osoba „{h}“ " + ("v P není." if not kand else "je víc: " + "; ".join(f"{kk} {P[kk]['n']}" for kk in kand)
                                              + " – napiš číslo, nebo delší část jména."))
            k = kand[0]
        if k not in P:
            sys.exit(f"Osoba {k} v P (data/osoby.py) není.")
        otec = k - k % 2
        d, v = deti_paru(otec // 2)
        navrhy.append((otec, d, v))

    zapsano = ukazano = 0
    for otec, d, v in navrhy:
        k = cil(otec)
        stary = [f for f in P[k].get("f", []) if DETI.match(f.strip())] if k else []
        if vse and stary:
            continue
        ukazano += 1
        jm = " a ".join(P[x]["n"] for x in (otec, otec + 1) if x in P and not zastupna(P[x])) or f"pár {otec}/{otec + 1}"
        print(f"{jm} (děti páru {otec}/{otec + 1}):")
        for n, rok, zdroj in d:
            print(f"   {n} {rok}  ({zdroj})")
        for n, duvod in v:
            print(f"   – {n}: {duvod}")
        if not d:
            print("   žádné dítě s rokem – fakt nevznikne.")
            continue
        veta = "děti: " + ", ".join(f"{n} {rok}" for n, rok, _ in d)
        if len(d) == 1:
            print(f"   navržený fakt: {veta}  (jedno dítě – na stránce Statistiky se nepočítá, přidej až s dalším)")
        else:
            print(f"   navržený fakt pro osobu {k}: {veta}")
        if k is None:
            print("   rodiče nejsou v P – fakt nemá komu patřit.")
            continue
        if stary:
            print("   osoba už má: " + stary[0] + (" (stejné)" if stary[0] == veta else " – změň ji ručně (jednou náhradou řetězce v osoby.py)"))
            continue
        if zapsat and len(d) >= 2:
            r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(TOOLS, "zapis.py"), "fakt", str(k), veta],
                               cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
            print("   " + (r.stdout.strip() or r.stderr.strip()))
            zapsano += r.returncode == 0
    if zapsat:
        print(f"Zapsáno: {zapsano}. Dál: python3 -I tools/kontrola.py")
    elif ukazano:
        print("Zapsat: přidej --zapsat (nebo `python3 -I tools/zapis.py fakt <číslo> \"děti: …\"`).")
    elif vse:
        print("Žádný další pár nemá aspoň dvě děti s rokem narození.")


if __name__ == "__main__":
    main()
