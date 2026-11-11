---
name: rodokmen
description: >-
  Průvodce tvorbou rodokmenu z českých matrik a rodinného webu pro lidi bez zkušeností s genealogií i programováním.
  Použij, když chce uživatel začít nebo pokračovat v rodokmenu, hledat předky v matrikách (ARON, archivy),
  číst a přepisovat matriční zápisy, psát zajímavosti a příběh rodu nebo postavit a zveřejnit rodinný web s vějířem předků,
  mapou a zápisy. Spouštěcí fráze: „rodokmen“, „předci“, „matriky“, „chci zjistit, odkud pochází moje rodina“.
---

# Rodokmen z matrik + rodinný web

Vedeš člověka, který **nikdy nedělal genealogii ani neprogramoval**, od rodinných vzpomínek přes matriky
až k hezkému rodinnému webu. Ty děláš technickou práci (stahování snímků, čtení, zápis dat, web);
uživatel dodává znalost rodiny, rozhoduje sporná místa a schvaluje, co jde ven.

**Složka tohoto skillu** (dále `SKILL_DIR`) je ta, kterou ti systém ukázal při načtení skillu („Base directory“).
Najdeš v ní `tools/` (nástroje), `template/` (šablona projektu a webu) a `reference/` (podrobné návody – čti je, až je potřebuješ):
`instalace.md` (příprava počítače, Windows), `matriky.md` (čtení matrik, pasti), `portaly.md` (archivy), `metodika.md`
(spojování záznamů, ztotožnění, mrtvé body, prameny mimo ČR), `data.md` (formát dat, import stromu), `pribehy.md`,
`web.md`, `soukromi.md`.

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
   **Verze:** spusť `python3 -I SKILL_DIR/tools/verze.py <složka projektu>` a řiď se posledním řádkem:
   - `NOVA_VERZE_SKILLU` → jednou větou řekni, že vyšla nová verze, a poraď, jak aktualizovat skill (vypíše jak);
     projekt aktualizuj až z nového skillu (po restartu), nikdy ne z klonu GitHubu. `PROJEKT_NOVEJSI` → jen poraď
     aktualizovat skill. `SKILL_NEZJISTEN` → spusť kontrolu znovu ze `SKILL_DIR`.
   - `AKTUALIZUJ_PROJEKT` → nabídni `python3 -I SKILL_DIR/tools/novy_projekt.py <složka projektu>` (data zůstanou,
     vlastní úpravy webu a `tools/` se sloučí s novou šablonou), pak ve `web/` `npm install`. Výpis projdi s uživatelem
     podle `reference/web.md` → Aktualizace staršího projektu. Odmítne-li, připomeň to až příště. Po aktualizaci ať
     uživatel restartuje Claude Code (změny v `.claude/settings.json` se jinak nemusí projevit). Hlásí-li výpis
     „Hlídač sítě: vypnutý“, zeptej se, jestli ho zapnout (`--hlidac`, vysvětlení v `reference/instalace.md`).
   - Hlídač sítě kontrolu zamítne (starší projekt) → spusť ji přes brzdu: `python3 -I tools/slusne.py SKILL_DIR/tools/verze.py <složka projektu>`.
2. Projekt ještě není → **Fáze 0**.

## Fáze 0 – Příprava (jednou)
**Než začneš, přečti `reference/instalace.md`** a postupuj podle něj: kontrola nástrojů (Python ≥ 3.9, Node ≥ 20, ImageMagick, git), certifikáty na
macOS, Windows, prohlížeč pro archivy, založení projektu (`python3 -I SKILL_DIR/tools/novy_projekt.py <složka>`,
volitelně `--ukazka` a `--hlidac`), `git init`, „Pro koho“ ve `STAV.md` a název webu.
**Windows:** ve všech příkazech skillu místo `python3 -I` piš `python -I -X utf8` (`python3` je tam nefunkční alias
a bez `-X utf8` se rozbije čeština), ImageMagick jen jako `magick`, nikdy `convert`.

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
- **Rodinný strom** (GEDCOM `.ged`, záloha MyHeritage `.ftb`): `tools/ged_import.py`, `tools/ftb_export.py` – postup
  v `reference/data.md` → Import rodinného stromu. Strom, který si rodina vede sama, má stav `fam`; cizí stromy
  z internetu (MyHeritage, Geni, FamilySearch, Smart Match) jsou **jen vodítko**, stav `mh`, nikdy `doc`.

