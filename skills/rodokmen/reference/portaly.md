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
| ZA Opava | severní Morava a Slezsko, Olomoucko a Litovelsko | Digitální badatelna – digi.archives.cz/da/ | **částečně – `soal_zoomify.py`** (jen s prohlížečem, CAPTCHU řeší uživatel) |
| Národní archiv | židovské matriky (HBMa), soupisy; pražské policejní přihlášky 1850–1914 | HBMa: VadeMeCum NA – vademecum.nacr.cz (Digitální badatelna → Matriky židovských náboženských obcí; stará adresa badatelna.eu už nepatří archivu); digi.nacr.cz/prihlasky2 | přihlášky **ano – `policie_prihlasky.py`** |

Adresy u nevyzkoušených portálů ověř při prvním použití (portály se mění). Pro pohraničí a mimo ČR viz `playbook.md` §2
(Matricula pro Rakousko/Německo, Geneteka pro Polsko, FamilySearch pro Slovensko) a níže.

## ARON (SOA Zámrsk) – hotové nástroje
- **Hledání svazků:** `python3 -I tools/aron_search.py "Holice"` → řádky `apu_id | signatura, roky | druh, obce`.
  Popis obsahuje druh knihy (NAROZENÝCH / ODDANÝCH / ZEMŘELÝCH, index) a všechny obce farnosti.
- **Informace o svazku:** `python3 -I tools/aron_img.py <apu_id> info` → název a počet snímků.
- **Stažení snímku:** `python3 -I tools/aron_img.py <apu_id> <snímek> 1 pracovni/holice_n_57.jpg`
  (úroveň 1 = poloviční rozlišení – stačí na orientaci; 0 = plné rozlišení – na čtení a výřez).
  Jen část stránky v plném rozlišení: `… <snímek> 0 pracovni/detail.jpg 0.0,0.4,1.0,0.7`.
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
- **Od 2. 11. 2026 archiv nástroj odmítá** (HTTP 403 podle User-Agentu „rodokmen“), `trebon.py` je vypnutý a brzda
  skripty na digi.ceskearchivy.cz zastaví. Neobcházej to (jiný User-Agent, vlastní skript). Matriky čti v prohlížeči
  (nejlépe Playwright) stejně jako u MZA: přiblížit zápis, uložit snímek obrazovky, `vyrez.py`. Tempo jako člověk, jen
  stránky, které čteš, žádní pomocníci. Bez prohlížeče ať pošle snímky obrazovky uživatel.
- Obec: `https://digi.ceskearchivy.cz/<Obec>` (bez diakritiky a mezer, např. `RatiborskeHory`) → stránka místa, vlevo
  „Matriční knihy“ (stránka je v rámci `ram_obsah`) → seznam knih s roky a obcemi; kliknutí otevře knihu v nové záložce.
  **Zkontroluj název a okres**: u stejnojmenných obcí portál vybere jinou (Buk → Bukovka), u měst i okres nebo synagogu.
  Malé osady portál nezná (Malá Chyška) – hledej farní nebo sousední obec a osadu v popisu knih.
- Snímek: `https://digi.ceskearchivy.cz/<kniha>/<snímek>` (zároveň trvalý odkaz). Knihy mívají dobrovolnický jmenný
  rejstřík (stránka místa → „Rejstříky“) – obrovská úspora; ne každá kniha ho má.
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
- Svazek do `svazky.json` ručně (Ostatní portály, krok 4, klíč `trebon_<kniha>`).
- Některé fary mají knihy po vesnicích, které nejsou v seznamu knih místa (Vacov → Žár) – hledej podle titulků knih fary.
- **Civilní matriky (1920–1945) lidí bez vyznání** jsou v knihách okresních úřadů (např. Tábor, kniha 12304) a mají
  dobrovolnický rejstřík. Dobrá cesta, když farní matrika mlčí. U obce se neukážou (patří okresu) – hledej u okresního města.

