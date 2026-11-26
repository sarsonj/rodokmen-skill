# Sčítání lidu (sčítací operáty 1857–1921)

Sčítací arch zachycuje **celou domácnost v jednom domě k jednomu dni**: jména, vztah k hlavě domácnosti, data a místa
narození, náboženství, povolání, domovskou obec. Matriky zapisují události, sčítání ukazuje, kdo spolu bydlel.

## Kdy sčítání použít
- **Narození, která ještě nejsou v archivu.** Kniha narozených se zveřejňuje až 100 let po *posledním* zápisu, takže
  děti narozené po ~1910 často online nejsou (`matriky.md` → Lhůty). Sčítání **1921** (a 1910) je ukáže s datem
  a místem narození – stačí znát dům. Pak teprve žádost na matriční úřad (`archivni_dotazy.md`) s přesným datem.
- **Složení rodiny a sourozenci** – celá domácnost naráz, včetně dětí, které v matrikách farnosti chybí (narozené
  jinde).
- **Odkud kdo přišel** – od 1869 rodiště (obec, okres, země) u každé osoby; 1921 i „od kdy bydlí v obci“.
- **Domovská obec** (domovská příslušnost) – kam člověk úředně patřil; vede k matrikám jinde.
- **Vztahy, které matriky neukážou** – tchyně, výměnkáři, bratři, podruzi a čeledíni v domě.
- **Kontrola věku a data narození.** Arch píše hlava domácnosti nebo komisař z paměti – data se často liší od matriky
  o rok i víc. **Matrika má přednost**; rozdíl zapiš do poznámky osoby, sčítání nedělá z osoby `doc` narození.

Vztah z archu (tchyně, bratr) je doklad, že spolu žili – příbuzenství ověř matrikou. Z tchyně se dá odvodit rodné
příjmení manželky (ale tchyně mohla být podruhé vdaná).

## Ročníky
| rok | rozhodný den | co v něm je |
|---|---|---|
| 1857 | 31. 10. | německé formuláře, **jen rok narození** |
| 1869 | 31. 12. | jméno, pohlaví, rok narození, náboženství, stav, povolání, **rodiště**, domovská příslušnost; MZA: i datum |
| 1880, 1890, 1900, 1910 | 31. 12. | jako 1869, datum a místo narození; formuláře česky nebo německy |
| 1921 | 15. 2. | 20 sloupců (viz vzor přepisu), i povolání k 16. 7. 1914 |
| 1930 a mladší | – | jen Národní archiv, online ne, na žádost |

Dochovanost záleží na obci: u obce bývá jen některý rok. Na Moravě jsou starší ročníky úplnější.

## Jak je sada uspořádaná
**Sada = obec × rok** (osada mívá vlastní sadu). Porta fontium ji dělí po domech (čísla popisná), Třeboň a MZA ji
mají jako jednu řadu snímků seřazenou po domech. U obce bývá **souhrn** (soupis obce s rozpisem čísel). U každého domu:
1. **sběrný arch domovní** – země, soudní okres, obec, čp., majitel domu, byty a počet osob v každém,
2. **sčítací arch** pro každý byt – osoby po řádcích, často na dvoustraně (vlevo osobní údaje, vpravo národnost,
   náboženství, povolání), na konci podpis hlavy domácnosti a komisaře.

**Červená čísla tužkou** přes sloupce jsou statistické kódy úřadu – nepřepisuj je. Datum narození bývá psané svisle
(při čtení výřez otoč o 90°). Sloupec „od kdy bydlí v obci“ komisaři často vyplnili datem narození i u přistěhovalých.

## Kde jsou online
Sčítací operáty uchovávají **okresní archivy (SOkA)** a hledají se podle **soudního okresu**, ne politického
(Neprochovy na Klatovsku → soudní okres **Plánice**). Soudní okres uvádí matriční zápis po 1870 („okres soudní: Plánice“)
nebo Wikipedie obce.

