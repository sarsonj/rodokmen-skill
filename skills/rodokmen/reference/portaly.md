# Portály archivů a jak z nich dostat snímky

Matriky jsou online u osmi státních archivů – podle toho, **kde předci žili** (dnešní kraje zhruba odpovídají):

| Archiv | Oblast | Portál s matrikami | Vyzkoušeno se skillem |
|---|---|---|---|
| SOA Zámrsk | východní Čechy (Hradecký a Pardubický kraj) | ARON – aron.vychodoceskearchivy.cz | **ano – hotové nástroje** |
| SOA Praha | střední Čechy | eBadatelna – ebadatelna.soapraha.cz | **jen v prohlížeči** – archiv nástroj od 2. 11. 2026 zakazuje (postup níže; i urbáře a gruntovní knihy) |
| SOA Plzeň | západní Čechy | Porta fontium – portafontium.eu | **ano – nástroj `portafontium.py`** |
| SOA Třeboň | jižní Čechy | digi.ceskearchivy.cz | **jen v prohlížeči** – archiv nástroj od 2. 11. 2026 odmítá (postup níže) |
| SOA Litoměřice | severní Čechy | Digitální badatelna – digi.soalitomerice.cz | **částečně – `soal_zoomify.py`** (knihu najdi v prohlížeči) |
| AHMP | hl. m. Praha | katalog.ahmp.cz (Pragapublica) | **ano – `ahmp_search.sh`, `ahmp_scan.py`** |
| MZA Brno | jižní Morava, Vysočina z části | Acta Publica – www.mza.cz/actapublica | **jen v prohlížeči** – snímek obrazovky přiblíženého zápisu (postup níže) |
| ZA Opava | severní Morava a Slezsko, Olomoucko a Litovelsko | Digitální badatelna – digi.archives.cz/da/ | **jen v prohlížeči, nejlépe Playwright** – celý snímek z dlaždic, které načte prohlížeč (postup níže; CAPTCHU řeší uživatel) |
| Národní archiv | židovské matriky (HBMa), soupisy; pražské policejní přihlášky 1850–1914 | HBMa: VadeMeCum NA – vademecum.nacr.cz (Digitální badatelna → Matriky židovských náboženských obcí; stará adresa badatelna.eu už nepatří archivu); digi.nacr.cz/prihlasky2 | přihlášky **ano – `policie_prihlasky.py`** |

Adresy u nevyzkoušených portálů ověř při prvním použití (portály se mění). Pro pohraničí a mimo ČR viz `metodika.md`
(Matricula pro Rakousko/Německo, Geneteka pro Polsko, FamilySearch pro Slovensko) a níže. Hroby na Slovensku
(i na několika českých hřbitovech) najde `tools/cintoriny.py`, viz oddíl Hroby a hřbitovy.

**Claude in Chrome – výstup JavaScriptu** (platí pro všechny portály):
- Výstup, který obsahuje adresu s parametry (`?`, `&`, `=`) nebo dlouhý hex, rozšíření zahodí jako
  „[BLOCKED: Cookie/query string data]“. Vracej jen cestu (`location.pathname`, `new URL(a.href).pathname`) a hodnoty
  parametrů zvlášť, případně znaky `?&=` nahraď mezerami; celou adresu slož až v shellu.
- Výstup se ořízne asi na 1000 znaků (u seznamů asi 30 řádků) – delší seznamy vypisuj po částech (`.slice(0, 25)`, …).
- Snímky obrazovky na těžkých stránkách padají na timeout; text čti přes `get_page_text` / `read_page` nebo
  `innerText`.

## ARON (SOA Zámrsk) – hotové nástroje
- **Hledání svazků:** `python3 -I tools/aron_search.py "Holice"` → řádky `apu_id | signatura, roky | druh, obce`.
  Popis obsahuje druh knihy (NAROZENÝCH / ODDANÝCH / ZEMŘELÝCH, index) a všechny obce farnosti.
- **Informace o svazku:** `python3 -I tools/aron_img.py <apu_id> info` → název a počet snímků.
- **Stažení snímku:** `python3 -I tools/aron_img.py <apu_id> <snímek> 1 pracovni/holice_n_57.jpg`
  (úroveň 1 = poloviční rozlišení – stačí na orientaci; 0 = plné rozlišení – na čtení a výřez).
  Jen část stránky v plném rozlišení: `… <snímek> 0 pracovni/detail.jpg 0.0,0.4,1.0,0.7`.
  Nástroj stáhne celý sken jedním požadavkem (jako tlačítko „stáhnout“ v ARONu) a zmenšení i výřez dělá z disku;
  další výřezy téže stránky už na archiv nejdou. Dlaždice (desítky pomalých požadavků) jen jako záloha.
- **Odkaz na snímek** (pole `odkaz` v `zaznamy.json`): `python3 -I tools/aron_img.py <apu_id> link <snímek>`.
- **Svazek do dat:** `python3 -I tools/aron_img.py <apu_id> svazek` (klíč = prvních 8 znaků apu_id → pole `svazek` v zápisu).
- V ARON jsou i další fondy (sčítání lidu, některé gruntovní knihy, kroniky) – `aron_search.py "Obec" "název fondu"`.
- Stejnojmenných obcí bývá víc (Vinice u Hořic × Vinice u Velké Jesenice). Výsledky jsou seřazené podle farnosti;
  zúžit jde víc slovy oddělenými čárkou, která musí být v popisu všechna: `aron_search.py "Vinice,Hořice"`
  (nebo hledej sousední obec či farní obec).
- U starých far hledej nejdřív **souhrnné indexy** (popis „index NAROZENÝCH…“ přes mnoho let), často sahají do 17. století.
- Obec nenalezena? Zkus název **bez přívlastku** („Lhota“ místo „Horní Lhota“) a starý název. Starší matriky
  (před ~1784) bývají ve faře sousedního města; indexy fary mají oddíly po vesnicích
  („Copulati Gross Lhota“).
- Ber ohled na server: stahuj jen to, co čteš; žádné hromadné stahování celých svazků.

## SOA Třeboň (digi.ceskearchivy.cz) – jen v prohlížeči
- **Od 2. 11. 2026 archiv nástroj odmítá** (HTTP 403 podle User-Agentu „rodokmen“), `trebon.py` je odstraněn a brzda
  skripty na digi.ceskearchivy.cz zastaví. Neobcházej to (jiný User-Agent, vlastní skript). Matriky čti v prohlížeči
  (nejlépe Playwright) stejně jako u MZA: přiblížit zápis, uložit snímek obrazovky, `vyrez.py`. Tempo 5–10 s mezi
  stránkami (SKILL.md, Šetrně k archivům), jen stránky, které čteš, žádní pomocníci. Bez prohlížeče ať pošle snímky
  obrazovky uživatel.
- Obec: `https://digi.ceskearchivy.cz/<Obec>` (bez diakritiky a mezer, např. `RatiborskeHory`) → stránka místa, vlevo
  „Matriční knihy“ (stránka je v rámci `ram_obsah`) → seznam knih s roky a obcemi; kliknutí otevře knihu v nové záložce.
  **Zkontroluj název a okres**: u stejnojmenných obcí portál vybere jinou (Buk → Bukovka), u měst i okres nebo synagogu.
  Malé osady portál nezná (Malá Chyška) – hledej farní nebo sousední obec a osadu v popisu knih.
- Snímek: `https://digi.ceskearchivy.cz/<kniha>/<snímek>` (zároveň trvalý odkaz). Knihy mívají dobrovolnický jmenný
  rejstřík (stránka místa → „Rejstříky“) – obrovská úspora; ne každá kniha ho má.
- **Každé zobrazení snímku stáhne všechny dlaždice znovu** – i šipka zpět na snímek, který byl právě na obrazovce
  (rám se načte znovu s novým tokenem, mezipaměť prohlížeče nepomůže). Na snímku proto vyřiď všechno najednou: přibliž
  a přečti všechny zápisy, které můžeš potřebovat, než přejdeš dál.