## SOA Plzeň (Porta fontium, portafontium.eu) – `tools/portafontium.py`, bez prohlížeče
- `portafontium.py fara <fara>` → knihy fary: kniha | obce | roky a druhy (`*` N, `oo` O, `+` Z, `i` index) | popis.
  `<fara>` je název římskokatolické fary („Dolní Bělá“, „Mýto“ – diakritiku nástroj odstraní) nebo přímo část
  její adresy (`dolni-bela` =
  `…/contents/register/soap-pn/cirkev-rimskokatolicka/dolni-bela`). Obec → faru nástroj nehledá: faru zjisti ve vyhledávání
  matrik na portálu (pole Místo, v prohlížeči) nebo v popisech knih okolních far. Bez prohlížeče: stránka
  `https://www.portafontium.eu/searching/register?search_api_views_fulltext_1=<obec>` vypíše odkazy
  `/register/soap-pn/<kniha>` – `<kniha>` (např. `kdyne-29`) rovnou použij v `portafontium.py info`.
- `portafontium.py info <kniha>` (`dolni-bela-17`) → signatura, druh, text desky a **obsah** – u knih psaných po vesnicích
  vypíše, na kterých foliích je která obec („Ves X z let 1862–1901 = fol. 121–200“).
- `portafontium.py snimek <kniha> <snímek> pracovni/x.jpg [nahled] [x0,y0,x1,y1]` → celá stránka v plném rozlišení jedním
  požadavkem (IIIF), `nahled` = 1/4. Číslo snímku = pořadí náhledu v prohlížeči; soubory nesou číslo folia
  (`dolni-bela-17_0951` = fol. 95), takže u knih se souvislou foliací je **snímek ≈ folio**.
- `link <kniha> <snímek>` → trvalý odkaz, `svazek <kniha>` → `svazky.json` (klíč `pf_<kniha>`).
- Bez prohlížečového User-Agentu portál vrací 403 (nástroj ho posílá). Jmenné hledání portál nemá – indexy jsou jen uvnitř knih
  (`*i`, `ooi`, `+i` v seznamu knih fary).

## SOA Praha (eBadatelna, ebadatelna.soapraha.cz) – jen v prohlížeči
- **Od 2. 11. 2026 archiv nástroj zakazuje** (robots.txt „User-agent: rodokmen – Disallow: /“, HTTP 403),
  `ebadatelna.py` je vypnutý (fungují jen `link`, `a-link`) a brzda skripty na soapraha.cz zastaví. Neobcházej to
  (jiný User-Agent, vlastní skript, stahování snímku z prohlížeče). Matriky čti v prohlížeči (nejlépe Playwright).
  Tempo jako člověk, jen stránky, které čteš, žádní pomocníci. Bez prohlížeče ať pošle snímky obrazovky uživatel.
- Hledání: Matriky → pole „lokalita“ vyplň obcí bez posledního písmene (`browser_type`) a poslední písmeno napiš
  se `slowly` (teprve to ukáže našeptávač; psaní po písmenech do prázdného pole se připojí k textu „lokalita“). Vyber
  celý název (`.ui-menu-item`, „Obec - obec X - okres Y“), Vyhledat. Seznam knih jedním `browser_evaluate`:
  `[...document.querySelectorAll('table tr')].map(r => [...r.cells].map(c => c.innerText.trim()).join(' | ') + ' | ' + (r.querySelector('a')?.getAttribute('href') ?? ''))`
  (kniha | původce | okres | lokality | roky N, O, Z, indexy | snímků | `/pages/MatrikaPage/matrikaId/<id>`).
- Popis knihy: `https://ebadatelna.soapraha.cz/pages/MatrikaPage/matrikaId/<id>` (archiválie
  `…/pages/ArchivaliePage/archivalieId/<id>`) – `document.body.innerText`. „Obecný popis matriky“ uvádí u knih psaných
  po vsích **rozvržení stran** („1–48 Ves A, 49–82 Ves B …“, každá ves může mít vlastní stránkování) – neodhaduj snímek
  podle roku, ale podle stran vsi; je-li rejstřík, začni jím.
