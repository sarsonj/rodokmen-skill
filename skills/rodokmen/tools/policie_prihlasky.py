#!/usr/bin/env python3
"""Pražské policejní přihlášky 1850–1914 (Národní archiv, digi.nacr.cz/prihlasky2) bez prohlížeče.

Použití (z kořene projektu):
  policie_prihlasky.py <Příjmení> [Jméno] [rok_od] [rok_do]  -> pořadí | příjmení | jméno | rok narození
Příjmení je začátek jména bez diakritiky („Kolar“ najde Kolář, Kolár, Kolarik…). Roky = rok narození osoby.
Web vrátí bez prohlížeče jen prvních 20 výsledků – když je jich víc, zúži hledání jménem nebo roky.
  policie_prihlasky.py karta <pořadí> <výstup.jpg> <Příjmení> [Jméno] [rok_od] [rok_do]
      -> stáhne kartu (hlava rodiny, manželka s místem narození, děti, adresy) z výsledku stejného hledání (i pořadí nad 20)
         a vypíše citaci a trvalý odkaz (portál dává kartu jen v 1000 × 1333 px). Nástroj ověří, že je na kartě
         vyznačená hledaná osoba – při přiškrcení portál umí vrátit cizí kartu; pak skončí chybou a nic neukládá.
Portál přiškrcuje podle IP: karty stahuj po jedné (brzda: 1 dotaz za 4 s).
Trvalý odkaz na kartu:
  https://digi.nacr.cz/prihlasky2/index.php?action=link&ref=czarch:CZ-100000010:874&karton=<K>&folium=<F>
Pokrývá Prahu I–VIII. Smíchov, Vinohrady, Žižkov, Karlín ap. byly do 1922 samostatná města – tam přihlášky nejsou.
"""
import html, re, sys, time, unicodedata, urllib.parse, urllib.request
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://digi.nacr.cz/prihlasky2/"
_op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
_op.addheaders = [("User-Agent", "Mozilla/5.0 (rodokmen)")]


def get(url, data=None):
    if data:
        data = urllib.parse.urlencode(data).encode()
    for i in range(5):   # server občas neodpovídá
        try:
            return _op.open(url, data, timeout=40).read().decode("utf-8", "replace")
        except Exception as e:
            print("znovu", i + 1, e, file=sys.stderr)
            time.sleep(5 * (i + 1))
    sys.exit("server neodpovídá")


