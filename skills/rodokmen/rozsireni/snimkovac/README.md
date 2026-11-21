# Snímkovač

Malé rozšíření prohlížeče (Comet, Chrome, Edge), které **samo ukládá snímky matrik, jež si zobrazíš** na eBadatelně
SOA Praha (`https://ebadatelna.soapraha.cz/d/<kniha>/<snímek>`). Nemusíš pak posílat Claudovi snímky obrazovky:
Claude si uložené snímky přečte najednou a může najít souvislosti, které by ti při listování ušly.

## Co dělá
- Při listování na eBadatelně uloží každý nově zobrazený snímek **v plném rozlišení** (původní obrázek, ne snímek obrazovky)
  jako `<kniha>_<snímek>.jpg` a vedle něj malý soubor `.json` (adresa, číslo knihy a snímku, název knihy, čas, rozměry).
- Každý snímek uloží jen jednou. Přiblížení nic nespustí. Přepnutí na další snímek (šipkami, adresou) = nové uložení.
  Znovu otevřený snímek se neukládá podruhé.
- Ikona rozšíření ukazuje počet uložených dnes; v okénku (klik na ikonu) je přepínač **Ukládat: ZAP / VYP**.

## Co NEDĚLÁ (důležité – pravidla projektu)
- **Nelistuje sám, nepředbíhá, nestahuje další snímky, nemá žádné smyčky.** Ukládá jen to, co jsi sám zobrazil.
- Neptá se archivu na nic navíc: kreslí z obrázku, který už stránka načetla (server o ukládání nic nepozná).
- Nic neposílá na internet. Vše jde jen na tvůj disk. Neukládá hesla ani cookies.
- Sám od sebe běží **jen na `ebadatelna.soapraha.cz`**. SOA Praha od 2. 11. 2026 zakazuje roboty a skripty; pasivní uložení
  toho, co zobrazuješ sám, je jediná cesta, kterou tam projekt používá. Rozšíření nikdy nepřidávej žádné automatické procházení.

## Jiné weby (zapíná se ručně, jen na tvé potvrzení)
Na jiném webu rozšíření nic nedělá, dokud ho tam sám nezapneš: otevři stránku, klikni na ikonu, v okénku zaškrtni
„Rozumím“ a klikni na **„Zapnout na tomto webu“**. Prohlížeč se pak jednou zeptá na oprávnění k tomu webu. Seznam webů a jejich stavu je v `weby.js`:
- **povoleno** – pravidla serveru pasivní ukládání nezakazují (sem se web přidává až po přečtení jeho `robots.txt` a podmínek
  užití; zatím je tu jen eBadatelna). Zapne se bez dalšího varování.
- **zakázáno** – server nástroje výslovně zakazuje; před zapnutím výzva, že tím porušuješ jeho pravidla.
- **neověřeno** (MZA a všechno ostatní) – výzva ukáže, co o pravidlech webu víme (u MZA: robots.txt nezakazuje,
  podmínky užití o ukládání mlčí, ale zakazují zveřejňování bez souhlasu), a bez tvého potvrzení se nic nezapne.
  Rozhodnutí i odpovědnost jsou tvoje.
- Zapnutí jde kdykoli vypnout stejným tlačítkem („Vypnout na tomto webu“).
- Funguje jen tam, kde je snímek **jeden velký obrázek** (min. 1200 px široký). Dlaždicové prohlížeče (MZA, SOA Třeboň, ARON,
  Porta fontium) **neumí** – ty chtějí složit dlaždice, to je odložené. Když obrázek pochází z jiného serveru než stránka,
  prohlížeč ho nedovolí přečíst a popup to ohlásí.
- Soubory z cizích webů jdou do `rodokmen-snimky/<název stránky>/`; import je dá do mezipaměti podle adresy obrázku a do
  rejstříku jako archiv `jiny` (kniha = web, snímek = otisk adresy).

## Dlaždicové prohlížeče (MZA Acta Publica a další s OpenSeadragonem)
Po zapnutí na webu (tlačítko „Zapnout na tomto webu“, u MZA s potvrzením) rozšíření ukládá **dlaždice, které prohlížeč
sám načetl** při tvém prohlížení, do úložiště rozšíření. Nic nestahuje navíc, samo nepřibližuje ani neposouvá.
- **Okénko Snímkovače** (klik na ikonu nebo **Alt+S**): nahoře přepínač ukládání. Pod ním **karta „tento web“** s jedním
  hlavním tlačítkem podle stavu (Ukládat na tomto webu / Uložit teď / Povolit focení …) a u dlaždicových prohlížečů
  pruhy pokrytí Přehled / Čtení / Záznam. Méně častá nastavení (hranice úrovní, smazat rozpracovanou stránku, zapomenout
  uložené) jsou v **Pokročilých**, ladicí nástroje (Analyzovat stránku, statistika) v **Pro ladění**.
