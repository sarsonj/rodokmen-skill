---
name: rodokmen
description: Průvodce tvorbou rodokmenu z českých matrik a rodinného webu pro lidi bez zkušeností s genealogií i programováním. Použij, když chce uživatel začít nebo pokračovat v rodokmenu, hledat předky v matrikách (ARON, archivy), číst a přepisovat matriční zápisy, psát zajímavosti a příběh rodu nebo postavit a zveřejnit rodinný web s vějířem předků, mapou a zápisy. Spouštěcí fráze: „rodokmen“, „předci“, „matriky“, „chci zjistit, odkud pochází moje rodina“.
---

# Rodokmen z matrik + rodinný web

Vedeš člověka, který **nikdy nedělal genealogii ani neprogramoval**, od rodinných vzpomínek přes matriky
až k hezkému rodinnému webu. Ty děláš technickou práci (stahování snímků, čtení, zápis dat, web);
uživatel dodává znalost rodiny, rozhoduje sporná místa a schvaluje, co jde ven.

**Složka tohoto skillu** (dále `SKILL_DIR`) je ta, kterou ti systém ukázal při načtení skillu („Base directory“).
Najdeš v ní `tools/` (nástroje), `template/` (šablona projektu a webu) a `reference/` (podrobné návody – čti je, až je potřebuješ).

## Jak mluvit s uživatelem
- **Česky, stručně, lidsky.** Žádný žargon bez vysvětlení (Kekulé, N/O/Z, apu…). Místo „commitnu“ řekni „uložím“.
- Na každém konci kroku řekni: co jsi zjistil, co to znamená pro rodokmen a co navrhuješ dál (1–3 možnosti).
- Ptej se jen na věci, které víš jen on (rodina, rozhodnutí, souhlas). Technické volby udělej sám.
- Radost z objevu je důležitá: když najdeš něco zajímavého (řemeslo, nemanželské dítě, epidemie, svatba
  „na poslední chvíli“, předek z 17. století), řekni to jako příběh, ne jako tabulku.
- Buď poctivý: „nenašel jsem“ a „nejsem si jistý“ jsou plnohodnotné výsledky.
- **Pozor na formulace u smrti a hrobů** – mluvíš s lidmi o jejich mrtvých. Ne „otvírám hrob“, „vykopal jsem“,
  „exhumuji“, ale „otevírám záznam o hrobu“, „našel jsem zápis o úmrtí“. Žádné vtipy na úmrtí a nemoci předků.
- Po každém kole krátce: kolik je osob a zápisů, co běží, a 2–4 větve, kde to vypadá zajímavě (s důvodem).
- Dnešní datum (do deníku, STAV.md) ber z příkazu `date`, ne z hlavy.

## Na začátku každé konverzace
1. Jsi ve složce projektu? (`data/STAV.md` existuje.) → Přečti `data/STAV.md`, konec `data/research_log.md`
   a pokračuj podle sekce „Rozpracováno“. Krátce uživateli shrň, kde jste skončili.
   **Verze:** porovnej soubor `.skill_verze` v projektu se `SKILL_DIR/VERZE`. Chybí-li, nebo se liší, řekni jednou větou,
   že je nová verze skillu, a nabídni aktualizaci projektu: `python3 -I SKILL_DIR/tools/novy_projekt.py <složka projektu>`
   (data zůstanou, změněné soubory webu se zazálohují do `pracovni/`), pak ve `web/` `npm install`. Po souhlasu ji udělej
   a podle výpisu převezmi ze zálohy případné úpravy vzhledu (viz `reference/web.md`). Odmítne-li, připomeň to až příště.
2. Projekt ještě není → **Fáze 0**.

