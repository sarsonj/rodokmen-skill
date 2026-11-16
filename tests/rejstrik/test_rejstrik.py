"""Testy rejstříku projektu (skills/rodokmen/tools/rejstrik.py) nad ukázkovými daty šablony.

Každý test si založí dočasný projekt z `template/ukazka`, doplní do deníku a kontextu záludné případy
(svislítko v buňce, řádek „2b“, 6sloupcový řádek, skloňovaná jména, vygenerované podklady) a pustí nástroj.
Jen standardní knihovna, nic nestahuje. Z kořene repozitáře: python -I -X utf8 tests/rejstrik/test_rejstrik.py
"""
import os, shutil, sqlite3, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILL = os.path.join(REPO, "skills", "rodokmen") if os.path.isdir(os.path.join(REPO, "skills")) else os.path.join(REPO, "rodokmen")
PY = [sys.executable, "-I", "-X", "utf8"]
VYSLEDKY = []

DENIK_NAVIC = """| 3 | 2026-01-02 | ARON, O Holice 1915–1925 | sn. 10–40 | sňatek Jana Nováka (č. 8) | nalezeno: přepis „Ho-\\|lice“ zalomen svislítkem | ukazka_snatek_jan_novak_josefa_pokorna_1919 |
| 3 | 2026-01-02 | ARON, Z Holice 1940–1950 | sn. 1–5 | úmrtí | duplicitní číslo řádku | — |
| 4 | 2026-01-03 | Kramerius, Holické listy sn. 3 | kovárna Jana Nováka | zmínka o kovárně Jana Nováka v Holicích | — |
| 5 | 2026-01-04 | ARON, N Holice 1880–1900 | sn. 1–49 | sourozenci | křest sestry Josefy Pokorné, otec uveden jako Pokorný | — |
"""


def projekt():
    d = tempfile.mkdtemp(prefix="rejstrik_")
    shutil.copytree(os.path.join(SKILL, "template", "ukazka"), os.path.join(d, "data"))
    os.makedirs(os.path.join(d, "tools"))
    shutil.copy(os.path.join(SKILL, "tools", "rejstrik.py"), os.path.join(d, "tools"))
    with open(os.path.join(d, "data", "research_log.md"), "a", encoding="utf-8", newline="\n") as f:
        f.write(DENIK_NAVIC)
    zapis(os.path.join(d, "kontext", "pomocnici", "holice.md"),
          "# Výstup pomocníka\n\n## Holice 1890\nKovář Jan Novák má v roce 1890 dílnu u náměstí.\n")
    zapis(os.path.join(d, "kontext", "souhrn.md"), "# Souhrn\n\n## Pozemková kniha\nUnikátníslovo123 grunt čp. 112.\n")
    zapis(os.path.join(d, "kniha", "podklady", "rod_8.md"),
          "# Podklady: rod 8\n\nVygenerováno nástrojem `tools/rejstrik.py podklady` z dat projektu.\n\n## X\nGenerovaneslovo456\n")
    return d


