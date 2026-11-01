# Co je nového

Změny ve skillu rodokmen, nejnovější verze nahoře. Každá verze má na GitHubu i
[vydání (Releases)](https://github.com/sarsonj/rodokmen-skill/releases) – kdo chce dostávat upozornění,
dá v repozitáři **Watch → Custom → Releases**.

Projekt založený starší verzí Claude sám nabídne aktualizovat (pozná to podle souboru `VERZE`).

## 0.6.0 – 2. 11. 2026

Brzda proti zablokování archivem.

**Nové**
- Brzda `tools/slusne.py`: společný limit dotazů pro každý archiv a všechny procesy na počítači
  (stránky 1 za 2 s, obrázky 10 za s). Když archiv dá najevo, že ho zatěžujeme, stahování se na 30 minut
  zastaví. Nástroje ji mají samy, vlastní skripty a `curl` se spouštějí přes ni (#45).
- Volitelný hlídač sítě (`novy_projekt.py --hlidac`): zamítne příkazy, které by šly na archiv mimo brzdu.
- Projekt má v `.claude/settings.json` zakázané přímé `curl` a `wget`.

**Opravy**
- Úvodní stránka webu s prázdným úvodem už nevypíše „0“.
- `kontrola.py`: žádné falešné poplachy u obce Petrovice nebo kontaktu „Petrovi“, zápisy z hypotéz
  se počítají jako citované, chybějící přihlašovací otázku hlídá až nasazení.
- Legenda vějíře neusekne popis rodu na „čp.“, „roz.“ a podobně.
- `novy_projekt.py --help` už nezaloží složku „--help“.

**Návody**
- SKILL.md: „Šetrně k archivům“ – síť jen přes brzdu, i u pomocníků, na jeden archiv nejvýš jeden pomocník.

Brzdu navrhl MarekLu (#45). Děkuji i všem, kdo poslali vlastní vyzkoušená řešení a zkušenosti s blokacemi.

## 0.5.0 – 24. 10. 2026

Zpětná vazba uživatelů (přes čtyřicet podnětů od šesti lidí).

**Nové**
- `zapis.py` – změní jednu položku dat a formát souboru nechá beze změny.
- `kontrola.py`: schválené citlivé zmínky (`citlive_schvaleno` ve `web.json`) a hranice 100 let.
- `mista.py` zkusí i sousední země.

**Opravy**
- Bezpečnost: otevřené přesměrování po přihlášení na webu.
- Konce řádků LF ve všech zápisech nástrojů.
- `soal_zoomify` bez `montage` (padal na ImageMagick 7.1.2), 4 vlákna, úklid dočasné složky.
- ImageMagick 6 (`convert`) mimo Windows.
- `vyrez` a `overit` odmítnou souřadnice v pixelech.
- `aron_search` při chybě opakuje dotaz.
- Mapa na webu přes celou šířku.

**Návody**
- ZA Opava (přepsáno), MZA Acta Publica, Geneteka API, rejstříky v Matricule.
- Druhopisy, roční výtahy, obce mezi farami, nejisté datum, chybějící nejmladší svazky.
- Přihlášení k Netlify v agentovi, oběti 2. světové války.

## 0.4.7 – 22. 10. 2026

**Opravy**
- Roky „– před 1888“ / „po 1921“ ve vějíři i na webu.
- `policie_prihlasky.py`: karta i pro pořadí nad 20.
- Konce řádků LF (`.gitattributes`, `novy_projekt` převede `.sh`).

**Návody**
- Příbuzenství doslova, datum sňatku ve křtu, špatný měsíc v oddacím zápisu, posun snímek–strana, Windows.

## 0.4.6 – 22. 10. 2026

**Opravy**
- UTF-8 výstup ve všech nástrojích (#11).
- Certifikát Porta fontium.
- `ged_import` čte Brother's Keeper (ANSI, česká data).
- `trebon`: hláška pro neznámá místa.

**Návody**
- winget, kontrola Pythonu, rejstřík místo chybějící matriky, pomocníci, Geneteka.

## 0.4.5 – 22. 10. 2026

**Opravy**
- `trebon.py`: místo bez diakritiky a mezer.
- `soal_zoomify` stahuje jen ze serverů archivů.
- `ramecek` ověří ImageMagick před zápisem.
- `.claude/launch.json` pro náhled webu v Claude desktop.

**Návody**
- Netlify Team protection, civilní matriky v Třeboni, posun stran v eBadatelně, víceznačné obce, heredoc ve Windows.

## 0.4.4 – 22. 10. 2026

**Opravy**
- Kontrola ImageMagicku před stahováním.
- `aron_search`: víc slov a řazení podle fary.
- Kontrola nefunkčních odkazů v textech webu.
- ZA Opava přes `soal_zoomify`.

**Návody**
- Rejstříky podle německého pravopisu.

## 0.4.3 – 21. 10. 2026

**Opravy**
- `overit.py` bere souřadnice jako zlomky.

**Návody**
- Rejstříky o pár stran vedle, evangelické a židovské matriky, údaje z cizích stromů ověřit jménem.

## 0.4.2 – 21. 10. 2026

**Nové**
- Claude sám nabídne aktualizaci projektu (verze skillu v `VERZE`, projekt si ji pamatuje v `.skill_verze`).
- Aktualizace projektu přepíše i změněné šablony webu (se zálohou do `pracovni/`); export odmítne starou šablonu přihlášení (#9).

**Opravy**
- `ftb_export`: vazby v rodinách jen na osoby, které jsou v exportu (#4).
- Porta fontium: odkaz spárovaný přímo se snímkem, kontrola výřezu, čekání po HTTP 429 a pauza mezi požadavky (#5).

## 0.4.1 – 21. 10. 2026

**Nové**
- Vedlejší nálezy se nezahazují (jedna věta v deníku).
- Hřbitovy jako doplňující otázka k úmrtí; formulace k hrobům bez návrhů na otevírání.
- FamilySearch: snímky filmů a limit 429.

**Bezpečnost** (podle externí analýzy)
- Nasazení bez přihlašovací otázky skončí chybou, v cookie jen otisk odpovědi.
- Escapování v mapě, v tooltipu mapy a v legendě vějíře.
- Cache ARON ve složce projektu, `novy_projekt` nepíše přes symlinky.

## 0.4.0 – 21. 10. 2026

**Nové**
- `portafontium.py` – matriky SOA Plzeň bez prohlížeče.
- `ebadatelna.py` – matriky a archiválie SOA Praha bez prohlížeče.
- `ftb_export.py` – záloha MyHeritage (`.ftb`) → GEDCOM a přehled přímé linie.
- Podpora Windows (Python bez `python3`, UTF-8, limit délky příkazu, Chrome/Edge).
- Bohatší ukázková rodina, licence MIT, upozornění v README, odkazy na genealogické společnosti, hlášení chyb přes issues.

**Opravy**
- `ged_import --osoby` escapuje jména (uvozovky ve jménu rozbily `osoby.py`).
- `vyrez.py` maže EXIF/GPS z fotek a otáčí je podle orientace.
- `fan_chart.py`: předek starší než 10. generace neshodí vějíř ani export webu.
- `ebadatelna.py`: stránkování u obcí s víc než 50 knihami; `portafontium.py`: název fary s diakritikou.

## 0.3.0 – 20. 10. 2026

- Oprava roků u neznámého narození.
- Policejní přihlášky, SOA Litoměřice.
- Pomocníci na modelu Sonnet, sporná čtení.

## 0.2.0 – 16. 10. 2026

Poučení z prvního ostrého projektu.

- Nové nástroje: `trebon.py`, `ahmp_*`, `matricula_*`, `anno*`, `kramerius.py`, `overit.py`, `ged_import.py`, `napady.py`.
- Metodika: začínat od nejmladšího zápisu, ověřování pomocníků, noviny u úředníků a vojáků.
- Zajímavosti průběžně a „Příběh rodu“ s konceptem ke schválení.
- `kontrola.py`: citlivé údaje z 20. století na webu.

## 0.1.0 – 16. 10. 2026

První verze: průvodce, nástroje, šablona webu a ukázka.