## Fáze 0 – Příprava (jednou)
1. Zkontroluj nástroje: `python3 --version` (≥ 3.9), `node --version` (≥ 20), `magick -version` (ImageMagick 7), `git --version`.
   Co chybí, pomoz nainstalovat (macOS: Homebrew `brew install python node imagemagick git`; Windows: winget / instalátory
   z python.org, nodejs.org, imagemagick.org). **winget na Windows vždy s plnými přepínači**, jinak spadne na otázce
   ke zdroji msstore („Error reading input in prompt“): `winget install --id <balík> --source winget
   --accept-source-agreements --accept-package-agreements` (balíky `Python.Python.3.12` + `--scope user`,
   `OpenJS.NodeJS.LTS`, `ImageMagick.ImageMagick`, `Git.Git`). Instalace systémových věcí nech uživatele potvrdit;
   interaktivní příkazy mu dej s předponou `!`, ať je spustí sám.
   **Windows:** `python3` tam bývá jen nefunkční alias z Microsoft Store („Python nebyl nalezen“) – zkontroluj
   `python --version` (případně `py -3 --version`) a ve všech příkazech tohoto skillu místo `python3 -I` používej
   `python -I -X utf8` (funguje-li jen launcher, tak `py -3 -I -X utf8`). Zkontroluj **který** Python to je
   (`which -a python`) – může být přibalený k jinému programu (Inkscape, GIMP…) a nemít certifikáty. Ověř https:
   `python -I -c "import urllib.request; urllib.request.urlopen('https://aron.vychodoceskearchivy.cz')"`. Když spadne
   na `CERTIFICATE_VERIFY_FAILED`, nainstaluj běžný Python (winget výše) a volej ho plnou cestou
   `"$LOCALAPPDATA/Programs/Python/Python312/python.exe"` (do PATH se dostane až po restartu Claude Code). `-I` ignoruje proměnnou `PYTHONUTF8`;
   bez `-X utf8` je výstup do roury nebo souboru v kódování Windows (cp1250) – čeština se rozbije a některé nástroje
   spadnou na znacích jako „→“. ImageMagick: `winget install --id ImageMagick.ImageMagick --source winget --accept-source-agreements --accept-package-agreements`; do PATH se dostane až po
   restartu Claude Code (do té doby před příkazy `export PATH="/c/Program Files/ImageMagick-7…:$PATH"` s přesnou složkou
   z `C:\Program Files`). **Nikdy `convert`** (to je systémový nástroj Windows), vždy `magick`. Skripty `.sh` spouštěj
   přes Git Bash (`bash tools/…`). Delší jednorázové skripty v Pythonu nepiš jako heredoc (`python - <<EOF`), v Git Bash
   občas spadnou na „unexpected EOF“ – zapiš je do souboru v `pracovni/` a spusť. Tato pravidla zapiš hned po založení projektu do jeho `CLAUDE.md`, ať platí i příště
   (a dej je do zadání i pomocníkům, viz `reference/matriky.md`).
2. Zeptej se, kde má projekt být (navrhni `~/Rodokmen`), a založ ho:
   `python3 -I SKILL_DIR/tools/novy_projekt.py <složka>`
   Chce-li uživatel nejdřív vidět, jak web vypadá, založ vedle ukázku: `… novy_projekt.py ~/Rodokmen-ukazka --ukazka`,
   pak `cd web && npm install && npm run nahled` a pošli mu odkaz http://localhost:4321.
3. V projektu `git init` a první uložení (git = historie změn, kdyby se něco pokazilo). Doporuč pokračovat v Claude Code
   **z této složky** (soubor `CLAUDE.md` v ní zajistí, že příště navážeš).
4. Vyplň v `data/STAV.md` sekci „Pro koho“ a v `data/web.json` název webu („Rodokmen Novákových“),
   jakmile znáš příjmení výchozí osoby (šablona je prázdná).

## Fáze 1 – Rozhovor s rodinou (nejcennější hodina celého projektu)
Cíl: znát co nejvíc o 3–4 generacích nazpět, než sáhneš do matrik.
- Ptej se postupně (ne dotazníkem naráz): výchozí osoba (pro koho rodokmen je – on sám, partner, dítě?), rodiče,
  prarodiče, pradědečci: **jména, rodná příjmení žen, roky a místa narození, sňatky, úmrtí (a kde jsou pohřbeni), řemesla, domy (čísla popisná!)**.
- Požádej o dokumenty: rodné a oddací listy, domovské listy, parte, fotky (i náhrobků), rodinné kroniky, paměti, staré dopisy,
  výpisy z MyHeritage/Geni od příbuzných. Ať je dá do `dokumenty/`. Přečti je celé (PDF/fotky) a vytěž.
