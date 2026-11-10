# Jak číst matriky – praktický návod

## Druhy knih
| Zkratka | Kniha | Co v ní je | Proč je cenná |
|---|---|---|---|
| **N** | narození (křty), *Liber natorum / baptisatorum*, *Geburtsbuch* | datum narození a křtu, dům (čp.), dítě, rodiče (od ~1784 i jejich rodiče a bydliště), kmotři, porodní bába | pohlaví, legitimita, rodiče matky → další generace |
| **O** | oddaní (sňatky), *Liber copulatorum*, *Trauungsbuch* | datum, dům, ženich a nevěsta (věk, stav, náboženství), jejich rodiče, svědci | **nejlepší první cíl** – otevírá dvě rodiny naráz |
| **Z** | zemřelí, *Liber defunctorum*, *Sterbebuch* | datum úmrtí a pohřbu, dům, jméno, věk, příčina | věk → odhad roku narození, stav (vdova po…) |
| **I** | index (rejstřík) k N/O/Z | jméno → datum / strana | rychlé hledání; **index bývá neúplný**, negativní výsledek v indexu nic nedokazuje – a „v rejstříku není“ ověř čtením po sloupcích (Čtení písma) |

Další prameny: sčítání lidu (1857–1921; domácnosti s daty narození; operáty 1930 jsou jen v Národním archivu,
běžně nepřístupné a online nejsou), soupis poddaných 1651 (celé rodiny s věkem),
berní rula 1654 (jen hospodáři), gruntovní/pozemkové knihy (kdo vlastnil který dům – propojí generace přes dům),
vojenské záznamy, domovské listy, parte. Viz `portaly.md` a `metodika.md` (prameny mimo ČR).

## Lhůty (zákon 301/2000 Sb.)
Do archivu (a tedy online) jde svazek, až od jeho **posledního** zápisu uplyne: narození **100 let**, sňatky **75**, úmrtí **30**.
Mladší knihy jsou na matričním úřadě obce s rozšířenou působností / pověřeném úřadě. **Matriční úřad ale počítá lhůtu
u každého zápisu zvlášť** (§ 25b zákona 301/2000 Sb.): zápis starší 100 / 75 / 30 let (narození / sňatek / úmrtí) vydá
**komukoli** i ze svazku, který je ještě na úřadě, a dovolí do knihy nahlédnout. Mladší zápis dostane jen osoba, které
se týká, nebo člen rodiny (manžel, partner, rodiče, děti, sourozenci, prarodiče, vnuci, pravnuci) s doložením
příbuzenství. Žádej o **doslovný výpis** – na rozdíl od rodného či oddacího listu obsahuje i okrajové poznámky
(pozdější sňatek, úmrtí, legitimaci). Stejné lhůty platí pro sbírku listin a druhopisy do roku 1958. Slovensko má jiná
pravidla (`metodika.md` → Prameny mimo ČR, Slovensko). Zapiš do `archivni_dotazy.md`.
Katalogy archivů uvádějí **i svazky, které jsou ještě na úřadě**: v detailu „Technická poznámka: MATRIKA JE DOSUD
ULOŽENA NA MATRIČNÍM ÚŘADĚ“, „Místo uložení: Obecní úřad X“ a 0 příloh (snímků). Tu poznámku přečti dřív, než hledáš
snímky; svazek rovnou zapiš do `archivni_dotazy.md` i s místem uložení (tam se píše o výpis). Zkus **samostatný rejstřík**
(I-N, I-O, I-Z) přes stejné roky nebo **druhopis** (může končit dřív než originál, a být tak už v archivu) – bývá online a dá aspoň datum a číslo domu. Uživateli řekni předem, že narození
zhruba po roce 1910 často online nebudou (kniha pokračuje za rok 1926, lhůta běží od posledního zápisu).

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
   **Posun nikdy nedomýšlej:** přečti „Pag./fol.“ na 2–3 snímcích, spočítej ho a teprve pak skoč (bývá +1, +2, ale i −19).
   U knih **dodatečně přefoliovaných** odkazuje rejstřík na původní ruční číslo listu (vpravo nahoře), ne na archivní
   foliaci. Farní rejstřík bývá společný pro víc obcí (sloupec obec) a folio pak platí v knize té obce.
   U starých far se vyplatí nejdřív najít **souhrnný index** přes víc desetiletí (např. N/O/Z 1636–1746) – dovede
   rychle až do 17. století. Rejstříky bývají podle **německého pravopisu**: česká jména na O a V hledej i pod W
   (Otava = Wotawa, Vávra = Wawra). Knihy pro více obcí bývají řazené po obcích, rejstřík na konci (viz níže).
   Velké fary mají rejstříky i jako **samostatné svazky** (např. rejstřík oddaných přes 300 let) – hledej je nejdřív.
   **Když matrika chybí** (není online nebo se nedochovala), zkus rejstřík – bývá vedený zvlášť a přežil i tam, kde kniha
   ne. Zápis v rejstříku dokládá datum, místo a otce; zapiš ho jako `prob` (opis, ne originál) a matriku zkus později.