def zapis(cesta, text):
    os.makedirs(os.path.dirname(cesta), exist_ok=True)
    with open(cesta, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def spust(d, *args):
    r = subprocess.run(PY + [os.path.join(d, "tools", "rejstrik.py"), *args], cwd=d, capture_output=True,
                       text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r.stdout


def db(d):
    return sqlite3.connect(os.path.join(d, "pracovni", "rejstrik.sqlite"))


def test(nazev):
    def obal(fn):
        d = projekt()
        try:
            fn(d)
            VYSLEDKY.append((nazev, None))
        except AssertionError as e:
            VYSLEDKY.append((nazev, str(e) or "assert"))
        finally:
            shutil.rmtree(d, ignore_errors=True)
        return fn
    return obal


@test("postaví rejstřík a vypíše počty")
def _(d):
    out = spust(d)
    assert "osoby:" in out and "denik: 6" in out, out


@test("svislítko \\| v buňce deníku neposune sloupce")
def _(d):
    spust(d)
    vys, cit = db(d).execute("SELECT vysledek, citace FROM denik WHERE radek=3").fetchone()
    assert "Ho-|lice" in vys and cit == "ukazka_snatek_jan_novak_josefa_pokorna_1919", (vys, cit)


@test("duplicitní číslo řádku se neztratí (3b)")
def _(d):
    spust(d)
    assert db(d).execute("SELECT count(*) FROM denik WHERE radek='3b'").fetchone()[0] == 1


@test("6sloupcový řádek (bez rozsahu) se srovná na 7 sloupců")
def _(d):
    spust(d)
    r = db(d).execute("SELECT rozsah, hledano, citace FROM denik WHERE radek=4").fetchone()
    assert r[0] == "" and r[1] == "kovárna Jana Nováka" and r[2] == "—", r


@test("citace klíče zápisu propojí řádek deníku s osobou (jistě)")
def _(d):
    spust(d)
    jak = {r[0] for r in db(d).execute("SELECT jak FROM zminky WHERE druh='denik' AND ref='3' AND cislo=8")}
    assert "citace" in jak, jak


@test("jméno v jiném pádě (Josefy Pokorné) najde osobu jako vodítko")
def _(d):
    spust(d)
    jak = {r[0] for r in db(d).execute("SELECT jak FROM zminky WHERE druh='denik' AND ref='5' AND cislo=9")}
    assert jak & {"jmeno", "jmeno_rok", "jmeno_vice"}, jak


@test("osoba 8: fakta, zápisy i řádky deníku")
def _(d):
    out = spust(d, "osoba", "8")
    assert "Jan Novák" in out and "ukazka_krest_jan_novak_1890" in out and "ř. 3" in out, out[:2000]


@test("hledej bez diakritiky najde kontext; pomocníci až na konci")
def _(d):
    out = spust(d, "hledej", "kovar novak")
    assert "pomocni" in out.lower(), out[:1500]
    assert "unikatnislovo123" in spust(d, "hledej", "Unikátníslovo123").lower().replace("í", "i").replace("á", "a")


@test("vygenerované podklady se neindexují")
def _(d):
    spust(d)
    assert "Generovaneslovo456" not in spust(d, "hledej", "Generovaneslovo456")
    n = db(d).execute("SELECT count(*) FROM texty WHERE text LIKE '%Generovaneslovo456%'").fetchone()[0]
    assert n == 0, n


@test("denik --posledni 2 vypíše jen konec")
def _(d):
    out = spust(d, "denik", "--posledni", "2")
    assert "ř. 4" in out and "ř. 5" in out and "ř. 1 " not in out, out


@test("zapis podle klíče: svazek, přepis, osoby, deník")
def _(d):
    out = spust(d, "zapis", "ukazka_krest_jan_novak_1890")
    assert "Jan Novák" in out and "ř. 1" in out, out[:1500]


@test("podklady jdou do pracovni/podklady, --do jinam")
def _(d):
    spust(d, "podklady", "osoba", "8")
    assert os.path.exists(os.path.join(d, "pracovni", "podklady", "osoba_8.md"))
    spust(d, "podklady", "osoba", "8", "--do", "kniha/podklady/rejstrik")
    assert os.path.exists(os.path.join(d, "kniha", "podklady", "rejstrik", "osoba_8.md"))
    out = spust(d, "hledej", "Podklady osoba")  # ani podklady z --do se neindexují
    assert "rejstrik/osoba_8" not in out, out


@test("změna zdroje rejstřík sám přestaví")
def _(d):
    spust(d)
    zapis(os.path.join(d, "kontext", "novy.md"), "## Nové\nNovéslovo789\n")
    assert "kontext/novy.md" in spust(d, "hledej", "Noveslovo789")


@test("data/*.md mimo výchozí seznam se indexují (ukoly.md)")
def _(d):
    zapis(os.path.join(d, "data", "ukoly.md"), "# Úkoly\n\n## Zajít do archivu\nSlovoukolu42\n")
    out = spust(d, "hledej", "Slovoukolu42")
    assert "ukoly" in out, out


@test("chybi a rod proběhnou")
def _(d):
    spust(d, "chybi")
    assert "Novák" in spust(d, "rod", "8")


if __name__ == "__main__":
    for nazev, chyba in VYSLEDKY:
        print(f"  [{'OK' if not chyba else 'CHYBA'}] {nazev}" + (f"\n      {chyba[:600]}" if chyba else ""))
    ok = sum(1 for _, c in VYSLEDKY if not c)
    print(f"== rejstrik: {ok} z {len(VYSLEDKY)} správně")
    sys.exit(0 if ok == len(VYSLEDKY) else 1)