## Fáze 2 – Matriky, generace po generaci
Podrobný postup čtení: `reference/matriky.md`. Archivy: `reference/portaly.md`. Sporná ztotožnění, mrtvé body,
prameny mimo ČR: `reference/metodika.md`.

Základní smyčka pro každou osobu:
1. **Vyber cíl a začni od nejmladšího zápisu.** Vezmi nejmladšího předka bez dokladu a hledej jeho **nejmladší
   známou událost**: úmrtí (ve 20. století uvádí datum a místo narození i rodiče), pak sňatek (rodiče a bydliště obou
   snoubenců), a teprve z nich křest. **Nikdy nehledej křest naslepo** po stovkách snímků bez rejstříku, když je známé
   úmrtí nebo sňatek. Není-li nejmladší událost online, začni nejmladším svazkem, který online je (křty sourozenců,
   sňatek rodičů, rejstříky), a chybějící zápis dej do `archivni_dotazy.md`.
2. **Ověř přístupnost**: matriky jsou v archivu až po uplynutí lhůty od *posledního* zápisu ve svazku (narození 100 let,
   sňatky 75, úmrtí 30; `matriky.md` → Lhůty). Mladší údaje jsou na matričním úřadě – zápis starší lhůty tam
   dostane kdokoli, mladší jen rodina (`matriky.md` → Lhůty); zapiš do `data/archivni_dotazy.md`.
3. **Najdi svazek**: podle obce → farnost → archiv. ARON: `python3 -I tools/aron_search.py "Obec"`, SOA Plzeň:
   `python3 -I tools/portafontium.py obec "Obec"`, Praha: `tools/ahmp_search.sh`; SOA Praha, MZA Brno a SOA Třeboň
   jen v prohlížeči, ostatní v `reference/portaly.md`. Sňatek hledej nejdřív ve farnosti nevěsty. Je-li ke svazku
   rejstřík, začni jím.
4. **Stáhni snímek** do `pracovni/<svazek>/` a nech ho tam – před dalším stažením se podívej, jestli ho už nemáš.
   Najdi zápis, **přečti ho sám ze snímku** (přiblíž si výřez v plném rozlišení).
5. **Zapiš nález** (vždy všech 6 kroků, i když to zdržuje):
   1. svazek do `data/svazky.json` (ARON: `python3 -I tools/aron_img.py <apu> svazek`, jinak `tools/zapis.py svazky`),
   2. zápis do `data/zaznamy.json` (klíč = popisný název, např. `holice_krest_jan_novak_1890`; odkaz na snímek) přes `tools/zapis.py`,
   3. výřez: `python3 -I tools/vyrez.py pracovni/<stránka>.jpg <klíč> x0,y0,x1,y1` (zlomky 0–1 stránky; velkoryse – celý zápis s hlavičkou sloupců a okrajovými poznámkami),
   4. rámeček čteného místa: `python3 -I tools/ramecek.py <klíč> x0,y0,x1,y1` (zlomky 0–1 **výřezu** `vyrezy/<klíč>.jpg`, ne stránky) a **prohlédni si** `pracovni/ramecek_<klíč>.jpg`,
   5. přepis originálu a český překlad do `data/prepisy.json` (nejistá místa „(?)“, nečitelná „[…]“),
   6. osobu/osoby do `data/osoby.py` (`f` fakta, `r` klíč zápisu, `st="doc"`), sourozence a kmotry-příbuzné do `SIDE`;
      klíč zápisu k existující osobě přidej `python3 -I tools/zapis.py odkaz <číslo osoby | část jména z SIDE> <klíč>`.
   Nová obec předků → `tools/mista.py pridej "Obec"` (mapa), nový pradědeček nebo prababička (8–15) → rod do `LINES`.
   Má-li projekt `tools/nalez.py`, udělej kroky 1–5 a řádek deníku jedním příkazem: `nalez.py nahled pracovni/x.json`
   (zkontroluje vstup a ukáže výřez a rámeček), pak `nalez.py zapis pracovni/x.json`.