| archiv | portál | stav se skillem |
|---|---|---|
| SOA Plzeň a SOkA západních Čech | Porta fontium – `portafontium.eu/contents/census` | **ano – `portafontium.py scitani`** (níže) |
| MZA Brno (Morava) | `www.mza.cz/scitacioperaty/digisada/search` | **jen v prohlížeči** (níže), ověřeno |
| SOA Třeboň (jižní Čechy) | `digi.ceskearchivy.cz` – stránka obce → Sčítání lidu | **jen v prohlížeči** (brzda); **jmenné rejstříky napříč archivem** (níže) |
| SOA Litoměřice (severní Čechy) | Digitální badatelna `digi.soalitomerice.cz` → ikona **Operáty** | **sadu najít v prohlížeči, snímky `soal_zoomify.py`** (níže) |
| ZA Opava (sev. Morava, Slezsko) | Digitální badatelna `digi.archives.cz/da/` → ikona **Sčítání** | **jen v prohlížeči, Claude in Chrome** (podmínky archivu, níže) |
| SOA Zámrsk (východní Čechy) | ARON – jen katalog fondů, **bez snímků** | online ne → FamilySearch (okresy Hradec Králové, Náchod, Trutnov…) |
| SOA Praha (střední Čechy) | eBadatelna → Archiválie, typ **Sčítací operáty** (asi 260 sad, hlavně 1869) | **jen v prohlížeči** (brzda; níže) |
| AHMP (Praha) | Praga Publica (`portaly.md` → AHMP) | ve starém katalogu operáty nenalezeny (11/2026), v novém `digi.ahmp.cz` neověřeno → pražské policejní přihlášky 1850–1914 |
| více archivů | FamilySearch: „Czech Republic Censuses and Inhabitant Registers, 1800–1990“ (kolekce 1930345) | v prohlížeči, procházení po okresech (níže) |

Nevyzkoušený portál při prvním použití ověř a postup zapiš do `poznamky_pro_skill.md`. Placené databáze (Ancestry,
MyHeritage 1900–1921) jen zmiň.

### FamilySearch – kolekce 1930345
Ověřeno 11/2026 (bez přihlášení až po otevření snímku; zda se snímek bez účtu zobrazí, neověřeno – postup
s přihlášeným prohlížečem je v `portaly.md` → FamilySearch).
- `https://www.familysearch.org/search/collection/1930345` – jen asi 2 300 indexovaných záznamů, ale **4,9 milionu
  snímků** z okresů celé ČR (u kolekce je jako místo originálů uvedena MZA Brno). Hledání podle jména tu skoro
  nepomůže – **procházej snímky**: „Procházet všechny snímky“ → **okres** (~80, např. Hradec Králové, Náchod,
  Trutnov – východní Čechy, kde jsme v ARONu starší operáty zatím nenašli) → **obec** → **rok** → **archivní číslo**
  → snímky (adresa `ark:/61903/3:1:…` = trvalý odkaz).
- Kolekce nemusí mít všechny roky obce (Dolní Přím: jen 1869), další bývají ve **Katalogu** pod obcí
  („Czech Republic, <okres>, <obec>, census, 1869–1921“, filmy s ikonou fotoaparátu).
- Cookie lištu odmítni (jen nezbytné). Rozšíření Claude in Chrome na stránce snímku nemusí smět dělat snímky
  obrazovky – pak ať snímek uloží uživatel.

### Porta fontium – `tools/portafontium.py`
1. `python3 -I tools/portafontium.py scitani` – přehled: archiv | soudní okres | roky (32 okresů).
2. `python3 -I tools/portafontium.py scitani "Neprochovy" "Plánice"` – roky, ve kterých obec je:
   `1880 | Těchonice - Neprochovy (…) | 31 domů | 34439398 | souhrn 34439397 | soap-kt/okres-planice`.
   Sedí i na osadu vedenou pod jinou obcí a na německý název. Roky okresu, kde obec chybí, vypíše zvlášť.
   Bez okresu projde poslední rok všech okresů (asi 6 minut, stránky se uloží) – raději okres zjisti.
3. `python3 -I tools/portafontium.py domy 34427048` – čísla popisná sady a id stránky domu; „1a“ nebo „8_0001_1“ = další
   část či arch téhož čísla. Na konci **tentýž dům v jiných letech** (id pro `domy` nebo `info`).