- Snímek: `https://ebadatelna.soapraha.cz/d/<matrikaId>/<snímek>` (archiválie `/a/<archivalieId>/<snímek>`, zároveň
  trvalý odkaz, do `odkaz`). Prohlížeč načte celý snímek v plném rozlišení (2–3 MB, chvíli trvá) a jen ho zmenší.
  Postup: snímek okna (scale css) → odečti rohy zápisu → úryvek (`browser_evaluate`) vykreslí výřez z už načteného
  snímku přes okno (bez dalšího dotazu na archiv) → snímek prvku `#rodokmen-vyrez` v rozlišení zařízení do
  `pracovni/ebad_<id>_<snímek>.png` → `vyrez.py` jako u jiných archivů:
  ```js
  async () => {
    const [x0, y0, x1, y1] = [60, 245, 600, 435];   // rohy zápisu na snímku okna (CSS px)
    const im = document.getElementById('scanImage'), r = im.getBoundingClientRect();
    const k = im.naturalWidth / r.width, w = (x1 - x0) * k, h = (y1 - y0) * k;
    document.getElementById('rodokmen-vyrez')?.remove();
    const c = document.createElement('canvas');
    c.id = 'rodokmen-vyrez'; c.width = Math.round(w); c.height = Math.round(h);
    c.getContext('2d').drawImage(im, (x0 - r.left) * k, (y0 - r.top) * k, w, h, 0, 0, c.width, c.height);
    const s = Math.min(1, innerWidth / w, innerHeight / h);
    Object.assign(c.style, {position: 'fixed', left: 0, top: 0, width: w * s + 'px', height: h * s + 'px',
      zIndex: 99999, pointerEvents: 'none'});
    document.body.append(c);
    return [c.width, c.height, location.href];
  }
  ```
  Souřadnice ber z aktuálního snímku okna; snímek neotáčej ani nepřibližuj (úryvek počítá s výchozím zobrazením).
  Před dalším krokem výřez odstraň: `document.getElementById('rodokmen-vyrez').remove()`.
- Starší snímky bývají z mikrofilmu nebo silně vybledlé – čti se zvýšeným kontrastem:
  `magick x.png -colorspace Gray -contrast-stretch 2%x30% x_k.png` (výřez pak dělej z kontrastní verze a poznamenej to v přepisu).
- Svazek do `svazky.json` ručně (Ostatní portály, krok 4, klíč `ebad_<matrikaId>`, archiválie `ebad_a_<id>`).
  Denní údržba portálu kolem 4:44 (asi 2 minuty).

## AHMP Praha – `tools/ahmp_search.sh`, `tools/ahmp_scan.py`
- `bash tools/ahmp_search.sh "Smíchov"` → svazky Sbírky matrik: popis | farnost | (XID, id, počet snímků).
- `python3 -I tools/ahmp_scan.py <XID> <snímek> pracovni/x.jpg [1] [x0,y0,x1,y1]` → snímek (1 = poloviční rozlišení).
- Trvalý odkaz `https://katalog.ahmp.cz/pragapublica/permalink?xid=<XID>&scan=<N>`.
- Nový portál digi.ahmp.cz má ochranu proti robotům – nepoužívat. Pražské matriky 1890–1940 většinou **nemají rejstříky**
  a farností je mnoho – bez přesného data a farnosti (z úmrtí/sňatku nebo od rodiny) je hledání velmi drahé.

## SOA Litoměřice (severní Čechy) – `tools/soal_zoomify.py`
- Digitální badatelna digi.soalitomerice.cz má na vstupu automatické ověření (asi 15 s „počítání“) → knihu a snímek
  najdi v prohlížeči. Pak zjisti **celou adresu obrázku** (`https://images.soalitomerice.cz/…`): v síťovém provozu
  požadavek na `…/ImageProperties.xml`, nebo `document.querySelector('#navigatorImage').src` na stránce snímku.
  Archiv koncem října 2026 změnil cesty (nově `…/CZ-214000010/NAD-<číslo>/dao/images/<složka>/<uuid>.jpg`),
  starší zkrácená `<cesta>` za `…/matriky/` pak vrací 404 – nástroji dávej vždy celou adresu.
- Snímky stahuj nástrojem: `python3 -I tools/soal_zoomify.py "<celá adresa>" 0 pracovni/x.jpg` (0 = plné rozlišení,
  1 = poloviční). Obrázkový server neomezuje a cookies nepotřebuje.
- **POZOR: po zhruba 100 rychlých požadavcích na stránky aplikace (prohlížení snímků, detail výsledku) archiv zablokuje
  přístup na 30 minut.** V prohlížeči proto jen najdi knihu a cestu k obrázkům, pak už jen nástroj. Pomocníkům to napiš do zadání.

