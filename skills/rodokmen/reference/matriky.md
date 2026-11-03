# Jak číst matriky – praktický návod

## Druhy knih
| Zkratka | Kniha | Co v ní je | Proč je cenná |
|---|---|---|---|
| **N** | narození (křty), *Liber natorum / baptisatorum*, *Geburtsbuch* | datum narození a křtu, dům (čp.), dítě, rodiče (od ~1784 i jejich rodiče a bydliště), kmotři, porodní bába | pohlaví, legitimita, rodiče matky → další generace |
| **O** | oddaní (sňatky), *Liber copulatorum*, *Trauungsbuch* | datum, dům, ženich a nevěsta (věk, stav, náboženství), jejich rodiče, svědci | **nejlepší první cíl** – otevírá dvě rodiny naráz |
| **Z** | zemřelí, *Liber defunctorum*, *Sterbebuch* | datum úmrtí a pohřbu, dům, jméno, věk, příčina | věk → odhad roku narození, stav (vdova po…) |
| **I** | index (rejstřík) k N/O/Z | jméno → datum / strana | rychlé hledání; **index bývá neúplný**, negativní výsledek v indexu nic nedokazuje |

Další prameny: sčítání lidu (1857–1921; domácnosti s daty narození), soupis poddaných 1651 (celé rodiny s věkem),
berní rula 1654 (jen hospodáři), gruntovní/pozemkové knihy (kdo vlastnil který dům – propojí generace přes dům),
vojenské záznamy, domovské listy, parte. Viz `portaly.md` a `playbook.md` §2.

## Lhůty (zákon 301/2000 Sb.)
Do archivu (a tedy online) jde svazek, až od jeho **posledního** zápisu uplyne: narození **100 let**, sňatky **75**, úmrtí **30**.
Mladší knihy jsou na matričním úřadě obce s rozšířenou působností / pověřeném úřadě – výpis dostane přímý příbuzný
(žádost + doklady o příbuzenství). Zapiš do `archivni_dotazy.md`.

## Jak vypadá hledání v praxi
1. **Obec → farnost.** Malé vesnice patřily k faře v sousední obci; popis svazku vyjmenovává všechny obce farnosti.
   Hledej obec v popisu svazku (`aron_search.py "Obec"`), ne jen v názvu – a hledej i podle obce, ne jen podle fary
   z pozdějšího zápisu: obec mohla mít vlastní matriku (filiální kostel, lokálie), i když list vydala mateřská fara.
   Obec rozdělená mezi dvě fary má dvě řady knih, každou jen pro „svá“ čísla domů.
2. **Svazek podle roku a druhu.** Pozor na překryvy: jedna kniha pro více obcí, zvláštní knihy pro jednotlivé obce.
   **Druhopisy** (duplikáty pro děkanát nebo úřad, např. „T“ svazky v ZA Opava) mívají N, O a Z jednoho roku u sebe –
   hodí se, když originál chybí, je nečitelný nebo velký.
3. **Index, pak kniha.** Index řazený po písmenech a letech dá stránku/folio; snímek odhadni (snímek ≈ folio × 1 až 2) a dolaď.
   Starší rejstříky (18. stol.) občas ukazují o 1–4 strany vedle – když zápis na udané straně není, listuj kolem.
   Posun „snímek – strana“ se v knize mění (vložené listy, chybějící strany) – přečti číslo strany na náhledu a dopočítej.
   U starých far se vyplatí nejdřív najít **souhrnný index** přes víc desetiletí (např. N/O/Z 1636–1746) – dovede
   rychle až do 17. století. Rejstříky bývají podle **německého pravopisu**: česká jména na O a V hledej i pod W
   (Otava = Wotawa, Vávra = Wawra). Knihy pro více obcí bývají řazené po obcích, rejstřík na konci.
   Velké fary mají rejstříky i jako **samostatné svazky** (např. rejstřík oddaných přes 300 let) – hledej je nejdřív.
   **Když matrika chybí** (není online nebo se nedochovala), zkus rejstřík – bývá vedený zvlášť a přežil i tam, kde kniha
   ne. Zápis v rejstříku dokládá datum, místo a otce; zapiš ho jako `prob` (opis, ne originál) a matriku zkus později.
4. **Bez indexu: listuj chronologicky.** Odhadni pozici podle let na prvních a posledních snímcích svazku (půlení intervalu).
   Staré knihy svázané z **ročních výtahů** (Extractus, Consignatio, 18. stol.) nemusí jít po sobě a ročníky chybí;
   rok bývá jen v nadpisu výtahu. Než napíšeš „zápis tam není“, ověř hlavičky ročníků.
   **Nejisté datum** (číslice z pozdější poznámky): nejdřív projdi všechny možné roky v domovské farnosti, teprve pak
   okolní fary. (Skutečná chyba: „9?“ přečteno jako 97, prošlo se pět okolních far; sňatek byl doma o pět let dřív.)