- **Panel na stránce** (vlevo dole; tažením za tmavou hlavičku ho přesuneš, ▾ sbalí, ⚙ ukáže nastavení; poloha se pamatuje):
  - **Mapa stránky** v barvách úrovní; šedá = neviděno, červená = málo přiblíženo, modrý rámeček = co je vidět.
  - **Přehled / Čtení / Záznam** – cíl (zároveň legenda a pokrytí stránky). Cíl je **detail** = skutečné body obrazu na bod
    snímku, takže funguje stejně na každém PC bez ohledu na škálování Windows.
  - **Další pole ▸** přiblíží na první nehotové pole (jeden klik = jeden pohyb), **Uložit teď** uloží hned.
    Hotovo: „✓ Stránka hotová – můžeš na další“; sbalený panel ukazuje v hlavičce „4/6“.
  - **⚙**: jemné doladění cíle v % a výběr mřížky (auto podle cíle, bez mřížky, 2×1 … 3×3).
  - **Kalibrace:** každý archiv, prohlížeč a počítač potřebuje pro stejnou kvalitu jiné přiblížení (dlaždice ve stupních,
    škálování Windows). Dokud zvolená úroveň na webu není zkalibrovaná, **mřížka se neukazuje** a panel napíše
    „Kalibrace (záznam): přibližuj kdekoli na stránce, dokud místo tmavě nezezelená“. Jakmile zezelená, hodnota se
    **zamkne** pro tento web (✓) a mřížka se objeví. Další stránky ani rozmazané dlaždice na začátku ji nezmění;
    znovu ji nastavíš v ⚙ tlačítkem **Znovu kalibrovat …** (jen zvolená úroveň).
  - Když se nedaří fotit, žlutý pruh řekne proč a nabídne **Fotit teď**.
  - **Focení záložky** (AHMP): Chrome dovolí fotit buď po kliknutí na ikonu (Alt+S, platí do načtení další stránky),
    nebo trvale po jednorázovém povolení „Povolit focení“ (prohlížeč se zeptá na přístup ke všem webům; Snímkovač dál
    fotí jen archivy, které jsi povolil, a nic nikam neposílá).
- **Minimapa** vlevo dole: obdélník stránky, barvy podle nejlepšího uloženého přiblížení v každém místě –
  šedá nic, červená málo, **oranžová přehled** (čitelná jména), **světle zelená čtení**, **tmavě zelená záznam**;
  modrý rámeček = co je teď vidět. Pod ní „Přiblížení 45 %“ (100 % = plné rozlišení snímku) a kolik stránky je
  v přehledu, ve čtení a v záznamu.
- **Prahy** se nastavují v okénku. Výchozí **přehled 25 %, čtení 50 %, záznam 75 %** plného rozlišení – změřeno na MZA
  (14. 11. 2026, Velký Újezd sn. 70): při 25 % jsou jména čitelná, při 50 % skoro jako v plném rozlišení, 12,5 % už
  nestačí; na AHMP (HOS N11 sn. 97) je při 58 % drobné písmo měkké, při 70–80 % ostré → záznam (zápis, který se bude
  přepisovat do rodokmenu) od 75 %.
  Plné rozlišení (100 %) jen u těžko čitelných míst; 50 % potřebuje 4× méně dlaždic než 100 %, 25 % 16× méně.
- Dlaždice zůstávají i po zavření prohlížeče: když se na stejnou stránku vrátíš jindy a přiblížíš jiné místo,
  **snímek se doskládává**.
- **Ukládá se samo:** asi 8 s po posledním přiblížení, při přechodu na jiný snímek a při zavření stránky se snímek
  poskládá a uloží do `rodokmen-snimky/<kniha>/<detail>_<snímek>.jpg`. Každý kus stránky je v nejlepším rozlišení,
  jaké jsi kdy viděl (dlaždice mají pevné místo v mřížce, takže do sebe zapadnou); zbytek je rozmazaný z hrubší
  úrovně, místa bez dlaždic bílá. Další uložení soubor přepíše úplnější verzí. Pod minimapou je „uloženo 14:43“.