## ZA Opava (severní Morava, Slezsko, Olomoucko, Litovelsko) – `tools/soal_zoomify.py`
- Pozor na hranici: obce na Litovelsku a Olomoucku patří pod **ZA Opava**, ne pod MZA Brno.
- **Bez prohlížeče to nejde.** Badatelna `https://digi.archives.cz/da/` (stará adresa matriky.archives.cz jen přesměruje)
  má ochranu proti robotům – curl ani WebFetch se nedostanou ani na hledání. Potřebuješ připojený prohlížeč (Claude in
  Chrome – uživatel ho připojí příkazem `/chrome` – nebo Playwright); jinak ať knihu najde a snímky uloží uživatel.
  Úvodní ověření projde samo, ale hledání často skončí **CAPTCHou: tu vyřeší uživatel** v okně prohlížeče, ty nikdy.
- Hledej obec a vyfiltruj Matriky (ikona, potom znovu lupa). Hledání vrací i civilní matriky (u obce stovky svazků) –
  filtr „Datum od – do“ (podle začátku svazku, např. 1680–1873) nechá jen církevní. Knihy bývají řazené po obcích
  a na konci mají rejstřík. Vedle farních knih bývají i **druhopisy** („T“ v signatuře, viz `matriky.md`).
- **Seznam svazků a ID snímků si hned ulož** do `pracovni/<svazek>/` – relace po pár hodinách vyprší a výsledky
  hledání platí jen v ní. Na detailu svazku: entita `document.querySelector('[entityuuid]').getAttribute('entityuuid')`
  (u svazků uložených v jiném archivu nemá tvar UUID – nehledej ji regexem), ID snímků jsou hodnoty
  `select.getScanSelect option` (tvar „N%20uuid“). Snímek pak otevřeš kdykoli bez hledání:
  `/da/showZoomifySeparate?imageNumberSeparate=N&myEntityUuid=<entita>&myImageUuid=<uuid>`.
- Adresa obrázku: `fetch('/da/showZoomify/<id svazku z URL>/<část option.value za „%20“>')` vrátí HTML s cestou
  `…/images/<složka>/<uuid>.jpg`. Cesta se u svazků liší (`…/CZ-217000010/NAD-165/dao/images/…`, `…/zao/matriky/dao/images/…`)
  a přípona bývá i `.JPG` – nástroji dej vždy **celou adresu z HTML**:
  `python3 -I tools/soal_zoomify.py "<adresa>" 2 pracovni/x.jpg` (2 = čtvrtinové rozlišení na orientaci podle záhlaví
  stránek, 0 = plné jen u nalezeného zápisu). Obrázkový server images.archives.cz neomezuje a cookies nepotřebuje.
- **POZOR na blokování** (jen stránky aplikace, obrázky ne): rychlé dotazy → CAPTCHA, „operace vyhodnoceny jako
  nestandardní“ nebo „Access blocked“ na 30 minut; po desítkách dotazů za den vrací showZoomify „Server Exception“
  (denní limit – pokračuj až další den). Pauza 3–6 s mezi stránkami, dávky do ~80 stránek, žádné rychlé `fetch` hned
  po hledání a stránky výsledků neprocházej za sebou. Delší smyčku pusť v prohlížeči na pozadí, výsledky ukládej do
  `window` nebo `localStorage` a vyzvedávej po částech (nástroj pro JavaScript má limit asi 45 s). Pomocníkům to napiš do zadání.

## MZA Brno (jižní Morava, Acta Publica) – jen v prohlížeči
- Portál `https://www.mza.cz/actapublica/`, bez přihlášení. **Od 2. 11. 2026 MZA blokuje stahovací skripty** (ověření
  Altcha, adresy dlaždic s tokenem) a výjimky nedělá. Skriptem jen hledání knih (níže, brzda 1 dotaz za 4 s, jiné
  adresy MZA brzda zastaví). Snímky jen v jejich prohlížeči: přiblížit zápis a uložit snímek obrazovky. Žádné
  stahování, `fetch` ani skládání dlaždic, žádní pomocníci. Nejlépe Playwright (uloží
  snímek do souboru); jinak ať uživatel pošle snímky obrazovky sám (celá dvoustrana na orientaci, pak přiblížený zápis
  – kolečko myši, macOS Cmd+Shift+4, Windows Win+Shift+S) a ulož je do `pracovni/`.
- Kniha: `python3 -I tools/slusne.py curl -s "https://www.mza.cz/actapublica/matrika/hledani?typ=obec&search_by_obec=<obec>&page=<n>"`
  → HTML tabulka (číslo knihy, původce, roky N/O/Z, počet snímků, odkaz `matrika/detail/<id>`; číslo knihy ≠ id).
  Výsledky po 20 – projdi i další stránky, než řekneš, že tam obec není. U velkých far jsou samostatné svazky rejstříků (N/O/Z) – začni jimi. Fary založené
  kolem 1784 mají starší zápisy v mateřské faře. Ověření na detailu knihy proběhne samo za pár sekund.
