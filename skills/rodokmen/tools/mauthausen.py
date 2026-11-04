#!/usr/bin/env python3
"""Raum der Namen – zemřelí v koncentračním táboře Mauthausen a pobočkách (Gusen, Ebensee, Melk…), bez prohlížeče.

Použití (z kořene projektu):
  mauthausen.py hledat "text" [--stran N]
        -> příjmení nebo jméno (i „Novak 1905“); N stran po 20 osobách (výchozí 2).
           Výpis: jméno | roky | narozen (místo) | zemřel (místo) | odkaz na stránku osoby (s fotkami a životopisem, je-li)
Jen osoby, které v táboře zemřely; přeživší tu nejsou (hledej v `arolsen.py`). Jména bývají v místním tvaru (Novak, Nowak).
Údaje o obětech jsou citlivé – na web jen se souhlasem rodiny (soukromi.md).
"""
import html, re, sys, time, urllib.parse, urllib.request
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://raumdernamen.mauthausen-memorial.org/"


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


def hledat(dotaz, stran):
    q = urllib.parse.quote(dotaz)
    n, videno, celkem = 0, set(), None
    for p in range(1, stran + 1):
        page = get(f"{BASE}?txtFullSearch={q}&L=0&id=5&page={p}&count=20")   # strany portálu jsou číslované od 1
        celkem = re.search(r'([\d.\s\xa0]+) Personen', page)
        osoby = re.findall(r'<div class="entry">.*?<h1><a href="([^"]+)">(.*?)</a></h1>\s*(?:<p class="subtext">(.*?)</p>)?', page, re.S)
        osoby = [o for o in osoby if o[0] not in videno]
        videno |= {o[0] for o in osoby}
        for href, jm, sub in osoby:
            roky = re.search(r'<span class="years">(.*?)</span>', jm)
            jmeno = text(re.sub(r'<span class="years">.*?</span>', "", jm))
            radky = [text(x) for x in re.split(r"<br\s*/?>", sub) if text(x)]
            nar = next((r.replace("Geboren ", "") for r in radky if r.startswith("Geboren")), "-")
            zem = next((r.replace("Gestorben ", "") for r in radky if r.startswith("Gestorben")), "-")
            print(f"{jmeno} | {text(roky.group(1)) if roky else '-'} | nar. {nar} | zem. {zem} | {html.unescape(href)}")
            n += 1
        if not osoby:
            break
        time.sleep(0.7)
    if n == 0:
        print("Nic nenalezeno (zkus jiný pravopis nebo jen příjmení).", file=sys.stderr)
    elif celkem and n < int(re.sub(r"\D", "", celkem.group(1)) or 0):
        print(f"… celkem {celkem.group(1).strip()} osob, zobrazeno {n}; zúžit jde křestním jménem nebo rokem, víc dá --stran", file=sys.stderr)


if __name__ == "__main__":
    a = sys.argv[1:]
    stran = 2
    if "--stran" in a:
        i = a.index("--stran")
        if i + 1 >= len(a) or not (a[i + 1].isdigit() and int(a[i + 1]) >= 1):
            sys.exit("--stran chce kladné číslo.")
        stran = int(a[i + 1])
        del a[i:i + 2]
    if len(a) == 2 and a[0] == "hledat" and a[1].strip():
        hledat(a[1], stran)
    else:
        sys.exit(__doc__)