4. Dům jako kniha: `info <id>`, `snimek <id> <snímek> pracovni/scitani/<obec>_<rok>_cp<čp>_<snímek>.jpg [nahled] [výřez]`,
   `link <id> <snímek>`, `svazek <id>` (klíč `pf_<id>`, archiv podle kódu sady, např. SOkA Klatovy).
   Snímek 1 = sběrný arch domovní, další = sčítací archy.

### SOA Třeboň – jen v prohlížeči
Archiv skripty odmítá (brzda je zastaví) – vše v prohlížeči, tempo a pravidla jako u třeboňských matrik
(`portaly.md` → SOA Třeboň). Ověřeno 11/2026.
- **Hledání podle jména – začni jím.** Záložka HLEDÁNÍ → Typ: **Jmenné rejstříky** → Příjmení (případně Jméno,
  Lokalita) a **Typ materiálu: Sčítání lidu** → Hledat. Prohledá dobrovolnické rejstříky sčítání v celém archivu
  (i bez obce): u každé osoby rok, lokalita, osada, **číslo popisné a snímek**, náhled odkazuje na snímek.
  Rejstříky nemají všechny sady – negativní výsledek nic nedokazuje.
- **Sady obce:** `https://digi.ceskearchivy.cz/<Obec>` (jako u matrik; zkontroluj název a okres – portál přesměruje
  na stránku místa, v závorce je obec a okres) → vlevo **SČÍTÁNÍ LIDU** (adresa
  `…/<místo>/scitani-lidu`) → tabulky „Sčítání lidu: <obec> <rok>“ s inventárním číslem; osady mají vlastní sady.
  Ikona lupy otevře snímky v nové záložce `https://digi.ceskearchivy.cz/<sada>/<snímek>` (zároveň trvalý odkaz), název
  sady v tabulce otevře popis.
- **Sada = obec × rok v jedné řadě snímků** (menší obec 1921: kolem 90 snímků), ne po domech. Hlavička okna: archiv
  (SOkA), datace, soudní okres, inventární číslo. 1921 je na formuláři „Popisný arch“, 1857 „Aufnahmsbogen“.
- **Rejstřík sady:** záložka REJSTŘÍKY → Jmenný rejstřík po písmenech: příjmení, jméno, vyznání, lokalita,
  **číslo popisné**, rok; kliknutí na řádek otevře snímek (`…/<sada>/<snímek>`). Export TEXTOVÝ FORMÁT / XLSX je
  stažení souboru – jen se souhlasem uživatele. Na snímku vpravo panel „Index“ = osoby zapsané na tomto snímku.
- **Čtení a uložení:** prohlížeč je stejný jako u matrik (Zoomify v rámci `ram_obsah`, `Z.Viewport`) – úryvek
  z `portaly.md` (SOA Třeboň) přiblíží zápis a vrátí odkaz; snímek okna → `vyrez.py`. Svazek ručně
  (`zapis.py svazky`, klíč `trebon_<sada>`): archiv = SOkA z hlavičky, `svazek` = „Sčítání lidu <rok>, soudní okres
  <okres>, <obec>, inv. č. <číslo>“, `url` = `https://digi.ceskearchivy.cz/<sada>/1`.

### SOA Litoměřice – prohlížeč + `tools/soal_zoomify.py`
Stejná Digitální badatelna jako u matrik (`portaly.md` → SOA Litoměřice): vstupní ověření, **blokace aplikace po
25–100 rychlých krocích** (pauzy aspoň 3 s, žádné smyčky přes celou sadu). Ověřeno 11/2026 na Lužici (SOkA Teplice).
- **Hledání:** `https://digi.soalitomerice.cz/digitalnibadatelna/` (stará adresa VadeMeCum sem přesměruje) → ikona
  **Operáty** („Sčítací operáty“) → obec do pole **Místo / Lokalita** → **Enter v tom poli** (lupa nahoře po
  novém ověření filtry vymaže). Výsledek: „Lužice • čp.:1-74“, fond „NAD 1204 Sčítání lidu 1921 Teplice“,
  digitální sada, karton. Větší obce mají víc sad podle rozsahu čísel popisných; ve výsledcích bývají i „Přehledy
  sčítacích obvodů“ okresu. U Lužice byl online jen rok 1921 – další roky hledej stejně, mohou chybět.