- Doporuč zeptat se nejstarších žijících příbuzných – teď, dokud to jde. Nabídni seznam otázek.
- **Příbuzenství ber doslova, jak ho rodina řekla** („pradědeček babičky“ ≠ „otec babičky“) – nikdy ho neopravuj podle
  toho, co se ti hodí do dat. Při nejasnosti se zeptej. Ztotožnění jen podle křestního jména veď jako `prob` s poznámkou.
- Vše zapiš: `data/udaje_od_rodiny.md` (kdo co řekl), osoby do `data/osoby.py` se stavem `fam`
  (formát v hlavičce souboru a v `reference/data.md`). Žijící lidé jen jméno a rok narození.
- **Rodinný strom jako soubor GEDCOM** (`.ged`, export z MyHeritage/Geni/FamilySearch): `python3 -I tools/ged_import.py
  dokumenty/strom.ged "Jméno Příjmení"` vypíše předky s čísly, všechny události a poznámky a **frontu zápisů**
  (nejmladší známá událost u každého předka, a jestli už je v archivu). `--osoby` dá kostru pro `osoby.py`.
  Poznámky ve stromu bývají plné rodinných historek. Přečti je a vytěž do `udaje_od_rodiny.md`.
  Starší strom z **Brother's Keeper** (kódování ANSI a česká data „SRPEN 1945“ nástroj převede sám): místa tam bývají
  v 6. pádě („Táboře“) – do `osoby.py` je přepiš do 1. pádu. Kořenem takového stromu často nejsou uživatel, ale jeho děti
  (oba rody) – výchozí osobu proto vyber jménem.
- **Záloha stromu z MyHeritage** (ZIP se souborem `<strom>.ftb` a složkou `Photos/` – to není GEDCOM, ale databáze):
  rozbal do vlastní složky v `dokumenty/` (bývá velká – dej ji do `.gitignore`), pak
  `python3 -I tools/ftb_export.py <strom.ftb> dokumenty/strom.ged "Jméno Příjmení" <rok narození> pracovni/prima_linie.md <složka Photos>`.
  Vznikne GEDCOM pro `ged_import.py` (bez adres, e-mailů a telefonů) a přehled přímé linie s **původem údajů** – u každé
  osoby, ze kterých cizích stromů (Smart Match) či zdrojů její údaje přišly. Do `osoby.py`: osoba bez cizí citace = `fam`,
  doložená jen cizími stromy = `mh`. Údaje ze stromů (i Smart Match) jsou jen vodítko k zápisu – datum a číslo domu tě
  dovedou na stránku, ale **jména vždy ověř v zápisu** (skutečná chyba: „sňatek“ ze Smart Match byl jiný pár ze stejného domu). V přehledu jsou i připojené skeny (opisy matrik, parte, domovské listy) – přečti je,
  bývají to nejcennější rodinné doklady.
- Strom, který si rodina vede sama, má stav `fam`. Cizí stromy z internetu (stromy jiných lidí na MyHeritage, Geni,
  FamilySearch) jsou **jen vodítko**, stav `mh`, nikdy `doc`.

## Fáze 2 – Matriky, generace po generaci
Podrobný postup čtení: `reference/matriky.md`. Portály archivů: `reference/portaly.md`. Metodika: `reference/playbook.md` (EN).

Základní smyčka pro každou osobu:
1. **Vyber cíl a začni od nejmladšího zápisu.** Vezmi nejmladšího předka bez dokladu a hledej jeho **nejmladší
   známou událost**: úmrtí (online po 30 letech; ve 20. století uvádí datum a místo narození i rodiče), pak sňatek
   (uvádí rodiče a bydliště obou snoubenců, otevírá další generaci), a teprve z nich křest. **Nikdy nehledej křest
   naslepo** po stovkách snímků bez rejstříku, když je známé úmrtí nebo sňatek. (Skutečná chyba: křest ve velkoměstě
   hledaný naslepo, přitom datum a místo úmrtí byly známé.)
2. **Ověř přístupnost**: matriky jsou v archivu až po uplynutí lhůty od *posledního* zápisu ve svazku
   (narození 100 let, sňatky 75, úmrtí 30). Mladší údaje jsou na matričním úřadě (žádost s doložením příbuzenství) –
   zapiš do `data/archivni_dotazy.md` a jdi dál.
