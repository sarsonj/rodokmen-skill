# Metodika – spojování záznamů, ztotožnění, mrtvé body, prameny mimo ČR

Čti podle potřeby: když nevíš, jestli jde o tutéž osobu, když se hledání zasekne (mrtvý bod), nebo když stopa vede
mimo ČR (Slovensko, Rakousko, Polsko, Německo, Maďarsko). Čtení matrik a slovníček: `matriky.md`, portály a jak
z nich brát snímky: `portaly.md`, formát dat: `data.md`.

## Spojování záznamů – čím propojit generace
- **Číslo popisné.** Jan Novák v čp. 12 v úmrtí 1820 (70 let) a Jan Novák v čp. 12 v oddacím zápisu 1788 = nejspíš
  tatáž usedlost. **Přečíslování** (po požáru, novou výstavbou, ve městech a předměstích) rozdělí ves; jeden dům mívá
  v čase dvě čísla. Pochybnost ověř na indikační skice stabilního katastru 1824–43 (`portaly.md` → Starší prameny).
- **Jméno po chalupě (vulgo).** „Wenzel Schmid vulgo Bauer“ – jméno gruntu přežije výměnu držitele a přejde i na
  zetě, který se přiženil. **Není to příjmení:** když se „příjmení“ při převzetí statku změní, vysvětlí to gruntovní kniha.
- **Kmotři a svědci (okruh rodiny a sousedů).** Stejné tři kmotrovské páry u osmi křtů 1790–1810 = jedna rodina;
  změna kmotrů může znamenat nové manželství. Pozor: kmotři často pocházeli z ustálených „kmotrovských“ rodin, nejsou
  to nutně příbuzní.
- **Stav v zápisu.** Sedlák → výměnkář ve stejném domě = starý hospodář předal grunt. **Výměnkář není automaticky
  otec** nového hospodáře (může být tchán, nevlastní otec, cizí prodávající) – vztah uvádí gruntovní kniha.
  Domkář ≠ sedlák stejného jména; stav se ale může zvednout sňatkem na grunt.
- **Gruntovní kniha jako doklad původu.** „Václav prodává synu Janovi … dědické díly bratru Matějovi, sestře Anně“ –
  jeden zápis jmenuje rodiče, dítě i sourozence. Gruntovní knihy bývají pečlivější než matriky („šlo o peníze“).
  Výplaty dílů se připisovaly i o desítky let později – datuj každou zvlášť.
- **Sirotčí knihy** uvádějí věk sirotků → okno pro křty (věky zaokrouhlené).
- **Svatební smlouvy:** věno nevěsty „od otce Jiřího, sedláka v X“ ukáže farnost jejího původu. Bývají
  v městských knihách, ne jen v knihách panství.
- **Pozůstalosti (po 1850 u soudního okresu)** jmenují dědice i v jiných okresech a ve Vídni. Fondy bývají
  vybírkové nebo skartované.
- **Pojmenování:** první syn často po dědovi. Samo o sobě slabý doklad.
- **Pomaďarštění a poněmčení jmen osob i míst:** Kováč → Kovács, Šimek → Schimek, Bytča = Nagybiccse; v maďarských
  pramenech příjmení před křestním jménem, v polských -owa místo -ová. Hledej všechny jazykové tvary.
- **Místopisné slovníky:** Retrospektivní lexikon obcí, Historický lexikon obcí (ČR), Helységnévtár 1877/1913
  (Uhry, tedy i Slovensko), Słownik geograficzny (Polsko), místopisný slovník GenTeam / oefr (asi 72 000 obcí
  Předlitavska s farní příslušností). Farní příslušnost ber podle roku události.
- **Legitimace na okraji** („legitimiert durch nachfolgende Ehe am …“) určí otce – poznámka může být i v jiné knize
  (v oddacím zápisu rodičů, v pozdějším opise).
- **Domovské právo (Heimatrecht).** Vídeňská policejní přihláška, kmenový list vojáka i domovský list uvádějí
  domovskou obec → domovská farnost. **Domovská obec ≠ místo narození** (domovské právo se získávalo i pobytem nebo
  sňatkem).