- Prohlížeč je Zoomify v rámci `ram_obsah`. Postup: snímek okna (scale css) → odečti rohy zápisu → úryvek níže
  (browser_evaluate) schová panely Navigátor a Náhledy, přiblíží zápis a vrátí odkaz `/<kniha>/<snímek>/<x>/<y>/<zoom>/0`
  přímo na zápis (do `odkaz`) → snímek okna v rozlišení zařízení do `pracovni/trebon_<kniha>_<snímek>.png` → `vyrez.py`
  (ořízni lištu nahoře a dole):
  ```js
  async () => {
    const [x0, y0, x1, y1] = [185, 688, 590, 795];   // rohy zápisu na snímku okna (CSS px)
    const f = document.querySelector('iframe[name=ram_obsah]'), d = f.contentDocument, vp = f.contentWindow.Z.Viewport;
    if (!d.getElementById('rodokmen-skryj')) d.head.insertAdjacentHTML('beforeend',
      '<style id="rodokmen-skryj">#navigat_b,#thumbs_b{display:none!important}</style>');
    const r = f.getBoundingClientRect(), z = vp.getZoom(), c = vp.calculateCurrentCenterCoordinates();
    const W = vp.getViewW(), H = vp.getViewH();
    const obr = (x, y) => ({x: (x - r.left - W / 2) / z + c.x, y: (y - r.top - H / 2) / z + c.y});
    const a = obr(x0, y0), b = obr(x1, y1);
    vp.zoomAndPanToView((a.x + b.x) / 2, (a.y + b.y) / 2, Math.min(W / (b.x - a.x), H / (b.y - a.y)));
    await new Promise(ok => setTimeout(ok, 6000));
    return location.href;
  }
  ```
  Souřadnice ber vždy z aktuálního snímku okna (po načtení stránky nebo `vp.reset()`), ne ze staršího.
- Svazek do `svazky.json` přes `zapis.py` (Ostatní portály, krok 4, klíč `trebon_<kniha>`).
- Některé fary mají knihy po vesnicích, které nejsou v seznamu knih místa (Vacov → Žár) – hledej podle titulků knih fary.
- **Civilní matriky (1920–1945) lidí bez vyznání** jsou v knihách okresních úřadů (např. Tábor, kniha 12304) a mají
  dobrovolnický rejstřík. Dobrá cesta, když farní matrika mlčí. U obce se neukážou (patří okresu) – hledej u okresního města.

## SOA Plzeň (Porta fontium, portafontium.eu) – `tools/portafontium.py`, bez prohlížeče
- **Obec → knihy:** `portafontium.py obec "<obec>"` → všechny knihy s obcí v popisu, seskupené podle fary a seřazené podle
  let (kniha | obce | roky a druhy: `*` N, `oo` O, `+` Z, `i` index | popis). Je z něj vidět i přechod obce mezi farami
  (Bučí: Dolní Bělá do 1795, Krašovice od 1787) a civilní matriky okresních úřadů. Portál hledá i historické a podobné
  názvy – stejnojmenné obce jiných far (Bučí × Buč u Komárova) vyřaď podle sloupce obcí. Nic nenalezeno? Zkus jiný tvar
  (Stajanovice × Stojanovice, německý název) nebo sousední obec.
- `portafontium.py fara <fara>` → všechny knihy fary ve stejném tvaru. `<fara>` je název („Dolní Bělá“, „Mýto“ –
  diakritiku nástroj odstraní) nebo část adresy fary (`dolni-bela`); stejnojmenné fary mají příponu okresu
  (`plana-ps`, `radnice-ro`) – správnou adresu ukáže `obec`.
- `portafontium.py info <kniha>` (`dolni-bela-17`) → signatura, druh, text desky a **obsah** – u knih psaných po vesnicích
  vypíše, na kterých foliích je která obec („Ves X z let 1862–1901 = fol. 121–200“).
- `portafontium.py snimek <kniha> <snímek> pracovni/x.jpg [nahled] [x0,y0,x1,y1]` → celá stránka v plném rozlišení jedním
  požadavkem (IIIF), `nahled` = 1/4. Číslo snímku = pořadí náhledu v prohlížeči; soubory nesou číslo folia
  (`dolni-bela-17_0951` = fol. 95), takže u knih se souvislou foliací je **snímek ≈ folio**.
  Odkaz z cizího rodokmenu (MyHeritage) s `…_0450` v adrese je proto folio 45, ne snímek – stáhni i sousední snímek.
- `link <kniha> <snímek>` → trvalý odkaz, `svazek <kniha>` → `svazky.json` (klíč `pf_<kniha>`).
- **Tempo:** portál žádá 10 s mezi dotazy (robots.txt „Crawl-delay: 10“) – brzda to drží sama, i u snímků.
- Bez prohlížečového User-Agentu portál vrací 403 (nástroj ho posílá). Jmenné hledání portál nemá – indexy jsou jen uvnitř knih
  (`*i`, `ooi`, `+i` v seznamu knih fary).

## SOA Praha (eBadatelna, ebadatelna.soapraha.cz) – jen v prohlížeči
- **Od listopadu 2026 archiv omezuje i automatizovaný provoz** (oznámení na úvodní stránce: „automatizované bezpečnostní
  opatření a limity“). Čtení v prohlížeči tempem člověka dál funguje (ověřeno 13. 11. 2026 v Playwrightu). Narazíš-li
  na stránku s omezením, „Forbidden“ nebo snímek, který se nenačte, skonči: `python3 -I tools/slusne.py zastav
  ebadatelna.soapraha.cz "omezení v prohlížeči"` a čtení předej uživateli.
- **Od 2. 11. 2026 archiv nástroj zakazuje** (robots.txt „User-agent: rodokmen – Disallow: /“, HTTP 403),
  `ebadatelna.py` stahovat nesmí (fungují `link`, `a-link` a `snimek` ze snímků uložených z prohlížeče) a brzda
  skripty na soapraha.cz zastaví. Neobcházej to (jiný User-Agent, vlastní skript, fetch). Matriky čti v prohlížeči
  (nejlépe Playwright).
  Tempo 5–10 s mezi stránkami (SKILL.md, Šetrně k archivům), jen stránky, které čteš, žádní pomocníci. Bez prohlížeče
  ať pošle snímky obrazovky uživatel.
- Hledání: Matriky → pole „lokalita“ vyplň obcí bez posledního písmene (`browser_type`) a poslední písmeno napiš
  se `slowly` (teprve to ukáže našeptávač; psaní po písmenech do prázdného pole se připojí k textu „lokalita“). Vyber
  celý název (`.ui-menu-item`, „Obec - obec X - okres Y“), Vyhledat. Seznam knih jedním `browser_evaluate`:
  `[...document.querySelectorAll('table tr')].map(r => [...r.cells].map(c => c.innerText.trim()).join(' | ') + ' | ' + (r.querySelector('a')?.getAttribute('href') ?? ''))`
  (kniha | původce | okres | lokality | roky N, O, Z, indexy | snímků | `/pages/MatrikaPage/matrikaId/<id>`).
- Popis knihy: `https://ebadatelna.soapraha.cz/pages/MatrikaPage/matrikaId/<id>` (archiválie
  `…/pages/ArchivaliePage/archivalieId/<id>`) – `document.body.innerText`. „Obecný popis matriky“ uvádí u knih psaných
  po vsích **rozvržení stran** („1–48 Ves A, 49–82 Ves B …“, každá ves může mít vlastní stránkování) – neodhaduj snímek
  podle roku, ale podle stran vsi; je-li rejstřík, začni jím.
  Archiv popis ořezává asi na 250 znaků (konec rozvržení chybí) – úplný seznam vsí je v poli Lokality, zbytek viz
  `matriky.md` (Knihy řazené po vsích).