6. **Zapiš hledání do deníku** `data/research_log.md` – i neúspěšné, s rozsahem (které roky / snímky jsi prošel).
   **Zjevně související výskyt** po cestě (vzácné příjmení rodu, stejný dům, jméno z rodinného vyprávění) zapiš do
   výsledku se snímkem – je to stopa, ne doklad. Když se hledání zasekne, projdi deník právě kvůli takovým stopám.
   Řádek přidávej `python3 -I tools/denik.py pridej --zdroj … --rozsah … --hledano … --vysledek …` (vezme další číslo,
   ohlídá sloupce, svislé čáry a prázdné řádky), **nikdy `printf >>` nebo `echo >>`** – rozbije tabulku a web ji pak neukáže.
7. Spusť `python3 -I tools/kontrola.py` a oprav chyby. `tools/kontrola_dat.py` (volá ho `kontrola.py`, nebo samostatně)
   hlídá obsahové chyby: roky v `y` × fakta, roky z cizího stromu u `doc`, kandidátní zápis citovaný jako doklad,
   zastaralé věty („neověřeno“, „křest se nečetl“) a ženich „ledig“ v přepisu × „vdovec“ ve faktech.

Pravidla, která chrání kvalitu:
- **Než něco ohlásíš jako nové, prohledej** `data/osoby.py`, `data/zaznamy.json` a `data/research_log.md`
  (jméno, místo, rok). Snadno „objevíš“ něco, co už v datech je.
- **Zápis do dat:** `zaznamy`, `svazky`, `prepisy`, `dokumenty` přes `python3 -I tools/zapis.py <soubor> <klíč> pracovni/x.json`
  (objekt napiš do `pracovni/x.json`, nástroj změní jen tu položku; `--sloucit` změní jen uvedená pole); odkaz na zápis u osoby v `osoby.py` přes
  `tools/zapis.py odkaz` (ohlídá uvozovky a čárky), ostatní úpravy `osoby.py` a markdown nástrojem pro úpravu souborů.
  Nikdy `sed -i` ani skript, který soubor přepíše celý – rozbije formát a v historii je pak změněný celý soubor.
- **`doc` jen to, co jsi četl přímo na snímku.** Shoda jména a doby bez přímého dokladu = `prob` + poznámka proč.
- **Nic nedomýšlej.** Nejisté čtení „(?)“, rozpory zapiš do `ISSUES`. Písaři se pletli (jména sourozenců, věk, Anna/Františka).
- **Čti celý zápis včetně okrajů** – pozdější poznámky o úmrtí, sňatku, legitimaci bývají nejcennější.
- **Rodina přes čísla domů**: stejné číslo popisné a řemeslo přes generace je silná stopa; v knize hledej celé domácnosti.
- **Ztotožnění míst ověř** podle panství/kraje v zápisu (německé „Langenau“ je v Čechách několikrát – rozhodne
  „bey Hohenelbe“ = u Vrchlabí).
- U úředníků, vojáků, lékařů, učitelů, farářů zkus noviny a ročenky (`portaly.md` → Noviny); pro 17. století soupis
  poddaných 1651, berní rulu a gruntovní knihy (`portaly.md` → Starší prameny) – matriky před ~1650 skoro nejsou.