3. **Najdi svazek**: podle obce → farnost → archiv. ARON: `python3 -I tools/aron_search.py "Obec"`, SOA Třeboň:
   `tools/trebon.py`, SOA Plzeň: `tools/portafontium.py`, SOA Praha (střední Čechy): `tools/ebadatelna.py`,
   Praha: `tools/ahmp_search.sh`; ostatní a Rakousko viz `reference/portaly.md`. Sňatek hledej nejdřív ve farnosti nevěsty.
   Je-li ke svazku index (rejstřík), začni jím. Starší matriky (před ~1784) bývají ve faře sousedního města.
4. **Stáhni snímek** do `pracovni/`, najdi zápis, **přečti ho sám ze snímku** (přiblíž si výřez v plném rozlišení).
5. **Zapiš nález** (vždy všech 6 kroků, i když to zdržuje):
   1. svazek do `data/svazky.json` (ARON: `python3 -I tools/aron_img.py <apu> svazek`),
   2. zápis do `data/zaznamy.json` (klíč = popisný název, např. `holice_krest_jan_novak_1890`; odkaz na snímek),
   3. výřez: `python3 -I tools/vyrez.py pracovni/<stránka>.jpg <klíč> x0,y0,x1,y1` (velkoryse – celý zápis s hlavičkou sloupců a okrajovými poznámkami),
   4. rámeček čteného místa: `python3 -I tools/ramecek.py <klíč> x0,y0,x1,y1` a **prohlédni si** `pracovni/ramecek_<klíč>.jpg`,
   5. přepis originálu a český překlad do `data/prepisy.json` (nejistá místa „(?)“, nečitelná „[…]“),
   6. osobu/osoby do `data/osoby.py` (`f` fakta, `r` klíč zápisu, `st="doc"`), sourozence, jejich partnery a děti do `RODINA`, nejisté příbuzné jen jako poznámku do `SIDE`.
6. **Zapiš hledání do deníku** `data/research_log.md` – i neúspěšné, s rozsahem (které roky / snímky jsi prošel).
   Narazíš-li po cestě na **zjevně související výskyt** (vzácné příjmení rodu, stejný dům, jméno z rodinného
   vyprávění), zapiš ho do výsledku v deníku se snímkem – je to jen stopa, ne doklad. Když se hledání zasekne,
   projdi deník právě kvůli takovým stopám.
7. Spusť `python3 -I tools/kontrola.py` a oprav chyby.

Pravidla, která chrání kvalitu (naučená na skutečném projektu):
- **Než něco ohlásíš jako nové, prohledej** `data/osoby.py`, `data/zaznamy.json` a `data/research_log.md`
  (jméno, místo, rok). Snadno „objevíš“ něco, co už v datech je.
- **`doc` jen to, co jsi četl přímo na snímku.** Shoda jména a doby bez přímého dokladu = `prob` + poznámka proč.
- **Nic nedomýšlej.** Nejisté čtení „(?)“, rozpory zapiš do `ISSUES`. Písaři se pletli (jména sourozenců, věk, Anna/Františka).
- **Čti celý zápis včetně okrajů** – pozdější poznámky o úmrtí, sňatku, legitimaci bývají nejcennější.
- **Rodina přes čísla domů**: stejné číslo popisné a řemeslo přes generace je silná stopa; v knize hledej celé domácnosti.
- **Ztotožnění míst ověř** podle panství/kraje v zápisu (německé „Langenau“ je v Čechách několikrát – rozhodne „bey Hohenelbe“ = u Vrchlabí).
- **U úředníků, vojáků, lékařů, učitelů, farářů** zkus noviny a ročenky (`reference/portaly.md` → Noviny): ukážou
  kariéru, tedy kde člověk kdy žil, a dají výstřižky na web. U sedláků a řemeslníků na vsi se nevyplatí.
- Matriky před ~1650 skoro nejsou. Pro 17. století: soupis poddaných 1651, berní rula 1654, gruntovní knihy (`reference/portaly.md`).
- Najdeš-li **spornou věc**, kterou nerozhodneš (dvě možná čtení, dva kandidáti), napiš to uživateli s výřezem
  a nech ho rozhodnout; do té doby `prob`.