- Snímek: `https://ebadatelna.soapraha.cz/d/<matrikaId>/<snímek>` (archiválie `/a/<archivalieId>/<snímek>`, zároveň
  trvalý odkaz, do `odkaz`; šipky „<“ a „>“ v prohlížeči na tuto adresu taky přejdou). Prohlížeč načte celý snímek
  v plném rozlišení. **Ulož ho jednou do mezipaměti a dál pracuj z disku** – archiv už nedostane žádný další dotaz.
  Při listování ulož každý zobrazený snímek hned (uložení archiv nic nestojí) a před dalším krokem se podívej, jestli
  další snímek už nemáš – pak ho čti z disku a v prohlížeči přejdi rovnou na adresu toho, který ještě nemáš:
  1. Už ho máš? `python3 -I tools/cache.py najdi <adresa snímku> --nahled pracovni/nahled.jpg` – vypíše cestu
     a udělá náhled (1600 px), pak prohlížeč neotevírej.
  2. Jinak otevři adresu, počkej na načtení (pár s) a ulož ho (`browser_evaluate` s `filename: "pracovni/ebad.json"`):
     ```js
     () => {
       const im = document.getElementById('scanImage');
       if (!im || !im.complete || !im.naturalWidth) return 'snímek se ještě načítá – zkus to za chvíli';
       const c = document.createElement('canvas'); c.width = im.naturalWidth; c.height = im.naturalHeight;
       c.getContext('2d').drawImage(im, 0, 0);
       return JSON.stringify({w: c.width, h: c.height, adresa: location.origin + new URL(im.src).pathname.split(';')[0],
                              data: c.toDataURL('image/jpeg', 0.92)});
     }
     ```
     a `python3 -I tools/cache.py uloz pracovni/ebad.json --nahled pracovni/nahled.jpg` (uloží snímek, udělá náhled
     1600 px ke čtení stránky a soubor .json smaže).
  3. Jiný náhled nebo výřez z uloženého snímku bez sítě: `python3 -I tools/ebadatelna.py snimek <matrikaId> <snímek>
     pracovni/x.jpg [nahled] [x0,y0,x1,y1]` (archiválie `a-snimek`), dál `vyrez.py` jako u jiných archivů.
  Bez Playwrightu (Claude in Chrome neumí výsledek uložit do souboru) ať snímek uloží uživatel (snímek obrazovky).
- Starší snímky bývají z mikrofilmu nebo silně vybledlé – výřez dělej s `--kontrast` (`vyrez.py`, `overit.py`;
  viz `matriky.md`, Čtení písma) a poznamenej to v přepisu.
- Svazek do `svazky.json` přes `zapis.py` (Ostatní portály, krok 4, klíč `ebad_<matrikaId>`, archiválie `ebad_a_<id>`).
  Denní údržba portálu kolem 4:44 (asi 2 minuty); večer a v noci bývá nedostupná (zhruba 22:45–0:45 a kolem 2:00).

## AHMP Praha – `tools/ahmp_search.sh`, `tools/ahmp_scan.py`
- `bash tools/ahmp_search.sh "Smíchov"` → svazky Sbírky matrik: popis | farnost | (XID, id, počet snímků).
- `python3 -I tools/ahmp_scan.py <XID> <snímek> pracovni/x.jpg [1] [x0,y0,x1,y1]` → snímek (1 = poloviční rozlišení).
- Trvalý odkaz `https://katalog.ahmp.cz/pragapublica/permalink?xid=<XID>&scan=<N>`.
- Nový portál digi.ahmp.cz má ochranu proti robotům – nepoužívat. Pražské matriky 1890–1940 většinou **nemají rejstříky**
  a farností je mnoho – bez přesného data a farnosti (z úmrtí/sňatku nebo od rodiny) je hledání velmi drahé.

## SOA Litoměřice (severní Čechy) – `tools/soal_zoomify.py`
Stejný software jako ZA Opava (Digitální badatelna; Opava ale nástroje už nepouští) – platí i tamní pasti (`vysledekDetail` přímou adresou ukáže jiný
svazek, výstup JavaScriptu bez parametrů v Claude in Chrome).
- `https://digi.soalitomerice.cz/digitalnibadatelna/` má na vstupu automatické ověření (asi 15 s „počítání“, projde
  samo) → knihu a cestu k obrázkům najdi v prohlížeči (Playwright nebo Claude in Chrome), snímky stahuj nástrojem.
- **Hledání:** ikona Matriky a obec do pole **„Místo / Lokalita“** (hlavní fulltext vrací všech ~18 000 matrik), Enter.
  Výsledky všechny najednou (počet na stránku přepni jedním výběrem, neprocházej stránky). Svazek otevři kliknutím
  ve výsledcích a **na detailu ověř signaturu**. Popis knihy uvádí „Územní rozsah“ (obce knihy) – čti ho první.
  Knihy bývají **rozdělené po obcích** s vlastním stránkováním a rejstříkem na konci.
- **Adresy snímků** (záložka snímků, `actualDetailTab=attachmentsImg`) zjisti úryvkem – jen pro snímky, které čteš
  (nejvýš pár najednou), postupně s pauzou 3 s (`browser_evaluate`; na stránce téhož svazku, jinak showZoomify vrací prázdnou odpověď):
  ```js
  async () => {
    const snimky = [1, 50, 120];   // jen snímky, které opravdu čteš
    const ent = document.querySelector('[entityuuid]').getAttribute('entityuuid');
    const ids = Object.fromEntries([...document.querySelectorAll('select.getScanSelect option')].map(o => o.value.split('%20')));
    const out = [];
    for (const n of snimky) {
      if (!ids[n]) { out.push(`${n}: snímek v knize není`); continue; }
      const h = await (await fetch(`/digitalnibadatelna/showZoomify/${ent}/${ids[n]}`)).text();
      if (h.trim().length < 300 && !/images\//.test(h)) { out.push(`${n}: BLOKACE („${h.trim().slice(0, 20)}“) – přestaň na 35 minut`); break; }
      const m = h.match(/https?:\/\/images\.[^"'\s]+?\/images\/[^"'\s]+?\.jpe?g/i);
      out.push(`${n}: ${m ? m[0] : 'adresa v odpovědi nenalezena'}`);
      await new Promise(ok => setTimeout(ok, 3000));
    }
    return out.join('\n');
  }
  ```
  Složka v cestě (`…/images/0046/…`, `…/NAD-856/dao/images/0701/…`) se liší mezi knihami i uvnitř jedné knihy –
  adresu nikdy neskládej, vždy celou z výstupu.
- Snímky stahuj nástrojem: `python3 -I tools/soal_zoomify.py "<celá adresa>" 0 pracovni/x.jpg` (0 = plné rozlišení,
  1 = poloviční, 2 = čtvrtinové na orientaci). Obrázkový server images.soalitomerice.cz neomezuje a cookies nepotřebuje.
- **POZOR na blokaci aplikace** (obrázky ne): přijde už po 25–100 rychlých krocích (listování výsledky, Zpět, rychlé
  `fetch`). Ohlásí ji stránka „!“ s **HTTP 200** (asi 116 bajtů) – kontroluj obsah, ne stavový kód. Dotazy jen postupně
  (žádné `Promise.all`), pauza aspoň 3 s, vždy jen jedna smyčka; po blokaci 35 minut nic (další pokusy ji prodlužují).
  Pomocníkům to napiš do zadání.