- **Spornou věc**, kterou nerozhodneš (dvě čtení, dva kandidáti), ukaž uživateli s výřezem a nech ho rozhodnout; do té
  doby `prob`. Desítky sporných čtení po velkém kole nedávej do chatu po jednom: sesbírej je do
  `pracovni/sporna_cteni.json` (klíč zápisu, výřez, otázka, možnosti, tvůj návrh) a udělej jednu stránku, kde
  uživatel u každého klikne na odpověď (artefakt s ukládáním odpovědí, jinak HTML s tlačítkem „stáhnout odpovědi“).
  Odpovědi pak zapracuj do dat a zapiš do deníku.

### Šetrně k archivům – brzda `tools/slusne.py`
Archivy blokují IP adresu po sérii rychlých dotazů (MZA i celou síť na hodiny, ZA Opava na 30 minut). Blokaci
nezpůsobují nástroje, ale rychlé dočasné skripty a smyčky `curl`. Nástroje v `tools/` mají brzdu samy: společný limit
pro každý web pro všechny procesy na počítači.
- **Síť jen přes brzdu, i u pomocníků:** vlastní skript `python3 -I tools/slusne.py pracovni/x.py …`, curl
  `python3 -I tools/slusne.py curl …` (jedna adresa na příkaz), shellový skript `python3 -I tools/slusne.py bash pracovni/x.sh`.
  Přímé `curl`/`wget` má projekt zakázané (`.claude/settings.json`); i místní náhled webu zkoušej přes `slusne.py curl`.
- **Hláška „slusne: … je zastavený“ (kód 3)** = archiv dal najevo, že ho zatěžujeme (429/503/403, stránka
  „zablokováno“, spojení odmítnuto). Nezkoušej to znovu, neobcházej to (jiný nástroj, prohlížeč), řekni to uživateli
  a dělej jinou práci. Stav: `slusne.py stav`. `slusne.py odblokuj` jen když víš, že šlo o tvou chybu (špatná adresa).
- **Výpadky** (večer a v noci, údržba, prošlý certifikát): nástroj hlásí „neodpovídá“ a brzda po 3 neúspěšných
  spojeních za sebou web zastaví. Přepni na jiný archiv nebo práci. Kontrolu certifikátu nikdy nevypínej, na prošlý jen počkej.
- **V prohlížeči brzda neplatí, hlídáš se sám:** při cíleném hledání (konkrétní snímek, rejstřík) aspoň 5 s mezi
  stránkami, při listování stránku po stránce 10 s; má-li archiv v `portaly.md` vlastní tempo, platí to. Na jednom
  archivu jen jeden prohlížeč, žádní pomocníci, žádné souběžné dotazy (`Promise.all`) ani smyčky přes celé svazky.
  Postupná smyčka `fetch` jen pro snímky, které opravdu čteš, a jen tam, kde ji `portaly.md` u archivu uvádí.
- **Archiv může zablokovat i prohlížeč** (403 po stovkách snímků za den). Když se snímek nenačte nebo stránka hlásí
  chybu, podívej se do síťových požadavků prohlížeče. Při 403, 429 nebo 503 hned skonči, zapiš to brzdě
  (`python3 -I tools/slusne.py zastav <web> "HTTP 403 v prohlížeči"` – zastaví i skripty a pomocníky), řekni to
  uživateli a na tom archivu ten den už nepokračuj. Když nejde ani prohlížeč, ať uživatel snímek uloží sám do
  `pracovni/` a pošle adresu stránky (z ní je kniha a číslo snímku pro `odkaz`).
- **Na jeden archiv nejvýš jeden pomocník.** Víc projektů na jednom počítači má jednu IP adresu.
- **Mezipaměť obrázků:** co se stáhne přes brzdu, uloží se a příště se vezme z disku (`tools/cache.py`, společná pro
  všechny projekty; `cache.py stav` ukáže úsporu). Snímky eBadatelny ukládej z prohlížeče (`portaly.md`).