5. **Přečti celý zápis**, pak se podívej i na okolí (dvojčata, další děti stejných rodičů).
6. **Sňatek se obvykle konal ve farnosti nevěsty** (v jejím bydlišti) – hledej ho nejdřív tam, pak ve faře ženicha.
   Nedaří se? Ve křtu dítěte bývá (Praha ~1880–1890) připsané datum a místo sňatku rodičů – ověř ho v oddaných.
7. **Rodina v katolické matrice chybí? Zkus evangelickou nebo židovskou.** Po toleranci (1781) vedly vlastní matriky
   evangelické sbory (a. v. i h. v.), jeden sbor pokrýval desítky obcí; v ARONu mají signatury „R …“ a `aron_search.py`
   je najde podle obce. Ve východních Čechách časté (Rychnovsko, Dobrušsko, Opočensko). Židovské matriky viz `portaly.md`.
   Ve 20. století (1920–1945) zkus i **civilní matriky** lidí bez vyznání u okresních úřadů (vyzkoušeno v SOA Třeboň, viz `portaly.md`).

## Čtení písma
- Kurentový rejstřík: stáhni plné rozlišení a rozřež stránku na čtvrtiny (sloupec jmen + data),
  `magick f.jpg -crop 1250x1650+X+Y +repage ctvrt.jpg`. **Dopisované řádky** se snadno přečtou špatně (Franziska × Heinrich,
  strana 131 × 151) – údaj z rejstříku vždy ověř v matrice.
- Do ~1780 latina nebo čeština, pak hodně němčina (kurent), od ~1860 často čeština, ve 20. století čeština.
- Česká jména v němčině/latině: Johann/Joannes = Jan, Wenzel/Wenceslaus = Václav, Joseph = Josef, Franz/Franciscus = František,
  Maria = Marie, Anna, Katharina = Kateřina, Barbara = Barbora, Magdalena = Majdalena/Magdaléna, Theresia = Terezie,
  Ludmilla = Lidmila, Dorothea = Dorota, Apollonia = Apolena, Georg/Georgius = Jiří, Matthias = Matěj, Adalbert = Vojtěch.
- Příjmení se píše foneticky a mění se (Šaršon/Scharschon/Šaršoun, Kroupa/Kraupa). Hledej všechny varianty.
- Ženská příjmení v němčině bez „-ová“ (Maria Novak = Marie Nováková).
- Názvy obcí mívají staré tvary, třeba s předsunutým „V“ („Volešnice“ = Olešnice); při hledání obce zkus i ty.
- Kurent: dlouhé „ſ“ vypadá jako „f“, „e“ jako „n“, „h“ s kličkou dolů. Při nejistotě porovnej se stejným písmenem
  jinde na stránce stejné ruky – i u „divného“ příjmení (koncové „k“ psané skoro jako „r“: „-ek“ vypadá jako „-er“).
  Slovo rozdělené přes konec řádku („Urlau-“ / „ber“) dočti na začátku dalšího řádku.
- Daty bývají svátky (*Dominica*, *festum S. Joannis*) – v nejasných případech dopočítej.

### Slovníček (lat. / něm. → česky)
| výraz | význam |
|---|---|
| *natus / geboren*, *baptisatus / getauft* | narozen, pokřtěn |
| *copulati / getraut*, *sponsus / Bräutigam*, *sponsa / Braut* | oddáni, ženich, nevěsta |
| *mortuus, sepultus / gestorben, begraben* | zemřel, pohřben |
| *legitimus / ehelich*, *illegitimus / unehelich* | manželský, nemanželský |
| *viduus, vidua / Witwer, Witwe* | vdovec, vdova |
| *filius, filia / Sohn, Tochter* | syn, dcera |
| *patrini / Pathen*, *testes / Zeugen*, *obstetrix / Hebamme* | kmotři, svědci, porodní bába |
| *agricola, rusticus / Bauer* | sedlák, rolník |
| *Häusler*, *casarius* | domkář |
| *Inwohner / inquilinus*, *podruh* | podruh (bydlel v cizím domě) |
| *Gärtner* (na vsi) | zahradník = malý usedlík, ne nutně pěstitel |
| *Inleute*, *Taglöhner* | podruzi, nádeníci |
| *Bürger*, *civis* | měšťan |
| *Schneider / sartor*, *Schuhmacher / sutor*, *Weber / textor*, *Schmied / faber*, *Müller / molitor* | krejčí, švec, tkadlec, kovář, mlynář |
| *N.* / *No.* / *Haus Nr.* | číslo domu (popisné) |
| *ex*, *aus*, *von* | z (obce) |
| *Lungensucht*, *Abzehrung* | souchotiny (TBC) |
| *Cholera*, *Blattern* | cholera, neštovice |
| *Fraisen* | křeče (časté u kojenců) |

## Odhad roků
- Věk při úmrtí/sňatku je často zaokrouhlený o ±2–5 let. Uváděj „asi 1756“ a hledej křest v širším okně.
  I přesné datum narození v oddacím zápisu mívá špatný měsíc: když křest v něm není, projdi celý rok ±1 a farnost
  matky (dítě se často narodilo u jejích rodičů).