## ZA Opava (severní Morava, Slezsko, Olomoucko, Litovelsko) – jen v prohlížeči, nejlépe Playwright
- Pozor na hranici: obce na Litovelsku a Olomoucku patří pod **ZA Opava**, ne pod MZA Brno.
- **Bez prohlížeče to nejde.** Badatelna `https://digi.archives.cz/da/` (stará adresa matriky.archives.cz jen přesměruje)
  má ochranu proti robotům (Radware) a od listopadu 2026 nepouští nástroje ani k obrázkům (robots.txt „Disallow: /“,
  images.archives.cz vrací skriptům 403/404) – `soal_zoomify.py`, curl ani WebFetch, brzda je zastaví. Archiv na úvodní
  stránce upozorňuje, že nestandardní práce s aplikací vede k blokaci: pracuj jako člověk, jeden snímek po druhém.
  **Doporučený prohlížeč je Playwright** – jen v něm jde snímek uložit celý (níže). Jde i Claude in Chrome (uživatel ho
  připojí příkazem `/chrome`), tam ale jen snímky obrazovky přiblíženého zápisu. Bez prohlížeče ať knihu najde a snímky
  uloží uživatel.
  **Vestavěný prohlížeč aplikace Claude** (desktop, Code) archiv odmítne hned („Anomaly detected“) – nepoužívej ho.
  Úvodní ověření projde samo, ale jen v kartě v popředí. Okno nastav aspoň na 1400×900, v užším se nezobrazí
  filtry ani snímek. **CAPTCHA přijde typicky už u prvního hledání**, pak zhruba po hodině a v nové relaci
  prohlížeče vždy znovu: **vyřeší ji uživatel** v okně prohlížeče, ty nikdy.
- Hledej obec a vyfiltruj Matriky (ikona, potom znovu lupa). Hledání vrací i civilní matriky (u obce stovky svazků) –
  filtr „Datum od – do“ (podle začátku svazku, např. 1680–1873) nechá jen církevní. Knihy bývají řazené po obcích
  a na konci mají rejstřík. Vedle farních knih bývají i **druhopisy** („T“ v signatuře, viz `matriky.md`).
  Když pole Signatura „zamrzne“ a vrací pořád předchozí knihu, napiš obec do hlavního fulltextového pole (Enter)
  nebo ji vyber v poli „Územní rozsah“ z našeptávače.
- **Detail svazku nikdy neotvírej přímou adresou `vysledekDetail/<id>`.** Badatelna drží výsledky hledání v relaci
  a taková adresa ukáže N-tý (bez `page` první) výsledek posledního hledání nebo snímky naposledy otevřeného
  svazku – ne svazek z adresy. Svazek otevři trvalým odkazem `https://digi.archives.cz/da/permalink?xid=<id>`
  (id je konec cesty odkazu ve výsledcích, `vysledekDetail/<id>`) – ten ukáže svazek podle id bez ohledu na poslední
  hledání, ale jen v prohlížeči, který už prošel ověřením. Jinak klikni ve výsledcích (ikona snímků v řádku, nebo
  mozaika výsledků a dvojklik na náhled). **Vždy na stránce ověř signaturu a název knihy**, než z ní cokoli čteš.
- **Seznam svazků a ID snímků si hned ulož** do `pracovni/<svazek>/` – relace po pár hodinách vyprší a výsledky
  hledání platí jen v ní. Na detailu svazku: entita `document.querySelector('[entityuuid]').getAttribute('entityuuid')`
  (u svazků uložených v jiném archivu nemá tvar UUID – nehledej ji regexem), ID snímků jsou hodnoty
  `select.getScanSelect option` (tvar „N%20uuid“). Snímek pak otevřeš kdykoli bez hledání (jediná přímá adresa,
  která na relaci nezávisí):
  `/da/showZoomifySeparate?imageNumberSeparate=N&myEntityUuid=<entita>&myImageUuid=<uuid>`.
- **Snímek celý (Playwright)** – funkci ke stažení badatelna nemá a snímek posílá jen po dlaždicích 256 px; obrázky
  nemají CORS, takže je stránka sama do souboru nesloží. Playwright ale umí zachytit dlaždice, které si prohlížeč snímků
  při přiblížení sám načte – archiv nedostane žádný dotaz navíc a snímek pak čteš z disku (ověřeno 13. 11. 2026):
  1. Už ho máš? `python3 -I tools/cache.py najdi "<adresa showZoomifySeparate…>" --nahled pracovni/nahled.jpg`
     (vypíše cestu a rozměr) – pak snímek neotvírej.
  2. Otevři snímek **jeho adresou** `showZoomifySeparate…` (ne šipkami v prohlížeči – adresa určuje klíč v mezipaměti),
     počkej na načtení a spusť `browser_run_code_unsafe`; prohlížeč snímků přiblíží a projde stránku po pohledech
     (2,5 s na pohled, jako když ji člověk posouvá):
     ```js
     async (page) => {
       const z = 0.5;   // 0.5 = poloviční rozlišení, na čtení stačí; 1 = plné (4× víc dlaždic) jen na těžko čitelné místo
       const img = await page.evaluate(() => Z.imagePath);
       const dl = await page.evaluate(() => window.__dlazdice || {});   // při opakování doplní jen chybějící
       const h = async (r) => { const m = r.url().match(/TileGroup\d+\/(\d+-\d+-\d+)\.jpg/);
         if (m && r.url().startsWith(img) && r.status() === 200) try { dl[m[1]] = (await r.body()).toString('base64'); } catch {} };
       page.on('response', h);
       const [W, H, vw, vh] = await page.evaluate(() => [Z.imageW, Z.imageH, Z.viewerW, Z.viewerH]);
       const sx = vw / z, sy = vh / z, nx = Math.ceil(W / sx), ny = Math.ceil(H / sy);
       const stred = (n, i, s, D) => n === 1 ? D / 2 : Math.min(D - s / 2, s / 2 + i * s);
       for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
         await page.evaluate(([x, y, zz]) => Z.Viewport.zoomAndPanToView(x, y, zz), [stred(nx, i, sx, W), stred(ny, j, sy, H), z]);
         await page.waitForTimeout(2500);
       }
       page.off('response', h);
       await page.evaluate((t) => { window.__dlazdice = t; }, dl);
       return `${Object.keys(dl).length} dlaždic, ${nx * ny} pohledů`;
     }
     ```
  3. Slož snímek (`browser_evaluate` s `filename: "pracovni/zaopava.json"`):
     ```js
     async () => {
       const t = window.__dlazdice || {}, T = 256, dims = [];
       for (let w = Z.imageW, h = Z.imageH; ; w = Math.ceil(w / 2), h = Math.ceil(h / 2)) { dims.unshift([w, h]); if (w <= T && h <= T) break; }
       const L = Math.max(...Object.keys(t).map(k => +k.split('-')[0])), [W, H] = dims[L];
       const c = document.createElement('canvas'); c.width = W; c.height = H; const g = c.getContext('2d');
       let chybi = 0;
       for (let y = 0; y < Math.ceil(H / T); y++) for (let x = 0; x < Math.ceil(W / T); x++) {
         const b = t[`${L}-${x}-${y}`]; if (!b) { chybi++; continue; }
         const i = new Image(); i.src = 'data:image/jpeg;base64,' + b; await i.decode(); g.drawImage(i, x * T, y * T);
       }
       return JSON.stringify({w: W, h: H, chybi, adresa: location.href, data: chybi ? '' : c.toDataURL('image/jpeg', 0.92)});
     }
     ```
     a `python3 -I tools/cache.py uloz pracovni/zaopava.json pracovni/x.jpg --nahled pracovni/nahled.jpg` (uloží snímek
     do mezipaměti a do `pracovni/x.jpg`, udělá náhled). Chybí-li dlaždice, zopakuj krok 2 (doplní jen ty chybějící).
     Dál `vyrez.py` jako u jiných archivů. Plné rozlišení (`z = 1`) přepíše v mezipaměti poloviční, opačně ne.
  Jen snímky, které čteš, žádné dávky celých svazků ani pomocníci na tomto archivu.
- **Claude in Chrome** odpovědi zachytit neumí: přibliž zápis (`Z.Viewport.zoomAndPanToView(x, y, 0.6)` na stránce
  `showZoomifySeparate`, souřadnice originálu, rozměr v `Z.imageW`/`Z.imageH`) a ulož snímek obrazovky; dlaždice
  nestahuj ani neskládej vlastním `fetch`/`new Image()` – to jsou dotazy navíc, které prohlížeč sám nedělá.
