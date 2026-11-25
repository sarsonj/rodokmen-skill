"""Testy drobných oprav: roky ve vějíři a na webu (years), brzda po čekání na slot (slusne.pockej),
CITLIVÉ v hypotézách a deníku a ISSUES bez stavu (kontrola.py).

Z kořene repozitáře:
  python3 -I tests/drobne/test_drobne.py
  (Windows: python -I -X utf8 tests/drobne/test_drobne.py)
Nic nestahuje: brzda jen rezervuje sloty v dočasném stavu, kontrola běží v dočasném projektu.
"""
import importlib.util, os, shutil, subprocess, sys, tempfile, threading, time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "skills", "rodokmen", "tools")
os.environ["SLUSNE_STAV"] = tempfile.mkdtemp(prefix="drobne_slusne_")
vysledky = []


def nacti(jmeno, slozka=TOOLS):
    spec = importlib.util.spec_from_file_location(jmeno, os.path.join(slozka, jmeno + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def ok(nazev, podminka, detail=""):
    vysledky.append(bool(podminka))
    print(("OK   " if podminka else "CHYBA"), nazev, "" if podminka else detail)


# 1) roky: horní odhad úmrtí se neztratí, nejisté úmrtí má otazník – web i vějíř stejně
vejir = tempfile.mkdtemp(prefix="drobne_vejir_")   # fan_chart.py při importu čte data/osoby.py
os.makedirs(os.path.join(vejir, "data"))
os.makedirs(os.path.join(vejir, "tools"))
with open(os.path.join(vejir, "data", "osoby.py"), "w", encoding="utf-8") as f:
    f.write("P = {1: dict(n='Petr Novák', y='1990')}\n")
shutil.copy(os.path.join(TOOLS, "fan_chart.py"), os.path.join(vejir, "tools"))
for modul, slozka in (("export_web", TOOLS), ("fan_chart", os.path.join(vejir, "tools"))):
    years = nacti(modul, slozka).years
    for y, cekam in (("1889 – před 1936", "1889–před 1936"), ("1849 – 1901 (?)", "1849–1901?"),
                     ("1820 – po 1852", "1820–po 1852"), ("asi 1795 – asi 1850", "≈1795–≈1850"), ("1820 – 1890", "1820–1890")):
        ok(f"{modul}.years({y!r})", years(y) == cekam, f"vyšlo {years(y)!r}, čekal jsem {cekam!r}")

# 2) brzda: dotaz čeká na slot, mezitím jiné vlákno web zastaví → dotaz neodejde
sl = nacti("slusne")
host = "digi.archives.cz"   # limit 4 s mezi dotazy
sl.pockej(host, obrazek=False)   # první dotaz projde hned, další čeká ~4 s
vysledek = []


def druhy():
    try:
        sl.pockej(host, obrazek=False)
        vysledek.append("odešel")
    except sl.Zastaveno:
        vysledek.append("zastaven")


t = threading.Thread(target=druhy)
t.start()
time.sleep(0.5)
try:
    sl.zastav(host, "test: 429 během čekání")
except sl.Zastaveno:
    pass
t.join(10)
ok("brzda: zastavení během čekání na slot", vysledek == ["zastaven"], f"druhý dotaz: {vysledek}")

# 3) kontrola: citlivé slovo v hypotéze a v deníku, ISSUES bez stavu
d = tempfile.mkdtemp(prefix="drobne_kontrola_")
try:
    os.makedirs(os.path.join(d, "data"))
    os.makedirs(os.path.join(d, "tools"))
    for n in ("kontrola.py", "export_web.py"):
        shutil.copy(os.path.join(TOOLS, n), os.path.join(d, "tools"))
    P = {1: dict(n="Petr Novák", st="doc", f=["* 1990"])}
    with open(os.path.join(d, "data", "osoby.py"), "w", encoding="utf-8") as f:
        f.write(f"P = {P!r}\n"
                "ISSUES = [('Kde se narodil Jan?', 'Hledáme křest v Hořicích.'), ('Otec Anny', 'Otevřené: nevíme.')]\n"
                "HYPOTEZY = [dict(nadpis='Rozvod 1975', text='Anna se v roce 1975 rozvedla a odstěhovala.')]\n")
    with open(os.path.join(d, "data", "research_log.md"), "w", encoding="utf-8") as f:
        f.write("| # | datum | zdroj | rozsah | hledáno | výsledek | citace |\n|---|---|---|---|---|---|---|\n"
                "| 1 | 2026-01-01 | Matrika N 1780–1800 | sn. 5 | křest 1789 | nemanželské dítě 1789, matka Anna | – |\n"
                "| 2 | 2026-01-02 | Matrika O 1780–1800 a obecní kronika | – | sňatek 1789 | v kronice: rozvod 1975 u vnuka | – |\n")
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(d, "tools", "kontrola.py")],
                       capture_output=True, text=True, encoding="utf-8")
    out = r.stdout + r.stderr
    ok("kontrola: CITLIVÉ v hypotéze", "CITLIVÉ (hypotéza Rozvod 1975)" in out, out)
    ok("kontrola: CITLIVÉ v deníku u nedávného roku", "CITLIVÉ (deník ř. 2)" in out, out)
    ok("kontrola: deník – starý zápis citlivý není", "CITLIVÉ (deník ř. 1)" not in out, out)
    ok("kontrola: ISSUES bez stavu", "ISSUES: „Kde se narodil Jan?“" in out and "„Otec Anny“" not in out, out)
finally:
    shutil.rmtree(d, ignore_errors=True)

print(f"\n{sum(vysledky)}/{len(vysledky)} v pořádku")
sys.exit(0 if all(vysledky) else 1)