- **Detail sady:** soudní okres (1930), územní rozsah, čísla popisná, počet snímků; „Pomocný pohled“ ukáže strom fondu
  se všemi obcemi okresu. Trvalý odkaz `https://digi.soalitomerice.cz/digitalnibadatelna/permalink?xid=<id>`
  (id = konec adresy `vysledekDetail/<id>`) – do `url` svazku.
- **Sada = jedna řada snímků po domech** (Lužice 1921: 173 snímků; snímek 1 štítek sady, pak u každého domu sběrný arch
  domovní a sčítací archy; formuláře česko-německé). Dům odhadni podle pořadí (čp. 8 = snímek 24–25) a ověř na
  sběrném archu.
- **Snímky:** adresy zjisti úryvkem z `portaly.md` (SOA Litoměřice) jen pro snímky, které čteš – u sčítání mají cestu
  `https://images.soalitomerice.cz/ximage/operaty/zoomify/cz/archives/CZ-<kód SOkA>/operaty/dao/images/<složka>/<uuid>.jpg`
  (SOkA Teplice = CZ-224106010). Stahuj `python3 -I tools/soal_zoomify.py "<celá adresa>" 2 pracovni/x.jpg`
  (2 = čtvrtina na orientaci, 0 = plné rozlišení na čtení); po jednom a jen snímky, které čteš.
- Svazek ručně (`zapis.py svazky`, klíč např. `soal_<id>`): archiv = „SOkA Teplice – Sčítání lidu 1921 Teplice
  (NAD 1204)“, `svazek` = „Sčítání lidu 1921, soudní okres Bílina, Lužice čp. 1–74, karton 33“, `url` = permalink.

### ZA Opava – jen v prohlížeči, Claude in Chrome
**Nejdřív si přečti `portaly.md` (ZA Opava) a drž se ho celého** – pro operáty platí totéž co pro matriky: **podmínky
archivu** (vysvětli je uživateli a nech rozhodnout jeho), prohlížeč Claude in Chrome, CAPTCHU řeší uživatel, žádný
`fetch` ani dávky, tempo a denní limit. Bez asistovaného prohlížení čte uživatel sám a posílá snímky obrazovky, nebo
zkus FamilySearch (níže). Hledání a uspořádání sad ověřeno 11/2026 na Štěpánkovicích (Hlučínsko).
- **Hledání:** ikona **Sčítání** → obec do pole **Místo / Lokalita** → Enter v tom poli. Pozor, formulář se po prvním
  hledání posune – zkontroluj, že obec není v poli „Číslo / Název arch. souboru“. Výsledek: „Štěpánkovice, série
  čp. 2-302…, 1921“, fond **NAD 158 Okresní úřad Hlučín** (inv. č., karton) – operáty bývají ve fondech okresních
  úřadů, ne v samostatném fondu. Velká obec = víc sérií podle čísel popisných.
- **Sada = jedna řada snímků** (Štěpánkovice 1921: 614); snímek 1 je list s metadaty digitalizace. Trvalý odkaz
  `https://digi.archives.cz/da/permalink?xid=<id>` (`portaly.md` → ZA Opava).
- **Čtení:** snímek obrazovky přiblíženého zápisu → `vyrez.py`; celý snímek volitelně z mezipaměti Chromu
  (`cache.py z-chromu`) – obojí postupem z `portaly.md` (ZA Opava; u sad sčítání zatím neověřeno). `soal_zoomify.py`
  ani jiné skripty nepoužívej, archiv je nepouští.
- Svazek ručně: archiv podle detailu sady (ikona „i“: archiv a fond, např. „Okresní úřad Hlučín (NAD 158), inv. č. 46“),
  `svazek` = „Sčítání lidu 1921, Štěpánkovice čp. 2–302“, `url` = permalink.

