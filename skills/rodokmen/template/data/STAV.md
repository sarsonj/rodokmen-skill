# Stav rodokmenu a pravidla práce

Tento soubor je vstupní bod. Po každém restartu (nová konverzace, zkrácený kontext) ho Claude čte jako první,
pak posledních pár řádků deníku (`tail -n 5 data/research_log.md | cut -c1-600`) a sekci „Rozpracováno“. Drž ho krátký:
starší body z „Rozpracováno“ patří do `historie_kol.md`, podrobnosti do deníku.

## Pro koho
- Výchozí osoba: (doplnit – jméno, rok a místo narození)
- Kdo s Claudem pracuje a jak chce komunikovat: (doplnit)

## Kde co je
| Soubor | Obsah |
|---|---|
| `data/osoby.py` | Přímí předci podle Kekulého čísla + rody, boční příbuzní, otevřené otázky, hypotézy. |
| `data/zaznamy.json` | Každý použitý zápis z matriky (klíč = název obrázku). |
| `data/svazky.json` | Matriční svazky (archiv, signatura, odkaz). |
| `data/prepisy.json` | Přepis originálu a český překlad každého zápisu. |
| `data/zvyrazneni.json` | Rámečky – které místo výřezu čteme. |
| `data/research_log.md` | Deník VŠECH hledání, i neúspěšných. Nečíst celý – hledat (`grep -i`). |
| `data/historie_kol.md` | Starší body z „Rozpracováno“ (nejnovější nahoře). Nečte se při startu. |
| `data/udaje_od_rodiny.md` | Co řekla rodina, rodinné dokumenty. |
| `data/zajimavosti.md`, `data/pribeh.md` | Texty na web. |
| `data/archivni_dotazy.md` | Co by šlo zjistit jen v archivu. |
| `data/mista.json`, `data/dokumenty.json`, `data/web.json` | Mapa, rodinné fotky a dokumenty, nastavení webu. |
| `vyrezy/`, `zdroje/` | Výřezy zápisů pro web (1800 px) a v plném rozlišení. |
| `dokumenty/` | Rodinné dokumenty a fotky od uživatele (originály). |
| `pracovni/` | Pracovní soubory (stažené stránky, kontrolní obrázky) – nejdou na web ani do gitu. |
| `kontext/` | Vytěžené souhrny a výstupy pomocníků (neověřené), na které se odkazuje z dat – v gitu. |
| `web/` | Rodinný web. `cd web && npm run nahled` (data + sestavení + náhled); po změně dat stačí `npm run data && npm run build`. |

## Pravidla
1. Než něco ohlásím jako nové, prohledám `osoby.py`, `zaznamy.json` a `research_log.md` (jméno, místo, rok).
2. Údaj je „doloženo“ (doc) jen tehdy, když jsem ho přečetl přímo na snímku. Čtení od pomocníků ověřím sám.
3. Každé hledání (i neúspěšné) zapíšu do `research_log.md`.
4. Nejistá čtení označím (?) – nic nedomýšlím.
5. Ke každému novému zápisu: výřez (`tools/vyrez.py`), rámeček (`tools/ramecek.py`) a přepis s překladem.
6. Po změně dat spustím `python3 -I tools/kontrola.py`.

## Rozpracováno (aktualizovat průběžně; nejvýš ~6 bodů po 2–3 větách, starší → `historie_kol.md`)
- (zatím nic)