4. **Bez indexu: listuj chronologicky** – ale nejdřív ověř, že kniha není řazená po vsích (níže). Odhadni pozici podle let na prvních a posledních snímcích svazku (půlení intervalu).
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
   **Smíšená manželství:** od roku 1868 šli synové po otci a dcery po matce, pokud se rodiče nedohodli jinak.
   Před rokem 1868 byly při katolickém otci katolické všechny děti. Dceru evangelíka a katoličky proto hledej
   nejdřív v katolické matrice, syna v evangelické.

## Knihy řazené po vsích (časté 1784–1900, všechny archivy)
Venkovské fary vedly knihu často **po vsích**: každá ves má vlastní oddíl s vlastním stránkováním (foliací) a roky běží
jen uvnitř oddílu. Oddíly nejdou podle let, pokračují vzadu („ad pag. 70“, „vide reliquos pag.“) a oddíl jedné vsi bývá
až na konci knihy. Odhad snímku podle roku pak selže a „zápis tam není“ bývá omyl (skutečné chyby: prošel se jen oddíl
vsi a sňatek byl v oddílu městyse; ves měla oddíl až na snímcích 380–405).
1. **Popis knihy první:** eBadatelna „Obecný popis“ (rozvržení stran po vsích), MZA „Části matriky“, ARON „územní
   rozsah“, Porta fontium `info`. Přechody vsí mezi farami mívají mezery – zápis z mezery hledej v obou farách.
   Popis bývá **neúplný**: eBadatelna rozvržení ořízne asi na 250 znaků (konec chybí i na webu archivu), u jiných knih
   chybí úplně, i když je kniha po vsích řazená, a název vsi bývá zkomolený („Onšovec“ = Vonšovec). Úplný seznam vsí
   knihy je v poli **Lokality**; zbylé oddíly najdi mapou knihy (bod 3) podle čísel stran „Pag.“ a nadpisu vsi
   (bývá jen na první straně oddílu).
2. **Rejstřík fary:** uvádí ves (písmenem nebo „tom“ = kniha vsi, ne pořadí svazku) a **stranu uvnitř oddílu**, ne celé
   knihy. Snímek ≈ začátek oddílu + strana/2 (folio/2), dolaď podle čísla na snímku. Uvnitř písmene jde rejstřík podle let.
   Staré rejstříky odkazují často na **přeškrtnutá stará čísla** listů a rok s listem bývá posunutý o řádek proti jménu –
   čti i sousední položky a ověř na snímku. Na konci knih bývá i ručně psaný **rejstřík po obcích** (prohlédni poslední
   snímky). Dobrovolnické rejstříky nejsou úplné – při neúspěchu čti oddíl vsi přímo.
   Klíč písmeno/tom → ves zjistíš ze záhlaví stránek; sestav si tabulku do deníku.
3. **Mapa knihy:** z každého 5.–30. snímku jen horní pruh (název vsi, rok) v malém rozlišení, slepit pod sebe s číslem
   snímku → stavba celé knihy na jednom obrázku: `python3 -I tools/mapa_knihy.py aron|pf|ahmp <kniha> <od> <do> [krok]`
   (u archivů jen v prohlížeči z uložených snímků obrazovky: `mapa_knihy.py soubory pracovni/x_*.png`). Pak v plném
   rozlišení jen oddíl hledané vsi. Mapu oddílů zapiš do deníku.
4. **Montáž sloupců:** uvnitř oddílu vyřízni sloupec se jmény (ženich/nevěsta, dítě, ves na okraji – aspoň 35 % šířky
   strany, užší usekne jména) ze 4–8 snímků a slep vedle sebe (`mapa_knihy.py … <od> <do> 1 --vedle --ostre --vyrez
   x0,y0,x1,y1`); celý zápis čti jen u kandidátů. U vybledlých knih se
   zápisy snadno přehlédnou – tam raději celé strany.
5. **Pasti:** sňatek bývá v oddílu vsi nevěsty, ale některé fary řadily podle ženicha (Držkov); starší knihy mají
   narozené, oddané a zemřelé proložené a bez obsahu; čísla stran v samostatném rejstříku nemusí sedět se stránkováním
   knihy. Než napíšeš „nenalezeno“, zmapuj **všechny** oddíly.