### SOA Praha – jen v prohlížeči
Archiv nástroj zakazuje (brzda) – vše v prohlížeči, tempo a ukládání snímků jako u archiválií v `portaly.md`
(SOA Praha). Ověřeno 11/2026.
- **Hledání:** `https://ebadatelna.soapraha.cz/pages/SearchArchivaliePage` → Typ archiválie **Sčítací operáty**,
  případně Lokality (našeptávač jako u matrik) → Vyhledat. Bez obce asi 260 sad (52 stran po 5) – stránky
  neprocházej, zadej obec. Řádek: „Sčítání lidu 1869: Okres Slaný - obec Bdín“, fond (okresní úřad), lokality, rok,
  počet snímků a odkaz `/pages/ArchivaliePage/archivalieId/<id>`; osady mají vlastní sady.
- Snímky `https://ebadatelna.soapraha.cz/a/<archivalieId>/<snímek>` (zároveň trvalý odkaz) – ulož je postupem pro
  archiválie (`cache.py uloz`, `ebadatelna.py a-snimek` z disku). Svazek klíč `ebad_a_<id>`.
- Pokrytí je malé (podle FamilySearch hlavně 1869, část 1880 a 1900) – když obec chybí, zkus FamilySearch.

### MZA Brno – jen v prohlížeči
Portál `https://www.mza.cz/scitacioperaty/digisada/search` (ne Acta Publica; brzda jiné adresy MZA skriptům nepustí,
žádné stahování ani skládání dlaždic). Hledej obec v poli „Město/obec nebo část obce/osada“ (Enter); výsledek
uvádí rok, rozsah a **rozpis čísel popisných** (chybějící domy), archiv (SOkA), fond (obvykle okresní úřad) a **kód
sady** (BV0124). Větší obec má v jednom roce víc sad podle čísel popisných – vyber sadu podle rozpisu. Ověřeno
11/2026 na Velkých Pavlovicích: 1857, 1869, 1880, 1910 (3 sady), 1921 (2 sady), 1890 a 1900 chybí. Detail `…/digisada/detail/<id>` má stejný prohlížeč `viewer` jako matriky
(`portaly.md` → MZA Brno: přiblížení, snímek obrazovky, limit snímků za den). Snímek 1 je soupis s metadaty
(rozpis čísel, poznámky typu „čp. 134 má 2 archy“), pak archy po domech. 1857 uvádí jen rok narození, 1869 a 1880
místo i datum.

### ARON (SOA Zámrsk) a AHMP – sčítání online nenalezeno
- **ARON:** ověřeno 11/2026 – fondy „Sčítací operáty“ (SOkA Náchod 1900–1910, SOkA Svitavy) jsou jen v katalogu,
  bez strukturovaného popisu a **bez snímků** (`aron_img.py <apu> info` → scans: 0); slovo „sčítání“ mají jinak hlavně
  operáty 1980 (SOkA Jičín). Pro východní Čechy použij **FamilySearch** (okresy Hradec Králové, Náchod, Trutnov,
  Pardubice, Jičín, Ústí nad Orlicí, Svitavy…), jinak dotaz na SOkA do `archivni_dotazy.md`.
- **AHMP:** ve starém katalogu Praga Publica digitalizované sčítací operáty nejsou (fulltext 11/2026). Starý katalog
  končí 30. 11. 2026, v novém (`digi.ahmp.cz`, pravidla v `portaly.md` → AHMP) to ověřené není – při prvním použití
  zjisti a zapiš do `poznamky_pro_skill.md`. Pro Prahu 1850–1914 jsou náhradou **policejní přihlášky** (Národní
  archiv, `policie_prihlasky.py`, `portaly.md`) – karta celé rodiny s daty a místy narození.

## Pasti
- **Soudní okres** místo politického; obec mohla v různých letech patřit pod jiný soudní okres.
- **Osada pod jinou obcí** (Neprochovy 1880 = „Těchonice – Neprochovy“) – hledej i pod obcí, kam osada patřila.
- **Chybějící rok nebo dům** = nedochováno nebo jinde; zapiš do deníku jako negativní výsledek s rozsahem.
- **Přečíslování domů** (zvlášť po 1900) – tentýž rod může být v jiném roce pod jiným čp.; „tentýž dům v jiných
  letech“ z `domy` vede podle portálu, ne podle rodiny.