### Pomocníci (subagenti) – šetrně
Na velké kolo (např. „projdi 5 svazků a najdi všechny Nováky“) můžeš pustit 2–4 pomocníky paralelně, každého na
jinou větev nebo archiv (jedno kolo ≈ 15–25 nových předků). Stojí hodně kreditů – před velkým kolem řekni uživateli,
co plánuješ a proč, a nech si to schválit. **Spouštěj je na levnějším modelu** (Agent s `model: "sonnet"`):
hledání a první čtení zvládnou, ověření na snímku a zápis do dat děláš ty. Řekni to uživateli, ať ví, proč kredity
tolik neubývají.
- Přesné zadání: svazek, snímky, koho hledat, formát výsledku (klíč, snímek, souřadnice zápisu, přepis), technické
  pasti z `reference/matriky.md` a pravidla brzdy (síť jen přes `tools/slusne.py`, při hlášce „zastavený“ skončit
  a ohlásit). Ať u každého prošlého snímku napíše, co na něm skutečně přečetl (rok, první jméno), a zmíní i zjevně
  související výskyty.
- Pomocník píše jen do `pracovni/pom_<větev>/`, **do `data/` nikdy**. Zapisuješ ty; výstupy nemaž, dokud nejsou vytěžené.
- **Jejich čtení vždy ověř sám na snímku** (`python3 -I tools/overit.py <snímek> x0,y0,x1,y1 pracovni/over`, zlomky
  0–1, rozdělí zápis na dvě čitelné poloviny), než ho zapíšeš jako `doc`. Uživateli to vysvětli správně: je to stejný
  model, jde o princip čtyř očí – pomocník nemá kontext (dvě rodiny stejného jména ve vsi).
- Na špatně čitelné knihy (kurent 1. poloviny 19. století, vybledlé snímky) pomocníky nepouštěj, nebo jim dej přesný
  snímek; ARON a Porta fontium zvládají dobře. Prohlížeč může mít najednou jen jeden pomocník, proto dávej přednost
  nástrojům bez prohlížeče.
- Pomocníkovi dej **jednu úzkou stopu** (jedna kniha, jedna osoba). Široké zadání („4 stopy najednou“) nestihne – udělá jednu.
- **Kontrola vyšším modelem po každé větší větvi:** 1–2 pomocníci na nejsilnějším modelu (Agent s `model: "opus"`), každý
  na jednu skupinu větví, **jen čtení nad daty a výřezy, bez sítě**. Zadání: projdi osoby, zápisy, přepisy a výřezy a hledej
  chybná čtení, ztotožnění jen podle jména, roky bez dokladu, rozpory mezi zápisy. Při skutečném výzkumu tak našli dvě chybně
  přečtené kolonky „svobodný/vdovec“, přehozené rodiče a roky z MyHeritage vydávané za doložené. Opravy dělej ty, po ověření
  na výřezu. Zprávy pomocníků ukládej do složky, která je v gitu (např. `pomocne/`), ne do `pracovni/` – jinak je jiný počítač nevidí.

### Kdy přestat
Linie končí, když matriky mlčí (nemanželské dítě bez otce, shořelé knihy, chybějící svazky) nebo když jsi
v 17. století. Zapiš to do `ISSUES`/`archivni_dotazy.md` (náhradní prameny: `metodika.md` → Mrtvé body) a jdi na jinou
větev. Průběžně aktualizuj `data/STAV.md` („Rozpracováno“), aby šlo kdykoli navázat.

## Fáze 3 – Zajímavosti a Příběh hlavního rodu
Podrobně `reference/pribehy.md`. Tohle rodina na webu čte nejradši – nenechávej to na konec.
- **Zajímavosti** sbírej **průběžně** do `data/zajimavosti.md` a řekni je uživateli; po každém kole spusť
  `python3 -I tools/napady.py` (svatby krátce před porodem, rod v jednom domě, dlouhověkost, epidemie…), ověř a napiš.
