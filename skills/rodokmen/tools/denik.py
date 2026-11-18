#!/usr/bin/env python3
"""Výzkumný deník (data/research_log.md) – přidání řádku se správným číslem a sloupci, kontrola tabulky.

Proč: deník je na webu jedna markdown tabulka. Prázdný řádek ji ukončí (web pak ukáže jen řádky nad ním),
chybějící sloupce rozhodí zobrazení a server sloučí větev jen tehdy, když nový řádek má číslo, které v `main` ještě není.

Použití (z kořene projektu):
  denik.py pridej --zdroj "…" --rozsah "…" --hledano "…" --vysledek "…" [--citace "…"] [--datum RRRR-MM-DD | "9. 11. 2026"]
      zdroj    archiv, kniha a apu_id / číslo knihy („ARON, Choceň, zemřelí sign. 2112 (apu b156902e…)“)
      rozsah   co přesně bylo prohlédnuto („sn. 10 (fol. 14, 1791)“, „rejstřík P 1791–1810, sn. 47–48“)
      hledano  co se hledalo („úmrtí Tomáše Příhody * 1731“)
      vysledek co se našlo, i neúspěch s rozsahem („**nalezeno** … zapsáno `klíč`“ / „nenalezeno v …“)
      citace   kdo četl a odkud („Petra + Claude“, odkaz) – nepovinné
    Vypíše číslo nového řádku. Číslo = nejvyšší číslo v místním deníku i v origin/main + 1.
    Sloupce řádku se řídí hlavičkou tabulky (starší deník se 6 sloupci bez „rozsah“: rozsah se připíše ke zdroji)
    a datum se zapíše ve stejném tvaru, jaký má poslední řádek deníku (RRRR-MM-DD, nebo „9. 11. 2026“).
  denik.py pridej <vstup.json>     totéž, vstup {"zdroj": …, "rozsah": …, "hledano": …, "vysledek": …, "citace": …}
  denik.py dalsi                   jen vypíše, jaké číslo dostane další řádek
  denik.py kontrola [--od N]       prázdné řádky v tabulce, chybné sloupce a zdvojená čísla (od řádku N, výchozí DENIK_OD
                                   nebo proměnná prostředí DENIK_OD). Doplněné řádky „533b“ mezi existujícími jsou v pořádku.

Svislou čáru „|“ v textu nástroj sám zapíše jako „\\|“ a konce řádků nahradí mezerou.
"""
import datetime, json, os, re, subprocess, sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "data", "research_log.md")
SLOUPCE = ["#", "datum", "zdroj", "rozsah", "hledáno", "výsledek", "citace"]
# číslo řádku, od kterého se kontrolují sloupce (projekt se staršími řádky jiného tvaru: --od N nebo proměnná DENIK_OD)
DENIK_OD = int(os.environ["DENIK_OD"]) if os.environ.get("DENIK_OD", "").isdigit() else 1
RADEK = re.compile(r"^\| (\d+)([a-z]?) \|")   # „| 533 |“ i doplněný řádek „| 533b |“
SEP = re.compile(r"(?<!\\)\|")
ODDELOVAC = re.compile(r"^\|(\s*:?-+:?\s*\|)+\s*$")   # |---|---| pod hlavičkou (prázdný deník ze šablony)


POLE = {"#": "#", "č.": "#", "datum": "datum", "zdroj": "zdroj", "rozsah": "rozsah", "hledáno": "hledano",
        "hledano": "hledano", "výsledek": "vysledek", "vysledek": "vysledek", "citace": "citace"}
CESKE_DATUM = re.compile(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})")


def hlavicka(text):
    """Sloupce tabulky deníku podle hlavičky (řádek nad |---|); bez hlavičky výchozích 7 sloupců."""
    radky = text.splitlines()
    for i in range(1, len(radky)):
        if ODDELOVAC.match(radky[i]) and radky[i - 1].lstrip().startswith("|"):
            return [c.lower() for c in bunky(radky[i - 1])]
    return list(SLOUPCE)


def datum_iso(v):
    """RRRR-MM-DD z „2026-11-09“ i „9. 11. 2026“; None, když to datum není."""
    v = str(v or "").strip()
    m = CESKE_DATUM.fullmatch(v)
    if m:
        v = f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    try:
        return datetime.date.fromisoformat(v).isoformat() if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) else None
    except ValueError:
        return None


def tvar_data(iso, text):
    """Datum ve tvaru, jaký má poslední řádek deníku (aby se tvary v jednom deníku nemíchaly)."""
    posl = [l for l in text.splitlines() if RADEK.match(l)]
    if posl:
        b = bunky(posl[-1])
        if len(b) > 1 and CESKE_DATUM.fullmatch(b[1]):
            d = datetime.date.fromisoformat(iso)
            return f"{d.day}. {d.month}. {d.year}"
    return iso


def bunky(radek):
    return [c.strip() for c in SEP.split(radek.strip())[1:-1]]


def cisla(text):
    return [int(m.group(1)) for m in map(RADEK.match, text.splitlines()) if m]


def text_main():
    """Deník z origin/main (bez sítě – jen co už je stažené přes git fetch); prázdný řetězec, když nejde."""
    try:
        r = subprocess.run(["git", "-C", ROOT, "show", "origin/main:data/research_log.md"],
                           capture_output=True, text=True, encoding="utf-8", timeout=30)
        return r.stdout if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def dalsi_cislo(text=None):
    text = open(LOG, encoding="utf-8-sig").read() if text is None else text
    return max(cisla(text) + cisla(text_main()) + [0]) + 1


