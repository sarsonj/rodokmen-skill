# Formát dat projektu

Všechna data jsou v `data/`. Web se z nich generuje (`npm run data`), nikdy needituj `web/src/data/site.json` ručně.
Po změnách spusť `python3 -I tools/kontrola.py`. Ukázku vyplněných dat má `SKILL_DIR/template/ukazka/`.
Položky do JSON souborů přidávej a měň přes `python3 -I tools/zapis.py` (zachová formát souboru, viz SKILL.md).

## `osoby.py` – předci
Kekulého čísla: 1 = výchozí osoba, otec osoby n = 2n, matka = 2n+1.
| číslo | kdo |
|---|---|
| 1 | výchozí osoba (u ženy `sex="F"`) |
| 2, 3 | otec, matka |
| 4–7 | prarodiče (4, 5 otcovi rodiče; 6, 7 matčini) |
| 8–15 | pradědečci a prababičky = **8 rodů** (`LINES`) |
| 16–31, 32–63 … | každá další generace dvojnásobek |

Otec předka 22 je 44, matka 45; dítě předka 45 je 22 (45 // 2). Muži mají sudá čísla.

```python
P = {
 8: dict(n="Jan Novák", y="1890–1944", st="doc",
         f=["* 14. 2. 1890 Holice čp. 112", "kovář", "× 20. 6. 1919 Holice Josefa Pokorná", "† 1944 Holice"],
         r=["holice_krest_jan_novak_1890", "holice_snatek_jan_novak_josefa_pokorna_1919"],
         note="Proč nejistota / rozpor / odkud údaj"),
 9: dict(n="Josefa Pokorná", y="* 1895", st="doc", f=[...], r=[...]),
 33: dict(n="otec neuveden", st="unk", f=[], note="Nemanželský syn; otec v matrice není."),
}
```
- `n` jméno (ženy rodným příjmením), `y` roky pro přehledy (`"* 1895"`, `"1890–1944"`, `"asi 1720–1785"`, `"1680 – před 1740"`,
  `"† 1940"` když známe jen úmrtí; nic nevíme → `""`).
- `f` fakta: začínají `*` (narození), `×` (sňatek), `†` (úmrtí) nebo jsou volný text (řemeslo, bydliště).
  Názvy obcí ve faktech používá mapa (`mista.json` → `re`).
  Sňatek jmenuje partnera (`× 1919 Holice Josefa Pokorná`); `kontrola.py` hlásí, když žádný sňatek nejmenuje osobu
  na sousedním čísle (manžel 2k, manželka 2k+1, i přes `SAME`). U `doc` hlásí `čp.`, které není v žádném citovaném
  zápisu (`shrnuti`, přepis) jako číslo domu (`čp. 23`, `No 23`, `N. 23`, `[Dům] 23`, `z Ostřetína 23`; datum, věk ani
  číslo zápisu, strany či snímku neplatí); číslo převzaté odjinud označ ve faktu zdrojem: `* 1862 Ostřetín čp. 23 (podle stromu)`; za zdroj platí
  i pozemková kniha, kronika, kniha či literatura v závorce a citace matriky `(N … pag./str./sn. …)`.
- `ged`, `uid` – ID osoby v původním stromu (GEDCOM z MyHeritage…) a jeho `_UID`; doplňuje `ged_import.py`
  (`--osoby`, `--ged-id`) nebo `zapis.py ged`, ručně je neměň.
- `r` klíče zápisů ze `zaznamy.json`; přidávej je `python3 -I tools/zapis.py odkaz <číslo> <klíč> [<klíč> …]` (u `SIDE`
  místo čísla část jména) – nástroj zachová zbytek souboru a ověří, že zápis existuje. `st` viz `matriky.md`: `doc` přečteno v matrice, `prob` pravděpodobné,
  `fam` od rodiny (i strom, který si rodina vede sama, např. GEDCOM z jejího MyHeritage), `mh` cizí strom z internetu, `unk`.
- `LINES = {8: ("Novákové", "Kováři z Holic…"), …}` – jen čísla 8–15; název rodu = příjmení v množném čísle. Vyplň hned, jak znáš pradědečka nebo prababičku – bez LINES web neukáže rody a nepřijde rada k příběhu.
- `SIDE` – sourozenci a další příbuzní: `dict(k=<číslo předka>, n="Josef Novák (1865–1920)", t="text", r=[klíče])`.
- `ISSUES` – dvojice `("Otázka", "Vyřešeno: … / Hypotéza: … / Otevřené: …")` → stránka „Co hledáme“ (vyřešené se skryjí).
  Jde na web – nepiš sem citlivé věci (příčiny úmrtí, rodinné spory) bez souhlasu.
- `HYPOTEZY` – `dict(rod=8, nadpis="…", text="…", polozky=[("jméno", "text")], zaznamy=[klíče])` → stránka rodu.
- `SAME = {350: 140}` – předek, který je v rodokmenu dvakrát (alias → hlavní číslo; alias v `P` může mít `f=["TÁŽ OSOBA jako 140"]`).

## `zaznamy.json` – zápisy
```json
[{"klic": "holice_krest_jan_novak_1890", "svazek": "1a0b2337", "snimek": 57, "druh": "N",
  "datum": "14. 2. 1890", "nazev": "Křest Jana Nováka",
  "shrnuti": "Jan, syn Václava Nováka, kováře v Holicích čp. 112, a Barbory roz. Malé z Ostřetína.",
  "odkaz": "https://aron.vychodoceskearchivy.cz/apu/…/dao/…/file/…"}]
```
- `klic`: malá písmena bez diakritiky, `obec_druh_kdo_rok` (druh: krest, snatek, umrti, index, scitani…). Je to i název obrázku.
- `druh`: N, O, Z, I (index/rejstřík), S (sčítání), J (jiný pramen).
- `datum` jako v češtině („14. 2. 1890“, „3/1867“, „1797“) – web podle něj řadí.

## `svazky.json`
`{"1a0b2337": {"archiv": "SOA Zámrsk – Sbírka matrik…", "portal": "ARON", "svazek": "N Holice 1880–1900, sign. …",
"popis": "obce", "url": "odkaz na svazek"}}` – u ARON zapisuje `aron_img.py <apu> svazek`.

## `prepisy.json`
`{"<klic>": {"orig": "[Datum] 14. února 1890\n[Dům] 112\n[Otec] …", "cs": "Český překlad celou větou…"}}`
- `orig` věrný přepis po sloupcích, `[Název sloupce]` v hranatých závorkách, nejisté „(?)“, nečitelné „[…]“, zkratky ponechat.
- `cs` srozumitelný překlad pro rodinu; vysvětli staré pojmy (domkář, podruh).

## `zvyrazneni.json`
`{"<klic>": {"boxes": [[x0, y0, x1, y1]], "status": "ok", "note": ""}}` – zlomky šířky/výšky obrázku `vyrezy/<klic>.jpg`.
Zapisuje `ramecek.py`. Rámeček má obepnout celý čtený zápis (ne jen jméno).

## `mista.json`
`{"Holice": {"re": "Holic", "dotaz": "Holice, Česko", "lat": 50.066, "lon": 15.986}}` – `re` je regulární výraz hledaný
ve faktech osob (kmen slova, aby sedělo skloňování: „Holic“ najde Holice i v Holicích). Spravuje `mista.py`.
Pozor na kolize (Hradec Králové × Nový Hradec Králové – použij `(?<!Nový )Hradec`; krátká jména jako `\bBuku?\b`).
Hypotéza: `"hypoteza": true, "rod": 8`. Když OpenStreetMap obec nenajde („Žár“, malé osady), zkus třetí parametr – dotaz: `mista.py pridej "Žár" "Žár" "Žár, Zdíkov, okres Prachatice"`
nebo dotaz s větší obcí či okresem. U **víceznačných názvů** (Podolí, Dub, Lhota) vezme OpenStreetMap kteroukoli ves
(„Podolí, Česko“ = Podolí u Brna) – v posledním sloupci výpisu zkontroluj okres a dej dotaz se sousední obcí
(`mista.py pridej "Podolí" "Podol" "Podolí, Odlochovice"`). Místopis nejlíp zná rodina – když si nejsi jistý, zeptej se.
`mista.py` hledá jen sídla a pod seznamem upozorní, když našel něco jiného než obec (bar, ulici) nebo když je nový bod
víc než 50 km od všech ostatních míst projektu (nejspíš jiná obec stejného jména). Kontrola mapy (`kontrola.py`) u
předků bez obce vypíše v hranatých závorkách slova z faktů, která vypadají jako obec. Když je obec v `mista.json`,
jen ji výraz `re` nechytí ve skloňovaném tvaru („v Přesece“ × `Přesek`) – uprav výraz (`Přese?[kc]`).

## `dokumenty.json` – rodinné fotky a dokumenty na webu
`[{"img": "foto_svatba_1919", "popis": "Svatba Jana a Josefy, Holice 1919.", "osoby": [8, 9]}]` – `popis` je na webu
vidět jako popisek, vyplň ho (stejně jako `t` u bočních příbuzných).
Obrázek ulož přes `vyrez.py dokumenty/<sken>.jpg foto_svatba_1919` (vznikne `vyrezy/` i `zdroje/`).

## `web.json` – nastavení webu
Viz `web.md`.

## Markdown poznámky
- `research_log.md` – tabulka `| # | datum | zdroj | rozsah | hledáno | výsledek | citace |`, nové řádky na konec, i negativní.
  Web ji zobrazuje jako „Výzkumný deník“.
- `zajimavosti.md` – `## Nadpis` + text, odkazy `[Jméno](/osoba/<slug>/)`.
- `pribeh.md` – „Příběh <hlavního rodu>“: frontmatter `title`, `lead` + kapitoly `##`; když soubor neexistuje,
  položka menu se skryje. Jak psát: `pribehy.md`.
- Poznámky pro Clauda v markdownu piš jako `<!-- … -->` – na web nejdou.
- `archivni_dotazy.md`, `udaje_od_rodiny.md` – volný text.

## Odkazy na osoby (slug)
Slug = jméno bez diakritiky + rok, např. `jan-novak-1890`; při kolizi přidá číslo osoby. Přesné slugy po `npm run data`
v `web/src/data/site.json` (`people`). Při přejmenování osoby se slug změní – oprav odkazy v textech.

## Import rodinného stromu (Fáze 1)
- **GEDCOM** (`.ged`, export z MyHeritage/Geni/FamilySearch): `python3 -I tools/ged_import.py dokumenty/strom.ged "Jméno Příjmení"`
  vypíše předky s čísly, všechny události a poznámky a **frontu zápisů** (nejmladší známá událost u každého předka,
  a jestli už je v archivu). `--osoby` dá kostru pro `osoby.py`. Poznámky ve stromu bývají plné rodinných historek –
  přečti je a vytěž do `udaje_od_rodiny.md`.
- **Vazba na původní strom** (pro pozdější sloučení s MyHeritage): kostra z `--osoby` má u každé osoby `ged="@I…@"`
  (ID ve stromu) a `uid` (`_UID`) – **nemaž je**, ani při úpravách osoby. Původní `.ged` nech v `dokumenty/` a do
  `data/STAV.md` zapiš jeho název a datum stažení. Projekt, který strom importoval dřív (bez `ged`):
  `python3 -I tools/ged_import.py dokumenty/strom.ged "Výchozí osoba" --ged-id` – stejné číslo = stejná osoba, nástroj
  ověří jméno (i příjmení po sňatku z „provd.“) a rok narození (±1). Shody zapiš přidáním `--zapsat`; neshody ukaž
  uživateli (jiná osoba ve stromu, nebo jen jiný pravopis?) a potvrzené zapiš `python3 -I tools/zapis.py ged <číslo> <@I…@> [<uid>]`.
  Nově zjištění předci `ged` nemají – to je v pořádku, při sloučení budou nové osoby (`kontrola.py` je vypíše jako informaci).
- Starší strom z **Brother's Keeper** (kódování ANSI a česká data „SRPEN 1945“ nástroj převede sám): místa tam bývají
  v 6. pádě („Táboře“) – do `osoby.py` je přepiš do 1. pádu. Kořenem takového stromu často nejsou uživatel, ale jeho
  děti (oba rody) – výchozí osobu proto vyber jménem.
- **Záloha stromu z MyHeritage** (ZIP se souborem `<strom>.ftb` a složkou `Photos/` – databáze, ne GEDCOM): rozbal do
  vlastní složky v `dokumenty/` (bývá velká – dej ji do `.gitignore`), pak
  `python3 -I tools/ftb_export.py <strom.ftb> dokumenty/strom.ged "Jméno Příjmení" <rok narození> pracovni/prima_linie.md <složka Photos>`.
  Vznikne GEDCOM pro `ged_import.py` (bez adres, e-mailů a telefonů) a přehled přímé linie s **původem údajů** – u každé
  osoby, ze kterých cizích stromů (Smart Match) či zdrojů její údaje přišly. Osoba bez cizí citace = `fam`, doložená jen
  cizími stromy = `mh`. V přehledu jsou i připojené skeny (opisy matrik, parte, domovské listy) – přečti je, bývají to
  nejcennější rodinné doklady.
- Údaje ze stromů (i Smart Match) jsou jen vodítko k zápisu – datum a číslo domu tě dovedou na stránku, ale **jména vždy
  ověř v zápisu** (skutečná chyba: „sňatek“ ze Smart Match byl jiný pár ze stejného domu).

## Export do GEDCOM
`python3 -I tools/ged_export.py` → `pracovni/rodokmen.zip`: `rodokmen.ged` (GEDCOM 5.5.1, UTF-8) a složka `media/`
s výřezy zápisů, rodinnými fotkami a portréty (dokument s „portrét“ v názvu a jednou osobou je její hlavní fotka). ZIP se **rozbalí** (`rodokmen.ged` a `media/` vedle sebe) a importuje
se `.ged` – obrázky si program načte podle relativních cest (Gramps ano, **Family Tree Builder ne**). **Pro import
rovnou použij `--slozka`**: nástroj zapíše rozbalenou složku `pracovni/rodokmen/` (s `--koren 3`
`pracovni/rodokmen_koren3/`), ZIP nevznikne a cesty k obrázkům jsou **absolutní** – Family Tree Builder je načte.
Složku před importem nepřesouvej (po přesunu export zopakuj). Výřez zápisu je v citaci u události a se `--slozka`
i přímo u osoby (FTB obrázky z citací zahodí – formulář citace pole pro obrázek nemá). Se `--slozka` je navíc
zdrojem jeden zápis (titul „zápis, svazek, snímek“, archiv svazku) s výřezem – FTB ho ukáže ve „Zdrojích fotografií“;
bez `--slozka` je zdrojem svazek. Soubor ve složce je UTF-8 s BOM a CRLF – bez BOM FTB špatně přečte cestu
s diakritikou a obrázky nenačte. Obrázky ve složce jsou v plném rozlišení ze `zdroje/` (jinak `vyrezy/`),
`--plne-rozliseni` je u `--slozka` zbytečné. Portrét je ve složce i osobní fotkou FTB (okénko osoby ve stromu):
dvojice `OBJE` s `_PRIM_CUTOUT`/`_CUTOUT`/`_PARENTRIN`, čísla fotek `MH:P500001…` a `RIN MH:I<číslo>` u osob; `_PHOTO_RIN` a `_FILESIZE` má každý obrázek (jinak je
FTB nenačte).
- **MyHeritage s obrázky:** jen přes desktopový **Family Tree Builder** (zdarma): export s `--slozka`, File → Import GEDCOM →
  `rodokmen.ged` z té složky (z ručně rozbaleného ZIPu FTB obrázky nenačte – „Failed to Load Image“) → nový projekt (nebo „Merge into project“), **FTB restartovat** (obrázky jsou vidět až po restartu), zkontrolovat fotky u osob, pak **Sync** – strom i obrázky
  se nahrají na web. Web MyHeritage přijímá jen `.ged` (ZIP odmítne) a obrázky z GEDCOM nenačte nikdy (soubor
  obsahuje jen odkazy na ně); nahrání jen `.ged` na web = strom bez obrázků, fotky pak jen ručně.
  Pro MyHeritage exportuj s **`--cp-v-miste`**: číslo popisné jde i do místa události („Holice čp. 112, okres …“),
  protože adresu (`ADDR`) u narození, sňatku a úmrtí MyHeritage nezobrazí (jeho vlastní stromy mají číslo domu
  v místě, např. „Obora č.21“). Každý dům je pak pro MyHeritage samostatné místo (rozpoznání místa a mapa ho
  mohou vynechat) – proto to není výchozí; bez volby je čp. jen v adrese (Gramps ji zobrazí).
- **Gramps:** importovat rozbalený `.ged`.
Volby: `--bez-obrazku` (jen `pracovni/rodokmen.ged`), `--plne-rozliseni` (i výřezy ze `zdroje/`), `--vystup <soubor>`,
`--koren <číslo>` (jen tato osoba a její předci, např. `--koren 3` = maminčina strana jako samostatný strom; čísla osob
zůstanou, aliasy `SAME` z jiné větve se přiberou i s předky; výchozí soubor `pracovni/rodokmen_koren3.zip`).
Existující soubor nástroj nepřepíše (jen s `--prepsat`), do `web/` nezapíše a hlídá příponu (`.zip`, s `--bez-obrazku` `.ged`).
U `--slozka` nahradí `--prepsat` jen `rodokmen.ged` a `media/`; složku s jinými soubory nepřepíše nikdy.
- Rodiny se odvozují z čísel (otec 2k, matka 2k+1), aliasy `SAME` jsou jedna osoba, zástupní rodiče („otec neuveden“)
  se nevyváží. Fakta se převádějí na události: `*`, `×` (sňatek v rodině), `†`; datum do tvaru GEDCOM (`asi` → ABT,
  `před` → BEF, `po` → AFT, `mezi … a …` → BET), obec podle `mista.json` (název z OpenStreetMap a souřadnice),
  `čp.` do adresy, závorky do poznámky. Ostatní fakta jsou povolání nebo poznámka. `SIDE` → poznámka u osoby,
  stav `st` → kvalita citací a poznámka „Původ údajů“. `LINES`, `ISSUES` a `HYPOTEZY` se nevyvážejí.
- Prameny: svazek = `SOUR` (archiv jako `REPO`), zápis = citace se snímkem, shrnutím, přepisem a výřezem. Zápis se cituje
  u události jen při shodě druhu a roku – křest syna v `r` otce není otcovo narození, ten se cituje u osoby.
- **Soukromí:** žijící (poznámka „Žijící…“, bez úmrtí a narození v posledních 100 letech) a zemřelí před méně než 30 lety
  zůstanou jen jako „Žijící osoba“, resp. „Chráněná osoba“ u zemřelých (vazby bez údajů, fotek a zápisů). U lidí z posledních ~100 let se vynechá poznámka
  a příčina úmrtí, boční příbuzní z té doby a dokumenty s chráněnou osobou také. Zápis, ve kterém je i chráněná osoba,
  jde bez obrázku a přepisu – souhrn ho vypíše ke kontrole. `udaje_od_rodiny.md` se nevyváží.
- **Před exportem se vždy zeptej, jestli má export obsahovat i žijící osoby** (a kam soubor půjde). Vysvětli rozdíl:
  bez nich jsou žijící a nedávno zemřelí jen „Žijící / Chráněná osoba“ (údaje si uživatel doplní ručně); s nimi (`--zijici`) jsou
  v souboru jejich jména, data, místa, poznámky i fotky. Nahráním do cizí služby (MyHeritage, Ancestry…) je dostane
  i ta služba – u vlastního stromu je MyHeritage ostatním skrývá, ale data u ní budou. Výchozí odpověď je „ne“;
  `--zijici` použij jen na výslovné „ano“ a připomeň souhlas dotčených (`soukromi.md`). Na web takový soubor nepatří.
  Když projekt leží ve složce synchronizované do cloudu (Google Disk, OneDrive, Dropbox), řekni, že soubor s žijícími
  dostane i ten cloud, a nabídni ho po nahrání smazat.
- Projdi s uživatelem souhrn na konci (chránění, vynechané, chybějící obrázky, data, která nešla převést) dřív, než
  soubor nahraje. Nahrání GEDCOM na web MyHeritage vytvoří **nový samostatný strom** (se stávajícím se nesloučí).

### Sloučení se stromem na MyHeritage (rozdílový export)
Když má uživatel vlastní strom na MyHeritage (stažený `dokumenty/strom.ged`) a chce do něj dostat, co skill zjistil,
**neposílej celý export** – vznikl by druhý strom nebo stovky duplicit. Postup:
Celé sloučení jde přes **Family Tree Builder** (FTB) synchronizovaný se stromem na MyHeritage – web MyHeritage
GEDCOM do existujícího stromu nesloučí a obrázky nenačte.
1. **Čerstvý GEDCOM z FTB:** uživatel ve FTB otevře synchronizovaný projekt (předtím Sync) → Soubor → Export GEDCOM
   → uloží do `dokumenty/` jako `strom_<datum>.ged` (ID a `_UID` jsou stejné jako v exportu z webu). Starší strom
   nezná osoby přidané mezitím (Smart Match) a vznikly by duplicity; nástroj na strom starší než týden upozorní.
   Vazba osob na strom (`ged` u osob, viz Import rodinného stromu): `ged_import.py dokumenty/strom.ged "Výchozí osoba"
   --ged-id --zapsat`; neshody projdi s uživatelem.
2. `python3 -I tools/ged_export.py --rozdil dokumenty/strom.ged --slozka --cp-v-miste` → `pracovni/rozdil/`
   (`rodokmen.ged` + `media/`) a **přehled `pracovni/rozdil_zmeny.md`**. V souboru jsou **nové osoby** (bez `ged`)
   a **kotvy** – osoby ze stromu, ke kterým se nové připojují (rodiče, dítě, partner); kotva má jméno (i `_MARNM`) a data
   převzatá ze stromu, aby ji FTB v Kontrole duplicit našel. Osoby ze stromu s novými zápisy a obrázky jsou jen
   v přehledu; s **`--se-zmenenymi`** jdou i do souboru (každá = jedno spojení navíc – nabídni podle počtu).
   Kotva má jméno a data ze stromu i u chráněné osoby – vrací jen to, co strom už má; z projektu u ní nic není.
3. **Projdi s uživatelem přehled před importem**, hlavně „POZOR“: nová osoba na místě, kde strom už někoho má
   (výzkum našel jiného předka → po importu rozhodnout ve FTB; tatáž osoba jinak zapsaná → `zapis.py ged <číslo> <@I…@>`
   a export zopakovat), a rozpory dat (strom × doložený zápis).
4. Uživatel ve FTB (předem Soubor → Záloha): Import GEDCOM → **Merge into project** do synchronizovaného projektu →
   restart FTB → spojit kotvy podle přehledu: přehled uvádí **dvojice ID** (importovaná osoba dostane ve FTB ID podle
   pořadí v souboru 1, 2, 3…, originál má ID ze stromu 500…). Nástroje → Kontrola duplicit se sníženou citlivostí
   (~40 %) najde většinu kotev (ověřeno 8 z 10) – spojovat jen dvojice z přehledu, ostatní nálezy ne (u nových osob
   s upozorněním „nespojujte“). Kotvy, které kontrola nenajde, spoj ručně (importovanou kotvu poznáš podle nových
   rodičů nebo dětí z přehledu, originál je nemá) → Sync.
   FTB při importu nic sám nespojí (ověřeno: ani podle `_UID`), spojení kotev je vždy ruční.
5. Po Sync znovu Export GEDCOM z FTB do `dokumenty/` (`strom_<datum>.ged`), znovu `--ged-id --zapsat` (nové osoby dostanou `ged`)
   a do `data/STAV.md` zapsat, který strom platí. Bez toho by se příště tvářily jako nové.