- **„Příběh <hlavního rodu>“**: jakmile má hlavní rod ~5 doložených generací, nabídni ho. Koncept napiš **do chatu**
  ke schválení, pak `data/pribeh.md` a ve `web.json` menu, tlačítko a úvod.

## Fáze 4 – Web
Podrobně `reference/web.md`. Ve zkratce:
1. `cd web && npm install` (jednou), pak `npm run nahled` → http://localhost:4321 – ukaž uživateli. V cloudovém
   prostředí (claude.ai) localhost neuvidí – pošli mu snímky stránek nebo nasaď náhled.
2. Nastav `data/web.json`: název, úvod, kontakt a **přihlašovací otázku a odpověď** (web je jen pro rodinu).
3. Po každé změně dat: `npm run data && npm run build`. Hlášky `POZOR: nefunkční odkaz` oprav hned. Po větším kole
   zkontroluj i texty úvodu ve `web.json` (`uvod`, `zajimavosti_na_uvodu`) – zastarávají.
4. Před zveřejněním projdi s uživatelem `reference/soukromi.md` (co na webu bude, žijící lidé, hlášky `CITLIVÉ`
   z `kontrola.py`; schválené zapiš do `web.json` → `citlive_schvaleno`).

## Fáze 5 – Zveřejnění (volitelné, jen se souhlasem)
Výchozí je **Cloudflare** (zdarma, bez limitu nasazení): `npx -y wrangler@4 login`, název adresy do `web.json`
(`cloudflare.nazev`) a `npm run nasadit-cloudflare` – postup v `reference/web.md`. Kdo už má web na Netlify, pokračuje
`npm run nasadit`. Nic nezveřejňuj bez výslovného souhlasu uživatele. Po zveřejnění **nenasazuj po každém kole**
(Netlify zdarma vystačí asi na 20 nasazení měsíčně) – obnovuj jen náhled a nasazuj na pokyn nebo jednou na konci sezení.

## Poznámky pro správce skillu
Skill se zlepšuje podle zkušeností lidí, kteří ho používají. **Průběžně zapisuj do `poznamky_pro_skill.md`**
(v kořeni projektu) chyby nástrojů a webu (příkaz, co se stalo, jak jsi to obešel), nové archivy a postupy, které
fungovaly, místa, kde návod mlčel nebo radil špatně, a co uživatel chtěl, ale skill to neuměl. Piš obecně a stručně –
technický postup, ne údaje o rodině.
**Ve vhodnou chvíli** (po zveřejnění webu, na konci velkého kola, když je v poznámkách něco podstatného; ne pořád)
připomeň uživateli, že je může poslat správci skillu:
1. Projdi poznámky a odstraň nebo zobecni osobní údaje.
2. Vypiš je do chatu celé, jako jeden blok k zkopírování.
3. Požádej uživatele, ať je pošle e-mailem na **sarsonj@gmail.com** (předmět třeba „Rodokmen skill – poznámky“) –
   autor užitečné změny rád zapracuje, aby je měli i ostatní; může připsat i vlastní postřehy.
**Nic sám neposílej** (žádný e-mail, formulář ani issue). Až uživatel řekne, že poslal, zapiš do
`poznamky_pro_skill.md` „odesláno <datum>“ a další poznámky piš pod tuto čáru.

## Co nikdy
- Nestahuj hromadně z placených služeb (MyHeritage, Ancestry, Geni…) a neobcházej jejich ochranu –
  automatické procházení stovek záznamů vede k **zablokování účtu**. Čti jen to, co uživatel otevře, nebo co potřebuješ jednotlivě.
- Nezadávej za uživatele hesla, platební údaje, neřeš CAPTCHA, nekupuj předplatné.
- Neobcházej brzdu `tools/slusne.py` ani blokaci archivu.
- Nedávej na web podrobnosti o žijících lidech bez jejich souhlasu.
- Nepřepisuj data bez zálohy v gitu; po větším kroku navrhni uložení (`git add -A && git commit -m "…"`).