- Ty jen listuješ a přibližuješ, kde potřebuješ. Výřezy k osobám si Claude udělá sám z uloženého snímku.
  Když bude potřebovat místo ostřeji, řekne ti třeba „snímek 70, přibliž pravý dolní roh, až na minimapě zezelená“.
- Tlačítko „Uložit teď“ a v části „Pro pokročilé“ uložení výřezu a „Přejít na výřez“ (souřadnice od Clauda) jsou jen záloha.
- Při přiblížení se načítají **jen dlaždice toho, co je vidět**, ne celá stránka. Celou stránku v plném rozlišení
  bys musel projet posouváním – u MZA to zbytečně čerpá denní limit (asi 45 snímků na IP, počítá se i přibližování).
  **Doporučení: ukládej vždy celou stránku, ne jen řádek se zápisem** – celou stránku aspoň
  ve **čtení** (u MZA kvůli limitu stačí **přehled**), zápis navíc v **záznamu**. Celá stránka ukáže sousední zápisy,
  začátek roku a vsi a dá se k ní vrátit bez dalšího stahování.
- **Od 0.16.3:** při procházení polí se snímek skládá a ukládá **až po posledním poli** (dřív po každém poli, to brzdilo);
  jinak po 45 s klidu, při přepnutí snímku nebo odchodu. Na pole tedy nečekej na „Uloženo“, stačí počítadlo polí.
  **Stav pro Clauda skriptem:** `document.querySelector('[data-snimkovac-mapa]').dataset` → `snimek`, `pole` („3/6“),
  `ulozeno` (čas), `uklada` („1“ = čeká na uložení), `skok`, `verze`.
  **MZA – snímek, na který stránka skočila sama** (chybný konec adresy `?image=…`, prohlížeč otevře snímek 1): Snímkovač ho
  sám neuloží a „drž pohled“ na něm nepřibližuje; panel ukáže ⚠ a `skok`. Oprav adresu (konec jména se v knihách liší).
  **„nenačteno N“** v patičce = server dlaždici nevrátil (síť, 403). Dlaždice, které prohlížeč archivu zrušil sám při rychlém
  listování („Image load aborted“), se už jako chyby nepočítají.