- Detail knihy má „Části matriky“ s rozsahy snímků (narození 1–43, index narozených 43–93, u knih pro víc obcí po obcích).
  Snímek s hledaným rokem odhadni (snímky ÷ roky). Rejstříky uvádějí stranu, ne snímek: přečti čísla stran na 1–2 snímcích
  a dopočítej (vztah bývá lineární, kniha od knihy jiný).
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
- Nezobrazuj celou stránku v plném rozlišení (velké okno) – stovky dlaždic naráz a MZA vrací 503. Tempo jako člověk,
  jen stránky, které opravdu čteš. Když ověření nepustí nebo MZA hlásí chybu, skonči a řekni to uživateli.
- Trvalý odkaz = adresa v prohlížeči `…/matrika/detail/<id>?image=<soubor>.jp2` (soubor končí číslem snímku × 10:
  snímek 16 → `…-00160.jp2`). Svazek do `svazky.json` ručně (Ostatní portály, krok 4).
- Adresa actapublica.eu bývá za Cloudflare zablokovaná podle IP; když blokuje i mza.cz, ať uživatel vypne VPN nebo zkusí
  jinou síť.

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

## Hroby a hřbitovy
- Kde jsou předci pohřbeni, víš z rozhovoru s rodinou (Fáze 1). Fotky náhrobků (jména, data, rodná příjmení) jsou
  cenný pramen hlavně pro 20. století, kde matriky ještě nejsou přístupné.
- Evidence hrobových míst: správa hřbitova (kdo je v hrobě uložen, kdo platí nájem – často žijící potomek);
  řada měst má online vyhledávání hrobů. Mezinárodně BillionGraves a Find a Grave.

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
   jen snímky, které čteš. Krajní možnost: požádej uživatele, ať snímek uloží a dá do `pracovni/`.
3. **Trvalý odkaz** na snímek (tlačítko „trvalý odkaz“/permalink, jinak URL svazku + číslo snímku) dej do `odkaz` v zápisu.
4. Svazek zapiš do `data/svazky.json` ručně: `"klic": {"archiv": "SOA Třeboň", "portal": "digi.ceskearchivy.cz",
   "svazek": "N Volary 1784–1820, sign. …", "popis": "obce…", "url": "<odkaz na svazek>"}`.
5. Dál stejně jako u ARON: `vyrez.py`, `ramecek.py`, přepis, osoby, deník.
6. Když se postup osvědčí, napiš pro portál vlastní malý nástroj podle `portafontium.py` (bez prohlížeče, jen když to archiv nezakazuje)
   a postup zapiš do `STAV.md`. Poznatek zapiš i do `poznamky_pro_skill.md` (pro správce skillu).

## Starší prameny (17.–18. století)
- **Soupis poddaných podle víry 1651** – celé rodiny s věkem, po krajích; edice Národního archivu jako PDF
  (nacr.cz, hledej „Soupis poddaných podle víry“ + kraj). Fulltext v PDF, příjmení často bez diakritiky / s jinou ortografií
  (Šaršoun → „Šaroun“, dlouhé ſ jako f). Ves je v rámci panství; poznamenej si stránku edice.
- **Berní rula 1654** – jen hospodáři s půdou; edice a rejstříky v knihovnách (Kramerius/DNNT).
- **Gruntovní (pozemkové) knihy** – převody domů z otce na syna; online jen část (SOA Plzeň téměř vše, SOA Praha část,
  ostatní spíš badatelna). Fond „Velkostatek <panství>“.
- **Mapy stabilního katastru (1824–43)** – kde stál dům s číslem popisným: ags.cuzk.gov.cz/archiv (Archiv ČÚZK; stará adresa archivnimapy.cuzk.cz už nefunguje).
  Na **císařských otiscích** chybí u části listů barvy a čísla domů. Lepší jsou **indikační skici**: mají čísla domů
  a u pozemků jméno majitele („N. 13“ = patří k domu čp. 13). Dům bez pozemků mimo ves = domkář bez polí.
  Jméno majitele samotného domu bývá jen v písemném operátu (archiv, ne online). Výřezy map patří na web k rodině.
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