## Soubory projektu
`data/`: `STAV.md` (vstupní bod), `osoby.py` (předci, `LINES`, `SIDE`, `ISSUES`, `HYPOTEZY`, `SAME`), `zaznamy.json`,
`svazky.json`, `prepisy.json`, `zvyrazneni.json`, `research_log.md` (deník), `udaje_od_rodiny.md`, `archivni_dotazy.md`,
`zajimavosti.md`, `pribeh.md`, `web.json`, `dokumenty.json`, `mista.json` (formát `reference/data.md`). Dál `vyrezy/`
a `zdroje/` (výřezy pro web / plné rozlišení), `dokumenty/` (originály od rodiny), `pracovni/` (nejde na web),
`poznamky_pro_skill.md`, `tools/` (kopie ze skillu – aktualizuje se celý projekt přes `novy_projekt.py`), `web/`.

## Nástroje (`tools/`, z kořene projektu `python3 -I tools/<nástroj>`, skripty `.sh` přes `bash`; přepínače vypíše `--help`)
| Nástroj | K čemu |
|---|---|
| `aron_search.py`, `aron_img.py` | ARON (SOA Zámrsk): hledání svazků; snímek, trvalý odkaz, zápis svazku |
| `portafontium.py` | SOA Plzeň (Porta fontium) bez prohlížeče |
| `ebadatelna.py` | SOA Praha: trvalý odkaz, náhled a výřez ze snímku uloženého z prohlížeče (stahovat nesmí) |
| `ahmp_search.sh`, `ahmp_scan.py` | matriky Prahy (AHMP) |
| `policie_prihlasky.py` | pražské policejní přihlášky 1850–1914 |
| `soal_zoomify.py` | snímek SOA Litoměřice nebo ZA Opava (knihu najdi v prohlížeči) |
| `matricula_dl.sh`, `matricula_batch.sh` | snímky z Matriculy (Rakousko, Bavorsko, Polsko…) |
| `anno.py`, `anno_snap.py`, `kramerius.py` | noviny: ANNO (rakouské, `--ztraty` = seznamy ztrát 1914–1919), Kramerius (české) |
| `mapa_knihy.py` | mapa knihy po vsích a montáž sloupce jmen (`matriky.md`) |
| `cache.py` | sdílená mezipaměť snímků; uložení snímku z prohlížeče |
| `ged_import.py`, `ftb_export.py` | rodinný strom (GEDCOM, záloha MyHeritage) – `data.md` |
| `vyrez.py`, `ramecek.py`, `overit.py` | výřez zápisu (zlomky stránky), rámeček (zlomky výřezu, `--pozn` poznámka), ověření čtení na dvou polovinách |
| `zapis.py` | zápis do `data/*.json` a odkazů `r` v `osoby.py` beze změny formátu |
| `mista.py` | místa pro mapu (OpenStreetMap) |
| `napady.py` | náměty na zajímavosti z dat |
| `kontrola.py` | kontrola dat; hlásí i citlivé údaje na webu a kdy psát příběh |
| `kontrola_dat.py` | obsahové kontroly (y × fakta, cizí stromy u `doc`, kandidáti v `r`, zastaralé věty, ledig × vdovec) |
| `denik.py pridej --zdroj … --rozsah … --hledano … --vysledek … / dalsi / kontrola` | řádek deníku bez rozbití tabulky; kontrola sloupců, prázdných řádků a čísel |
| `nalez.py nahled\|zapis vstup.json` | zápis nálezu jedním příkazem: snímek, výřez, rámeček, zápis, přepis, osoby, deník, rejstřík snímků |
| `slusne.py` | brzda proti zablokování archivem (`stav`, `zastav`, `odblokuj`) |
| `export_web.py`, `fan_chart.py` | data → web (volá ho `npm run data`); vějíř jako plakát k tisku |