- Nevěsta mívala 18–28, ženich 22–32; děti po 1,5–3 letech.
- „Vdovec“ u ženicha = hledej první manželství a děti z něj.
- Při přepisu křtu ověř měsíc podle záhlaví příslušného sloupce a nepopleť číslo domu porodní báby
  (*obstetrix*, *Hebamme*) s rodištěm dítěte.

## Stavy údajů v datech
| stav | kdy |
|---|---|
| `doc` | přečteno přímo na snímku zápisu, který osobu jednoznačně identifikuje |
| `prob` | silná shoda (jméno, doba, místo, dům, řemeslo), ale bez přímého zápisu; vždy `note` proč |
| `fam` | od rodiny / z rodinného dokumentu |
| `mh` | jen z cizího stromu na internetu |
| `unk` | známe jen místo v rodokmenu |

## Typické pasti (ze skutečného výzkumu)
- Písař spletl jméno dědečka (Josef místo Václava) – rozhodne více zápisů téže rodiny.
- Dítě zapsané pod jiným křestním jménem, než jakým ho volala rodina (Františka → v rodině Anna).
- Sňatek pár měsíců před porodem nebo po něm – není chyba, jen „svatba na poslední chvíli“; zajímavost pro web.
- Nemanželské dítě nese příjmení matky; otec chybí nebo je dopsán později (legitimace na okraji).
- Stejný předek dvakrát v rodokmenu (vzdálení příbuzní se vzali) – v datech `SAME`.
- Index nenašel ≠ zápis neexistuje. Zapiš, co přesně jsi prošel.
- Pomocníci (subagenti) a OCR/AI čtou historické písmo chybně – vždy ověř sám (viz `playbook.md` §1 bod 10).

## Technické pasti (macOS, zsh) – napiš je i pomocníkům do zadání
- Shell je zsh: `for a in "x y z"; do set -- $a` slova nerozdělí (v zsh `${=a}`); `ls F*` bez shody = chyba
  „no matches found“; `echo ====` je chyba (`=` na začátku slova). Složitější smyčky pouštěj přes `bash -c '…'`.
- ImageMagick: seznam souborů předávej jako jednotlivé argumenty, ne jednou proměnnou s mezerami.
  `-annotate` potřebuje písmo: `-font /System/Library/Fonts/Supplemental/Arial.ttf` (bez něj spadne na „unable to read
  font“; totéž `montage` s popisky) – pořadí výřezů raději vypiš zvlášť.
- Ověření čtení: `python3 -I tools/overit.py <snímek> x0,y0,x1,y1 pracovni/over [v]` (zlomky 0–1, ne pixely) – zápis rozdělený na dvě poloviny
  zmenšené na 1900 px (dvoustrana je jinak nečitelná).
- Výřez pro web (`vyrez.py`) dělej jen na **čtený zápis** (případně s hlavičkou sloupců), ne na celou dvoustranu –
  na webu by byl nečitelně malý. Celá stránka je v `zdroje/` a na portálu přes odkaz.

## Technické pasti (Windows) – napiš je i pomocníkům do zadání
(Nahrazují první dva body macOS sekce; body o `overit.py` a výřezu platí i tady.)
- Python: `python -I -X utf8 tools/<nástroj>.py` (ne `python3` – bývá to nefunkční alias z Microsoft Store). Bez `-X utf8`
  je výstup do roury v cp1250: čeština se rozbije a skripty spadnou na „≈“ a „→“ (nástroje skillu si výstup přepnou
  do UTF-8 samy, vlastní jednorázové skripty ne – `-X utf8` proto používej vždy). Totéž platí při
  přesměrování do souboru (soubor z `… --osoby > x.py` by jinak vznikl v cp1250; ve Windows PowerShellu 5.1 `>` dokonce
  zapisuje UTF-16 – přesměrovávej v Git Bash). Proměnná `PYTHONUTF8` s `-I` nefunguje.
- ImageMagick je `magick`, nikdy `convert` (`convert` je ve Windows systémový nástroj na převod disku z FAT na NTFS).
  Po instalaci přes winget je `magick` v PATH až po restartu Claude Code. Písmo pro `-annotate`: `-font C:/Windows/Fonts/arial.ttf`.
- Limit délky příkazové řádky je 32 767 znaků – stovky souborů (dlaždic) v jednom příkazu `magick` neprojdou
  (WinError 206); skládej po řádcích.
- Skripty `.sh` přes Git Bash (`bash tools/…`). Markdown a JSON nikdy neupravuj `sed -i` (escapy v Git Bash rozbijí
  soubor) – data zapisuj podle pravidla „Zápis do dat“ v SKILL.md.
- Windows nerozlišuje velikost písmen v názvech (`o_29.jpg` = `O_29.jpg`) – náhled a plné rozlišení odliš předponou
  (`nahled_`, `plne_`), jinak se přepíšou.
- Datové soubory zapisuj v UTF-8 **bez BOM** (Windows PowerShell 5.1 s `-Encoding UTF8` přidá BOM a `osoby.py` pak nejde načíst).
