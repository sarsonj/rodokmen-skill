# Rodokmen – skill pro Claude Code

![Rodokmen z matrik a rodinný web – vějíř předků, mapa a zajímavosti](docs/banner.jpg)

Claude vás provede tvorbou rodokmenu **od rodinných vzpomínek přes digitalizované matriky až k hezkému rodinnému webu**
s vějířem předků, mapou, příběhem rodu a výřezy původních zápisů s přepisem a překladem.
Je určený pro lidi, kteří genealogii nikdy nedělali a neprogramují – technickou práci dělá Claude, vy dodáváte
znalost rodiny a rozhodujete.

Vznikl při skutečném hledání předků jedné rodiny.

**Autor a správce:** Jindřich Šaršon ([sarsonj@gmail.com](mailto:sarsonj@gmail.com), [GitHub](https://github.com/sarsonj))

**Aktuální verze: 0.6.0 (listopad 2026).** Skill se průběžně vyvíjí – opravuji chyby a doplňuji postupy pro další archivy
podle toho, na co narazíte vy. Jak aktualizovat, najdete v části [Instalace](#instalace), seznam změn
v [historii repozitáře](https://github.com/sarsonj/rodokmen-skill/commits/main).

> **Než začnete**
>
> Tento skill **nenahrazuje genealoga** ani zkušeného badatele. Je to pomůcka, která umí rychle projít hodně matrik.
> Umělá inteligence ale dělá chyby: špatně přečte jméno, splete si dva Jany ze stejné vsi nebo spojí rodiny, které
> k sobě nepatří. Skill se tomu snaží bránit – u každého údaje je zdroj a výřez původního zápisu, údaje se navzájem
> kontrolují a nejisté věci jsou označené. Za správnost rodokmenu ale ručíte vy. Používáte ho na vlastní odpovědnost.
>
> Projekt vznikl i jako **test toho, kam současná AI dosáhne**. Chtěl jsem zkusit úkol, který je opravdu těžký:
> kurrent, latina, zkratky farářů, stejná jména a dlouhé řetězce závěrů. Výsledky mě překvapily, ale nejsou to
> výsledky profesionála.
>
> Kdo potřebuje rodokmen, na který se dá spolehnout (dědictví, publikace, sporné případy), nebo se zasekne na místě,
> kam matriky nestačí, ať se obrátí na genealoga. Začít můžete u
> [České genealogické a heraldické společnosti](https://www.genealogie.cz) (Praha a pobočky po Čechách) nebo
> u [Moravské genealogické a heraldické společnosti](https://www.mghs.cz) (Brno). Obě pořádají kurzy a přednášky
> a mají knihovnu. Rodokmen ze skillu, kde je u každého údaje zdroj a snímek, může genealogovi posloužit jako dobrý
> podklad.
>
> **Jste genealog nebo zkušený badatel?** Budu rád za kritiku. Když uvidíte chybu v postupu, ve čtení nebo v tom,
> co skill radí, [založte issue](https://github.com/sarsonj/rodokmen-skill/issues) nebo mi napište. Vaše zkušenost
> je přesně to, co AI chybí.

**Přečetla AI něco špatně, něco nefunguje nebo jste narazili na jiný problém?**
[Založte prosím issue na GitHubu →](https://github.com/sarsonj/rodokmen-skill/issues/new)
(víc v části [Zpětná vazba](#zpětná-vazba-a-vaše-zkušenosti)).

## Jak vypadá web
Ukázkový web s vymyšlenou rodinou Novákových (260 předků v 11 generacích) má na úvodní stránce příběh rodu, zajímavosti,
mapu, kde předci žili, osm rodů a vějíř předků. Další stránky: rodokmen po rodinách, karty osob, výřezy zápisů
s přepisem a překladem, „Co hledáme“ a deník hledání. **[Podívejte se na celou úvodní stránku ukázky →](docs/ukazka-web.png)**

## Co budete potřebovat
- **Claude Code** (aplikace pro Mac/Windows nebo příkazová řádka) a placené předplatné Claude. Rodokmen je
  dlouhá práce – počítejte s několika večery a s tím, že spotřebuje dost kreditů. Nejlevnější tarif **Pro bude
  nejspíš málo** (stačí na vyzkoušení), na celý rodokmen počítejte aspoň s nejnižším tarifem **Max**.
  Po dokončení můžete předplatné zase snížit nebo zrušit, web i data vám zůstanou.
- **Počítač s macOS nebo Windows** (obojí vyzkoušeno; Windows 11 s Pythonem z python.org a Git Bashem).
  Linux by měl fungovat, ale vyzkoušený není.
- Programy **Python 3, Node.js, ImageMagick a git**. Nemusíte je instalovat předem – Claude zkontroluje, co chybí,
  a pomůže s instalací (na Macu přes [Homebrew](https://brew.sh), na Windows přes winget).
- Volitelně účet na [Netlify](https://www.netlify.com) (zdarma), pokud chcete web zveřejnit pro rodinu.

## S jakými modely to vzniklo
AI se vyvíjí rychle a za pár měsíců může skill dávat lepší, nebo jen jiné výsledky. Proto je tu uvedeno, s čím byl
vyzkoušený.

- **Stav k listopadu 2026 (verze 0.6.0):** Claude Code s hlavním modelem **Claude Opus 5.5**. Pomocníci, kteří hledají
  a čtou matriky jako první, běží na **Claude Sonnet 5.5**. Každý jejich nález pak hlavní model ověřuje na snímku.
- Vyzkoušeno na několika skutečných rodokmenech (největší má 243 předků v 11 generacích a 192 matričních zápisů).
  Výsledek se porovnával s větví, kterou jsme léta dělali ručně.

S jiným nebo slabším modelem počítejte s víc chybami ve čtení starého písma.

## Instalace

### Varianta A – jako plugin (doporučeno)
V Claude Code napište:
```
/plugin marketplace add sarsonj/rodokmen-skill
/plugin install rodokmen@rodokmen-skill
```
Pak Claude Code restartujte (do běžící relace se nový plugin nenačte).
**Aktualizace.** Claude Code u pluginů od jiných autorů než Anthropic nové verze sám nehlídá. Máte dvě možnosti:
- **Automaticky (doporučuji):** jednou v `/plugin` na kartě **Marketplaces** vyberte `rodokmen-skill` a zapněte
  automatické aktualizace (Enable auto-update). Nová verze se pak stáhne při spuštění Claude Code.
- **Ručně:** v terminálu (nebo v Claude Code s `!` na začátku)
  ```
  claude plugin marketplace update rodokmen-skill
  claude plugin update rodokmen@rodokmen-skill
  ```
  O nových verzích se dozvíte přes **Watch → Custom → Releases** na GitHubu.

Po aktualizaci Claude Code restartujte. Rozpracovaný projekt pak Claude při další práci sám nabídne aktualizovat
na novou verzi (vaše data zůstanou, změněné soubory webu zazálohuje do `pracovni/`).

### Varianta B – ručně
Stáhněte repozitář (zelené tlačítko **Code → Download ZIP** na GitHubu, nebo `git clone`) a zkopírujte složku
`skills/rodokmen` do `~/.claude/skills/` (na Windows `C:\Users\<jméno>\.claude\skills\`). Výsledek:
`~/.claude/skills/rodokmen/SKILL.md`.

Pak Claude Code restartujte.

## První spuštění
1. Spusťte Claude Code (klidně v domovské složce) a napište třeba:
   > Chci udělat rodokmen své rodiny.

   nebo přímo `/rodokmen`.
2. Claude zkontroluje programy, založí složku projektu (např. `~/Rodokmen`) a začne se ptát na rodinu.
   Připravte si, co víte o rodičích, prarodičích a pradědečcích, a rodinné dokumenty (rodné a oddací listy, parte,
   fotky, kroniky) – stačí vyfotit mobilem.
3. **Příště otevírejte Claude Code přímo ve složce projektu** (`cd ~/Rodokmen && claude`, nebo v aplikaci
   vyberte tuto složku). Claude si přečte, kde jste skončili, a naváže.

Chcete nejdřív vidět, jak web vypadá? Řekněte: *„Ukaž mi ukázkový web.“* Claude založí ukázkový projekt
s vymyšlenou rodinou a spustí náhled.

## Jak to probíhá
| Fáze | Co děláte vy | Co dělá Claude |
|---|---|---|
| 0. Příprava | potvrdíte instalaci programů | založí projekt |
| 1. Rozhovor | vyprávíte, dodáte dokumenty, zeptáte se příbuzných | zapisuje, čte dokumenty, navrhuje otázky |
| 2. Matriky | rozhodujete sporná místa | hledá svazky, stahuje a čte zápisy, dělá výřezy, přepisy a překlady, vede deník hledání |
| 3. Příběhy | doplníte rodinné historky, schválíte texty | průběžně sbírá zajímavosti, napíše „Příběh <vašeho rodu>“ |
| 4. Web | díváte se a říkáte, co upravit | staví web a ukazuje náhled |
| 5. Zveřejnění | založíte účet na Netlify, schválíte obsah | nasadí web s přihlášením rodinnou otázkou |

Matriky jsou online jen do určitého data: narození starší než 100 let, sňatky 75 a úmrtí 30 let.
O mladší údaje se žádá na matričním úřadě. Claude vám řekne, kdy to je potřeba.

## Co je v repozitáři
```
skills/rodokmen/
  SKILL.md           průvodce pro Clauda (fáze, pravidla)
  reference/         podrobné návody: čtení matrik, portály archivů, formát dat, web, soukromí,
                     metodická příručka (playbook, anglicky)
  tools/             nástroje v Pythonu (ARON, výřezy, rámečky, mapa, kontrola dat, export do webu, vějíř)
  template/          šablona projektu: prázdná data, ukázková rodina, web (Astro)
.claude-plugin/      instalace jako plugin
```

## Co umí a co ne
- **Hotové nástroje** (bez prohlížeče) mají: východní Čechy (SOA Zámrsk, ARON), jižní Čechy (SOA Třeboň,
  včetně dobrovolnických rejstříků), západní Čechy (SOA Plzeň, Porta fontium), střední Čechy (SOA Praha, eBadatelna –
  i urbáře a gruntovní knihy) a Prahu (AHMP a policejní přihlášky 1850–1914). Pro severní Čechy (SOA Litoměřice)
  stahuje snímky nástrojem, knihu ale najde přes prohlížeč. Pro Rakousko je postup přes Matriculu.
- Ostatní archivy (Brno, Opava) Claude obsluhuje obecným postupem přes prohlížeč.
  Funguje to, ale je to pomalejší.
- U úředníků, vojáků a lékařů hledá i v **dobových novinách** (ANNO, Kramerius) – kariéra, vyznamenání, parte.
- Umí načíst **rodinný strom z MyHeritage** a dalších služeb (export GEDCOM, z MyHeritage i zálohu stromu z programu
  Family Tree Builder) a udělat z něj plán hledání.
- Průběžně sbírá **zajímavosti** (svatby na poslední chvíli, rod sto let v jednom domě…) a s vámi napíše
  **Příběh vašeho rodu** – hlavní článek webu.
- Claude čte staré písmo dobře, ale ne bezchybně. Proto ke každému zápisu ukládá výřez s vyznačeným místem,
  aby se to dalo zkontrolovat, a nejistá místa označuje otazníkem.
- Placené služby (MyHeritage, Ancestry) Claude hromadně neprochází – vede to k zablokování účtu.

## Soukromí
Projekt obsahuje osobní údaje vaší rodiny. Zůstává na vašem počítači. Web je chráněný rodinnou otázkou
a není indexovaný vyhledávači; bez nastavené otázky ho nástroj nenasadí. Je to lehká ochrana proti náhodným
návštěvníkům, ne trezor: kdo zná odpověď, vidí všechno, co na web dáte. Claude má pokyn psát o žijících lidech
jen jméno a rok narození a před zveřejněním s vámi projít, co o nich web říká – kód to ale nevynucuje,
rozhodnutí je na vás.
Pokud projekt chcete zálohovat na GitHub, použijte **soukromý** repozitář.

## Zpětná vazba a vaše zkušenosti
Děkuji všem, kdo mi poslali připomínky – jen verze 0.5.0 zapracovala přes čtyřicet podnětů od šesti lidí (podpora
Windows a staršího ImageMagicku, postupy pro MZA Brno a ZA Opava, bezpečná úprava dat a další). Každou připomínku čtu
a průběžně zapracovávám – ne každou hned a ne každou doslova, aby skill zůstal jednoduchý pro všechny.

**Chyby a problémy** – AI špatně přečetla zápis, spojila nesprávné lidi, nějaký krok nefunguje nebo spadl nástroj –
prosím [založte jako issue na GitHubu](https://github.com/sarsonj/rodokmen-skill/issues/new) (stačí bezplatný účet).
Popište, co se stalo, a pokud jde o čtení zápisu, přidejte odkaz na snímek v archivu. Issues jsou veřejné, proto
do nich nepište údaje o žijících lidech.

Budu rád i za další zkušenosti. Napište mi na **sarsonj@gmail.com**, co fungovalo, co ne, jaký archiv jste použili, co vám na webu chybělo.
Užitečné změny rád zapracuji do skillu, aby je měli k dispozici i ostatní. Další verze tak bude lepší pro každého,
kdo hledá své předky.

Nemusíte nic sepisovat sami. Claude si během práce zapisuje do `poznamky_pro_skill.md` (v projektu), co by šlo zlepšit:
chyby, nové archivy, postupy a nápady, bez údajů o vaší rodině. Občas vám je nabídne k odeslání. Nic se neposílá samo:
když budete chtít, zkopírujte je do e-mailu.

## Bezpečnost
Skill je obyčejný text (návod pro Clauda) a pár skriptů v Pythonu. Všechno si můžete před instalací prohlédnout
tady v repozitáři.
- **Žádný automaticky spouštěný kód.** Plugin nemá hooky ani MCP servery. Skripty spouští jen Claude, když je
  při práci potřebuje, a Claude Code se vás na ně zeptá.
  Jediná výjimka je volitelný **hlídač sítě**. Claude se na něj zeptá při zakládání projektu a bez vašeho souhlasu
  se nezapne. Je to malý skript v projektu (`tools/hlidac_site.py`, hook v `.claude/settings.json` projektu). Před
  každým příkazem zkontroluje, jestli nejde na web archivu mimo brzdu, a takový příkaz zamítne. Sám nic nestahuje
  ani nikam neposílá. Vypnete ho příkazem `novy_projekt.py <projekt> --bez-hlidace`.
- **Brzda proti zablokování archivem.** Archivy blokují IP adresu po sérii rychlých dotazů. Nástroje proto mají
  společný limit pro každý web (`tools/slusne.py`) a po varování archivu se na 30 minut zastaví. Projekt má
  v `.claude/settings.json` zakázané přímé `curl` a `wget`, stahuje se jen přes brzdu.
- **Kam skripty sahají:** zapisují do složky projektu rodokmenu (stažené snímky, mezivýsledky, web).
  Výjimkou jsou dočasné soubory systému, stav brzdy (pár malých souborů v `~/.cache/rodokmen_slusne`, na Windows
  v `%LOCALAPPDATA%`), npm při instalaci webu a přihlášení nástroje pro nasazení (Netlify, CapRover), pokud web
  zveřejňujete. Mimo projekt nic nemažou ani nepřepisují.
- **Na které servery chodí:** archivní portály (ARON SOA Zámrsk, SOA Třeboň, SOA Plzeň – Porta fontium, SOA Praha –
  eBadatelna, AHMP, Národní archiv, SOA Litoměřice, Matricula), noviny (ANNO, Kramerius), OpenStreetMap (mapa
  a souřadnice obcí) a při instalaci webu registr npm.
  Na Netlify jen tehdy, když web sami zveřejníte. Nikam jinam nic neposílají, ani vaše data, ani poznámky.
- **Doporučení:** nechte v Claude Code zapnuté schvalování příkazů, aspoň dokud si nezvyknete, co Claude dělá.
  Obecně instalujte skilly a pluginy jen od lidí, kterým věříte. Skill nikdo předem nekontroluje a Claude se
  jeho návodem řídí.

## Licence
Skill je pod licencí [MIT](LICENSE): smíte ho volně používat, upravovat a šířit dál, jen zachovejte uvedení autora (Jindřich Šaršon).
Výjimkou je metodická příručka `skills/rodokmen/reference/playbook.md`. Je to převzatá rešeršní zpráva bez uvedeného
autora, licence MIT se na ni nevztahuje (podrobnosti na začátku souboru).