def bunka(v):
    v = re.sub(r"\s*[\r\n]+\s*", " ", str(v or "")).strip()
    return re.sub(r"(?<!\\)\|", r"\\|", v)


def pridej(udaje):
    """Přidá řádek, vrátí jeho číslo. udaje: zdroj, rozsah, hledano, vysledek, citace, datum."""
    chybi = [k for k in ("zdroj", "rozsah", "hledano", "vysledek") if not str(udaje.get(k) or "").strip()]
    if chybi:
        sys.exit("Chybí: " + ", ".join(chybi) + " (každý řádek deníku má mít zdroj, rozsah, co se hledalo a výsledek).")
    datum = datum_iso(udaje.get("datum") or datetime.date.today().isoformat())
    if not datum:
        sys.exit(f"Datum „{udaje.get('datum')}“ není datum – piš RRRR-MM-DD nebo „9. 11. 2026“.")
    surovy = open(LOG, "rb").read()
    text = surovy.decode("utf-8-sig")
    eol = "\r\n" if b"\r\n" in surovy else "\n"
    cislo = dalsi_cislo(text)
    hodnoty = dict(udaje, datum=tvar_data(datum, text))
    hodnoty["#"] = str(cislo)
    sloupce = [POLE.get(s, s) for s in hlavicka(text)]
    if "rozsah" not in sloupce and str(hodnoty.get("rozsah") or "").strip():   # starší deník bez sloupce „rozsah“
        hodnoty["zdroj"] = f"{hodnoty.get('zdroj', '')}, {hodnoty['rozsah']}"
    radek = "| " + " | ".join(bunka(hodnoty.get(s)) if s != "#" else hodnoty["#"] for s in sloupce) + " |"
    # konec souboru: smazat prázdné řádky za tabulkou, ať nový řádek tabulku neukončí
    zbytek = text.rstrip("\r\n \t")
    posledni = zbytek.splitlines()[-1] if zbytek else ""
    if not (RADEK.match(posledni) or ODDELOVAC.match(posledni)):
        sys.exit("Deník nekončí řádkem tabulky – nový řádek by nebyl v tabulce. Oprav konec data/research_log.md ručně.")
    novy = zbytek + eol + radek + eol
    tmp = LOG + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(novy)
    os.replace(tmp, LOG)
    return cislo


def kontrola(text=None, od=DENIK_OD):
    """Seznam (chyby, upozornění) pro tabulku deníku."""
    text = open(LOG, encoding="utf-8-sig").read() if text is None else text
    radky = text.splitlines()
    idx = [i for i, l in enumerate(radky) if RADEK.match(l)]
    err, warn = [], []
    if not idx:
        return err, warn
    prazdne = [i + 1 for i in range(idx[0], idx[-1]) if not radky[i].strip()]
    if prazdne:
        err.append(f"deník: prázdný řádek uvnitř tabulky (řádek souboru {', '.join(map(str, prazdne[:5]))}) – "
                   "na webu tabulku ukončí, smaž ho")
    jine = [i + 1 for i in range(idx[0], idx[-1]) if radky[i].strip() and not RADEK.match(radky[i])]
    if jine:
        warn.append(f"deník: uvnitř tabulky je řádek, který není řádkem deníku (řádek souboru {', '.join(map(str, jine[:5]))})")
    sloupce = hlavicka(text)
    videne = {}
    for i in idx:
        c = bunky(radky[i])
        m = RADEK.match(radky[i])
        n, oznaceni = int(m.group(1)), m.group(1) + m.group(2)
        if n >= od:
            if len(c) != len(sloupce):
                err.append(f"deník #{oznaceni}: {len(c)} sloupců místo {len(sloupce)} ({' | '.join(sloupce)}) – "
                           "přidávej řádky přes tools/denik.py pridej")
            if oznaceni in videne:
                err.append(f"deník #{oznaceni}: číslo je v deníku dvakrát – přečísluj nový řádek (tools/denik.py dalsi)")
        videne[oznaceni] = i
    return err, warn


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("pridej", "dalsi", "kontrola"):
        sys.exit(__doc__)
    if a[0] == "dalsi":
        print(dalsi_cislo())
        return
    if a[0] == "kontrola":
        od = DENIK_OD
        if len(a) == 3 and a[1] == "--od" and a[2].isdigit():
            od = int(a[2])
        elif len(a) > 1:
            sys.exit(__doc__)
        err, warn = kontrola(od=od)
        for e in err:
            print("CHYBA:", e)
        for w in warn:
            print("upozornění:", w)
        print("Deník v pořádku." if not err and not warn else "")
        sys.exit(1 if err else 0)
    if len(a) == 2 and not a[1].startswith("--"):
        try:
            udaje = json.load(open(a[1], encoding="utf-8-sig"))
        except (OSError, ValueError) as e:
            sys.exit(f"Vstup {a[1]} není platný JSON: {e}")
    else:
        udaje, i = {}, 1
        while i < len(a):
            if not a[i].startswith("--") or i + 1 >= len(a):
                sys.exit(f"Nečekaný argument „{a[i]}“.\n\n" + __doc__)
            udaje[a[i][2:]] = a[i + 1]
            i += 2
    udaje = {{"hledáno": "hledano", "výsledek": "vysledek"}.get(k, k): v for k, v in udaje.items()}
    nezname = set(udaje) - {"zdroj", "rozsah", "hledano", "vysledek", "citace", "datum"}
    if nezname:
        sys.exit("Neznámé pole: " + ", ".join(sorted(nezname)) + "\n\n" + __doc__)
    print(pridej(udaje))


if __name__ == "__main__":
    main()