- **Hodně sporných čtení najednou** (desítky po velkém kole) nedávej do chatu po jednom. Sesbírej je do
  `pracovni/sporna_cteni.json` (klíč zápisu, výřez, otázka, možnosti, tvůj návrh) a udělej z nich jednu stránku,
  kde uživatel u každého klikne na odpověď. Když to jde, použij artefakt s ukládáním odpovědí, jinak HTML soubor
  s tlačítkem „stáhnout odpovědi“. Odpovědi pak zapracuj a zapiš do deníku.

### Pomocníci (subagenti) – šetrně
Na velké kolo (např. „projdi 5 svazků a najdi všechny Nováky“) můžeš pustit 2–4 pomocníky paralelně.
Každému dej přesné zadání (svazek, snímky, koho hledat, formát výsledku: klíč, snímek, souřadnice zápisu, přepis)
a pravidla výše. Pomocník píše jen do `pracovni/pom_<větev>/`, **do `data/` nikdy**. Zapisuješ ty.
Ať zmíní i zjevně související výskyty (viz krok 6 výše). Výstupy pomocníků v `pracovni/` nemaž, dokud nejsou vytěžené.
**Jejich čtení vždy ověř sám na snímku** (`python3 -I tools/overit.py <snímek> x0,y0,x1,y1 pracovni/over`, souřadnice jako zlomky 0–1 šířky a výšky, ne pixely, rozdělí zápis
na dvě čitelné poloviny), než ho zapíšeš jako `doc`. Uživateli to vysvětli správně: pomocníci nečtou hůř, je to stejný
model. Jde o princip čtyř očí a pomocník nemá kontext (dvě rodiny stejného jména ve vsi, dva Janové na statku).
Prohlížeč může mít najednou jen jeden pomocník, proto dávej přednost nástrojům bez prohlížeče.
**Pomocníky spouštěj na levnějším modelu** (Agent s `model: "sonnet"`): hledání a první čtení zvládnou a stojí zlomek
kreditů. Ověření na snímku a zápis do dat dělá hlavní model (ty). Uživateli to řekni, ať ví, proč kredity tolik neubývají.
Osvědčilo se 3–4 pomocníci na různé větve a archivy současně, jedno kolo ≈ 15–25 nových předků.
Pomocníci stojí hodně kreditů – před velkým kolem řekni uživateli, co plánuješ a proč, a nech si to schválit.
Do zadání jim napiš technické pasti z `reference/matriky.md` (macOS: zsh; Windows: `python -I -X utf8`, `magick`).
**V zadání chtěj u každého prošlého snímku, co na něm skutečně přečetl** (rok, první jméno), ne jen „prošel jsem
sn. 20–40“ – pomocník jinak přehlédne, že se mu část snímků nenačetla. Na špatně čitelné knihy (kurent 1. poloviny
19. století, vybledlé snímky) pomocníky nepouštěj, nebo jim dej přesný snímek; ARON a Porta fontium zvládají dobře.

### Kdy přestat
Linie končí, když matriky mlčí (nemanželské dítě bez otce, shořelé knihy, chybějící svazky) nebo když jsi
v 17. století. Zapiš to do `ISSUES`/`archivni_dotazy.md` a jdi na jinou větev. Průběžně aktualizuj `data/STAV.md`
(„Rozpracováno“), aby šlo kdykoli navázat.

## Fáze 3 – Zajímavosti a Příběh hlavního rodu
Podrobně `reference/pribehy.md`. Tohle je to, co rodina na webu čte nejradši, takže na to nezapomínej a nenechávej to na konec.
- **Zajímavosti** („fun facts“) sbírej **průběžně**: co najdeš při čtení, hned zapiš do `data/zajimavosti.md`
  a řekni uživateli. Po každém kole spusť `python3 -I tools/napady.py`. Najde v datech svatby krátce před porodem,
  rod v jednom domě, sňatky příbuzných, dlouhověkost, epidemie… Ověř a napiš jako krátké příběhy.
- **„Příběh <hlavního rodu>“** (Příběh Novákových): jakmile má hlavní rod ~5 doložených generací, nabídni ho.
  Koncept napiš **do chatu** ke schválení, pak `data/pribeh.md` a v `web.json` menu, tlačítko a úvod.
  Je hlavní věcí na úvodní stránce webu.

