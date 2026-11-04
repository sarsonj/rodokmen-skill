#!/usr/bin/env python3
"""Databáze obětí nacistické perzekuce (holocaust.cz, Terezínská iniciativa) bez prohlížeče.

Použití (z kořene projektu):
  obeti.py souhlas      -> uživatel (ne Claude!) jednou za 30 dní potvrdí „Podmínky vstupu do databáze“, které portál ukazuje při vstupu
                           (databáze obsahuje citlivé údaje; v Claude Code `!python3 -I tools/obeti.py souhlas`). Bez souhlasu nástroj nic nestahuje.
  obeti.py hledat [--prijmeni P] [--jmeno J] [--bydliste B] [--misto-narozeni M] [--rok R] [--stran N]
        -> jméno | narození | osud (transporty, úmrtí) | odkaz; N stran po 20 oběti (výchozí 3).
           Příjmení zadávej i v ženském tvaru a s diakritikou („Neumannová“); část jména hledá jako začátek.
  obeti.py detail <odkaz|číslo>
        -> poslední bydliště před deportací, adresa v protektorátu, transporty, osud, související dokumenty
Jde o údaje o zavražděných (Židé z českých zemí, i Romové v samostatné databázi) – jméno, datum narození, transporty. Je to
vodítko pro osud předka, ne náhrada matriky. Na web rodiny jen se souhlasem rodiny (viz `reference/soukromi.md`).
"""
import html, http.cookiejar, re, sys, time, urllib.parse, urllib.request
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)
import souhlas  # noqa: E402 – souhlas s podmínkami vstupu do databáze (tools/souhlas.py)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://www.holocaust.cz/databaze-obeti/"
SOUHLAS_KLIC, SOUHLAS_PORTAL, SOUHLAS_PRIKAZ = "holocaust_cz", "Databáze obětí (holocaust.cz)", "tools/obeti.py souhlas"
SOUHLAS_ZNENI = ("Databáze obětí nacistického pronásledování obsahuje jména a osudy Židů deportovaných z českých zemí a vězňů terezínského "
                 "ghetta z dalších evropských zemí a dále základní informace o Romech, Sintech a dalších osobách, které zemřely jako vězni "
                 "v takzvaném „Cikánském táboře I“ v Letech u Písku. Upozorňujeme, že databáze obsahuje citlivé osobní údaje a jejím účelem "
                 "je důstojné vzpomínání s respektem vůči pozůstalým. Vstupem do databáze uživatel potvrzuje, že se seznámil s informacemi "
                 "o jejím obsahu a je si plně vědom své osobní odpovědnosti za nakládání s materiály a informacemi, které v ní nalezne.")
SOUHLAS_URL = "https://www.holocaust.cz/databaze-obeti/help/"
_op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
_op.addheaders = [("User-Agent", "Mozilla/5.0 (rodokmen)")]