- **POZOR na blokování**: rychlé dotazy → CAPTCHA, „operace vyhodnoceny jako
  nestandardní“ nebo „Access blocked“ na 30 minut. Pauza aspoň 5 s mezi stránkami, stránky výsledků neprocházej
  za sebou a nepouštěj smyčky na pozadí ani dávky celých svazků. **Žádný `fetch`** (na `showZoomify`, permalinky
  ani nic jiného) – ochrana proti robotům ho zachytí, u permalinků hned napoprvé; čísla a adresy snímků zjišťuj
  jen běžnou navigací, po jednom.
  - **Denní limit:** oficiální archiv neuvádí; ze zkušenosti asi **50 snímků** (a 200–300 stránek aplikace) za den.
    Pak „Server Exception“ v okně snímku, „Přístup zablokován!“ i na úvodní stránce. Po prvním odmítnutí ten den
    skonči (`python3 -I tools/slusne.py zastav digi.archives.cz "denní limit"`) – druhé odmítnutí blokaci prodlouží.
  - **„Server Exception“ hned po CAPTCHA** (přesměrování přes `/da/human/verify`) limit není: otevři znovu
    `https://digi.archives.cz/da/` nebo adresu snímku; když to nepomůže, jednou zavři a znovu otevři prohlížeč
    (Playwright `browser_close`) – ověření pak obvykle projde samo. Teprve potom ber chybu jako limit.
- **Totéž na FamilySearch:** matriky ZA Opava (sbírka „Czech Republic, Church Books, 1552–1981“, signatury
  `217000010-…`) a pozemkové a gruntovní knihy Opavy a Olomouce („Land Records, 1450–1889“) jsou na FamilySearch
  v plném rozlišení a bez CAPTCHY – dobrá náhrada, když Opava blokuje nebo došel denní limit (postup v oddílu
  FamilySearch níže). Svazek páruj přes „vol. NNNN“ v katalogu FS = inventární číslo ZA Opava (popisky let ve FS bývají
  chybné). **Čísla snímků se liší knihu od knihy** (0, ±1, někde +7 až +8, jinde jiné pořadí listů): před čtením
  z FS porovnej stránku s archivem (folio nebo pagina, rok, aspoň dvě jména), nikdy nepočítej s odhadnutým posunem.
  Do `odkaz` dej snímek, ze kterého jsi opravdu četl.

## MZA Brno (jižní Morava, Acta Publica) – jen v prohlížeči
- Portál `https://www.mza.cz/actapublica/`, bez přihlášení. **Od 2. 11. 2026 MZA blokuje stahovací skripty** (ověření
  Altcha, adresy dlaždic s tokenem) a výjimky nedělá. Skriptem jen hledání knih (níže, brzda 1 dotaz za 4 s, jiné
  adresy MZA brzda zastaví). Snímky jen v jejich prohlížeči: přiblížit zápis a uložit snímek obrazovky. Žádné
  stahování, `fetch` ani skládání dlaždic, žádní pomocníci. **Prohlížeč: Playwright** (uloží snímek do souboru).
  **Vestavěný prohlížeč Claude desktop pro MZA nepoužívej** – podle hlášení uživatelů dostává na snímky 403 i po dni
  pauzy, zatímco běžný prohlížeč projde. Bez Playwrightu ať uživatel otevře snímek ve svém prohlížeči a pošle snímky
  obrazovky sám (celá dvoustrana na orientaci, pak přiblížený zápis – kolečko myši, macOS Cmd+Shift+4,
  Windows Win+Shift+S) a ulož je do `pracovni/`.
- Kniha: `python3 -I tools/slusne.py curl -s "https://www.mza.cz/actapublica/matrika/hledani?typ=obec&search_by_obec=<obec>&page=<n>"`
  → HTML tabulka (číslo knihy, původce, roky N/O/Z, počet snímků, odkaz `matrika/detail/<id>`; číslo knihy ≠ id).
  Výsledky po 20 – projdi i další stránky, než řekneš, že tam obec není. U velkých far jsou samostatné svazky rejstříků (N/O/Z) – začni jimi. Fary založené
  kolem 1784 mají starší zápisy v mateřské faře. Ověření na detailu knihy proběhne samo za pár sekund.
- Detail knihy má „Části matriky“ s rozsahy snímků (narození 1–43, index narozených 43–93, u knih pro víc obcí po obcích).
  Snímek s hledaným rokem odhadni (snímky ÷ roky). Rejstříky uvádějí stranu, ne snímek: přečti čísla stran na 1–2 snímcích
  a dopočítej (vztah bývá lineární, kniha od knihy jiný).
- **Listuj v otevřené stránce** (`viewer.goToPage(n-1)`, šipky) – návrat na už zobrazený snímek jde z mezipaměti
  prohlížeče a MZA nic nestojí. Stránku neobnovuj a adresu snímku znovu neotvírej: nové načtení dostane nový token
  a stáhne všechny dlaždice znovu.
- Prohlížeč je OpenSeadragon v proměnné `viewer`: `viewer.goToPage(n-1)`, `viewer.viewport.goHome(true)` a snímek okna
  (scale css) – rok a měsíc v záhlaví. U nalezeného zápisu odečti z aktuálního snímku okna rohy zápisu a přibliž ho
  úryvkem (browser_evaluate); pak ulož snímek prvního prvku `.openseadragon-container` v rozlišení zařízení do
  `pracovni/mza_<kniha>_<snímek>.png` (Playwright ukládá jen do složky projektu) a dál `vyrez.py` jako u jiných portálů:
  ```js
  async () => {
    const [x0, y0, x1, y1] = [145, 435, 595, 500];   // rohy zápisu na snímku okna (CSS px)
    const vp = viewer.viewport, e = viewer.container.getBoundingClientRect();
    const P = (x, y) => vp.pointFromPixel(new OpenSeadragon.Point(x - e.left, y - e.top));
    const a = P(x0, y0), b = P(x1, y1);
    vp.fitBounds(new OpenSeadragon.Rect(a.x, a.y, b.x - a.x, b.y - a.y), true);
    await new Promise(ok => setTimeout(ok, 5000));
    return location.href;
  }
  ```
- Nezobrazuj celou stránku v plném rozlišení (velké okno) – stovky dlaždic naráz a MZA vrací 503. Tempo 5–10 s mezi
  stránkami (SKILL.md, Šetrně k archivům), jen stránky, které opravdu čteš. Když ověření nepustí nebo MZA hlásí chybu, skonči a řekni to uživateli.
- **Blokace snímků (403):** MZA po zhruba 45–60 snímcích za den (počítá se každé přiblížení – stahuje nové dlaždice)
  přestane vydávat obraz: stránka i ověření projdou, ale snímek zůstane bílý a dlaždice vrací 403. **Není to pomalé
  načítání – okamžitě přestaň**, nezkoušej znovu a řekni to uživateli. Blokace trvala i druhý den; další den zkus nejvýš
  jeden snímek.
- Dlaždice vracející **410** není blokace – vypršel token v adrese; stačí znovu otevřít stejnou adresu snímku (`?image=…jp2`).
- Trvalý odkaz = adresa v prohlížeči `…/matrika/detail/<id>?image=<soubor>.jp2` (soubor končí číslem snímku × 10:
  snímek 16 → `…-00160.jp2`). Svazek do `svazky.json` přes `zapis.py` (Ostatní portály, krok 4).
- Doména actapublica.eu MZA nepatří (MZA to potvrdila) – nepoužívej ji, jen www.mza.cz/actapublica. Když MZA nejde
  načíst ani v prohlížeči, ať uživatel zkusí vypnout VPN nebo jinou síť.
- **Sčítací operáty (1857–1921) nejsou v Acta Publica**, ale v samostatném portálu
  `https://www.mza.cz/scitacioperaty/digisada/search` – jen v prohlížeči (brzda jiné adresy MZA nepustí), stejná pravidla
  jako u matrik: žádné stahování ani skládání dlaždic. Hledej obec (pole „Město/obec nebo část obce/osada“); sada =
  jedna obec a jeden rok (u obce bývá jen některý rok, např. jen 1921), s rozsahem čísel popisných. Detail
  `…/digisada/detail/<id>` má stejný prohlížeč `viewer` jako matriky (postup výše). Snímek 1 je soupis s metadaty
  (rozpis čísel, poznámky typu „čp. 134 má 2 archy“), pak archy po domech. 1857 uvádí jen rok narození, 1869 a 1880
  místo i datum; sloupec dat narození bývá psaný svisle – při čtení přiblížený výřez otoč o 90°.