- **Po obnovení rozšíření (↻ v chrome://extensions) vždy F5 na stránce archivu** – starý skript se sám odpojí a panel zmizí.
  **Od 0.16.4:** „Držet pohled“ nepřenese výřez menší než 2 % stránky ani přiblížení přes 2× plné rozlišení a přechod na pole
  (Zoomify: AHMP, Třeboň) nepřiblíží víc než 2×; po focení záložky se panel a ovládání archivu ukážou vždy (i když focení selže).
- Soubory: `rodokmen-snimky/<kniha>/<detail>_<snímek>.jpg` (+ `_vyrez_x0_y0_x1_y1`). Importér dá poskládaný snímek
  do mezipaměti a rejstříku (archiv `mza`, kniha = číslo z adresy `detail/<id>`); výřezy nechá ve složce pro Clauda.
- **Počítadlo pro denní limity:** pod minimapou a v okénku je „Dnes: 12 snímků, 840 dlaždic ze serveru (31 MB)“,
  kolik šlo z mezipaměti prohlížeče (to server nevidí) a chyby načtení s časem první chyby. Počítá se ze záznamů
  prohlížeče o stažení, nic se neposílá ven. Odkaz „Uložit přehled počítadla pro Clauda“ uloží historii (60 dní) do
  `_analyza/pocitadlo_<datum>.json` – z ní zjistíme, kde je opravdový limit MZA (poznámky projektu uvádějí asi 45 snímků).
- **Podmínky MZA:** snímky jsou k prohlížení; **zveřejňovat je (i na rodinném webu) bez písemného souhlasu MZA nesmíš.**

## Minimapa: přesun, skrytí, orazítkování
- Mapu přesuneš tažením za lištu „Snímkovač“, tlačítko **–** ji skryje (zůstane jen lišta). Poloha se pamatuje pro každý web.
- **drž** (zapnuto = „drž ✓“): po otevření dalšího snímku nastaví jednou stejné přiblížení a stejné místo jako na
  minulém snímku (třeba pole 1 mřížky). Bez „drž“ (nebo když ještě žádný pohled zapamatovaný není) ukáže celou stránku,
  pokud ji archiv otevřel přiblíženou (AHMP otevírá vpravo dole na největší přiblížení). Stane se to asi 1,5 s po otevření
  a jen když jsi mezitím sám nic neposunul ani nepřiblížil. Vypneš ho kliknutím; volba se pamatuje pro každý web.
- **Mřížka auto** (první volba tlačítka mřížky): vedle tlačítka je políčko s **cílovým přiblížením** (výchozí 76 %, tedy
  těsně nad záznamem; pamatuje se pro každý web). Rozšíření samo spočítá, kolik polí je potřeba, aby každé vyplnilo
  obrazovku přesně v tomto přiblížení, a **klik na pole přiblíží přesně na cíl** – nemusíš ladit kolečkem.
  Počet polí závisí na velikosti okna prohlížeče: čím větší okno (celá obrazovka F11, schovaný panel náhledů), tím méně
  polí. AHMP dvojstrana 4000×3000 při 76 % v okně 1537×794 = 3×4 pole.
- **Mřížka** (tlačítko na liště: vyp → 2×1 → 1×2 → 2×2 → 2×3 → 3×2 → 3×3, vždy sloupce × řádky; 2×1 = levá a pravá polovina (AHMP); vyber tu, kde jedno pole
  zhruba vyplní obrazovku v přiblížení pro čtení – u dvojstrany na širokém monitoru bývá nejlepší 2×3): mapa se rozdělí na pole s čísly. Pole, které už máš celé aspoň
  ve čtení, dostane ✓, v záznamu ✓✓; pod mapou je „Pole: čtení 3/4, záznam 1/4“. **Klik na pole na mapě** přiblíží prohlížeč na to pole
  (s malým překryvem) – jedno přiblížení na jedno tvoje kliknutí, jako bys přiblížil ručně. Tempo určuješ ty:
  počkej, až se pole vykreslí a na mapě zezelená, pak klikni na další. Rozšíření samo nikam nepřechází
  (pravidelné automatické procházení by server mohl vyhodnotit jako robota).

## Fronta ZIPů z eBadatelny (od 0.17.0)
Server eBadatelny pustí jen jedno stahování naráz (další vrátí chybu 500). Fronta ti hlídá, kdy ZIP doběhl, a přichystá
další knihu. **Stahování spouštíš vždy ty kliknutím**.
1. Otevři stránku knihy (`https://ebadatelna.soapraha.cz/pages/MatrikaPage/matrikaId/<id>`), vpravo dole je panel (tažením za zelené záhlaví ho přesuneš, poloha se pamatuje)
   „Snímkovač – fronta ZIPů“. Klikni **Do fronty** a kartu nech otevřenou. Tak přidej nejvýš 5 knih.
2. První kniha je hned na řadě: Snímkovač přepne na její kartu, otevře „Popis knihy“, zeleně orámuje
   **Stáhnout knihu jako ZIP**, pípne a ukáže oznámení systému. Klikneš ty.
3. Když ZIP doběhne, Snímkovač počká 10 s a stejně přichystá další knihu.
4. Klik na „Stáhnout“ u jiné knihy, zatímco se ještě stahuje, Snímkovač zadrží a napíše, na co čekáš (jinak by přišla chyba 500).
5. Když stahování selže (500, přerušení, odhlášení), fronta **stojí**. Nic se neopakuje samo, pokračuješ tlačítkem **Pokračovat**.

**Hranice:** do fronty přidáváš ty a na stažení klikáš ty. Rozšíření nic nestahuje samo, nečte přihlášení ani cookies
a nevolá odkazy `…-downloadZip`. Běží jen v otevřených kartách: zavřená karta z fronty zmizí a zavřením prohlížeče
se fronta smaže. SOA Praha od 13. 11. 2026 omezuje automatizované nástroje, proto rozšíření jen upozorní a samo neklikne.
Claude frontu neovládá. ZIPy se ukládají do složky stahování prohlížeče; rozbalit je jde potom zvlášť.

## Bez bubliny stahování
Snímkovač ukládá na pozadí: na dobu ukládání vypne bublinu „stahování“ prohlížeče (oprávnění `downloads.ui`)
a asi 1,5 s potom ji zase zapne. Uložené soubory jsou dál v seznamu stahování (Ctrl+J). Když si v té krátké chvíli
stáhneš něco jiného, bublina se pro to taky neukáže. Prohlížeč, který to neumí, bublinu ukazuje dál.

## AHMP – Praha Publica (katalog.ahmp.cz, digi.ahmp.cz)
- Prohlížeč Zoomify jako v Třeboni, ale dlaždice jdou z jiného serveru (images.ahmp.cz) a stránka je nesmí číst.
  Snímkovač proto ukládá **snímek viditelné části záložky** (jako snímek obrazovky): po ustálení pohledu na chvilku
  skryje minimapu, vyfotí záložku a vyřízne z ní stránku snímku. Nic se nestahuje. Dál platí minimapa, mřížka,
  „drž“ i skládání – jen rozlišení je dané obrazovkou, takže pro čtení stačí 2×1 nebo 1×2, pro záznam 2×2.
- Funguje jen v **aktivní záložce** (snímek obrazovky jde jen z toho, co je vidět). Kdyby minimapa hlásila
  „snímek obrazovky nepovolen“, klikni na ikonu Snímkovače (prohlížeč tím dá jednorázové povolení té záložce).
- **Pravidla:** robots.txt obou katalogů zakazuje všem robotům celý web; podmínky online katalogu o nástrojích nic
  neříkají. Badatelna AHMP dovoluje kopie vlastním zařízením pro osobní studijní potřebu. Proto je AHMP vedené jako
  neověřené: zapnutí chce zaškrtnout „Rozumím“. Snímky jen pro vlastní bádání.

## Matricula Online (rakouské a další matriky)
- Prohlížeč Matriculy si stáhne **celý snímek najednou** (žádné dlaždice). Snímkovač ho po zobrazení uloží celý
  v plném rozlišení – nemusíš nic přibližovat ani používat mřížku.
- Zapnutí: ikona → **Zapnout na tomto webu** → **obnov stránku (F5)**. Snímek, který byl otevřený už před zapnutím,
  se zachytí až po obnovení nebo přechodu na další snímek.
- Ukládá se do `rodokmen-snimky/Matricula <farnost> <signatura>/<farnost>_<signatura>_<snímek>.jpg` a `.json`
  (číslo snímku = `?pg=` v adrese, název stránky v knize, např. „03-Taufe_0187“, a původní adresa obrázku).
- **Pravidla:** snímky jsou pod licencí CC BY-NC-ND 2.0 – pro vlastní bádání v pořádku; zveřejnit jen nekomerčně,
  s uvedením zdroje (odkaz) a s informováním archivu. robots.txt zakazuje automatické procházení stránek snímků –
  listuj jen ručně, jako dosud.
- Import: `tools/snimky_import.py` je zapíše do mezipaměti (`matricula/<diecéze>/<farnost>/<signatura>/snNNNN.jpg`)
  a do rejstříku jako archiv `matricula`, kniha `<diecéze>/<farnost>/<signatura>`.

## SOA Třeboň (prohlížeč Zoomify ve vloženém rámu)
Po zapnutí na `digi.ceskearchivy.cz` funguje stejně jako u MZA (minimapa, prahy, samo se ukládá, doskládává se).
Adresy dlaždic jsou tu zašifrované, proto se neberou dlaždice, ale **to, co prohlížeč vykreslil**: když se pohled
ustálí (asi 1,5 s a znovu po 5 s, kdyby se dokreslovalo), uloží se viditelná část plátna i s polohou na snímku.
Nic se nestahuje navíc. Číslo snímku se bere z prohlížeče („Snímek 43“); trvalý odkaz portálu má číslo o jedna
větší (`/2231/44`). Kniha se jmenuje podle titulku stránky („Bílsko 12 1811-1895“).
Pozor: u Třeboně každé otevření snímku stáhne dlaždice znovu – na snímku přibliž vše, co potřebuješ, najednou.

## Analýza stránky (pro nové badatelny)
Tlačítko **„Analyzovat stránku“** v okénku funguje na kterémkoli webu (i nepovoleném) a uloží zprávu
`rodokmen-snimky/_analyza/<web>_<čas>.json`. Claude z ní pozná, jak daná badatelna snímky zobrazuje, a napíše pro ni úpravu.
Ve zprávě je:
- velké obrázky, plátna (`canvas`), typ prohlížeče snímků (OpenSeadragon, Zoomify, Leaflet, IIIF, DeepZoom …),
- vzory adres obrázků a dlaždic, které si stránka **už sama stáhla** (ze záznamu prohlížeče, žádný nový dotaz),
- výběry a pole s čísly snímků, texty v horní liště (název knihy), odkazy na podmínky užití,
- **robots.txt** webu: jestli zakazuje tuto stránku všem robotům, jestli žádá pauzu mezi dotazy a jestli jmenovitě
  zakazuje AI roboty (např. PerplexityBot, ClaudeBot). Shrnutí se ukáže hned v okénku.

Projde i vložené rámy stránky (SOA Třeboň má prohlížeč v rámu) a u každého plátna zjistí, jestli ho rozšíření
smí přečíst (obraz z cizího serveru bez povolení CORS přečíst nejde – pak se snímek uložit nedá). U prohlížeče Zoomify
(SOA Třeboň, ZA Opava, SOA Litoměřice) zapíše rozměry snímku a dlaždic.

Jediný dotaz na server navíc je načtení `/robots.txt` (jednou, po kliknutí). Z adres se mažou hodnoty parametrů
(mohou v nich být přístupové tokeny), cookies se nečtou. Složku `_analyza` importér přeskakuje.
robots.txt je jen dobrovolná dohoda pro automatické procházení webu; co smí uživatel s rozšířením a se snímky, říkají
podmínky užití nebo badatelský řád archivu – ty si přečti zvlášť (odkazy na ně jsou ve zprávě).

## Instalace (Comet / Chrome), jednou
1. Otevři `chrome://extensions` (v Cometu stejně).
2. Vpravo nahoře zapni **Režim pro vývojáře**.
3. Klikni **Načíst rozbalené** a vyber složku `nastroje/snimkovac` z projektu Rodokmen.
4. Rozšíření se objeví v seznamu. Připni si ho z ikony skládačky u adresního řádku (ať vidíš počítadlo a přepínač).
5. Nastavení prohlížeče → Stahování: **vypni „Před stažením se zeptat, kam soubor uložit“**, jinak bude vyskakovat okno u každého snímku.

Po změně souborů rozšíření v `chrome://extensions` klikni na kulatou šipku (obnovit) a stránku archivu načti znovu.
Každá úprava zvyšuje číslo verze – je vidět v `chrome://extensions` a dole v okénku rozšíření, takže poznáš, že máš novou.
Povolené weby (MZA aj.) si rozšíření po obnovení samo zaregistruje znovu.

## Jak to vyzkoušet
1. Otevři libovolný snímek na eBadatelně, např. `https://ebadatelna.soapraha.cz/d/<id>/<snímek>`.
2. Počkej, až se snímek načte (pár sekund). Na ikoně rozšíření naskočí číslo 1.
3. Ve složce **Stažené / rodokmen-snimky / <název knihy> /** je `<id>_<snímek>.jpg` a `.json`.
4. Šipkou přejdi na další snímek: číslo naskočí na 2. Vrať se na předchozí: číslo se nezmění.
5. V okénku přepni na **VYP**: další snímky se neukládají.

Název knihy se bere z hlavičky stránky (poslední část za „/“, např. „Benešov 58“). Pokud ji rozšíření nenajde, složka se
jmenuje `kniha <číslo>`; snímky to nerozbije. Napiš, ať se výběr názvu doladí.

## Předání Claudovi
V projektu spusť (nebo to nech udělat Clauda):

```
python3 -I tools/snimky_import.py
```

Skript projde `~/Downloads/rodokmen-snimky`, uloží snímky do sdílené mezipaměti (`tools/cache.py`, pak je najde
`cache.py najdi <adresa>` i `tools/ebadatelna.py`), zapíše řádky do rejstříku `data/snimky.tsv` (stav `nejisty` =
uloženo, ještě nepřečteno) a zpracované soubory přesune do `_importovano/`. Jiná složka: `… snimky_import.py <složka>`;
jen náhled: `--nahled`; nechat soubory na místě: `--nechat`. Uložené snímky jsou JPEG překódovaný z canvasu (kvalita 92),
ne bajt po bajtu původní soubor.

## Odloženo na později
- **ZA Opava**, SOA Litoměřice (Zoomify bez rámu?) a další prohlížeče (IIIF …): nejdřív „Analyzovat stránku“.
- Sdílený rejstřík přečtených zápisů pro jiné badatele (mimo tento repozitář): do veřejného rejstříku patří jen přečtené
  zápisy a čísla snímků, **ne obrázky**.