- **Více bytů v domě** – rodina může být na druhém sčítacím archu téhož čp.
- **Data z paměti** – rok narození o 1–2 roky vedle, u starých lidí i o víc; rozpor s matrikou nezahlaď.

## Přepis, citace a zápis do dat
Postup je stejný jako u matriky (`SKILL.md`, Fáze 2, krok 5). Rozdíly:
- **Jeden zápis na sčítací arch (byt)**, druh `S`, klíč `<obec>_scitani_<hlava domácnosti>_<rok>`
  (`horni_lhota_scitani_jan_novak_1921`), `datum` = rozhodný den („15. 2. 1921“), `snimek` = snímek sčítacího archu,
  `odkaz` = `link` toho snímku. U Porta fontium svazek = dům (`portafontium.py svazek <id>`).
- **Výřez celé strany** (`vyrez.py` bez souřadnic nebo s celou tabulkou) a rámeček kolem všech řádků osob.
- **Klíč archu patří do `r` všech zapsaných osob z rodokmenu** (`zapis.py odkaz <číslo> <klíč>`), údaje do `f`
  („tkadlec v Horní Lhotě čp. 12 (1921)“). Ostatní členy domácnosti (sourozence, tchyni) jen do přepisu, případně do `SIDE`.
- `shrnuti`: kdo v domě žil a s jakými daty narození; rozpory s matrikou výslovně.

Vzor `orig` v `prepisy.json` (sčítání 1921, údaje smyšlené; jedna osoba = jeden řádek, sloupce v pořadí archu
oddělené „|“):
```
[Arch] Sčítací arch pro bytovou stranu: Novák Jan, tkadlec. Země: Čechy, soudní okres: Holice, obec: Horní Lhota, čp. 12, byt 1
[Sloupce] pořadí | příjmení | jméno | poměr k majiteli bytu | pohlaví | rodinný stav | narozen | rodiště a) obec,
  b) soudní okres, c) země | od kdy bydlí v obci | domovská příslušnost | národnost | náboženství | čtení a psaní |
  povolání: druh, postavení, závod | 16. 7. 1914: činný?, druh, postavení
[1] Novák | Jan | majitel bytu | mužské | ženatý | 3. března 1885 | a) Horní Lhota, b) Holice, c) Čechy | od narození |
  Horní Lhota, Holice, Čechy | česká | římsko-katolické | čte a píše | tkalcovství, samostatný živnostník | ano, tkalcovství
[2] Nováková | Anna | manželka | ženské | vdaná | 12. října 1887 | …
[Podpis] V Horní Lhotě dne 17. února 1921, Novák Jan; sčítací komisař […]
```
Sloupce 1921: 1 pořadí, 2 příjmení, 3 jméno, 4 poměr k majiteli bytu, 5 pohlaví, 6 rodinný stav, 7 den / měsíc / rok
narození, 8 rodiště, 9 od kdy bydlí v obci, 10 domovská příslušnost, 11 národnost (mateřský jazyk), 12 náboženství,
13 čtení a psaní, 14–16 povolání (druh, postavení, závod), 17–19 povolání 16. 7. 1914, 20 poznámka.
Starší ročníky přepisuj stejně podle hlavičky jejich archu.

`cs`: souvislý text pro rodinu („Při sčítání v únoru 1921 žil v domě čp. 12 tkadlec Jan Novák (* 3. 3. 1885)
s manželkou Annou…“), vysvětli staré pojmy (domkář, výměnkář, podruh, domovská obec).

Svazek u ostatních portálů ručně (`zapis.py svazky`): `archiv` = archiv a fond („SOkA Pardubice – sčítací operáty“),
`svazek` = „Sčítání lidu 1921, soudní okres Holice, Horní Lhota čp. 12“, `url` = stránka sady nebo domu.