## Pražské policejní přihlášky 1850–1914 (Národní archiv) – `tools/policie_prihlasky.py`
- Karty pražských rodin: hlava rodiny, manželka s rokem a místem narození, děti s roky, adresy, někdy místo sňatku.
  Výborné, když rodina žila v Praze a nevíš farnost (pražské matriky nemají rejstříky).
- `python3 -I tools/policie_prihlasky.py Kolar [Jan] [1850] [1870]` – příjmení bez diakritiky (začátek jména), jméno a roky
  narození volitelně. Bez prohlížeče vrátí jen prvních 20 výsledků, proto hledej co nejúžeji.
  Kartu stáhni `policie_prihlasky.py karta <pořadí> pracovni/karta.jpg Kolar [Jan] [1850] [1870]` (stejné hledání; jde i pořadí
  nad 20) – vypíše citaci a trvalý odkaz (`index.php?action=link&ref=czarch:CZ-100000010:874&karton=K&folium=F`).
- **Nepokrývá Smíchov, Vinohrady, Žižkov, Karlín a další předměstí před 1922** (byla to samostatná města). Náboženství karty neuvádějí.

## Matricula (Rakousko, Bavorsko, Polsko…; data.matricula-online.eu) – `tools/matricula_*.sh`
- Bez přihlášení. Seznam knih: `…/de/oesterreich/<diecéze>/<farnost>/?page=N`; snímek knihy `…/<id>/?pg=<snímek>`
  (zároveň trvalý odkaz).
- URL obrázku obsahuje `csrf` a `ctrl` počítané JavaScriptem → je potřeba prohlížeč (Playwright / Claude in Chrome):
  otevři knihu, klikni na stránku (`.docview-pagelink`), URL obrázku vezmi z `performance.getEntriesByType('resource')`
  a stáhni `bash tools/matricula_dl.sh "<url>" pracovni/x.jpg`. Víc stránek: soubor řádků „<snímek> <url>“ → `matricula_batch.sh`.
- Rejstřík najdeš bez prohlížeče: HTML stránky knihy má seznam `labels` s popisky snímků („04-Index Taufe_0001“).
- Vojenské matriky (např. Štýrský Hradec) tam nejsou – jsou v Kriegsarchivu ve Vídni (offline).

## Polsko – Geneteka (geneteka.genealodzy.pl)
- Zdarma dobrovolnické indexy křtů, sňatků a úmrtí po farnostech; hledej ve webovém rozhraní (vojvodství → farnost →
  příjmení). Index je vodítko – skeny často online nejsou (farní nebo diecézní archiv), pak zápis žádej tam.
- **Farní příslušnost se měnila**: obec mohla patřit k sousední faře (Lipowa → Radziechowy do 1896) – hledej i tam.
- Nestahuj hromadně: PTG uvádí „linkujemy, nie pobieramy danych“ (odkazujeme, nestahujeme) a po desítkách rychlých dotazů
  server vrací nefiltrovaná data. Dotazy dávkuj, s pauzami, a výsledky si ověř.
- Jednotlivý dotaz jde i bez prohlížeče: `https://geneteka.genealodzy.pl/api/getAct.php?draw=1&start=0&length=10&bdm=B&rid=B&w=12sl&search_lastname=<příjmení>&search_name=&search_lastname2=&search_name2=&from_date=1850&to_date=1900&exac=1`
  (`bdm`/`rid` B křty, S sňatky, D úmrtí; `w` vojvodství, např. 12sl slezské, 08op opolské) → JSON. Past: `recordsTotal` > 0
  a prázdné `data` – zkus jen jedno příjmení bez křestního jména a užší roky. Stránkování opakuje řádky.
- Skeny některých polských far jsou i na Matricule (výše) nebo FamilySearch (níže).

## FamilySearch (přes uživatelův přihlášený prohlížeč)
- Přihlášení je potřeba i na hledání v indexech. České matriky tam skoro zindexované nejsou (Slovensko ano, hlavně křty).
- Jen když ho má uživatel otevřený a sám nabídne. Z kontextu stránky lze volat JSON API
  `https://www.familysearch.org/service/search/hr/v2/personas?q.surname=…&q.givenName=…&q.fatherGivenName=…&count=20`
  (`fetch(…, {credentials:'include'})`); výsledky v `entries[].content.gedcomx`.
- Užitečné na indexy matrik a hroby (BillionGraves, Find a Grave). Výsledek je vodítko – ověř v matrice.
- Neměň uživateli otevřené karty (po hledání vrať původní adresu). Stránky za Cloudflare neobcházej – ať je uživatel
  otevře sám a pošle snímek obrazovky.
- Snímky filmu (DGS): seznam přes `POST /search/filmdatainfo/image-data` s `{"type":"film-data","args":{"dgsNum":"00…","state":{"i":"0"},"locale":"cs"}}`
  (`images[]` = ARK). Snímek: `https://www.familysearch.org/service/records/storage/deepzoomcloud/dz/v1/<ARK 3:1:…>/$dist`
  (plné rozlišení), malé náhledy `…/image_files/8/0_0.jpg`. **Po ~1000 rychlých požadavcích přijde HTTP 429** a blokace
  na desítky minut – stahuj jen konkrétní snímky, nanejvýš pár za sekundu, hromadné procházení knih nedělej.
- **Slovensko** (sbírka „Slovakia Church and Synagogue Books 1592–1935“; bez účtu FamilySearch to nejde):
  1. **Fara:** katalog `https://www.familysearch.org/search/catalog/results?q.keywords=Farský úrad <obec>` (také
     „Grécko-katolícka …“, „Evanjelická …“). Najde i fary celého okolí – v závorce za farou je obec, pod kterou je
     katalog vede. Hledání podle místa (`q.place`) a maďarské názvy obcí často nenajdou nic nebo stejnojmennou obec v ČR.
  2. **Natočené roky:** v záznamu fary přečti tabulku filmů (`browser_evaluate`, jen text, bez odkazů):
     `[...document.querySelectorAll('tr')].map(r => [...r.cells].map(c => c.innerText.trim()).join(' | '))`
     → Poznámka (druhy a roky) | Film | **DGS**. Název záznamu přeceňuje: „Cirkevná matrika, 1762–1927“ má křty,
     sňatky i úmrtí jen do **1895** (do 1927 jen biřmování). Po ~1895 vedl stát civilní matriky – mladší zápisy jsou
     ve státním archivu nebo na matričním úřadě (na Slovensku státní matriky 100 let od posledního zápisu; církevní knihy v archivu po 90 letech od zápisu), ne online.
  3. **Index je neúplný** (hlavně křty) a jména zkomolená, u dvou křestních jmen bývá jen jedno; `q.anyPlace`
     výsledky nefiltruje, jen řadí. Hledej přes rodiče a bez křestního jména, jinak listuj snímky filmu (DGS výše;
     nejdřív rejstřík „Zoznam krstov A–Z“, bývá na začátku knihy).
  4. **1900–1940:** doklady od rodiny (rodné listy dětí uvádějí i prarodiče), náhrobky a evidence hrobů (Košice:
     gisplan.kosice.sk; cintoriny.sk jen část obcí). Rusíni vedení po 1950 jako pravoslavní mají starší zápisy
     v řeckokatolických knihách.
