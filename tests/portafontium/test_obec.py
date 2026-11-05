"""Test příkazu portafontium.py obec (knihy podle obce) – offline na uložených stránkách výsledků portálu.

Z kořene repozitáře:
  python3 -I tests/portafontium/test_obec.py skills/rodokmen/tools
Na archiv nechodí: get() se nahradí uloženými výřezy stránek (hledani_*.html, stav 5. 11. 2026).
"""
import contextlib, io, os, sys

TOOLS = os.path.abspath(sys.argv[1])
TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import portafontium as pf  # noqa: E402

vysledky = []


def check(nazev, ok, detail=""):
    vysledky.append(bool(ok))
    print(f"[{'OK ' if ok else 'CHYBA'}] {nazev}{'' if ok else '  ' + str(detail)[:600]}", flush=True)


def stranka(n):
    return open(os.path.join(TU, n), encoding="utf-8").read()


ADRESY = []


def fake_get(url, binary=False):
    ADRESY.append(url)
    if "Bu%C4%8D%C3%AD" in url:
        return stranka("hledani_buci.html")
    if "Kdyn%C4%9B" in url:
        # 1. stránka má odkaz na další, 2. stránka (page=1) už ne – stačí jiná uložená stránka bez odkazu
        return stranka("hledani_buci.html") if "page=1" in url else stranka("hledani_kdyne_0.html")
    return "<table></table>"


pf.get = fake_get

# Bučí: knihy dvou far – Dolní Bělá (do 1787) a Krašovice (od 1787)
knihy = pf.obec("Bučí")
check("adresa hledání má zakódovaný český název", any("search_api_views_fulltext_1=Bu%C4%8D%C3%AD" in u for u in ADRESY), ADRESY)
slugy = [k for k, _ in knihy]
check("najde 28 knih", len(knihy) == 28, len(knihy))
check("najde knihy fary Krašovice", "krasovice-01" in slugy, slugy)
check("najde starší knihy fary Dolní Bělá", any(s.startswith("dolni-bela-") for s in slugy), slugy)

out = io.StringIO()
with contextlib.redirect_stdout(out):
    pf.vypis_obec(knihy)
t = out.getvalue()
check("výpis seskupený podle fary – nadpis Krašovice s adresou fary", "Krašovice (fara krasovice)" in t, t[:800])
check("výpis seskupený podle fary – nadpis Dolní Bělá", "Dolní Bělá (fara dolni-bela)" in t, t[:800])
radek = next((r for r in t.splitlines() if r.strip().startswith("krasovice-01 ")), "")
check("řádek knihy: kniha | obce | roky a druhy", "Bučí" in radek and "1787-1828 *" in radek, radek)
check("archiv se v řádku neopakuje", "státní archiv" not in radek, radek)
kr = [r.split()[0] for r in t.split("Krašovice (fara krasovice)")[1].split("\n\n")[0].splitlines()[1:] if r.strip()]
check("knihy fary seřazené podle začátku let", kr.index("krasovice-01") < kr.index("krasovice-15"), kr)
check("upozornění na podobné a stejnojmenné obce", "stejnojmenné" in t, t[-400:])

# stránkování po 40: projde i další stránku
ADRESY.clear()
knihy = pf.obec("Kdyně")
check("stránkování: načte i page=1", any("page=1" in u for u in ADRESY), ADRESY)
check("stránkování: knihy z obou stránek", len(knihy) > 40, len(knihy))

# nic nenalezeno
check("obec bez výsledku vrátí prázdný seznam", pf.obec("Neexistujicí") == [])

print(f"\n{sum(vysledky)} z {len(vysledky)} správně")
sys.exit(0 if all(vysledky) else 1)