## Ztotožnění – kdy je to tatáž osoba
- **Výchozí pravidlo:** dvě osoby stejného jména spoj jen podle **dvou nezávislých znaků** – číslo domu, oba rodiče,
  manžel(ka), stejný okruh kmotrů, přesné datum narození. Každý znak z jiného zápisu (jiný písař/oznamovatel).
  Jeden znak nebo jen jméno a doba = `prob` s `note` proč; rozpor do `ISSUES`.
- **Bratranci stejného jména v jedné vsi:** dům sám nestačí (bydleli vedle sebe i v jednom domě) – žádej rodiče **a** manželku.
- **Vdova znovu vdaná** vystupuje pod dvěma příjmeními po mužích: spojuj podle **rodného příjmení a jména otce**
  v obou oddacích zápisech.
- **Rozpor mezi prameny:** originál má přednost před opisem; váž, kdo údaj oznámil a jak dlouho po události
  (datum narození v úmrtním zápisu, které hlásil soused, je slabší než křestní zápis). Rozpor zapiš do `ISSUES`.
- **Nevlastní rodiny:** výměnkář může být nevlastní rodič; vztah uvádí gruntovní kniha.
- **Nalezenci:** bez rodičů – spoj přes číslo nalezince (vídeňský nalezinec, Findelhaus) a obec kojné.
- **Vojáci:** dva znaky jsou **pluk a domovská obec** (z kmenového listu), ne jen místo narození.
- Před zápisem „tatáž osoba“ vyjmenuj **ostatní kandidáty** stejného jména ve farnosti a u každého, proč nesedí
  (do `note` nebo do deníku). A napiš, jaký nový doklad by závěr vyvrátil.

## Chyby, na které si dát pozor
(Doplněk k „Typickým pastem“ v `matriky.md`.)
- **Dva muži stejného jména slití v jednoho** – poznáš podle dětí „téhož“ páru narozených 10 měsíců po sobě. Rozhodnou oddací zápisy obou a čísla domů.
- **Otec nemanželského dítěte domyšlený** bez legitimační poznámky – hledej poznámku, pozdější sňatek matky, kmotry.
- **Špatná fara kvůli reorganizaci far po 1784** (nové lokálie a fary) – ves v očekávané knize chybí; ověř rok
  založení fary a starší zápisy hledej v mateřské faře.
- **Přečíslovaný dům** – stejná rodina, jiné čp.
- **Věk při úmrtí bez tolerance** – „křest nenalezen“; rozšiř okno, starým lidem věk spíš přibývá. Věk v letech,
  měsících a dnech bývá přesnější.
- **Místo sňatku = původ nevěsty** se nepředpokládá napevno – ohlášky (poznámka o ohláškách v jiné faře) a
  gruntovní kniha ukážou, odkud byla.
- **Latinské jméno špatně převedené** (Joannes ≠ Joachim).
- **Maďarský název obce nenapárovaný** – ves „na Slovensku neexistuje“; najdi ji v Helységnévtáru.
- **Kmotr považovaný za příbuzného, výměnkář za otce** – viz výše.
- **Místo narození vojáka zaměněné za domovskou obec.**
- **Židovská příjmení:** povinná od 1787, dřív jen otcovská jména (patronymika). Familiantské knihy.
- **Konvertita:** dřívější totožnost zmizí; křest dospělého mívá poznámku o konverzi → hledej v židovské matrice.
- **Evangelík hledaný jen v evangelické matrice:** i po toleranci zapisoval narození, sňatky a úmrtí nekatolíků
  zhruba do roku 1849 i katolický farář – zkus obě.
- **Starokatolíci** (státně uznaní 1877) – po tomto roce mohou v katolické knize chybět; ve Vídni jsou druhopisy
  starokatolických matrik v městském archivu (WStLA).
- **Úmrtí ve Vídni hledané v domovské faře** – zápis je ve vídeňské farnosti (nebo v protokolech ohledání mrtvol).
- **Jméno poangličtěné v USA** – v českých knihách „neexistuje“; původní tvar dají lodní seznamy a naturalizace.
- **Dítě vojáka „chybí“** – mohlo být zapsané ve vojenské matrice pluku, ne ve farní.
- **Dvojí započtení:** druhopis a originál nejsou dva nezávislé prameny – jeden je opis druhého.