- **Snímek do projektu (Playwright):** nástroje dostanou od FamilySearch 403, snímek vydá jen přihlášený prohlížeč.
  Uživatel se jednou přihlásí v okně Playwrightu (přihlášení zůstane). ARK snímku je v adrese prohlížeče
  (`/ark:/61903/3:1:…`) i ve výsledcích hledání. Nejdřív `python3 -I tools/cache.py najdi <adresa nebo ark>
  --nahled pracovni/nahled.jpg` – je-li snímek už uložený, prohlížeč nepotřebuješ. Jinak `browser_evaluate`
  s `filename: "pracovni/fs.json"`:
  ```js
  async () => {
    const ark = '3:1:XXXX-XXXX-XXX';
    const adresa = `https://www.familysearch.org/service/records/storage/deepzoomcloud/dz/v1/${ark}/$dist`;
    const r = await fetch(adresa, {credentials: 'include'});
    if (!r.ok) return `HTTP ${r.status} – snímek nejde stáhnout (přihlášení? omezený snímek?)`;
    const b = await r.blob(), bm = await createImageBitmap(b);
    const data = await new Promise(ok => { const f = new FileReader(); f.onload = () => ok(f.result); f.readAsDataURL(b); });
    return JSON.stringify({w: bm.width, h: bm.height, adresa, data});
  }
  ```
  a `python3 -I tools/cache.py uloz pracovni/fs.json pracovni/fs_<ark>.jpg --nahled pracovni/nahled.jpg` (snímek
  v plném rozlišení do mezipaměti i do `pracovni/`, json smaže). Dál `vyrez.py` jako u jiných archivů.
- **Bez Playwrightu (Claude in Chrome neumí ukládat do souboru):** ať uživatel snímek stáhne tlačítkem Download
  (nebo ho se souhlasem stáhneš ty) – soubor přijde do `~/Downloads` jako `<id snímku>.jpg`, chvíli může mít
  příponu `.tmp`. Přesuň **jen soubor s očekávaným názvem**, nikdy „nejnovější soubor ve Stažených“ (je tam i cizí).
  Žádné vlastní přijímače na localhostu ani jiné obcházení ochran prohlížeče.

## Hroby a hřbitovy
- Kde jsou předci pohřbeni, víš z rozhovoru s rodinou (Fáze 1). Fotky náhrobků (jména, data, rodná příjmení) jsou
  cenný pramen hlavně pro 20. století, kde matriky ještě nejsou přístupné.
- Evidence hrobových míst: správa hřbitova (kdo je v hrobě uložen, kdo platí nájem – často žijící potomek);
  řada měst má online vyhledávání hrobů. Mezinárodně BillionGraves a Find a Grave.
- **cintoriny.sk** (Slovensko, i několik českých hřbitovů – Motol, Strašnice, Vodňany…) – `tools/cintoriny.py`, bez prohlížeče a bez přihlášení:
  - `cintoriny.py hledat --prijmeni Izso [--jmeno J] [--rodne R] [--obec Lučenec | --hrbitov 1459] [--narozeni-od 1900 --narozeni-do 1910] [--umrti-od/-do]`
    vypíše jméno, data narození a úmrtí, věk, hřbitov s obcí a `hrob <hřbitov>:<hrob>`. Hledá od začátku slova a bez diakritiky
    (Kováč najde i Kovács, Izso i Izsof), po 50 záznamech na stránku (`--stran N`, výchozí 2). Ženy hledej i podle rodného příjmení (`--rodne`).
  - `cintoriny.py hrob 68:68002334 [--foto pracovni/hrob.jpg]` ukáže kartu hrobu: sektor, řadu, číslo (i dřívější), všechny uložené v hrobě
    s daty narození, úmrtí a uložení, rodným příjmením a místem narození, pokud je správa vede. Odkaz na kartu jde do `zdroje`.
  - `cintoriny.py hrbitovy "Obec"` vypíše hřbitovy v obci s ID pro `--hrbitov`.
  - Na Slovensku po roce 1900 matriky online nejsou, a tak hrob často jako jediný ukáže, kdo leží spolu (manželé, děti, rodiče), a dá přesné datum narození.
    **Datum 1. 1. bývá zástupné** (správa znala jen rok) a evidence správy hřbitova není matrika – data ber jako vodítko (stav `mh`) a ověř v matrice.

## Noviny a ročenky – `tools/anno.py`, `tools/anno_snap.py`, `tools/kramerius.py`
**Kdy se vyplatí:** státní a vrchnostenští úředníci, soudci, učitelé, faráři, důstojníci, vojenští lékaři, notáři,
poštmistři, starostové, podnikatelé – noviny otiskovaly jmenování, přeložení, vyznamenání, penze, konkurzy, oznámení
sňatků a parte (zhruba od 1860). Z toho plyne, **kde člověk kdy žil** → kde hledat křty dětí, sňatek, úmrtí.
A když osoba „chybí“ v očekávaných matrikách (stěhovala se se službou). **Spíš ne:** sedláci a řemeslníci na vsi.
- ANNO (rakouské noviny 1700–1950, i Prager Zeitung, Wiener Zeitung): `python3 -I tools/anno.py '"Johann Nowak"' 1860 1915 [stran] [--snip]`
  – jména **německy** („Johann Nowak“, „Wenzel Dworschak“). Výřez místa: `tools/anno_snap.py <docId> "<dotaz>" pracovni/x.jpg`.
  ALEX a annoshow jsou za Cloudflare – neobcházet.
- Kramerius NK ČR (české noviny, ročenky, adresáře): `python3 -I tools/kramerius.py 'text_ocr:"Jan Novák" AND datum_begin:[1900 TO 1910]'`.
- Vojenské schematismy: fulltext na archive.org (např. `militrschematis13kriegoog` = 1850).
- **Vojáci 1. světové války – seznamy ztrát** (ANNO, plný text): `python3 -I tools/anno.py '"Příjmení Jméno"' 1914 1919 3 --snip --ztraty`
  (jen `vll` Verlustliste, `vlv` abecední rejstřík s číslem seznamu, `nvv` Nachrichten über Verwundete; jiné listy
  `ANNO_TITLE=ptb,wrz`). Záznam: hodnost, pluk, setnina, **domovská obec, ročník**, raněn/zajat/padl – např.
  „Hromadko Wenzel, Inft., IR. Nr. 98, 4. Marschkomp., Rokosnitz, 1881, Schuß …“. Pořadí je „Příjmení Jméno“, německy
  (Wenzel, Johann) a zkus i bez háčků; shodu potvrď obcí a ročníkem. Běžná příjmení mají tisíce výskytů – hledej
  vzácným příjmením nebo domovskou obcí v německém tvaru. Krajské noviny otiskovaly seznamy padlých okresu.
  Padlí na frontě v domovské matrice zemřelých často nejsou. Kartotéka padlých VÚA je jen v Digitální badatelně MO
  po registraci (stará databáze VÚA už neexistuje).
- **Rizika:** jména se opakují a fulltext šumí („Winter“ = i zima, „Novák“ = nový obyvatel). Ztotožni jen při shodě víc údajů (bydliště,
  funkce navazující na matriku, časová posloupnost). Zdroj je „J“ (jiný pramen) – vodítko a příběh, ne náhrada matriky.
- Výstřižky jsou skvělé na web: ulož do `dokumenty/noviny/`, přes `vyrez.py` a do `dokumenty.json`.
- Pořadí: nejdřív matriky; noviny, když chybí stopa kvůli stěhování, nebo když jde o úředníka/vojáka a chceme příběh.

## Ostatní portály – obecný postup
Nástroje pro ně hotové nejsou. Postupuj takto a výsledek zapiš do `STAV.md`, ať to příště víš:
1. Otevři portál v prohlížeči (Claude in Chrome / Playwright, pokud jsou k dispozici; jinak požádej uživatele).
   Najdi fond „Sbírka matrik“ / „Matriky“ a svazek podle obce a let.
2. **Snímek:** většina prohlížečů má tlačítko ke stažení obrázku – ulož do `pracovni/`. Když ne, podívej se v síťovém
   provozu, odkud se načítají dlaždice/obrázky (IIIF, DeepZoom, Zoomify), a stáhni celý obrázek touto cestou – jednotlivě,
   jen snímky, které čteš, a jen když to archiv nezakazuje (`<portál>/robots.txt`, podmínky užití). Krajní možnost: požádej uživatele, ať snímek uloží a dá do `pracovni/`.
3. **Trvalý odkaz** na snímek (tlačítko „trvalý odkaz“/permalink, jinak URL svazku + číslo snímku) dej do `odkaz` v zápisu.
4. Svazek zapiš přes nástroj: objekt `{"archiv": "SOA Třeboň", "portal": "digi.ceskearchivy.cz",
   "svazek": "N Volary 1784–1820, sign. …", "popis": "obce…", "url": "<odkaz na svazek>"}` napiš do `pracovni/svazek.json`
   a spusť `python3 -I tools/zapis.py svazky <klíč> pracovni/svazek.json` (ručně ani skriptem `svazky.json` neupravuj).
5. Dál stejně jako u ARON: `vyrez.py`, `ramecek.py`, přepis, osoby, deník.
6. Když se postup osvědčí, napiš pro portál vlastní malý nástroj podle `portafontium.py` (bez prohlížeče, jen když to archiv nezakazuje)
   a postup zapiš do `STAV.md`. Poznatek zapiš i do `poznamky_pro_skill.md` (pro správce skillu).

## Starší prameny (17.–18. století)
- **Soupis poddaných podle víry 1651** – celé rodiny s věkem, po krajích; edice Národního archivu jako PDF
  (nacr.cz, hledej „Soupis poddaných podle víry“ + kraj). Fulltext v PDF, příjmení často bez diakritiky / s jinou ortografií
  (Šaršoun → „Šaroun“, dlouhé ſ jako f). Ves je v rámci panství; poznamenej si stránku edice.
- **Berní rula 1654** – jen hospodáři s půdou; edice a rejstříky v knihovnách (Kramerius/DNNT).
- **Gruntovní (pozemkové) knihy** – převody domů z otce na syna; online jen část: SOA Plzeň téměř vše, SOA Praha část,
  **SOA Třeboň** pozemkové knihy velkostatků (jen v prohlížeči: stránka obce → „Pozemkové knihy“; kniha je vidět jen
  u obce, ke které je přiřazená – hledej i u sídla panství), **ZA Opava** urbáře a pozemkové knihy v Digitální
  badatelně (snímky na stejném serveru jako matriky). Část knih z Třeboně a Opavy je i na FamilySearch („Czech Republic,
  Land Records, 1450–1889“). Ostatní archivy spíš badatelna. Fond „Velkostatek <panství>“.
- **Mapy stabilního katastru (1824–43)** – kde stál dům s číslem popisným: ags.cuzk.gov.cz/archiv (Archiv ČÚZK; stará adresa archivnimapy.cuzk.cz už nefunguje).
  Na **císařských otiscích** chybí u části listů barvy a čísla domů. Lepší jsou **indikační skici**: mají čísla domů
  a u pozemků jméno majitele („N. 13“ = patří k domu čp. 13). Dům bez pozemků mimo ves = domkář bez polí.
  Jméno majitele samotného domu bývá jen v písemném operátu (archiv, ne online). Výřezy map patří na web k rodině.
  - **Postup (jen v prohlížeči, služby jsou za tokenem – ten si stránka bere sama, nevypisuj ho):** na ags.cuzk.gov.cz/archiv
    najdi katastrální území, klikni do mapy na obec → „Indikační skici“ (nebo „Císařské povinné otisky“) → ID rastru
    (např. `HRA235018400`). Skica pak jde otevřít přímo: `https://ags.cuzk.gov.cz/archiv/openmap.html?typ=skicic&idrastru=<ID>`
    (list otisku `typ=cioc`); načítá se asi 20 s. ID rastru dá i tlačítko `#btn_skicic` v okně obce. Osada často nemá
    vlastní katastr (Polom → k. ú. Lhota u Dobrušky) – hledej podle sousední obce.
  - **Ostrý výřez vsi (lepší než snímek obrazovky):** stránka si skicu kreslí voláním `…/archiv_nespojene_skici/ImageServer/exportImage`
    (u otisku obdobná služba) s `bbox` v S-JTSK a `size` v pixelech. V prohlížeči (javascript) vezmi poslední takovou adresu
    z `performance.getEntriesByType('resource')`, přepočítej `bbox` na výřez vsi (bod obrázku px, py → x = x0 + (x1−x0)·px/W,
    y = y1 − (y1−y0)·py/H podle původního `bbox` a `size`), `size` nastav na šířku 2000–4000 px ve stejném poměru stran
    (server pustí nejvýš 15000 × 4100) a obrázek stáhni přes `fetch` ve stránce. Token v adrese nech být a nevypisuj ho.
    Uložení: `URL.createObjectURL(blob)` → odkaz `<a download="skica_obec.jpg">` a klik (prohlížeč ho uloží do stažených
    souborů, Playwright do své výstupní složky), pak přesuň do `dokumenty/`. Kolem 1,4 m na pixel jsou čitelná jména
    držitelů i čísla parcel. Jen výřezy vsí pro rodinu, žádné hromadné stahování listů.
  - **Morava:** odkaz vede do prohlížeče MZA (fond D 9, často dva listy: původní z 30. let a reambulace ze 70. let 19. stol.).
    MZA stahovací skripty zakazuje – jen přiblížit a snímek obrazovky (jako u matrik MZA). Listy Moravy nejsou georeferencované.
  - **Čtení:** v budově je **červeně číslo popisné** a **černě číslo stavební parcely** (pozemkové parcely mají čísla
    červená); záměna přečte celou ves obráceně. Při pochybnosti ověř na pár domech: vrstva pozemkového katastru
    (archiv_spojene_pk) s adresními body RÚIAN ukáže, na které parcele stojí dnešní čp. „N° 35 Příjmení“ u pozemku
    = patří k domu čp. 35.
    Žlutá stavba dřevěná, růžová zděná. Popisky bývají vzhůru nohama (výřez otoč o 180°). U měst bývá intravilán prázdný.
    Na web dej výřez se zakroužkovaným domem (u rodiny mívají staré mapy velký úspěch).