def holy(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


def over_kartu(h, poradi, prijmeni, jmeno, od, do, radek):
    """Portál při přiškrcení umí vrátit kartu z jiného hledání (B-712): ověř pořadí a hledanou osobu na kartě."""
    lide = [html.unescape(re.sub(r"<[^>]+>", "", x)).strip() for x in re.findall(r"<div>(.*?)</div>",
            (re.search(r'<div class="seznam_lidi">(.*?</div>)</div>', h, re.S) or re.search("()", "")).group(1))]
    osoba = re.search(r'<div class="seznam_lidi">.*?<strong>(.*?)</strong>', h, re.S)
    osoba = html.unescape(re.sub(r"<[^>]+>", "", osoba.group(1))).strip() if osoba else ""
    c = re.search(r"záznam č\.\s*(\d+)", h)
    chyby = []
    if not c or c.group(1) != str(poradi):
        chyby.append(f"portál ukazuje záznam č. {c.group(1) if c else '?'}, ne {poradi}")
    slova, rok = re.findall(r"[^\s()]+", holy(osoba)), re.search(r"\((\d{4})\)\s*$", osoba)
    if not osoba:
        chyby.append("na kartě není vyznačená hledaná osoba")
    else:
        if not any(w.startswith(holy(prijmeni)) for w in slova):
            chyby.append(f"vyznačená osoba „{osoba}“ nemá příjmení „{prijmeni}…“")
        if jmeno and not any(w.startswith(holy(jmeno)) for w in slova):
            chyby.append(f"vyznačená osoba „{osoba}“ nemá jméno „{jmeno}…“")
        if rok and ((od and int(rok.group(1)) < int(od)) or (do and int(rok.group(1)) > int(do))):
            chyby.append(f"rok narození {rok.group(1)} je mimo {od}–{do}")
        if radek and (holy(radek[1]) not in holy(osoba) or radek[3] and radek[3] not in osoba
                      or radek[2].strip() and holy(radek[2].strip()) not in slova):
            chyby.append(f"ve výsledcích je pod č. {poradi} „{radek[1]} {radek[2]} ({radek[3]})“, na kartě „{osoba}“")
    if chyby:
        sys.exit("Karta NEODPOVÍDÁ hledání – portál nejspíš přiškrcuje a vrátil cizí kartu. Nic nezapisuj, zkus to "
                 "později znovu (celé hledání).\n  " + "\n  ".join(chyby) + (f"\n  na kartě: {', '.join(lide)}" if lide else ""))
    return lide


def karta(session, poradi, out, overeni):
    h = get(f"{BASE}?session={session}&action=image&record={poradi}")
    m = re.search(r'src="images/((\d+)-(\d+)\.jpg)"', h)
    if not m:
        sys.exit(f"karta č. {poradi} nenalezena (je pořadí z tohoto hledání?)")
    lide = over_kartu(h, poradi, *overeni)
    for i in range(5):
        try:
            data = _op.open(BASE + "images/" + m.group(1), timeout=60).read()
            break
        except Exception as e:
            print("znovu", i + 1, e, file=sys.stderr)
            time.sleep(5 * (i + 1))
    else:
        sys.exit("server neodpovídá")
    if not data.startswith(b"\xff\xd8"):   # při přiškrcení místo obrázku stránka s chybou
        sys.exit("portál nevrátil obrázek karty (přiškrcuje?) – zkus to později, nic se neuložilo")
    with open(out, "wb") as f:
        f.write(data)
    k, fo = int(m.group(2)), int(m.group(3))
    print(out, f"– Národní archiv, Policejní ředitelství I, konskripce, karton {k}, obraz {fo}")
    print("na kartě:", ", ".join(lide), "(vyznačená = hledaná osoba; přesto ověř čtením)")
    print(f"odkaz: {BASE}index.php?action=link&ref=czarch:CZ-100000010:874&karton={k}&folium={fo}")


RX = re.compile(r'record=(\d+)">([^<]*)</a></td>\s*<td class="table_jmeno">([^<]*)</td>\s*<td class="table_rok">([^<]*)<')


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    args = sys.argv[1:]
    card = None
    if args[0] == "karta":
        if len(args) < 4 or not args[1].isdigit():
            sys.exit(__doc__)
        card, args = (args[1], args[2]), args[3:]
    a = args + ["", "", ""]
    prijmeni, jmeno, od, do = a[0], a[1], a[2], a[3]
    m = re.search(r"session=([0-9a-f]+)", get(BASE))
    if not m:
        sys.exit("nepodařilo se otevřít vyhledávání (změnil se web?)")
    h = get(BASE + "?session=" + m.group(1),
            {"prijmeni": prijmeni, "jmeno": jmeno, "action": "hledani2", "odroku": od, "doroku": do})
    if card:
        radky = {r[0]: r for r in RX.findall(h)}
        return karta(m.group(1), *card, (prijmeni, jmeno, od, do, radky.get(card[0])))
    m = re.search(r"záznamů:\s*(\d+)", h)
    n = int(m.group(1)) if m else 0
    print(f"# {prijmeni} {jmeno} {od}–{do}: {n} záznamů")
    for r in RX.findall(h):
        print("\t".join(x.strip() for x in r))
    if n > 20:
        print(f"# zobrazeno jen 20 z {n} – zúži hledání jménem nebo roky narození")


if __name__ == "__main__":
    main()