## Mrtvé body – co zkusit, v tomto pořadí
- **Před 1784 (staré matriky chybí nebo nestačí):** 1. starší společné knihy N/O/Z přečíst celé (nejen rejstřík)
  → 2. gruntovní knihy panství → 3. sirotčí knihy, svatební smlouvy → 4. tereziánský katastr (1713–57) → 5. soupis
  poddaných 1651, berní rula 1654 (Morava: lánové rejstříky 1669–79). Spojuje **grunt/dům a posloupnost držitelů**.
  U sedláků se zachovanými gruntovními knihami je reálné dno **kolem roku 1650**.
- **Kniha se nedochovala:** druhopisy a samostatné rejstříky, gruntovní knihy, soupisy (konskripce), u mužů
  vojenské odvodní listiny (Musterlisten). Spojuje číslo domu.
- **Nemanželské dítě:** legitimace na okraji → pozdější sňatek matky → kmotři → soudní spis o otcovství →
  gruntovní kniha. Spojuje matka a dům dítěte.
- **Odešel do Vídně:** vídeňská farnost → policejní přihlášky: pro narozené před 1897 sbírka „Austria, Vienna,
  Population Cards, 1850–1910“ na FamilySearch (Meldezettel, částečně indexovaná – jméno, narození, příchod
  a odchod), mladší asi 1904–1975 jen písemnou žádostí u WStLA (placené i při negativním výsledku) → pozůstalost →
  domovská obec.
- **Vystěhoval se do USA:** lodní seznamy → naturalizace → církevní a krajanské spolky → poznámky na okraji
  v domovské faře. Spojuje **název obce v původním pravopisu**.
- **Voják:** nejdřív **pluk** (podle domovské obce; doplňovací okrsky pluků uvádí Wredeho přehled) → do 1820
  odvodní listiny (Musterlisten, po plucích a letech) / od 1820 kmenové listy (Grundbuchblätter) → vojenské matriky
  pluku (ve Vídni, uzavřené 100 let) → seznamy ztrát 1914–18 (`portaly.md` → Noviny) a kartotéka ztrát ve Vídni.
  Kmenové listy mužů s domovskou obcí v Čechách, na Moravě a ve Slezsku: ročníky asi 1865–1886 ve VÚA–VHA Praha
  (Kriegsarchiv uvádí totéž), starší ročníky ve Vídni (Kriegsarchiv, asi 1820–1864 i na mikrofilmech FamilySearch),
  **ročníky 1887–1898 z velké části skartované** – tam hledej v seznamech ztrát a matrikách.
- **Nalezenec:** záznamy nalezince → fara kojné. Spojuje číslo nalezince.
- **Zápis 20. století ještě neveřejný:** matriční úřad (ČR: zápisy starší lhůty kdokoli, mladší rodina; SK: jen
  rodina), Standesamt (DE, AT),
  kartotéka HOK (sudetští Němci), policejní přihlášky. Do `archivni_dotazy.md`.
- **Sudetoněmecká rodina po 1945:** Heimatortskartei (HOK) → spisy Lastenausgleich → obecní seznamy obyvatel a
  pohřešovaných (vše Bundesarchiv Bayreuth, níže). Spojuje bydliště k 1. 9. 1939.
- **Změna jména, jazykové tvary:** všechny tvary osoby i místa (výše).

## Prameny mimo ČR
Portály, které skill zná (Matricula, Geneteka, FamilySearch), a jak z nich brát snímky: `portaly.md`.
Ostatní archivy jsou většinou jen na písemnou žádost – zapiš do `archivni_dotazy.md`.

**Slovensko**
- **Církevní matriky** (řkt., evangelické, reformované, židovské) od 1592, dnes ve státních archivech
  (Zbierka cirkevných matrík). Snímky a neúplný index (hlavně křty) na FamilySearch, zpravidla do ~1895. Zápisy
  po roce 1895 v církevních knihách (některé sahají do 1935) jsou v archivu přístupné po 90 letech.