6. **Samostatné knihy vsí:** velké fary vedly pro některé vesnice vlastní knihy (Nové Strašecí × Pecínov). Hledej knihy
   i podle obce bydliště, ne jen podle fary, a u každé zkontroluj Lokality. **„Nenalezeno“ platí jen pro knihu, která ves
   pokrývá** (skutečná chyba: sňatek „nenalezen“ ve dvou farách, přitom byl ve vesnické knize správné fary).

## Čtení písma
- **Rejstřík čti po sloupcích, ne celou dvoustranu naráz.** Při rychlém čtení sloupce příjmení se jméno snadno přehlédne
  (skutečná chyba: „v rejstříku oddaných 1686–1739 není“, a bylo tam třikrát – rod se pak dohledal o tři generace dál).
  Snímek v plném rozlišení rozřež na svislé pruhy a každý přečti zvlášť, řádek po řádku:
  `python3 -I tools/mapa_knihy.py aron <apu> <snímek> <snímek> --sloupce 4` (nebo `soubory <obrázek>`; hranice podle
  sloupců rejstříku, např. rodič – jméno – rok – folio: `--sloupce 0.3,0.55,0.8`; jednu stranu dvoustrany vybere
  `--vyrez 0,0,0.5,1`). **Negativní výsledek z rejstříku zapiš až po takovém čtení.**
- Ozdobná velká písmena v rejstřících 17. a 18. století řadí jména jinam, než čekáš: **Š psané jako „St“ / „Sſt“**
  (Sſtiepanek = Štěpánek), W místo V a O (Wawra, Wotawa), C/K a G/K zaměněné. Než napíšeš „pod písmenem není“, projdi
  i písmena, pod která mohl písař jméno zařadit.
- Kurentový rejstřík: totéž, plné rozlišení a pruhy (`--sloupce`). **Dopisované řádky** se snadno přečtou špatně
  (Franziska × Heinrich, strana 131 × 151) – údaj z rejstříku vždy ověř v matrice.
- **Vybledlé písmo** (mikrofilm, propiska nebo tužka 1945–1949, celé knihy hlavně v eBadatelně): je-li písmo zápisu
  světlé nebo stránka vypadá skoro prázdná, čti z výřezu s `--kontrast` (`vyrez.py … --kontrast`,
  `overit.py … --kontrast`; jinak `magick x.jpg -colorspace Gray -contrast-stretch 2%x35% x_k.jpg`). Stránku
  **neprohlašuj za prázdnou a zápis za nenalezený**, dokud ji nezkusíš s kontrastem. Do webu pak dej kontrastní výřez
  a poznamenej to v přepisu. Zelený tón snímku: `magick x.jpg -channel G -separate -normalize x_k.jpg`.
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
- Daty bývají svátky (*Dominica*, *festum S. Joannis*) – v nejasných případech dopočítej: *feria* = den v týdnu
  (*feria 2da* = pondělí), neděle se jmenují podle introitu (*Dominica Laetare* = 4. neděle postní), takže
  „feria 2da post Dominicam Laetare“ = pondělí po 4. neděli postní; přesné datum dá věčný (liturgický) kalendář pro
  daný rok (Velikonoce se mění).

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
| *Häusler*, *domunculus* | domkář |
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
| *avus, avia / Großvater, Großmutter* | děd, babička |
| *nepos / Enkel, Neffe* | vnuk i synovec (podle souvislosti) |
| *maritus, uxor / Ehemann, Ehefrau* | manžel, manželka |
| *gener / Schwiegersohn*, *nurus / Schwiegertochter* | zeť, snacha |
| *socer / Schwiegervater* | tchán |
| *vitricus / Stiefvater*, *noverca / Stiefmutter*, *privignus / Stiefsohn* | otčím, macecha, nevlastní syn |
| *tutor, curator / Vormund*, *orphanus / Waise* | poručník, sirotek |
| *gemelli / Zwillinge* | dvojčata |
| *posthumus / nachgeboren* | pohrobek (narozen po otcově smrti) |
| *expositus, inventus / Findelkind* | nalezenec |
| *spurius* | nemanželský (hanlivě) |
| *legitimatus per subsequens matrimonium / legitimiert durch nachfolgende Ehe* | legitimován následným sňatkem rodičů |
| *parvulus*, *infans / Kind* | nemluvně, dítě |
| *in periculo mortis baptizatus / nottgetauft*, *mortuus natus / totgeboren* | pokřtěn z nouze, mrtvě narozený |
| *proclamationes, banna / Aufgebot* | ohlášky |
| *consanguinitas*, *dispensatio / Dispens*, *Konsens* | pokrevní příbuzenství, dispens (od překážky sňatku), povolení k sňatku |
| *provisus sacramentis / versehen* | zaopatřen (svátostmi před smrtí) |
| *Ausgedinger, Auszügler* | výměnkář (předal grunt, žije na výměnku) |
| *colonus* | sedlák |
| *casarius / Chalupner* | chalupník (menší usedlost s polem) |
| *servus, famulus / Knecht*, *ancilla / Magd* | čeledín, děvečka |
| *subditus / Untertan*, *dominium / Herrschaft*, *judex / Richter* | poddaný, panství, rychtář |
| *miles / Soldat*, *miles emeritus / Invalide* | voják, vysloužilec |
| *ludimagister / Schullehrer*, *aedituus / Mesner* | učitel, kostelník |
| *Grund*, *Kaufbrief*, *Waisenbuch*, *Heiratsvertrag*, *Verlassenschaft* | grunt (usedlost), trhová smlouva, sirotčí kniha, svatební smlouva, pozůstalost |
| *Heimatrecht, Heimatschein*, *Entlassungsschein* | domovské právo, domovský list; výhostní list (propuštění z poddanství) |
| *vulgo / genannt*, *olim / ehemals* | řečený (jméno po chalupě), dříve |
| *quondam (q.) / weiland, verstorben*, *hujas / hiesig* | nebožtík (zesnulý), zdejší |
| *annorum 40 / alt 40 J.*, *eodem*, *ut supra (u. s.)*, *anno currente* | 40 let, téhož dne, jako výše, letošního roku |
| *7bris, 8bris, 9bris, Xbris* | září, říjen, listopad, prosinec (ne 7.–10. měsíc!) |
| *febris*, *hydrops / Wassersucht*, *apoplexia / Schlagfluss*, *marasmus senilis / Altersschwäche* | horečka, vodnatelnost, mrtvice, sešlost věkem |
| *dysenteria / Ruhr*, *typhus / Nervenfieber*, *angina, diphtheria / Halsbräune* | úplavice, tyfus, záškrt |
| *morbilli / Masern*, *pertussis / Keuchhusten*, *partus / Kindbett*, *submersus / ertrunken* | spalničky, černý kašel, šestinedělí, utonul |
| *obiit, denatus* | zemřel |
| *phthisis, tabes*, *variolae*, *convulsiones* | souchotiny, neštovice, křeče (u dětí „psotník“) |
| *confirmatus* | biřmován |
| *A.C. / Augsburger*, *H.C. / Helvetisch*, *acatholicus*, *Judaeus*, *conversus* | luterán, kalvinista (evangelík a. v. / h. v.), nekatolík, Žid, konvertita |
| *lanio*, *pistor*, *braxator*, *caupo* | řezník, pekař, sládek, hostinský |
| *figulus*, *faber lignarius*, *murarius* | hrnčíř, tesař, zedník |
| *opilio*, *pastor*, *venator* | ovčák, **pastýř** (ne farář!), myslivec |
| *mendicus*, *testamentum*, *mane / vespere* | žebrák, závěť, ráno / večer |