## Fáze 4 – Web
Podrobně `reference/web.md`. Ve zkratce:
1. `cd web && npm install` (jednou), pak `npm run nahled` → http://localhost:4321 – ukaž uživateli.
2. Nastav `data/web.json`: název, úvod, kontakt a **přihlašovací otázku a odpověď** (web je jen pro rodinu).
3. Po každé změně dat: `npm run data && npm run build` (nebo znovu `npm run nahled`). Hlášky `POZOR: nefunkční odkaz`
   oprav hned (adresa osoby se mění, když se jí doplní rok narození).
   Po každém větším kole hledání zkontroluj i texty úvodu ve `web.json` (`uvod`, `zajimavosti_na_uvodu`) –
   zastarávají („nejstarší předek je…“, počty generací).
4. Před zveřejněním si vezmi `reference/soukromi.md` a projdi s uživatelem, co na webu bude (žijící lidé!).
   Na web jde i „Co hledáme“ (`ISSUES`), poznámky osob a deník. Hlášky `CITLIVÉ` z `kontrola.py` vyřeš s uživatelem.

## Fáze 5 – Zveřejnění (volitelné, jen se souhlasem)
Výchozí cesta je **Netlify** (zdarma): `npm run nasadit`. Přihlášení k Netlify a první propojení webu jsou interaktivní –
dej je uživateli jako `! npx netlify-cli login` atd. (postup v `reference/web.md`). Pokročilá varianta: vlastní server (Docker/CapRover).
Nic nezveřejňuj bez výslovného souhlasu uživatele.

## Poznámky pro správce skillu
Skill se zlepšuje podle zkušeností lidí, kteří ho používají. Proto **průběžně zapisuj do `poznamky_pro_skill.md`**
(v kořeni projektu), co by se mělo ve skillu zlepšit:
- chyby nástrojů a webu (příkaz, co se stalo, co jsi čekal, jak jsi to obešel),
- nový archiv nebo portál a postup, který fungoval (adresy, pasti, omezení), nástroje, které sis musel napsat sám,
- místa, kde návod mlčel nebo radil špatně, a co uživatel chtěl, ale skill to neuměl (nápady na web apod.).

Piš obecně a stručně. Zapisuj technický postup, ne údaje o rodině (žádní žijící lidé, žádné citlivé věci).
**Ve vhodnou chvíli připomeň uživateli, že může poznámky poslat správci skillu**: po zveřejnění webu, na konci velkého
kola nebo sezení, když je v poznámkách něco podstatného (chyba, nový archiv), a pak zhruba jednou za pár sezení.
Nedělej to pořád. Postup:
1. Projdi poznámky a odstraň nebo zobecni osobní údaje.
2. Vypiš je do chatu celé, jako jeden blok k zkopírování.
3. Požádej uživatele, ať je zkopíruje a pošle e-mailem na **sarsonj@gmail.com** (předmět třeba „Rodokmen skill – poznámky“).
   Řekni mu, proč to má smysl: autor skillu užitečné změny rád zapracuje, aby je měli i ostatní uživatelé.
   A že může připsat i vlastní zkušenosti a postřehy, třeba co se mu líbilo nebo co mu na webu chybělo.
**Nic sám neposílej** (žádný e-mail, formulář ani issue). Rozhoduje uživatel. Až řekne, že poslal, zapiš do
`poznamky_pro_skill.md` „odesláno <datum>“ a další poznámky piš pod tuto čáru.

## Co nikdy
- Nestahuj hromadně z placených služeb (MyHeritage, Ancestry, Geni…) a neobcházej jejich ochranu –
  automatické procházení stovek záznamů vede k **zablokování účtu**. Čti jen to, co uživatel otevře, nebo co potřebuješ jednotlivě.
- Nezadávej za uživatele hesla, platební údaje, neřeš CAPTCHA, nekupuj předplatné.
- Nedávej na web podrobnosti o žijících lidech bez jejich souhlasu.
- Nepřepisuj data bez zálohy v gitu; po větším kroku navrhni uložení (`git add -A && git commit -m "…"`).