- **Civilní (štátne) matriky** od 1. 10. 1895 (uherský zákon), na matričním úřadě; do archivu až po 100 letech.
- **Sčítání 1869** na FamilySearch („Slovakia, Census, 1869“): celé domácnosti s roky a místy narození, náboženstvím
  a povoláním; jen snímky bez jmenného rejstříku a jen z archivů Bytča, Banská Bystrica a Nitra. Dobrá náhrada za
  neindexované matriky.
- **Matriční úřad:** dokud je kniha na úřadě (100 let od posledního zápisu), výpis dostane jen osoba, které se zápis
  týká, nebo člen rodiny (manžel, rodiče, děti, vnuci, pravnuci, prapravnuci, sourozenci a jejich děti) – bez ohledu
  na stáří zápisu (zákon 154/1994 Z. z., § 18). Doslovný výpis jen pro úřady; soukromá osoba může v přítomnosti
  matrikáře nahlédnout do knihy a udělat si výpis.
- Do 1918 Uhry – obce hledej i pod maďarským názvem (Helységnévtár).

**Rakousko (i Vídeň, Burgenland)**
- **Katolické matriky do 1938** v diecézních archivech, snímky na Matricule (Vídeň, Linec, St. Pölten, Štýrský
  Hradec, Tyrolsko, Korutany, Salcburk, Vorarlbersko). Burgenland (Eisenstadt) má vlastní portál matriken.at
  (zatím neúplný). Matricula nemá hledání podle jmen.
- **Evangelické matriky** (a. v., h. v.) od 1783, část také na Matricule.
- **Od 1. 1. 1939 civilní matriky** (Standesamt); církevní knihy po 1938 jsou jen církevní, bez práva nahlížet.
- **Kriegsarchiv (Vídeň), vše offline:** vojenské matriky 1633–1938 (podle pluku, 100 let uzavřené), kmenové listy
  1820–1918 (ročníky asi 1790–1900; ročníky do ~1864 jsou i na mikrofilmech FamilySearch), odvodní listiny
  1740–1820 (podle pluku a roku), kartotéky ztrát 1914–18 (asi 40 milionů karet vč. zajatců a padlých, písemná žádost).
  Přes 90 % písemností je německy – čtení kurentu je nutnost.
- **Wiener Stadt- und Landesarchiv (WStLA):** policejní přihlášky asi 1904–1975 (jen žádostí, originály nepůjčuje;
  starší pro narozené před 1897 na FamilySearch, viz Mrtvé body → Vídeň),
  protokoly ohledání mrtvol (Totenbeschauprotokolle), pozůstalosti (Verlassenschaften), druhopisy starokatolických matrik.

**Polsko (Těšínsko, Horní Slezsko, Halič)**
- **Farní matriky (metryki)** v diecézních a státních archivech (AP), část snímků na Matricule a FamilySearch,
  index Geneteka.
- **Civilní matriky (USC):** v pruském záboru od 1874, jednotně od dekretu 25. 9. 1945; do státního archivu (AP)
  po uplynutí lhůty. Katalog státních archivů: szukajwarchiwach.gov.pl (se skillem nevyzkoušeno).

**Německo (sudetští Němci, pohraničí)**
- **Standesamt** (civilní matriky) od 1. 1. 1876 (Prusko 1874) – pro rodiny, které přešly do Saska nebo Bavorska.
- **Heimatortskartei Sudetendeutsche (HOK)** – kartotéka podle bydliště k 1. 9. 1939 s poválečnou adresou;
  dnes Bundesarchiv Bayreuth (fond B 530), jen písemnou žádostí. Tamtéž **spisy Lastenausgleich** (odškodnění
  vysídlených, od 1949) a **Gemeindeseelenlisten / Gemeindevermisstenlisten** (seznamy obyvatel a pohřešovaných obcí,
  50. léta, i Sudety a Protektorát). Kirchlicher Suchdienst (Pasov, Regensburg) skončil 2015 – starší návody,
  které tam posílají, neplatí.

