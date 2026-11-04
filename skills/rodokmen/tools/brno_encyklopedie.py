#!/usr/bin/env python3
"""Encyklopedie dějin města Brna (encyklopedie.brna.cz; Masarykova univerzita a Muzeum města Brna) bez prohlížeče.

Osobnosti (s rodištěm, bydlišti – i čísla domů –, povoláním, hrobem a rodinou), ulice, objekty, spolky, školy a lokality.

Použití (z kořene projektu):
  brno_encyklopedie.py hledat "text"
        -> až ~30 nejlepších zásahů fulltextu (jméno, ulice, povolání, hřbitov…): typ | název | úryvek | odkaz.
           Portál vrací jen první stránku; chceš-li zúžit, přidej slova („Novák klempíř Králova“) nebo zadej přesnější jméno.
  brno_encyklopedie.py detail <odkaz|typ:id>
        -> celý text hesla (narození, úmrtí, bydliště, vzdělání, zaměstnání, hrob s číslem hrobu); typ:id např. osobnosti:15
Užitečné u předků, kteří žili v Brně: bydliště s adresou, povolání a hrob na Ústředním hřbitově vedou k matrice, rodině a hrobovému místu.
Heslo je tištěný životopis významné osoby, ne evidence obyvatel – běžní obyvatelé tu být nemusí. Zdroj cituj: „Encyklopedie dějin města Brna“.
"""
import html, json, re, sys, time, urllib.parse, urllib.request
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://encyklopedie.brna.cz/home-mmb/"
TYPY = {"profil-osobnosti": "osobnost", "profil-lokality": "lokalita", "profil-spolku": "spolek", "profil-ulice": "ulice",
        "profil-objektu": "objekt", "profil-stavby": "stavba", "profil-skoly": "škola", "profil-udalosti": "událost"}
ZKR = {"osobnosti": "profil-osobnosti", "lokality": "profil-lokality", "spolku": "profil-spolku", "ulice": "profil-ulice",
       "objektu": "profil-objektu", "stavby": "profil-stavby", "skoly": "profil-skoly", "udalosti": "profil-udalosti"}


def get(url):
    err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (rodokmen)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except OSError as e:
            err = e
            if getattr(e, "code", 0) in (403, 404):
                break
            time.sleep(2 * (attempt + 1))
    raise err


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ")).strip()


def hledat(dotaz):
    page = get(BASE + "?" + urllib.parse.urlencode({"q": dotaz, "json": "search-v2"}))
    try:
        h = json.loads(page)["html"]["search-results"]
    except (ValueError, KeyError):
        sys.exit("Portál vrátil neočekávanou odpověď (změnil se?). Hledej na encyklopedie.brna.cz v prohlížeči.")
    celkem = re.search(r"nalezeno (\d+)", h)
    n = 0
    for acc, i, nazev, popis in re.findall(r'<a href="\?acc=([a-z-]+)&load=(\d+)#generator" title="[^"]*">([^<]+)</a>\s*<p>(.*?)</p>', h, re.S):
        popis = re.sub(r"\(\(([^|)]*)\|?[^)]*\)\)", r"\1", text(popis))   # značky odkazů ((Heslo|text)) -> Heslo
        popis = re.sub(r"\[\[([^\]]*)\]\]", r"\1", popis)
        print(f"{TYPY.get(acc, acc)} | {text(nazev)} | {popis[:200]} | {BASE}?acc={acc}&load={i}")
        n += 1
    if n == 0:
        print("Nic nenalezeno (zkus jiný tvar jména nebo méně slov).", file=sys.stderr)
    elif celkem and n < int(celkem.group(1)):
        print(f"… celkem {celkem.group(1)} odkazů, zobrazeno {n}; zúžit jde dalším slovem (příjmení, ulice, povolání)", file=sys.stderr)


def detail(arg):
    m = re.fullmatch(r"([a-z]+):(\d+)", arg)
    if m and m.group(1) in ZKR:
        url = f"{BASE}?acc={ZKR[m.group(1)]}&load={m.group(2)}"
    else:
        q = urllib.parse.urlsplit(arg)
        par = urllib.parse.parse_qs(q.query)
        if q.hostname != "encyklopedie.brna.cz" or not re.fullmatch(r"profil-[a-z]+", (par.get("acc") or [""])[0]) \
                or not re.fullmatch(r"\d+", (par.get("load") or [""])[0]):
            sys.exit("Zadej odkaz z výpisu `hledat` nebo typ:id (např. osobnosti:15).")
        url = f"{BASE}?acc={par['acc'][0]}&load={par['load'][0]}"
    page = get(url)
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S)
    h1 = re.search(r"<title>(.*?)</title>", page, re.S)
    s = text(t)
    i = s.rfind(" Vyhledat ")   # za formulářem hledání začíná vlastní heslo
    s = s[i + len(" Vyhledat "):] if i >= 0 else s
    for konec in (" Facebook", " Přidat komentář", " Další projekty"):
        k = s.find(konec, 200)
        if k > 0:
            s = s[:k]
    print((text(h1.group(1)) if h1 else "") + "\n" + s[:6000])
    print(f"Odkaz: {url}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == "hledat" and a[1].strip():
        hledat(a[1])
    elif len(a) == 2 and a[0] == "detail":
        detail(a[1])
    else:
        sys.exit(__doc__)