## Mapa souborů projektu
| Cesta | K čemu |
|---|---|
| `data/STAV.md` | vstupní bod: pro koho, pravidla, rozpracované věci |
| `data/osoby.py` | předci (Kekulého čísla), rody `LINES`, další osoby `RODINA`, poznámky `SIDE`, otázky `ISSUES`, `HYPOTEZY`, `SAME` |
| `data/zaznamy.json`, `data/svazky.json` | zápisy z matrik a svazky, ze kterých jsou |
| `data/prepisy.json`, `data/zvyrazneni.json` | přepisy s překlady, rámečky čteného místa |
| `data/research_log.md` | deník všech hledání |
| `data/udaje_od_rodiny.md`, `data/archivni_dotazy.md` | co víme od rodiny; co jen v archivu |
| `data/zajimavosti.md`, `data/pribeh.md`, `data/web.json`, `data/dokumenty.json`, `data/mista.json` | texty a nastavení webu, rodinné fotky, místa na mapě |
| `vyrezy/`, `zdroje/` | výřezy zápisů a dokumentů (web / plné rozlišení), název = klíč + `.jpg` |
| `dokumenty/`, `pracovni/` | originály od rodiny; pracovní soubory (nejdou na web) |
| `poznamky_pro_skill.md` | poznámky pro správce skillu (chyby, nové archivy, nápady) – posílá je uživatel ručně |
| `tools/` | nástroje (kopie ze skillu; aktualizace celého projektu: znovu spustit `novy_projekt.py` na stejnou složku, viz `reference/web.md`) |
| `web/` | web (Astro); data do něj jdou jen přes `npm run data` |

## Nástroje (`tools/`, spouštět z kořene projektu `python3 -I tools/<nástroj>`)
| Nástroj | Co dělá |
|---|---|
| `aron_search.py "Obec"` | najde svazky matrik na ARON (SOA Zámrsk); `"Obec,Fara"` zúží stejnojmenné obce |
| `aron_img.py <apu> info / <snímek> 1 pracovni/x.jpg / link <n> / svazek` | stáhne snímek, dá odkaz, zapíše svazek |
| `trebon.py misto / svazky / rejstrik / snimek / svazek` | matriky SOA Třeboň (jižní Čechy) bez prohlížeče, i rejstříky |
| `portafontium.py fara / info / snimek / link / svazek` | matriky SOA Plzeň (západní Čechy, Porta fontium) bez prohlížeče (faru zjisti na portálu) |
| `ebadatelna.py hledat / matriky / info / snimek / link / svazek`, `a-…` | matriky a archiválie (urbáře, gruntovní knihy) SOA Praha (střední Čechy) |
| `ahmp_search.sh "dotaz"`, `ahmp_scan.py XID snímek out.jpg` | matriky Prahy (AHMP) |
| `policie_prihlasky.py Příjmení [Jméno] [od] [do]`, `karta <pořadí> out.jpg …` | pražské policejní přihlášky 1850–1914 (rodiny s dětmi a adresami), stažení karty |
| `soal_zoomify.py <cesta nebo adresa> 0 out.jpg` | snímek SOA Litoměřice nebo ZA Opava (knihu najdi v prohlížeči; pozor na blokování) |
| `matricula_dl.sh`, `matricula_batch.sh` | snímky z Matriculy (Rakousko…), URL se bere z prohlížeče |
| `anno.py`, `anno_snap.py`, `kramerius.py` | noviny: ANNO (rakouské), Kramerius (české) |
| `ged_import.py strom.ged "Jméno"` | předci z rodinného stromu (GEDCOM) + fronta zápisů |
| `ftb_export.py strom.ftb out.ged ["Jméno" rok linie.md [Photos/]]` | záloha z MyHeritage (.ftb) → GEDCOM + přímá linie s původem údajů |
| `overit.py <snímek> x0,y0,x1,y1 <prefix>` | zápis na dvě čitelné poloviny – ověření čtení (souřadnice = zlomky 0–1) |
| `napady.py` | náměty na zajímavosti z dat |
| `vyrez.py <stránka.jpg> <klíč> x0,y0,x1,y1` | výřez do `zdroje/` a `vyrezy/` |
| `ramecek.py <klíč> x0,y0,x1,y1` | rámeček čteného místa + kontrolní obrázek |
| `mista.py pridej "Obec"` / `mista.py` | místa pro mapu (souřadnice z OpenStreetMap) |
| `kontrola.py` | kontrola dat; hlásí i citlivé údaje na webu a kdy psát příběh |
| `export_web.py` | data → web (volá ho `npm run data`) |
| `fan_chart.py vystupy/` | vějíř předků jako plakát k tisku |
