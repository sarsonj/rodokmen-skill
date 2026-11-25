# Snímkovač – rozšíření prohlížeče pro archivy, které nepouštějí nástroje

Rozšíření `SKILL_DIR/rozsireni/snimkovac/` (Chrome, Edge, Comet; Manifest V3) **pasivně uloží snímky, které si uživatel
sám zobrazí** v prohlížeči archivu, i s údaji o knize a snímku. Nic nestahuje navíc, nic neprochází samo, nic neposílá
na internet. Hodí se tam, kde archiv skripty blokuje (403, robots.txt, denní limit) a čtení by jinak skončilo
u „pošli mi snímek obrazovky“.

## Kdy ho nabídnout
- Brzda nebo archiv zastavily stahování (eBadatelna SOA Praha, SOA Třeboň, MZA, AHMP, Matricula – viz `portaly.md`).
- Uživatel bude listovat víc snímků a posílat snímky obrazovky by bylo zdlouhavé.
- Nabídni ho jednou větou; instalaci udělá uživatel sám (rozbalené rozšíření), Claude ji neprovádí.

## Instalace (pro uživatele)
1. Prohlížeč → Rozšíření → zapnout **Režim pro vývojáře** → **Načíst rozbalené** → vybrat složku
   `SKILL_DIR/rozsireni/snimkovac` (cestu mu napiš celou).
2. eBadatelna SOA Praha funguje hned. Jiný archiv: otevřít ho, kliknout na ikonu Snímkovače → **Ukládat na tomto webu**
   (u archivů s neověřenými pravidly zaškrtnout „Rozumím“), prohlížeč se jednou zeptá na oprávnění → obnovit stránku (F5).
3. Soubory se ukládají do `Stažené/rodokmen-snimky/<kniha>/<id>_<snímek>.jpg` + `.json` (rozšíření smí ukládat jen do
   složky Stažené; importér ji najde i přesunutou, např. `D:\Downloads`).

## Co umí na kterém archivu (ověřeno 14. 11. 2026)
| Archiv | Prohlížeč | Jak ukládá |
|---|---|---|
| eBadatelna SOA Praha | jeden obrázek | celý snímek hned po zobrazení |
| MZA Acta Publica | OpenSeadragon (dlaždice) | skládá stránku z dlaždic, které prohlížeč sám načetl |
| MZA ARON (lánové rejstříky, rektifikační akta) | OpenSeadragon přibalený v aplikaci (DeepZoom přes iipsrv) | od 0.18: bere dlaždice a popis `.dzi` z odpovědí, které stránka sama stáhla; přiblížení a výřez z kreslení dlaždic |
| SOA Třeboň | Zoomify ve vloženém rámu | vykreslený pohled s polohou na snímku, skládá stránku |
| AHMP Praha Publica | Zoomify, dlaždice z cizího serveru | snímek viditelné části záložky (obraz nejde přečíst) |
| Matricula | OpenLayers, celý obrázek | celý snímek v plném rozlišení (na snímku vydržet ~1,5 s) |

Jiný archiv: v okénku **Pokročilé → Pro ladění → Analyzovat stránku** uloží popis prohlížeče a robots.txt do
`rodokmen-snimky/_analyza/` – podle něj jde rozšíření rozšířit.

## Jak s ním pracovat
- **Dej uživateli přímý odkaz** na snímek (trvalý odkaz z `portaly.md`) a řekni, co hledáš a jaký **cíl** zvolit v panelu
  na stránce: **Přehled** (jména čitelná – hledání), **Čtení** (běžné čtení), **Záznam** (zápis, který se bude přepisovat;
  ostré i drobné písmo). Výchozí hranice 25 / 50 / 75 % plného rozlišení.
- U dlaždicových prohlížečů panel ukazuje mapu pokrytí a mřížku; **Další pole ▸** přiblíží na nehotové pole (jeden klik =
  jeden pohyb, tempo určuje člověk). Na novém webu se úroveň nejdřív **kalibruje**: uživatel přibližuje, dokud místo
  nezezelená, hodnota se pro web zamkne.
- Po návratu načti snímky: `python3 -I tools/snimky_import.py [složka] [--nahled]` – uloží je do mezipaměti
  (`tools/cache.py`, klíče `ebadatelna/…`, `osd/<web>/<id>/snNNNN.jpg`, `matricula/<diecéze>/<farnost>/<signatura>/…`)
  a zapíše do rejstříku snímků (pokud projekt má `tools/snimky.py`), zpracované přesune do `_importovano/`.
  Pak čti z mezipaměti jako obvykle (`vyrez.py`, pomocníci); archiv už nezatěžuješ.
- `.json` u snímku říká, jak vznikl: `skala` (podíl plného rozlišení), `pokryti` (kolik stránky v přehledu/čtení/záznamu).
  Bílá místa = to, co uživatel nezobrazil – požádej o doplnění, nedomýšlej.

## Pasti
- **Číslo snímku:** SOA Třeboň ukazuje „Snímek N“, trvalá adresa je `/<kniha>/N+1`; rozšíření ukládá číslo z prohlížeče.
- **AHMP** otevírá snímek přiblížený vpravo dole; rozšíření nastaví celou stránku. Fotí jen **aktivní záložku**; bez
  trvalého povolení „Povolit focení“ (Chrome se zeptá na přístup ke všem webům) je po každém načtení stránky potřeba
  kliknout na ikonu (Alt+S).
- **Škálování Windows / displeje s vyšší hustotou:** rozšíření měří skutečný detail obrazu, ne body obrazovky.
- **Matricula:** snímek, ze kterého uživatel odklikne dřív než za ~1,5 s, se neuloží (záměr – nebrzdit prohlížeč).
- **Pravidla:** stav archivů je v `rozsireni/snimkovac/weby.js` (povoleno / neověřeno / zakázáno). Snímky jen pro vlastní
  bádání; Matricula CC BY-NC-ND 2.0 (zveřejnit nekomerčně s odkazem), MZA zakazuje zveřejnění bez souhlasu.
- **Známá vada:** v SOA Třeboň mřížka na začátku chvíli skáče, než se ustálí.
