#!/usr/bin/env python3
"""Hroby na portálu cintoriny.sk (slovenské a část českých hřbitovů – Motol, Strašnice, Vodňany…) bez prohlížeče.

Použití (z kořene projektu):
  cintoriny.py hledat [--prijmeni P] [--rodne R] [--jmeno J] [--obec O | --hrbitov ID]
                      [--narozeni-od X] [--narozeni-do X] [--umrti-od X] [--umrti-do X] [--stran N]
        -> jméno | narozen | zemřel | věk | hřbitov (obec) | hrob ID:ID; N stran po 50 záznamech (výchozí 2).
           Hledá od začátku slova a bez ohledu na diakritiku (Izso najde Izsó i Izsof). --rodne je rodné příjmení ženy.
           Datum X: rok (1903) nebo den (7. 5. 1903). Alespoň jedno z polí příjmení, rodné příjmení, jméno je povinné.
  cintoriny.py hrob <hřbitov:hrob | odkaz> [--foto pracovni/hrob.jpg]
        -> karta hrobu: sektor, řada, číslo (i dřívější), typ, správa hřbitova a všichni uložení v hrobě s daty
           narození, úmrtí a uložení, rodným příjmením a místy (u každého jeden dotaz navíc). --foto uloží fotku hrobu.
  cintoriny.py hrbitovy "Obec"
        -> hřbitovy v obci s jejich ID (pro --hrbitov).
Užitečné hlavně na Slovensku, kde matriky po roce 1900 nejsou online: hrob ukáže, kdo leží spolu (manželé, děti, rodiče),
a dá přesná data narození a úmrtí. Datum 1. 1. (01.01.RRRR) bývá zástupné, když správa znala jen rok – ověř v matrice.
Hrob je evidence správy hřbitova, ne matrika: chyby v datech i jménech se stávají. Zdroj cituj: „cintoriny.sk, <hřbitov>, hrob …“.
"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)

import html, re, sys, time, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://www.cintoriny.sk"
POLE = {"--prijmeni": "surname", "--rodne": "maidenSurname", "--jmeno": "name", "--obec": "city", "--hrbitov": "cemeteryId",
        "--narozeni-od": "birthDateFrom", "--narozeni-do": "birthDateTo", "--umrti-od": "deathDateFrom", "--umrti-do": "deathDateTo"}


def get(path, data=None, binary=False):
    err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(BASE + path, data=urllib.parse.urlencode(data).encode() if data is not None else None,
                                         headers={"User-Agent": "Mozilla/5.0 (rodokmen)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                b = r.read()
                return b if binary else b.decode("utf-8", "replace")
        except OSError as e:
            err = e
            if getattr(e, "code", 0) in (403, 404):
                break
            time.sleep(2 * (attempt + 1))
    raise err


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ")).strip()


def datum(s, konec):
    """Rok nebo „7. 5. 1903“ / „07.05.1903“ / „1903-05-07“ -> RRRR-MM-DD (portál jiný tvar ignoruje)."""
    s = s.strip()
    if re.fullmatch(r"\d{4}", s):
        return s + ("-12-31" if konec else "-01-01")
    m = re.fullmatch(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})", s)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s
    sys.exit(f"Nerozumím datu „{s}“ – zadej rok (1903) nebo den (7. 5. 1903).")


def hledat(pole, stran):
    if not any(pole.get(k) for k in ("surname", "maidenSurname", "name")):
        sys.exit("Zadej aspoň --prijmeni, --rodne nebo --jmeno.")
    hrbitovy = {}      # id -> (název, obec)
    obec = None
    n, celkem, dalsi = 0, None, {}
    for p in range(stran):
        h = get("/api/htmlSearch.php", {**pole, **dalsi})
        obec = obec if p == 0 else None      # další stránky záhlaví obce neposílají, jen hřbitova
        if celkem is None:
            m = re.search(r"Počet záznamov:\s*(\d+)", h)
            if not m:
                sys.exit("Portál vrátil neočekávanou odpověď (změnil se?). Hledej na www.cintoriny.sk v prohlížeči.")
            celkem = int(m.group(1))
        # projdi stránku po pořadí: záhlaví obce a hřbitova, pak lidé v něm
        for m in re.finditer(r"<div>Obec/mesto:\s*([^<]*)</div>|Cintorín:\s*<a data-cemetery-id=\"(\d+)\">([^<]*)</a>"
                             r"|<a data-grave-id=\"(\d+)\" data-deceased-id=\"\d+\">(.*?)</a></div>((?:<div[^>]*>[^<]*</div>){0,3})",
                             h, re.S):
            if m.group(1) is not None:
                obec = text(m.group(1))
            elif m.group(2):
                hrbitovy[m.group(2)] = (text(m.group(3)), obec)
            else:
                hid, jmeno = m.group(4), text(m.group(5))
                bunky = [text(x) for x in re.findall(r"<div[^>]*>(.*?)</div>", m.group(6), re.S)]
                bunky += [""] * (3 - len(bunky))
                cid = str(int(hid) // 1_000_000)     # ID hrobu začíná ID hřbitova (68002334 -> 68)
                nazev, o = hrbitovy.get(cid, ("?", None))
                narozen, zemrel = bunky[0].lstrip("* ").strip(), bunky[1].lstrip("† ").strip()
                print(f"{jmeno} | * {narozen} | † {zemrel} | {bunky[2]} | {nazev}{f' ({o})' if o else ''} | hrob {cid}:{hid}")
                n += 1
        m = re.search(r'<div class="more-rows"([^>]*)>', h)
        if not m:
            break
        a = dict(re.findall(r'data-([a-z-]+)="([^"]*)"', m.group(1)))
        dalsi = {"subsetFrom": a.get("from-id", ""), "shownSoFar": a.get("shown-so-far", "")}
    if not n:
        print("Nic nenalezeno (zkus kratší začátek příjmení, jiný tvar – Nováková / Novák – nebo bez obce).", file=sys.stderr)
    elif celkem and n < celkem:
        print(f"… celkem {celkem} záznamů, zobrazeno {n}; zúži hledání (--obec, --jmeno, roky) nebo přidej --stran", file=sys.stderr)


def _pole(h, nazev):
    m = re.search(rf'id="karta-{nazev}" value="([^"]*)"', h)
    return html.unescape(m.group(1)).strip() if m else ""


def hrob(arg, foto=None):
    m = re.fullmatch(r"(\d+):(\d+)", arg.strip())
    if m:
        cid, hid = m.groups()
    else:
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(arg).query)
        hid, cid = (q.get("hrobId") or [""])[0], (q.get("cintorinId") or [""])[0]
        if not (re.fullmatch(r"\d+", hid) and re.fullmatch(r"\d+", cid)):
            sys.exit("Zadej hřbitov:hrob z výpisu `hledat` (např. 68:68002334) nebo odkaz …index.php?hrobId=…&cintorinId=…")
    h = get("/api/htmlGetCard.php", {"cId": cid, "hId": hid})
    if "zosnuly-zoznam" not in h:
        sys.exit("Kartu hrobu se nepodařilo načíst (špatné ID, nebo se portál změnil).")
    hl = dict((k, text(v)) for k, v in re.findall(r'<div class="col[^"]*">(Sektor|Rad|Špecifikácia|Typ):\s*<span>(.*?)</span>', h))
    cislo = re.search(r'grave-numbers">.*?<span>Číslo:\s*</span>(.*?)</div>', h, re.S)
    print(f"Hrob {cid}:{hid} – sektor {hl.get('Sektor', '-')}, řada {hl.get('Rad', '-')}, číslo {text(cislo.group(1)) if cislo else '-'}"
          f" ({hl.get('Špecifikácia', '')}, {hl.get('Typ', '')})")
    stare = _pole(h, "hrob-starecislo")
    if stare:
        print(f"Dřívější číslo hrobu: {stare}")
    sprava = re.search(r'karta-sprava-cintorina">\s*<strong>[^<]*</strong>\s*<div class="comma-separated">(.*?)</div>', h, re.S)
    sprava = [text(x) for x in re.findall(r"<span>(.*?)</span>", sprava.group(1))] if sprava else []
    if any(sprava):
        print("Správa hřbitova: " + ", ".join(x for x in sprava if x))
    tb = re.search(r'<tbody id="zosnuly-zoznam">(.*?)</tbody>', h, re.S).group(1)
    lide = re.findall(r'data-deceased-id="(\d+)">(.*?)</span></td>(.*?)</tr>', tb, re.S)
    print(f"Uložení v hrobě ({len(lide)}):")
    for zid, prijmeni, zbytek in lide:
        b = [text(x) for x in re.findall(r"<td>(.*?)</td>", zbytek, re.S)]
        b += [""] * (7 - len(b))
        jmeno, titul, nar, umr, vek, ulozen, misto = b[:7]
        radek = f"- {' '.join(x for x in (titul, jmeno, text(prijmeni)) if x)} | * {nar or '?'} | † {umr or '?'} | {vek} r. | uložen {ulozen or '?'}"
        if misto:
            radek += f" ({misto})"
        d = get("/api/htmlGetDeceasedDetails.php", {"zId": zid})
        navic = [(t, _pole(d, f"zosnuly-{k}")) for t, k in (("rozená", "rodnepriezvisko"), ("místo narození", "miestonarodenia"),
                                                             ("místo úmrtí", "miestoumrtia"), ("způsob", "sposobulozenia"))]
        navic = [f"{t} {v}" for t, v in navic if v]
        print(radek + (" | " + ", ".join(navic) if navic else ""))
    if re.search(r'(?<!\d)01\.01\.\d{4}', tb):
        print("Pozor: datum 01.01. bývá zástupné (správa znala jen rok).")
    print(f"Odkaz: {BASE}/src/index.php?hrobId={hid}&cintorinId={cid}")
    if foto:
        if "getPhoto.php" not in h:
            print("Hrob nemá fotku.", file=sys.stderr)
            return
        b = get(f"/api/getPhoto.php?hId={hid}", binary=True)
        if not b.startswith(b"\xff\xd8"):
            print("Portál nevrátil fotku (JPEG).", file=sys.stderr)
            return
        _os.makedirs(_os.path.dirname(_os.path.abspath(foto)), exist_ok=True)
        with open(foto, "wb") as f:
            f.write(b)
        print(f"Fotka hrobu: {foto}")


def hrbitovy(obec):
    h = get("/api/htmlCemeteryQuickSearch.php", {"city": obec})
    r = re.findall(r'data-cemetery-id="(\d+)"[^>]*>(.*?)</li>', h, re.S)
    if not r:
        print("Žádný hřbitov nenalezen (zkus jiný tvar názvu obce; portál nemá všechny obce).", file=sys.stderr)
    for cid, nazev in r:
        print(f"{cid} | {text(nazev)}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 1 and a[0] == "hledat":
        pole, stran, i = {}, 2, 1
        while i < len(a):
            if a[i] == "--stran" and i + 1 < len(a) and a[i + 1].isdigit():
                stran = max(1, int(a[i + 1]))
            elif a[i] in POLE and i + 1 < len(a):
                k = POLE[a[i]]
                pole[k] = datum(a[i + 1], k.endswith("To")) if "Date" in k else a[i + 1].strip()
            else:
                sys.exit(__doc__)
            i += 2
        hledat(pole, stran)
    elif len(a) in (2, 4) and a[0] == "hrob" and (len(a) == 2 or a[2] == "--foto"):
        hrob(a[1], a[3] if len(a) == 4 else None)
    elif len(a) == 2 and a[0] == "hrbitovy" and a[1].strip():
        hrbitovy(a[1])
    else:
        sys.exit(__doc__)
