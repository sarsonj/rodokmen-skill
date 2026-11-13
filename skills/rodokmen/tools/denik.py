#!/usr/bin/env python3
"""Výzkumný deník (data/research_log.md) – přidání řádku se správným číslem a sloupci, kontrola tabulky.

Proč: deník je na webu jedna markdown tabulka. Prázdný řádek ji ukončí (web pak ukazoval jen do #367),
chybějící sloupce rozhodí zobrazení a server sloučí větev jen tehdy, když nový řádek má číslo, které v `main` ještě není.

Použití (z kořene projektu):
  denik.py pridej --zdroj "…" --rozsah "…" --hledano "…" --vysledek "…" [--citace "…"] [--datum RRRR-MM-DD]
      zdroj    archiv, kniha a apu_id / číslo knihy („ARON, Choceň, zemřelí sign. 2112 (apu b156902e…)“)
      rozsah   co přesně bylo prohlédnuto („sn. 10 (fol. 14, 1791)“, „rejstřík P 1791–1810, sn. 47–48“)
      hledano  co se hledalo („úmrtí Tomáše Příhody * 1731“)
      vysledek co se našlo, i neúspěch s rozsahem („**nalezeno** … zapsáno `klíč`“ / „nenalezeno v …“)
      citace   kdo četl a odkud („Petra + Claude“, odkaz) – nepovinné
    Vypíše číslo nového řádku. Číslo = nejvyšší číslo v místním deníku i v origin/main + 1.
  denik.py pridej <vstup.json>     totéž, vstup {"zdroj": …, "rozsah": …, "hledano": …, "vysledek": …, "citace": …}
  denik.py dalsi                   jen vypíše, jaké číslo dostane další řádek
  denik.py kontrola                prázdné řádky v tabulce, chybné sloupce a čísla u nových řádků (od DENIK_OD)

Svislou čáru „|“ v textu nástroj sám zapíše jako „\\|“ a konce řádků nahradí mezerou.
"""
import datetime, json, os, re, subprocess, sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "data", "research_log.md")
SLOUPCE = ["#", "datum", "zdroj", "rozsah", "hledáno", "výsledek", "citace"]
DENIK_OD = 384   # starší řádky mají často méně sloupců; měnit je smí jen účet brodek, kontrola je proto přeskakuje
RADEK = re.compile(r"^\| (\d+) \|")
SEP = re.compile(r"(?<!\\)\|")


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
    datum = udaje.get("datum") or datetime.date.today().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", datum):
        sys.exit(f"Datum „{datum}“ musí být RRRR-MM-DD.")
    surovy = open(LOG, "rb").read()
    text = surovy.decode("utf-8-sig")
    eol = "\r\n" if b"\r\n" in surovy else "\n"
    cislo = dalsi_cislo(text)
    radek = "| " + " | ".join([str(cislo), datum] + [bunka(udaje.get(k)) for k in ("zdroj", "rozsah", "hledano", "vysledek", "citace")]) + " |"
    # konec souboru: smazat prázdné řádky za tabulkou, ať nový řádek tabulku neukončí
    zbytek = text.rstrip("\r\n \t")
    if not RADEK.match(zbytek.splitlines()[-1]):
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
    videne = {}
    for i in idx:
        c = bunky(radky[i])
        n = int(c[0])
        if n >= od:
            if len(c) != len(SLOUPCE):
                err.append(f"deník #{n}: {len(c)} sloupců místo {len(SLOUPCE)} ({' | '.join(SLOUPCE)}) – "
                           "přidávej řádky přes tools/denik.py pridej")
            if n in videne:
                err.append(f"deník #{n}: číslo je v deníku dvakrát – přečísluj nový řádek (tools/denik.py dalsi)")
        videne[n] = i
    return err, warn


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("pridej", "dalsi", "kontrola"):
        sys.exit(__doc__)
    if a[0] == "dalsi":
        print(dalsi_cislo())
        return
    if a[0] == "kontrola":
        err, warn = kontrola()
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