- **Dnešní adresa domu** podle čísla popisného: RÚIAN (ČÚZK, vrstva AdresniMisto). Pozor, staré centrum mívá od 19. století
  stejná čp., ale předměstí a vesnice čísla přečíslovávaly. Hodí se na „procházku po stopách předků“.
  Stavbu podle obce a čísla popisného najde i nahlizenidokn.cuzk.gov.cz (ověření adresy z dokladu); vlastník je za
  CAPTCHou a je to údaj o žijícím člověku – nezjišťuj ho.

## Oběti 2. světové války
- **Arolsen Archives** (collections.arolsen-archives.org): dokumenty o vězních, nuceně nasazených a vysídlených. Vyhledávání
  v prohlížeči, vstupní prohlášení musí odsouhlasit uživatel.
- **Mauthausen – Raum der Namen** (raumdernamen.mauthausen-memorial.org): vězni zemřelí v Mauthausenu, s datem a místem
  narození i úmrtí. Takové údaje jsou citlivé – na web jen se souhlasem rodiny (`soukromi.md`).

## Příjmení dnes a DNA
- **Rozšíření příjmení dnes**: kdejsme.cz (počty nositelů po okresech). Rychle ukáže, jestli je příjmení vzácné a kde
  jsou jeho „hnízda“. Při hledání vzdálených příbuzných vyškrtni vlastní rodinu.
- **DNA** (jen když o to uživatel stojí, a jeho rozhodnutí): autosomální test (MyHeritage, Ancestry) najde bratrance
  do ~5. kolene. **Y-DNA** (FamilyTreeDNA, Y-37 až Big Y) se dědí po meči beze změny. Ověří, jestli dvě linie stejného
  příjmení mají společného předka, a u nemanželského dítěte může shoda s jiným příjmením ukázat otce. Kontakt se žijícími
  příbuznými vždy jen přes uživatele.
Všechno, co jde jen v badatelně, zapisuj do `data/archivni_dotazy.md` (archiv, fond, inventární číslo, co hledat).