**Maďarsko (vedlo matriky i pro Slovensko do 1918)**
- **Státní civilní matriky** od 1. 10. 1895; druhopisy do 31. 12. 1980 v župních archivech MNL, jinak matriční úřad
  (anyakönyvi hivatal).
- **Církevní matriky** v církevních archivech – každý má vlastní lhůty (např. 90 let od založení knihy).

## Lhůty přístupu mimo ČR
(ČR viz `matriky.md`.) Počty let narození / sňatky / úmrtí:
| země | lhůta | počítá se od | poznámka |
|---|---|---|---|
| **Slovensko** | státní matriky (od 1895): 100 / 100 / 100 | posledního zápisu | do té doby na matričním úřadě, jen pro rodinu; **církevní knihy ve státním archivu** jsou archiválie – osobní údaje přístupné 90 let od zápisu, dřív se souhlasem nebo pro historický výzkum s čestným prohlášením (zákon 395/2002 Z. z., § 13) |
| **Rakousko** | 100 / 75 / 30 | zápisu (zákon) – diecézní archiv Vídeň počítá od uzavření knihy | 100 a 75 let jen pokud zápis netýká žijící osoby; po 1938 Standesamt |
| **Německo** | 110 / 80 / 30 | roku registru | úmrtí Sonderstandesamt Bad Arolsen 80 let; dřív jen přímí příbuzní nebo právní zájem |
| **Polsko** | 100 / 80 / 80 | uzavření knihy | do státního archivu do 2 let po lhůtě – online dostupnost se zpožďuje |
| **Maďarsko** | 110 / 86 / 30 | roku po založení registru | starší stránky archivů MNL uvádějí neplatné lhůty z 2014; zvláštní údaje (náboženství, nemanželský původ, příčina smrti) až 60 let po smrti |

Lhůty počítané od roku registru nebo uzavření knihy (DE, PL) se posouvají jednou ročně. Citlivé údaje (náboženství,
nemanželský původ, příčina smrti) u nedávno zemřelých nezveřejňuj – viz `soukromi.md`.

## Milníky vedení záznamů
| rok | co se změnilo | co to znamená pro hledání |
|---|---|---|
| 1651 | soupis poddaných podle víry (Čechy) | celé rodiny s věkem; neúplný, bez rejstříku jmen |
| 1654 | berní rula (Čechy) | jen hospodáři s půdou; kotva posloupnosti na gruntu |
| 1740–1820 | vojenské odvodní listiny (Musterlisten) | věk, původ, rodina vojáka – potřebuješ pluk |
| 1770/71 | konskripce a číslování domů (Čechy, Morava) | čp. se stává klíčem k propojení; pozor na pozdější přečíslování |
| 1781 | toleranční patent | vznikají evangelické sbory, nekatolíky ale dál zapisuje i katolický farář |
| 1784 | josefínský patent: oddělené knihy N/O/Z s předepsanými sloupci | jednotné sloupce; dál viz `matriky.md` (Druhy knih) |
| 1785–89 | josefský katastr | majitelé pozemků po obcích (ne po domech) – Národní archiv (Čechy), MZA (Morava), jen badatelna |
| 1820 | kmenové listy vojáků (Grundbuchblätter) | osobní list s civilním povoláním, sňatkem a dětmi |
| 1850 | konec panství, vznik okresních hejtmanství a soudních okresů | pozemkové a sirotčí záznamy přecházejí z fondů velkostatků do soudních fondů |
| 1871 | nové pozemkové knihy u soudů | do 1950/64 u katastrálních úřadů, jen badatelna |
| 1895 | civilní matriky v Uhrách (i Slovensko) | souběžná státní řada, církevní knihy pokračují |
| 1914–18 | seznamy ztrát, kartotéky ztrát | hlavní náhrada za ztracené kmenové listy |
| 1919 | kmenové listy ročníků 1865–1900 s domovem v nástupnických státech zůstaly tam | listy Čechů ve VHA Praha, mladší ročníky z velké části zničené |
| 1939 | Rakousko: civilní matriky | církevní knihy po 1938 bez práva nahlížet |
| 1950 | Československo: státní matriky | farní knihy přestávají být úředními záznamy |