def get(url, data=None):
    err = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode() if data else None)
            with _op.open(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except OSError as e:
            err = e
            if getattr(e, "code", 0) in (403, 404):
                break
            time.sleep(2 * (attempt + 1))
    raise err


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ")).strip()


def vypis(page):
    out = []
    for blok in re.findall(r'<div class="victims-wrapper">(.*?)</div>', page, re.S):
        m = re.search(r'<p>\s*<a href="([^"]+)">(.*?)</a>(.*?)</p>', blok, re.S)
        if m:
            zbytek = [text(x) for x in re.split(r"<br\s*/?>", m.group(3)) if text(x)]
            out.append((text(m.group(2)), " | ".join(zbytek), m.group(1)))
    return out


def hledat(pole, stran):
    page = get(BASE, {"searchFirstname": pole.get("jmeno", ""), "searchSurname": pole.get("prijmeni", ""),
                      "searchPlaceLast": pole.get("bydliste", ""), "searchPlaceBirth": pole.get("misto-narozeni", ""),
                      "searchDateBirthDay": "0", "searchDateBirthMonth": "0", "searchDateBirthYear": pole.get("rok", ""),
                      "searchTransport": "", "searchSubmit": "Vyhledat v databázi"})
    celkem = re.search(r"Celkem nalezeno: ([\d\s\xa0]+)", page)
    n = 0
    for p in range(1, stran + 1):
        for r in vypis(page):
            print(" | ".join(r))
            n += 1
        nxt = re.search(r'<a href="(https://www\.holocaust\.cz/databaze-obeti/strana/\d+/)">další</a>', page)
        if not nxt or p == stran:
            break
        page = get(nxt.group(1))
        time.sleep(0.5)
    if not celkem:
        print("Portál nevrátil výsledky (změnil se formulář?). Hledej v prohlížeči.", file=sys.stderr)
    elif n == 0:
        print("Nic nenalezeno (zkus příjmení v ženském tvaru, bez křestního jména nebo s méně údaji).", file=sys.stderr)
    elif n < int(re.sub(r"\D", "", celkem.group(1)) or 0):
        print(f"… celkem nalezeno {celkem.group(1).strip()}, zobrazeno {n}; zúžit jde jménem nebo rokem, víc stran dá --stran", file=sys.stderr)


def detail(arg):
    if not arg.startswith("http") and not re.fullmatch(r"[0-9a-z-]+", arg):
        sys.exit("Zadej odkaz na oběť (z výpisu `hledat`) nebo její číslo s jménem, např. 111149-anna-neumannova.")
    url = arg if arg.startswith("http") else f"{BASE}obet/{arg}/"
    if not url.startswith(BASE):
        sys.exit("Odkaz musí být z databáze obětí na holocaust.cz.")
    page = get(url)
    jm = re.search(r"<h1>(.*?)</h1>", page, re.S)
    w = re.search(r'<div class="wrapper">.*?<p>(.*?)</p>', page, re.S)
    if not jm or not w:
        sys.exit("Oběť nenalezena (zkontroluj odkaz).")
    print(text(jm.group(1)))
    for r in re.split(r"<br\s*/?>", w.group(1)):
        if text(r):
            print("  " + text(r))
    for href, nazev in re.findall(r'<div class="victim-documents">\s*<a href="([^"]+)">.*?<span>(.*?)</span>', page, re.S):
        print(f"  dokument: {text(nazev)} | {href}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "souhlas" and len(a) == 1:
        souhlas.potvrd(SOUHLAS_KLIC, SOUHLAS_PORTAL, SOUHLAS_ZNENI, SOUHLAS_URL, SOUHLAS_PRIKAZ)
        sys.exit(0)
    if a[0] in ("hledat", "detail"):
        souhlas.vyzaduj(SOUHLAS_KLIC, SOUHLAS_PORTAL, SOUHLAS_ZNENI, SOUHLAS_PRIKAZ)
    if a[0] == "hledat":
        pole, stran, i = {}, 3, 1
        klice = {"--prijmeni": "prijmeni", "--jmeno": "jmeno", "--bydliste": "bydliste", "--misto-narozeni": "misto-narozeni", "--rok": "rok"}
        while i < len(a):
            if a[i] == "--stran" and i + 1 < len(a) and a[i + 1].isdigit() and int(a[i + 1]) >= 1:
                stran, i = int(a[i + 1]), i + 2
            elif a[i] in klice and i + 1 < len(a):
                pole[klice[a[i]]], i = a[i + 1], i + 2
            else:
                sys.exit(__doc__)
        if not pole:
            sys.exit("Zadej aspoň --prijmeni (nebo --jmeno, --bydliste, --misto-narozeni).")
        if "rok" in pole and not re.fullmatch(r"\d{4}", pole["rok"]):
            sys.exit("--rok chce čtyřmístný rok narození.")
        hledat(pole, stran)
    elif a[0] == "detail" and len(a) == 2:
        detail(a[1])
    else:
        sys.exit(__doc__)