## Odhad roků
- Věk při úmrtí/sňatku je často zaokrouhlený o ±2–5 let. Uváděj „asi 1756“ a hledej křest v širším okně.
  I přesné datum narození v oddacím zápisu mívá špatný měsíc: když křest v něm není, projdi celý rok ±1 a farnost
  matky (dítě se často narodilo u jejích rodičů).
- Nevěsta mívala 18–28, ženich 22–32; děti po 1,5–3 letech.
- „Vdovec“ u ženicha = hledej první manželství a děti z něj.

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
- Předek v dospělosti „Jan“ byl pokřtěn jako Václav: starší Václav zemřel a mladší dítě dostalo jeho jméno, v dospělosti
  ho volali jinak. V rejstříku proto hledej **všechny děti rodičů** (podle příjmení a domu), ne jen hledané jméno.
- Rejstřík ukazuje „špatné“ křestní jméno ve správné rodině nebo domě? Otevři zápis – písař mohl jméno v matrice
  opravit (přeškrtnuté Jan → František) a do rejstříku se opsalo to původní.
- Sňatek pár měsíců před porodem nebo po něm – není chyba, jen „svatba na poslední chvíli“; zajímavost pro web.
- Nemanželské dítě nese příjmení matky; otec chybí nebo je dopsán později (legitimace na okraji).
- Stejný předek dvakrát v rodokmenu (vzdálení příbuzní se vzali) – v datech `SAME`.
- Index nenašel ≠ zápis neexistuje. Zapiš, co přesně jsi prošel.
- Oddací zápis uvádí „narozen dle mat. IV f. 149“ – podle folia najdeš křest jedním stažením (folio ≈ snímek − posun knihy).
- Čtení pomocníků (subagentů) i jiných nástrojů na čtení písma vždy ověř sám na snímku (princip čtyř očí, SKILL.md → Pomocníci).

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

