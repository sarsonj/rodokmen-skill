// Snímkovač – dlaždicové prohlížeče (OpenSeadragon): minimapa pokrytí, ukládání dlaždic, poskládání snímku.
// Běží v izolovaném světě rozšíření vedle content.js; s háčkem osd_hook.js (svět stránky) mluví přes postMessage.
// Dlaždice se ukládají do úložiště rozšíření (IndexedDB ve workeru), takže se snímek doskládává i při dalších
// návštěvách. Barvy minimapy: šedá = nic, červená = pod minimem, oranžová = přehled (čitelná jména), světle zelená = čtení, tmavě zelená = záznam.
(() => {
  if (window.__snimkovacOsdUi) return;
  window.__snimkovacOsdUi = true;
  const TAG = 'snimkovac-osd';
  let info = null, procent = null, pohled = null, aktivni = false;
  let dlazdice = [];   // {skala, rect} pro tento snímek (z úložiště i nové)
  // změřeno na MZA 14. 11. 2026: 25 % jména čitelná, 50 % skoro jako plné; AHMP: 58 % drobné písmo měkké, 70–80 % ostré
  const VYCHOZI_PRAHY = { min: 25, ideal: 50, zapis: 75 };
  let prahy = { ...VYCHOZI_PRAHY };
  const nastavPrahy = p => { prahy = { ...VYCHOZI_PRAHY, ...(p || {}) }; };
  let obrazKlic = null;
  // Po obnovení (aktualizaci) rozšíření zůstane tento skript v otevřené stránce bez spojení s rozšířením
  // („Extension context invalidated“). Pak se tiše odpojí; nová verze se načte po obnovení stránky (F5).
  let odpojeno = false;
  function zivy() {
    if (odpojeno) return false;
    try { if (chrome.runtime && chrome.runtime.id) return true; } catch (e) { /* zneplatněno */ }
    odpojeno = true;
    try { odpoj(); } catch (e) { /* nic */ }
    return false;
  }
  let intervalPocitadla = null;
  function odpoj() { clearInterval(intervalPocitadla); clearTimeout(casovacUlozeni); if (box) box.remove(); }


  // --- totožnost snímku ---------------------------------------------------------------------------------------
  function popisStranky() {
    const u = new URL(location.href);
    if (location.hostname === 'digi.ceskearchivy.cz') {   // SOA Třeboň: prohlížeč v rámu view.php
      const id = (document.querySelector('input[name=id]') || {}).value || u.searchParams.get('id') || '';
      const dp = document.getElementById('dirpage');
      const vyber = document.getElementById('page');
      const zVyberu = vyber && vyber.options[vyber.selectedIndex] ? (vyber.options[vyber.selectedIndex].text.match(/\d+/) || [])[0] : null;
      const snimek = parseInt((dp && /^\d+$/.test(dp.value) ? dp.value : zVyberu) || '0', 10) || null;
      let kniha = '';
      try { kniha = (window.top.document.title || '').trim(); } catch (x) { /* jiný původ */ }
      kniha = kniha || `SOA Třeboň ${id}`;
      return { host: location.hostname, matrikaId: id, snimek, obraz: '', kniha,
               // trvalý odkaz portálu má číslo o jedna větší než „Snímek N“ v prohlížeči (Bílsko 12: sn. 43 = /2231/44)
               adresa: `https://digi.ceskearchivy.cz/${id}/${snimek ? snimek + 1 : ''}`,
               klic: `${location.hostname}|${id}|${snimek}` };
    }
    if (location.hostname === 'katalog.ahmp.cz' || location.hostname === 'digi.ahmp.cz') {   // AHMP Praha Publica (Zoomify)
      const xid = u.searchParams.get('xid') || '';
      const pole = document.querySelector('input[name=rowTxt], #rowTxt');
      const snimek = pole && /^\d+$/.test(pole.value.trim()) ? parseInt(pole.value, 10) : (parseInt(u.searchParams.get('scan'), 10) || null);
      const odkaz = [...document.querySelectorAll('a')].map(a => (a.textContent || '').trim()).find(t => /•/.test(t) && t.length < 60);
      const kniha = odkaz ? 'AHMP ' + odkaz.replace(/\s*•\s*/, ' ') : `AHMP ${xid.slice(0, 8)}`;
      // po kliknutí na náhled je stránka Zoomify.action bez xid – kniha se pak pozná podle názvu („HOS N11 • 1825-1846“)
      const id = xid || (odkaz ? odkaz.replace(/\s*•\s*/, '_').replace(/[^\w.-]+/g, '_') : 'ahmp');
      return { host: location.hostname, matrikaId: id, snimek, obraz: '', kniha,
               adresa: xid ? `https://${location.hostname}/pragapublica/permalink?xid=${xid}&scan=${snimek || ''}` : location.href,
               klic: `${location.hostname}|${id}|${snimek}` };
    }
    const detail = (location.pathname.match(/\/detail\/(\d+)/) || [])[1] || '';
    const obraz = u.searchParams.get('image') || '';
    const pole = document.getElementById('input-page');   // MZA: „Snímek: 70 z 146“
    const snimek = pole && /^\d+$/.test(pole.value) ? parseInt(pole.value, 10) : null;
    const popisek = t => {   // MZA hlavička: „Číslo knihy 11075“, „Původce Velký Újezd“
      const e = [...document.querySelectorAll('body *')].find(x => x.children.length === 0 && (x.textContent || '').trim() === t);
      if (!e) return '';
      let n = e.nextElementSibling || (e.parentElement && e.parentElement.nextElementSibling);
      return n ? (n.textContent || '').trim().slice(0, 60) : '';
    };
    // záloha: text stránky má popisek a hodnotu na dvou řádcích („Číslo knihy\n11075“)
    const zTextu = t => ((document.body.innerText || '').match(new RegExp(t + '\\s*\\n\\s*([^\\n]{1,60})')) || [])[1] || '';
    const puvodce = popisek('Původce') || zTextu('Původce');
    const cislo = popisek('Číslo knihy') || zTextu('Číslo knihy');
    const kniha = [puvodce, cislo].map(s => s.trim()).filter(Boolean).join(' ') || (detail ? `${location.hostname.replace(/^www\./, '')} ${detail}` : document.title.slice(0, 60));
    const id = detail || location.hostname;
    return { host: location.hostname, matrikaId: id, snimek: snimek ?? (obraz || location.pathname).slice(-40),
             obraz, kniha, adresa: location.origin + location.pathname + (obraz ? '?image=' + obraz : ''),
             klic: `${location.hostname}|${id}|${obraz || location.pathname + location.search}` };
  }

  // MZA (Acta Publica): při chybném tvaru adresy (?image=…-00170 místo …-01350) prohlížeč sám otevře snímek 1.
  // Takový snímek nikdo nechtěl: neukládá se sám a „drž pohled“ na něm nepřibližuje (každé přiblížení stojí denní limit).
  // Vrací důvod (text) nebo ''. Ručně („Uložit teď“) uložit jde dál.
  function skokStranky() {
    if (!/(^|\.)mza\.cz$/.test(location.hostname)) return '';
    const obraz = new URL(location.href).searchParams.get('image') || '';
    if (!obraz) return '';
    const jmeno = obraz.replace(/\.(jp2|jpe?g|tiff?)$/i, '');
    const zdroj = (info && info.zdroj) || '';
    // jen když zdroj má jméno snímku ve tvaru MZA (216000010-000253-…); jinak by se nedalo porovnat
    if (/\d{6,}-\d{6}-\d{6}-/.test(zdroj) && jmeno.length > 8) return zdroj.includes(jmeno) ? '' : 'prohlížeč ukazuje jiný snímek, než chce adresa';
    // záloha bez adresy zdroje: adresa míří jinam, a přitom je otevřený snímek 1
    const pole = document.getElementById('input-page');
    const n = parseInt((jmeno.match(/-(\d+)$/) || [])[1] || '', 10);
    if (pole && pole.value === '1' && n && n !== 1 && n !== 10) return 'adresa chce jiný snímek, prohlížeč otevřel snímek 1';
    return '';
  }

  // --- panel s minimapou -------------------------------------------------------------------------------------
  // Panel je ve stínovém DOM (Shadow DOM), aby mu styly archivu neměnily vzhled. Hlavní volba je CÍL (přehled / čtení /
  // záznam): nastaví přiblížení (práh + 1 %) a auto mřížku. Mřížka je druhá, volitelná volba (rozbalovací seznam).
  let box, koren, platno, chybaZachytu = '', stavZachytu = '', fotim = false, fotimPovoleni = false;
  const UROVNE = [
    { id: 'prehled', nazev: 'Přehled', prah: () => prahy.min, barva: '#ef8f00' },
    { id: 'cteni', nazev: 'Čtení', prah: () => prahy.ideal, barva: '#7cb342' },
    { id: 'zapis', nazev: 'Záznam', prah: () => prahy.zapis, barva: '#1b5e20' }
  ];
  let uroven = 'cteni';
  let cilRucne = {};   // ručně upravený cíl pro úroveň (pamatuje se pro web), jinak práh + 1
  const urovenInfo = () => UROVNE.find(u => u.id === uroven) || UROVNE[1];
  const cilUrovne = () => cilRucne[uroven] || (urovenInfo().prah() + 1);
  const H = location.hostname;
  const ulozNast = (k, v) => chrome.storage.local.set({ [k + '_' + H]: v });

  const CSS = `
    :host { all: initial; }
    .panel { width: 196px; box-sizing: border-box; background: #fff; color: #1f2328; border-radius: 10px;
      box-shadow: 0 4px 16px rgba(0,0,0,.28); font: 12px/1.35 system-ui, -apple-system, "Segoe UI", sans-serif; overflow: hidden; }
    .hlava { display: flex; align-items: center; gap: 6px; padding: 6px 8px; background: #24292f; color: #fff; cursor: move; user-select: none; }
    .hlava b { flex: 1; font-size: 12px; letter-spacing: .2px; }
    .hlava .stav { width: 8px; height: 8px; border-radius: 50%; background: #8c959f; }
    .hlava .stav.ok { background: #2da44e; } .hlava .stav.prace { background: #d29922; } .hlava .stav.chyba { background: #cf222e; }
    .ikona { all: unset; cursor: pointer; color: #fff; opacity: .8; padding: 0 4px; font-size: 13px; }
    .ikona:hover { opacity: 1; }
    .telo { padding: 8px; display: grid; grid-template-columns: minmax(0, 1fr); gap: 8px; }
    .radek > * { min-width: 0; }
    .telo[hidden] { display: none; }
    canvas { display: block; width: 180px; border-radius: 4px; box-shadow: inset 0 0 0 1px rgba(0,0,0,.15); }
    .urovne { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; }
    .urovne button { all: unset; cursor: pointer; text-align: center; border-radius: 6px; padding: 4px 2px;
      background: #f6f8fa; box-shadow: inset 0 0 0 1px #d0d7de; font-size: 11px; }
    .urovne button i { display: block; width: 100%; height: 3px; border-radius: 2px; margin-bottom: 3px; }
    .urovne button small { display: block; color: #57606a; font-size: 10px; }
    .urovne button.zvoleno { color: #1f2328; box-shadow: none; font-weight: 600; }
    .urovne button.zvoleno small { color: rgba(31,35,40,.75); }
    .urovne button.zvoleno.tmava { color: #fff; } .urovne button.zvoleno.tmava small { color: rgba(255,255,255,.85); }
    .legenda { display: flex; gap: 8px; font-size: 10px; color: #57606a; margin-top: -4px; }
    .legenda i { display: inline-block; width: 8px; height: 8px; border-radius: 2px; margin-right: 3px; vertical-align: -1px; }
    .akce { display: flex; gap: 6px; }
    .akce button { all: unset; cursor: pointer; flex: 1; text-align: center; border-radius: 6px; padding: 5px 4px; font-size: 11px;
      background: #f6f8fa; box-shadow: inset 0 0 0 1px #d0d7de; }
    .akce button.hlavni { background: #1b5e20; color: #fff; box-shadow: none; }
    .akce button:hover { filter: brightness(.96); }
    .hotovo { color: #1a7f37; font-weight: 600; }
    .nastaveni[hidden] { display: none; }
    .malé { font-size: 10px; color: #57606a; }
    .tl { all: unset; cursor: pointer; text-align: center; border-radius: 6px; padding: 4px; font-size: 11px; background: #fff; box-shadow: inset 0 0 0 1px #d0d7de; }
    .kalibrace { background: #ddf4ff; border: 1px solid #54aeff; border-radius: 6px; padding: 5px 6px; color: #0a3069; }
    .odkaz { all: unset; cursor: pointer; color: #0969da; text-decoration: underline; font-size: 11px; }
    .nastaveni { display: grid; gap: 6px; padding: 6px; border-radius: 6px; background: #f6f8fa; }
    .varovani { display: flex; gap: 6px; align-items: center; }
    .varovani button { all: unset; cursor: pointer; white-space: nowrap; font-weight: 600; text-decoration: underline; }
    .radek { display: flex; align-items: center; gap: 6px; font-size: 11px; color: #57606a; }
    .radek label { display: flex; align-items: center; gap: 4px; }
    input[type=number] { width: 38px; box-sizing: border-box; padding: 2px 4px; border: 1px solid #d0d7de; border-radius: 4px; font: inherit; color: #1f2328; }
    select { flex: 1; min-width: 0; padding: 2px; border: 1px solid #d0d7de; border-radius: 4px; font: inherit; color: #1f2328; background: #fff; }
    input[type=checkbox] { margin: 0; }
    .info { font-size: 11px; color: #1f2328; display: grid; gap: 2px; }
    .info .slabe { color: #57606a; }
    .varovani { background: #fff8c5; border: 1px solid #d4a72c; border-radius: 4px; padding: 3px 5px; color: #4d2d00; }
    .varovani[hidden] { display: none; }
    .pata { font-size: 10px; color: #8c959f; border-top: 1px solid #eaeef2; padding-top: 4px; }
  `;

  function vytvorMapu() {
    if (box) return;
    box = document.createElement('div');
    box.setAttribute('data-snimkovac-mapa', '1');
    box.style.cssText = 'position:fixed;left:12px;bottom:12px;z-index:2147483646';
    koren = box.attachShadow({ mode: 'open' });
    koren.innerHTML = `<style>${CSS}</style>
      <div class="panel">
        <div class="hlava" title="Tažením přesuneš"><span class="stav"></span><b>Snímkovač</b>
          <span data-souhrn style="font-size:11px;opacity:.85"></span>
          <button class="ikona" data-ozubene title="Nastavení: cílový detail a mřížka">⚙</button>
          <button class="ikona" data-skryj title="Sbalit / rozbalit">▾</button></div>
        <div class="telo">
          <canvas title="Modrý rámeček = co je vidět. Klik na pole přiblíží to pole."></canvas>
          <div class="legenda"><span><i style="background:#d0d7de"></i>neviděno</span><span><i style="background:#cf222e"></i>málo</span><span><i style="border:1.5px solid #0969da;box-sizing:border-box"></i>pohled</span></div>
          <div class="urovne">${UROVNE.map(u => `<button data-uroven="${u.id}" title="Cíl ${u.nazev.toLowerCase()} (od ${u.prah()} % plného rozlišení)"><i style="background:${u.barva}"></i>${u.nazev}<small data-pokryti="${u.id}">–</small></button>`).join('')}</div>
          <div class="akce"><button class="hlavni" data-dalsi title="Přiblíží na první pole, které ještě není hotové">Další pole ▸</button>
            <button data-ulozit title="Poskládat a uložit stránku hned">Uložit teď</button></div>
          <div class="nastaveni" data-nastaveni hidden>
          <div class="radek">
            <label title="Cílový detail (% plného rozlišení). Klik na pole mřížky přiblíží přesně na tuto hodnotu.">Detail <input type="number" data-cil min="10" max="200" step="1"> %</label>
            <select data-mrizka title="Mřížka na mapě – klik na pole přiblíží to pole">
              <option value="auto">mřížka auto</option><option value="0">bez mřížky</option>
              <option value="2x1">2×1</option><option value="1x2">1×2</option><option value="2x2">2×2</option>
              <option value="2x3">2×3</option><option value="3x2">3×2</option><option value="3x3">3×3</option>
            </select>
          </div>
          <div class="malé" data-kalinfo></div>
          <button class="tl" data-kalznovu title="Zapomene zjištěnou hodnotu zvolené úrovně pro tento web – pak stačí přibližovat, dokud nezezelená">Znovu kalibrovat</button>
          </div>
          <label class="radek" title="Po otevření dalšího snímku jednou nastaví stejné přiblížení a místo jako na minulém"><input type="checkbox" data-drz> Držet pohled mezi snímky</label>
          <div class="info"><div data-pohled></div><div data-pole></div><div data-ulozeni class="slabe"></div></div>
          <div class="varovani" data-varovani hidden><span data-varovani-text></span><button data-fotit>Fotit teď</button></div>
          <div class="pata" data-pata></div>
        </div>
      </div>`;
    document.body.appendChild(box);
    platno = koren.querySelector('canvas');
    const $ = s => koren.querySelector(s);
    const telo = $('.telo'), hlava = $('.hlava'), tlSkryj = $('[data-skryj]');

    // poloha a sbalení se pamatují (pro každý web zvlášť)
    const klicPolohy = 'mapa_' + H;
    const ukazSbaleni = () => { tlSkryj.textContent = telo.hidden ? '▸' : '▾'; };
    chrome.storage.local.get(klicPolohy).then(d => {
      const p = d[klicPolohy];
      if (p) { umisti(p.left, p.top); telo.hidden = !!p.skryto; ukazSbaleni(); }
    });
    const ulozPolohu = () => chrome.storage.local.set({ [klicPolohy]: { left: box.offsetLeft, top: box.offsetTop, skryto: telo.hidden } });
    let tah = null;
    hlava.addEventListener('pointerdown', e => {
      if (e.target.closest('button')) return;
      tah = { dx: e.clientX - box.offsetLeft, dy: e.clientY - box.offsetTop };
      hlava.setPointerCapture(e.pointerId);
    });
    hlava.addEventListener('pointermove', e => { if (tah) umisti(e.clientX - tah.dx, e.clientY - tah.dy); });
    hlava.addEventListener('pointerup', () => { if (tah) { tah = null; ulozPolohu(); } });
    tlSkryj.onclick = () => { telo.hidden = !telo.hidden; ukazSbaleni(); ulozPolohu(); };
    $('[data-ozubene]').onclick = () => { const n = $('[data-nastaveni]'); n.hidden = !n.hidden; };
    $('[data-kalznovu]').onclick = () => {   // jen zvolená úroveň
      delete kalibrace[uroven]; ulozNast('kal', kalibrace);
      if (mrizka !== 'auto') { mrizka = 'auto'; vyber.value = 'auto'; ulozNast('mrizka', 'auto'); }
      kresli();
    };
    $('[data-dalsi]').onclick = () => {   // jeden klik = jedno přiblížení na první nehotové pole
      if (!mrizka) { mrizka = 'auto'; vyber.value = 'auto'; ulozNast('mrizka', 'auto'); kresli(); }
      const [ns, nr] = rozmer(), stav = stavPoli();
      const i = stav.findIndex(h => !h);
      if (i < 0) return;
      window.postMessage({ [TAG + '-pokyn']: 'prejdi', vyrez: pole(Math.floor(i / ns), i % ns) }, location.origin);
    };
    $('[data-ulozit]').onclick = () => {   // uložit hned i bez nových kousků v tomto sezení
      if (!info) return;
      posledniPopis = posledniPopis || { ...popisStranky(), sirka: info.sirka, vyska: info.vyska };
      novych = Math.max(novych, 1);
      ulozPoskladany(true);
    };
    $('[data-fotit]').onclick = () => { chybaZachytu = ''; kresli(); window.postMessage({ [TAG + '-pokyn']: 'stav' }, location.origin); };
    // kolečko a klávesy v panelu nesmí ovládat prohlížeč archivu pod ním
    for (const ud of ['wheel', 'keydown']) box.addEventListener(ud, e => e.stopPropagation());

    const polCil = $('[data-cil]'), vyber = $('[data-mrizka]'), zaskrt = $('[data-drz]');
    chrome.storage.local.get(['uroven_' + H, 'cile_' + H, 'mrizka_' + H, 'drzet_' + H, 'kal_' + H]).then(d => {
      if (d['uroven_' + H]) uroven = d['uroven_' + H];
      cilRucne = d['cile_' + H] || {};
      kalibrace = d['kal_' + H] || {};
      // převod z 0.15.0: naučená hodnota bez zámku se zamkne
      for (const k of Object.values(kalibrace)) if (k && k.ok && !(k.ne >= k.ok)) k.zamceno = true;
      const v = d['mrizka_' + H];
      mrizka = v === undefined || v === 'auto' ? 'auto' : Array.isArray(v) ? v : (v ? [v, v] : 0);
      drzet = d['drzet_' + H] !== false;
      zaskrt.checked = drzet;
      vyber.value = mrizka === 'auto' ? 'auto' : mrizka ? mrizka.join('x') : '0';
      kresli();
    });
    for (const b of koren.querySelectorAll('[data-uroven]')) b.onclick = () => {
      uroven = b.dataset.uroven;
      ulozNast('uroven', uroven);
      if (mrizka !== 'auto') { mrizka = 'auto'; vyber.value = 'auto'; ulozNast('mrizka', 'auto'); }   // cíl = auto mřížka
      kresli();
    };
    polCil.onchange = () => {
      const v = Math.max(10, Math.min(200, Math.round(+polCil.value) || cilUrovne()));
      if (v === urovenInfo().prah() + 1) delete cilRucne[uroven]; else cilRucne[uroven] = v;
      ulozNast('cile', cilRucne);
      kresli();
    };
    vyber.onchange = () => {
      const v = vyber.value;
      mrizka = v === 'auto' ? 'auto' : v === '0' ? 0 : v.split('x').map(Number);
      ulozNast('mrizka', mrizka);
      kresli();
    };
    zaskrt.onchange = () => { drzet = zaskrt.checked; ulozNast('drzet', drzet); };
    // klik na pole mapy = jedno přiblížení na to pole (stejně, jako by ho uživatel přiblížil ručně)
    platno.addEventListener('click', e => {
      if (!mrizka) return;
      const [ns, nr] = rozmer();
      const r = platno.getBoundingClientRect();
      const s = Math.min(ns - 1, Math.floor((e.clientX - r.left) / r.width * ns));
      const rd = Math.min(nr - 1, Math.floor((e.clientY - r.top) / r.height * nr));
      window.postMessage({ [TAG + '-pokyn']: 'prejdi', vyrez: pole(rd, s) }, location.origin);
    });
  }

  function umisti(left, top) {
    box.style.left = Math.max(0, Math.min(innerWidth - 60, left)) + 'px';
    box.style.top = Math.max(0, Math.min(innerHeight - 30, top)) + 'px';
    box.style.bottom = 'auto';
  }

  // Mřížka pro ruční „orazítkování“: pole jsou hotová, když je mapa má celá aspoň ve zvolené úrovni (cíli).
  // Nic se neděje samo – přiblížení na pole jen na kliknutí uživatele.
  let mrizka = 'auto';   // 0, 'auto' nebo [sloupců, řádků]
  // Hustota obrazu prohlížeče = skutečné body obrazu na bod stránky (škálování Windows, displej s vyšší hustotou).
  // Detail = přiblížení × hustota; cíle (přehled / čtení / záznam) jsou v detailu, takže fungují stejně na každém PC.
  let hustota = 1;
  // Dlaždicové prohlížeče se stupni (OpenSeadragon, MZA): dlaždice jsou jen ve stupních 1, 1/2, 1/4 … plného rozlišení
  // a prohlížeč bere stupeň až do 1/minPixelRatio (obvykle 2×) ostřejší, než kolik je vidět. Potřebný detail na obrazovce
  // je proto menší: stupeň, který splní cíl, × minPixelRatio (+10 % rezerva).
  let stupne = false, minPixelRatio = 0.5;
  function odhadDetailu() {   // v % (detail obrazovky): výpočet z vlastností prohlížeče, když kalibrace ještě není
    const cil = cilUrovne();
    if (!stupne) return cil;
    const stupen = Math.min(1, Math.pow(2, Math.ceil(Math.log2(Math.max(0.01, (cil - 1) / 100)))));
    return Math.min(cil, Math.ceil(stupen * minPixelRatio * 110));
  }

  // Kalibrace (pro každý web a úroveň zvlášť, pamatuje se): rozšíření si všímá, při jakém detailu obrazovky přicházejí
  // kousky v jaké kvalitě. ok = nejmenší detail, při kterém úroveň přišla; ne = největší detail, při kterém nepřišla.
  // Každý prohlížeč, archiv a počítač se tak „naučí“ sám – stačí jednou pomalu přiblížit, dokud pole nezezelená.
  let kalibrace = {};   // { prehled: {ok, ne}, cteni: {...}, zapis: {...} }
  let casZoomu = 0, posledniProcent = null;
  function potrebnyDetail() {
    const k = kalibrace[uroven];
    if (k && k.zamceno && k.ok) return Math.ceil(k.ok * 1.02);       // zjištěno a zamčeno pro tento web (+2 % rezerva)
    const odhad = odhadDetailu();
    if (k && k.ne >= odhad) return Math.ceil(k.ne * 1.1);             // odhad nestačil – zkusit o kus víc
    return odhad;
  }
  const kalibrovano = () => { const k = kalibrace[uroven]; return !!(k && k.zamceno && k.ok); };
  // kalibrační režim: auto mřížka a zvolená úroveň ještě nezkalibrovaná → mřížka se neukazuje, jen se přibližuje
  const kalibrujeSe = () => mrizka === 'auto' && !kalibrovano();
  // Učí se z NEJLEPŠÍ kvality, která pro ustálený pohled přišla (prohlížeč nejdřív načte rozmazané dlaždice a ostré
  // až po nich) – vyhodnotí se 1,5 s po posledním kousku nebo při změně přiblížení.
  let nejlepsi = 0, detailPohledu = null, casUceni = null;
  function uc(skala) {
    const d = detail();
    if (!d || Date.now() - casZoomu < 500) return;   // ještě se přibližuje
    nejlepsi = Math.max(nejlepsi, skala);
    detailPohledu = d;
    clearTimeout(casUceni);
    casUceni = setTimeout(vyhodnotUceni, 1500);
  }
  function vyhodnotUceni() {
    clearTimeout(casUceni);
    const d = detailPohledu, s = nejlepsi;
    nejlepsi = 0; detailPohledu = null;
    if (!d || !s) return;
    let zmena = false;
    for (const u of UROVNE) {
      const k = kalibrace[u.id] || (kalibrace[u.id] = {});
      if (k.zamceno) continue;                               // zkalibrováno – drží až do „Znovu kalibrovat“
      if (s * 100 >= u.prah() - 0.5) { k.ok = d; k.zamceno = true; delete k.ne; zmena = true; }
      else if (!(k.ne >= d)) { k.ne = d; zmena = true; }
    }
    if (zmena) { ulozNast('kal', kalibrace); kresli(); }
  }
  const detail = () => procent == null ? null : Math.round(procent * hustota);
  let oknoPohledu = null;   // velikost oblasti prohlížeče v bodech obrazovky (z posledního pohledu)
  const PREKRYV = 0.06;
  // Auto: pole má velikost obrazovky při cílovém přiblížení (s malým překryvem) → klik přiblíží přesně na cíl
  // Auto mřížka: pole velikosti obrazovky při cílovém přiblížení. Počet polí = kolik jich je potřeba bez povinného
  // překryvu (překryv vznikne sám); když by pole o kousek nestačila (do 3 %), pole se mírně zvětší a přiblížení
  // klesne o 1–3 % – pořád nad prahem, protože cíl je práh + 1 % a výchozí prahy mají rezervu. Výsledek: méně záběrů.
  const TOLERANCE = 0.03, MIN_PREKRYV = 0.01;
  function autoMrizka() {
    if (!info || !oknoPohledu) return null;
    const t = potrebnyDetail() / 100 / hustota;   // přiblížení prohlížeče, při kterém má obraz cílový detail
    const cw = oknoPohledu.W / t, ch = oknoPohledu.H / t;   // pole v bodech snímku při cílovém přiblížení
    const ns = Math.max(1, Math.ceil(info.sirka / cw - TOLERANCE));
    const nr = Math.max(1, Math.ceil(info.vyska / ch - TOLERANCE));
    // nejmenší přiblížení, při kterém ns × nr polí pokryje snímek s malým překryvem
    const z = Math.min(t, oknoPohledu.W * ns / (info.sirka * (1 + MIN_PREKRYV)), oknoPohledu.H * nr / (info.vyska * (1 + MIN_PREKRYV)));
    return { ns, nr, w: oknoPohledu.W / z, h: oknoPohledu.H / z, z };
  }
  function velikostPole() { const a = autoMrizka(); return a && { w: a.w, h: a.h }; }
  function rozmer() {
    if (mrizka !== 'auto') return mrizka;
    const a = autoMrizka();
    return a ? [a.ns, a.nr] : [1, 1];
  }
  function pole(rd, s) {
    if (mrizka === 'auto') {
      const v = velikostPole(), [ns, nr] = rozmer();
      if (!v) return [0, 0, 1, 1];
      // pole rovnoměrně tak, aby krajní pole začínala na okraji snímku
      const x0 = ns > 1 ? s * (info.sirka - v.w) / (ns - 1) : (info.sirka - v.w) / 2;
      const y0 = nr > 1 ? rd * (info.vyska - v.h) / (nr - 1) : (info.vyska - v.h) / 2;
      return [x0 / info.sirka, y0 / info.vyska, (x0 + v.w) / info.sirka, (y0 + v.h) / info.vyska];
    }
    const kx = 1 / mrizka[0], ky = 1 / mrizka[1];
    return [Math.max(0, s * kx - PREKRYV), Math.max(0, rd * ky - PREKRYV), Math.min(1, (s + 1) * kx + PREKRYV), Math.min(1, (rd + 1) * ky + PREKRYV)];
  }

  function barva(skala) {
    const p = skala * 100;
    if (!skala) return '#d0d7de';
    if (p >= prahy.zapis - 0.5) return '#1b5e20';
    if (p >= prahy.ideal - 0.5) return '#7cb342';
    if (p >= prahy.min - 0.5) return '#ef8f00';
    return '#cf222e';
  }

  // Nejlepší uložená škála v každé buňce mřížky; vrací i podíl plochy nad prahy
  function pokryti(sloupcu) {
    if (!info) return null;
    const radku = Math.max(1, Math.round(sloupcu * info.vyska / info.sirka));
    const m = new Float32Array(sloupcu * radku);
    const cw = info.sirka / sloupcu, ch = info.vyska / radku;
    for (const d of dlazdice) {
      const [x, y, w, h] = d.rect;
      const c0 = Math.max(0, Math.floor(x / cw)), c1 = Math.min(sloupcu - 1, Math.floor((x + w - 1) / cw));
      const r0 = Math.max(0, Math.floor(y / ch)), r1 = Math.min(radku - 1, Math.floor((y + h - 1) / ch));
      for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) {
        // buňka se počítá, jen když v ní dlaždice leží středem buňky
        const sx = (c + 0.5) * cw, sy = (r + 0.5) * ch;
        if (sx >= x && sx < x + w && sy >= y && sy < y + h && d.skala > m[r * sloupcu + c]) m[r * sloupcu + c] = d.skala;
      }
    }
    let nadMin = 0, nadIdeal = 0, nadZapis = 0;
    for (const v of m) {
      if (v * 100 >= prahy.min - 0.5) nadMin++;
      if (v * 100 >= prahy.ideal - 0.5) nadIdeal++;
      if (v * 100 >= prahy.zapis - 0.5) nadZapis++;
    }
    const pr = x => Math.round(100 * x / m.length);
    return { m, sloupcu, radku, min: pr(nadMin), ideal: pr(nadIdeal), zapis: pr(nadZapis) };
  }

  // Pro každé pole mřížky: je celé (aspoň 95 % buněk mapy) ve zvolené úrovni?
  function stavPoli() {
    if (!mrizka || !info) return [];
    const p = pokryti(40), [ns, nr] = rozmer(), prah = urovenInfo().prah();
    const vys = [];
    for (let rd = 0; rd < nr; rd++) for (let s = 0; s < ns; s++) {
      let n = 0, ok = 0;
      for (let r = 0; r < p.radku; r++) for (let c = 0; c < p.sloupcu; c++) {
        const cx = (c + 0.5) / p.sloupcu, cy = (r + 0.5) / p.radku;
        if (cx >= s / ns && cx < (s + 1) / ns && cy >= rd / nr && cy < (rd + 1) / nr) {
          n++;
          if (p.m[r * p.sloupcu + c] * 100 >= prah - 0.5) ok++;
        }
      }
      vys.push(!!(n && ok / n >= 0.95));
    }
    return vys;
  }

  function kresli() {
    if (!aktivni || !info) return;
    vytvorMapu();
    const $ = s => koren.querySelector(s);
    const p = pokryti(40);
    const W = 180, Hm = Math.round(W * info.vyska / info.sirka);
    platno.width = W * 2; platno.height = Hm * 2;   // ostré i na displeji s vyšší hustotou
    platno.style.height = Hm + 'px';
    platno.style.cursor = mrizka ? 'pointer' : 'default';
    const g = platno.getContext('2d');
    g.setTransform(2, 0, 0, 2, 0, 0);
    const bw = W / p.sloupcu, bh = Hm / p.radku;
    for (let r = 0; r < p.radku; r++) for (let c = 0; c < p.sloupcu; c++) {
      g.fillStyle = barva(p.m[r * p.sloupcu + c]);
      g.fillRect(c * bw, r * bh, Math.ceil(bw), Math.ceil(bh));
    }
    // mřížka: pole hotové = celé aspoň ve zvolené úrovni
    let hotovo = 0, poli = 0;
    if (mrizka && !kalibrujeSe()) {
      const [ns, nr] = rozmer(), hotova = stavPoli();
      poli = ns * nr;
      g.font = '600 11px system-ui'; g.textAlign = 'center'; g.textBaseline = 'middle';
      for (let rd = 0; rd < nr; rd++) for (let s = 0; s < ns; s++) {
        const x0 = s * W / ns, y0 = rd * Hm / nr, w = W / ns, h = Hm / nr;
        const jeHotovo = hotova[rd * ns + s];
        if (jeHotovo) hotovo++;
        g.strokeStyle = 'rgba(255,255,255,.85)'; g.lineWidth = 1; g.strokeRect(x0 + 0.5, y0 + 0.5, w - 1, h - 1);
        const znak = jeHotovo ? '✓' : String(rd * ns + s + 1);
        g.lineWidth = 3; g.strokeStyle = 'rgba(0,0,0,.6)'; g.strokeText(znak, x0 + w / 2, y0 + h / 2);   // čitelné na každé barvě
        g.fillStyle = '#fff'; g.fillText(znak, x0 + w / 2, y0 + h / 2);
      }
    }
    if (pohled) {
      g.strokeStyle = '#0969da'; g.lineWidth = 2;
      const [x0, y0, x1, y1] = pohled.map((v, i) => Math.max(0, Math.min(1, v)) * (i % 2 ? Hm : W));
      g.strokeRect(x0 + 1, y0 + 1, Math.max(2, x1 - x0 - 2), Math.max(2, y1 - y0 - 2));
    }
    // úrovně (zároveň legenda): pokrytí stránky a zvolený cíl
    const pk = { prehled: p.min, cteni: p.ideal, zapis: p.zapis };
    for (const u of UROVNE) {
      const b = $(`[data-uroven="${u.id}"]`);
      b.classList.toggle('zvoleno', u.id === uroven);
      b.classList.toggle('tmava', u.id === 'zapis');
      b.style.background = u.id === uroven ? u.barva : '';
      b.title = `Cíl ${u.nazev.toLowerCase()}: od ${u.prah()} % plného rozlišení. Stránka v této úrovni: ${pk[u.id]} %`;
      $(`[data-pokryti="${u.id}"]`).textContent = `${pk[u.id]} %`;
    }
    const polCil = $('[data-cil]');
    if (koren.activeElement !== polCil) polCil.value = cilUrovne();
    const pd = potrebnyDetail(), d = detail();
    $('[data-pohled]').textContent = `Detail ${d ?? '?'} % · pro ${urovenInfo().nazev.toLowerCase()} ${kalibrovano() ? '' : 'asi '}${pd} %`
      + (kalibrovano() ? ' ✓' : '');
    $('[data-kalinfo]').textContent = 'Zjištěno na tomto webu: ' + UROVNE.map(u => { const k = kalibrace[u.id]; return `${u.nazev.toLowerCase()} ${k && k.zamceno ? k.ok + ' %' : '?'}`; }).join(', ');
    $('[data-kalznovu]').textContent = `Znovu kalibrovat ${urovenInfo().nazev.toLowerCase()}`;
    const pl = $('[data-pole]');
    const kal = kalibrujeSe();
    pl.className = kal ? 'kalibrace' : mrizka && poli && hotovo === poli ? 'hotovo' : '';
    pl.textContent = kal ? `Kalibrace (${urovenInfo().nazev.toLowerCase()}): přibližuj kdekoli na stránce, dokud místo `
        + `${uroven === 'zapis' ? 'tmavě ' : ''}nezezelená. Pak se mřížka ukáže sama.`
      : !mrizka ? '' : hotovo === poli ? '✓ Stránka hotová – můžeš na další'
      : `Zbývá ${poli - hotovo} z ${poli} polí (${urovenInfo().nazev.toLowerCase()})`;
    $('[data-souhrn]').textContent = kal ? 'kalibrace' : mrizka && poli ? `${hotovo}/${poli}` : '';
    $('[data-dalsi]').style.display = kal ? 'none' : '';
    $('[data-dalsi]').style.visibility = mrizka && hotovo === poli ? 'hidden' : '';
    const skok = skoky.get(obrazKlic);
    $('[data-ulozeni]').textContent = skok ? `⚠ Sám neukládám: ${skok}. Zkontroluj adresu snímku (uložit jde tlačítkem Uložit teď).`
      : (novych ? (mrizka && poli && hotovo < poli ? 'Uložím, až budou hotová všechna pole' : 'Ukládám…') : ulozenoV ? `Uloženo ${ulozenoV}` : 'Zatím nic k uložení') + (stavZachytu ? ` · ${stavZachytu}` : '');
    // stav čitelný skriptem (Claude v prohlížeči): document.querySelector('[data-snimkovac-mapa]').dataset
    try {
      Object.assign(box.dataset, { snimek: String(snimekOtevreny ?? ''), pole: mrizka && poli ? `${hotovo}/${poli}` : '',
        ulozeno: ulozenoV, uklada: novych ? '1' : '', skok: skok || '', verze: chrome.runtime.getManifest().version });
    } catch (x) { /* rozšíření mezitím obnoveno – stav se nezapíše, panel se odpojí sám */ }
    $('[data-varovani]').hidden = !chybaZachytu;
    $('[data-varovani-text]').textContent = chybaZachytu;
    const pata = $('[data-pata]');
    pata.textContent = dnes ? `Dnes ${dnes.snimku} snímků` + (dnes.chyby ? ` · nenačteno ${dnes.chyby} dlaždic ⓘ` : '') : '';
    pata.title = dnes ? `${dnes.zeServeru} dlaždic ze serveru (${(dnes.bajtu / 1048576).toFixed(1)} MB)`
      + (dnes.zruseno ? `, ${dnes.zruseno} zrušil prohlížeč archivu sám (rychlé listování – v pořádku)` : '')
      + (dnes.chyby ? `.\nNenačteno = server dlaždici nevrátil (výpadek sítě, 403 / blokace). Pár kusů nevadí, `
        + `snímek se doskládá. Když jich přibývá a snímky zůstávají bílé, přestaň – archiv nejspíš blokuje.`
        + (dnes.zpravy && dnes.zpravy.length ? `\nPoslední: ${dnes.zpravy[dnes.zpravy.length - 1]}` : '') : '') : '';
    const st = $('.hlava .stav');
    st.className = 'stav ' + (chybaZachytu ? 'chyba' : novych ? 'prace' : ulozenoV ? 'ok' : '');
  }

  // --- spojení s háčkem a workerem ----------------------------------------------------------------------------
  // --- automatické ukládání: po chvíli klidu, při přepnutí snímku a při odchodu ze stránky ---
  let novych = 0, ulozenoV = '', casovacUlozeni = null, posledniPopis = null;
  const skoky = new Map();   // klíč snímku → důvod: snímek, na který stránka skočila sama (neukládá se sám)
  let casOtevreni = 0, snimekOtevreny = null;
  const KLID_MS = 8000;

  function ulozPoskladany(rucne) {
    if (!zivy()) return Promise.resolve();
    clearTimeout(casovacUlozeni);
    if (!novych || !posledniPopis || !info) return Promise.resolve();
    // snímek, na který stránka skočila sama (MZA, chybná adresa), se neukládá – jen na „Uložit teď“
    if (rucne !== true && skoky.has(posledniPopis.klic)) { novych = 0; kresli(); return Promise.resolve(); }
    const p = pokryti(40);
    const zprava = { typ: 'osd-sloz', obraz: obrazKlic, popis: posledniPopis, vyrez: null,
                     pokryti: { prehled_procent: p.min, ideal_procent: p.ideal, zapis_procent: p.zapis, prahy } };
    novych = 0;
    return chrome.runtime.sendMessage(zprava).then(r => {
      if (r && r.ok) ulozenoV = new Date().toLocaleTimeString('cs-CZ', { hour: '2-digit', minute: '2-digit' });
      kresli();
      return r;
    }, () => {});
  }

  // Poskládání celého snímku v plném rozlišení trvá několik sekund. Při procházení polí (Další pole) se proto
  // neskládá po každém poli, ale až když jsou všechna pole hotová (pak hned) – nebo po delším klidu, při přepnutí
  // snímku a při odchodu ze stránky. Bez mřížky jako dřív po 8 s klidu.
  const KLID_POLE_MS = 45000, HOTOVO_MS = 1500;
  function naplanujUlozeni() {
    clearTimeout(casovacUlozeni);
    let ms = KLID_MS;
    if (mrizka && !kalibrujeSe()) {
      const stav = stavPoli();
      ms = stav.length && stav.every(Boolean) ? HOTOVO_MS : KLID_POLE_MS;
    }
    casovacUlozeni = setTimeout(ulozPoskladany, ms);
  }

  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') ulozPoskladany(); });
  window.addEventListener('pagehide', () => { posliPocitadlo(); ulozPoskladany(); });

  // --- počítadlo (denní limity archivu): jen čísla, ukládají se lokálně v rozšíření ---
  let dnes = null;
  const prazdny = () => ({ dlazdice: 0, zeServeru: 0, zMezipameti: 0, nevime: 0, bajtu: 0, chyby: 0, zruseno: 0, zpravy: [], snimky: [] });
  const sber = prazdny();
  function posliPocitadlo() {
    if (!zivy()) return;
    if (!sber.dlazdice && !sber.chyby && !sber.zruseno && !sber.snimky.length) return;
    const data = { ...sber, zpravy: sber.zpravy.slice(0, 5), snimky: [...sber.snimky] };
    Object.assign(sber, prazdny());
    chrome.runtime.sendMessage({ typ: 'pocitadlo', host: location.hostname, data }).then(r => { if (r) { dnes = r; kresli(); } }, () => {});
  }
  intervalPocitadla = setInterval(posliPocitadlo, 5000);
  chrome.runtime.sendMessage({ typ: 'pocitadlo', host: location.hostname, data: null }).then(r => { if (r) dnes = r; }, () => {});

  // Držení přiblížení mezi snímky: pamatuje poslední přiblížený pohled; po přepnutí snímku (tvým klikem v archivu)
  // ho jednou nastaví i na novém snímku – jen když jsi mezitím sám nepřiblížil jinam.
  let drzet = true, drzenyPohled = null, drzenyKlic = null, casDrz = 0;
  // pamatuje se i v úložišti: některé archivy (Třeboň) při přepnutí snímku načtou rám znovu
  const KLIC_DRZ = 'drzpohled_' + location.hostname;
  const nactenDrz = chrome.storage.local.get(KLIC_DRZ).then(d => {
    const z = d[KLIC_DRZ];
    if (z && Date.now() - z.cas < 30 * 60e3 && !drzenyPohled) { drzenyPohled = z.v; drzenyKlic = z.klic; }
  });
  function zapamatujPohled(v) {
    drzenyPohled = v; drzenyKlic = obrazKlic;
    const klic = obrazKlic;
    clearTimeout(casDrz);
    casDrz = setTimeout(() => chrome.storage.local.set({ [KLIC_DRZ]: { v, klic, cas: Date.now() } }), 400);
  }
  const jePriblizeny = v => v && (v[2] - v[0] < 0.92 || v[3] - v[1] < 0.92);
  // pohled k držení jen rozumný: aspoň 2 % stránky a ne přes 2× plné rozlišení (jinak by „drž“ přenesl extrémní přiblížení)
  const rozumnyPohled = v => v && v[2] - v[0] >= 0.02 && v[3] - v[1] >= 0.02 && !(procent > 200);
  // Po otevření snímku: s „drž“ poslední známý pohled, jinak (když archiv otevře snímek přiblížený, např. AHMP vpravo
  // dole) celá stránka. Jen když uživatel mezitím sám nic neposunul ani nepřiblížil. Do té doby se pohled nepamatuje,
  // aby si rozšíření nezapamatovalo výchozí pohled archivu.
  let casInterakce = 0, cekaNaObnovu = false;
  for (const ud of ['wheel', 'pointerdown', 'keydown']) window.addEventListener(ud, () => { casInterakce = Date.now(); }, true);
  function obnovPriblizeni(klic) {
    const start = Date.now();
    cekaNaObnovu = true;
    setTimeout(() => {
      cekaNaObnovu = false;
      if (obrazKlic !== klic || casInterakce > start) return;   // mezitím jiný snímek nebo uživatel sám pohnul
      const skok = skokStranky();   // snímek, který nikdo nechtěl: nepřibližovat (stálo by to denní limit)
      if (skok) { skoky.set(klic, skok); kresli(); return; }
      const cil = drzet && drzenyPohled && rozumnyPohled(drzenyPohled) ? drzenyPohled : (jePriblizeny(pohled) ? [0, 0, 1, 1] : null);
      if (cil) window.postMessage({ [TAG + '-pokyn']: 'prejdi', vyrez: cil }, location.origin);
    }, 1500);
  }

  async function nactiUlozene() {
    await nactenDrz;
    const predchozi = obrazKlic || drzenyKlic;
    sber.snimky.push(popisStranky().klic);   // otevřený snímek (worker počítá různé za den)
    await ulozPoskladany();   // předchozí snímek uložit dřív, než se přepne
    ulozenoV = '';
    const d = popisStranky();
    obrazKlic = d.klic;
    snimekOtevreny = d.snimek;
    casOtevreni = Date.now();
    let r = null;
    try { r = await chrome.runtime.sendMessage({ typ: 'osd-seznam', obraz: obrazKlic }); } catch (x) { /* worker se restartuje */ }
    dlazdice = (r && r.dlazdice) || [];
    kresli();
    if (predchozi !== obrazKlic) obnovPriblizeni(obrazKlic);
  }

  const doDataUrl = b => new Promise(ok => { const f = new FileReader(); f.onload = () => ok(f.result); f.readAsDataURL(b); });

  window.addEventListener('message', async e => {
    if (e.source !== window || !e.data || !e.data[TAG]) return;
    if (!zivy()) return;
    const typ = e.data[TAG];
    if (typ === 'pripojeno' || typ === 'otevreno') {
      aktivni = true;
      const s = await chrome.storage.local.get(['prahy']);
      if (s.prahy) nastavPrahy(s.prahy);
      setTimeout(nactiUlozene, 300);   // po přepnutí snímku se mění adresa a číslo snímku
    }
    if (typ === 'stav') {
      aktivni = true;
      if (obrazKlic !== popisStranky().klic) await nactiUlozene();
      info = e.data.info; procent = e.data.procent; pohled = e.data.pohled; hustota = e.data.hustota || 1;
      // až po ustálení (číslo snímku v poli stránky se po přepnutí chvíli nemění)
      if (obrazKlic && !skoky.has(obrazKlic) && Date.now() - casOtevreni > 1500) { const s = skokStranky(); if (s) skoky.set(obrazKlic, s); }
      if (procent !== posledniProcent) { if (detailPohledu) vyhodnotUceni(); posledniProcent = procent; casZoomu = Date.now(); }
      if (info && pohled && procent) {   // oblast prohlížeče v bodech obrazovky = viditelná část snímku × přiblížení
        // velikost okna prohlížeče: přímo od háčku (stabilní), jinak odvozená z pohledu
        oknoPohledu = Array.isArray(e.data.okno) && e.data.okno[0] > 0 ? { W: e.data.okno[0], H: e.data.okno[1] }
          : { W: (pohled[2] - pohled[0]) * info.sirka * procent / 100, H: (pohled[3] - pohled[1]) * info.vyska * procent / 100 };
        stupne = !!e.data.stupne;
        minPixelRatio = e.data.minPixelRatio || 0.5;
      }
      if (jePriblizeny(pohled) && rozumnyPohled(pohled) && obrazKlic && !cekaNaObnovu) zapamatujPohled(pohled.map(v => Math.max(0, Math.min(1, v))));
      kresli();
    }
    if (typ === 'nacteno') {
      sber.dlazdice++;
      if (e.data.zeServeru === true) { sber.zeServeru++; sber.bajtu += e.data.bajtu || 0; }
      else if (e.data.zeServeru === false) sber.zMezipameti++;
      else sber.nevime++;
    }
    if (typ === 'chyba') {
      // „Image load aborted“ = prohlížeč archivu sám zrušil dlaždici, která už nebyla potřeba (rychlé listování nebo
      // přibližování). Není to chyba serveru ani blokace – počítá se zvlášť a v panelu se nestraší.
      if (/abort/i.test(e.data.zprava || '')) { sber.zruseno++; return; }
      sber.chyby++;
      sber.zpravy.push(new Date().toLocaleTimeString('cs-CZ') + ' ' + e.data.zprava);
      posliPocitadlo();
    }
    if (typ === 'ladeni') { chybaZachytu = e.data.duvod; kresli(); return; }
    if (typ === 'zachyt-obrazovku') {   // plátno nejde přečíst: rozšíření vyfotí viditelnou část záložky
      aktivni = true;
      fotim = true;
      if (box) box.style.visibility = 'hidden';   // minimapa ani ovládání prohlížeče nesmí být na snímku
      const skryj = document.createElement('style');
      skryj.textContent = '[data-snimkovac-skryt]{visibility:hidden!important}';
      document.documentElement.appendChild(skryj);
      await new Promise(ok => requestAnimationFrame(() => requestAnimationFrame(ok)));
      let r = null;
      // panel a ovládání archivu se ukážou vždy – i když rozšíření mezitím odpadne nebo focení nedoběhne (nejvýš 10 s)
      try {
        r = await Promise.race([
          chrome.runtime.sendMessage({ typ: 'zachyt-obrazovku', klient: e.data.klient, okno: e.data.okno, rect: e.data.rect, hustota: e.data.hustota }),
          new Promise(ok => setTimeout(() => ok({ chyba: 'Focení nedoběhlo do 10 s – zkus Fotit teď' }), 10000))
        ]);
      } catch (x) { /* nic */ }
      finally {
        skryj.remove();
        for (const el of document.querySelectorAll('[data-snimkovac-skryt]')) el.removeAttribute('data-snimkovac-skryt');
        if (box) box.style.visibility = '';
      }
      if (!r || !r.dataUrl) {
        chybaZachytu = (r && r.chyba) || 'Nepovedlo se vyfotit – zkus to znovu';
        fotimPovoleni = !!(r && r.povoleni);
        kresli();
        return;
      }
      chybaZachytu = ''; fotimPovoleni = false;
      stavZachytu = 'vyfoceno ' + new Date().toLocaleTimeString('cs-CZ') + ` (${Math.round(r.skala * 100)} %)`;
      const blob = await (await fetch(r.dataUrl)).blob();   // data: URL – žádná síť
      window.postMessage({ [TAG]: 'dlazdice', info: e.data.info, level: Math.round(r.skala * 1000), x: Math.round(e.data.rect[0]),
                           y: Math.round(e.data.rect[1]), skala: r.skala, rect: e.data.rect, blob, prepsat: !!e.data.prepsat }, location.origin);
      return;
    }
    if (typ === 'dlazdice') {
      aktivni = true;
      if (typeof e.data.skala === 'number') uc(e.data.skala);
      const d = popisStranky();
      if (d.klic !== obrazKlic) await nactiUlozene();
      if (e.data.info) info = e.data.info;
      if (!info) return;
      const zpr = {
        typ: 'osd-dlazdice', obraz: obrazKlic, popis: { ...d, sirka: info.sirka, vyska: info.vyska },
        level: e.data.level, x: e.data.x, y: e.data.y, skala: e.data.skala, rect: e.data.rect, prepsat: !!e.data.prepsat,
        data: await doDataUrl(e.data.blob)
      };
      // Pozadí rozšíření (worker) se občas uspí nebo restartuje a zpráva se ztratí („message channel closed“,
      // „Receiving end does not exist“). Dlaždice by pak v uloženém snímku chyběla – jednou to zkusit znovu.
      let r = null;
      for (let pokus = 0; pokus < 2 && !r; pokus++) {
        if (!zivy()) return;
        try { r = await chrome.runtime.sendMessage(zpr); }
        catch (x) { await new Promise(ok => setTimeout(ok, 1000)); }
      }
      if (r && r.nova) {
        dlazdice.push({ skala: e.data.skala, rect: e.data.rect });
        novych++;
        posledniPopis = { ...d, sirka: info.sirka, vyska: info.vyska };
        naplanujUlozeni();
        kresli();
      }
    }
  });

  chrome.storage.local.get(['prahy']).then(s => { if (s.prahy) nastavPrahy(s.prahy); });
  chrome.storage.onChanged.addListener(z => { if (z.prahy) { nastavPrahy(z.prahy.newValue); kresli(); } });

  // Pokyny z popupu
  chrome.runtime.onMessage.addListener((z, od, odpoved) => {
    if (!z) return;
    if (!aktivni || !info) return;   // tady prohlížeč snímků neběží – odpoví jiný rám
    if (z.typ === 'osd-stav') {
      posliPocitadlo();
      // otevřením okénka dal prohlížeč záložce povolení ke snímku – když focení selhalo, vyfotit hned znovu
      // (uživatel nemusí hýbat přiblížením)
      const opakovat = !!chybaZachytu;
      odpoved({ procent, detail: detail(), pohled, pokryti: (() => { const p = pokryti(40); return { min: p.min, ideal: p.ideal, zapis: p.zapis }; })(),
                popis: popisStranky(), fotim, chyba: chybaZachytu, potrebujePovoleni: fotimPovoleni, ulozeno: ulozenoV });
      if (opakovat) { chybaZachytu = ''; kresli(); window.postMessage({ [TAG + '-pokyn']: 'stav' }, location.origin); }
    }
    if (z.typ === 'osd-smaz') {
      clearTimeout(casovacUlozeni);
      novych = 0;
      chrome.runtime.sendMessage({ typ: 'osd-smaz-obraz', obraz: obrazKlic }).then(r => {
        dlazdice = [];
        ulozenoV = '';
        kresli();
        odpoved(r);
      }, e => odpoved({ ok: false, chyba: String(e) }));
      return true;
    }
    if (z.typ === 'osd-prejdi') window.postMessage({ [TAG + '-pokyn']: 'prejdi', vyrez: z.vyrez }, location.origin);
    if (z.typ === 'osd-uloz') {
      clearTimeout(casovacUlozeni);
      novych = 0;
      const p = pokryti(40);
      chrome.runtime.sendMessage({ typ: 'osd-sloz', obraz: obrazKlic, popis: { ...popisStranky(), sirka: info.sirka, vyska: info.vyska },
                                   vyrez: z.vyrez ? pohled.map(v => Math.max(0, Math.min(1, v))) : null,
                                   pokryti: { prehled_procent: p.min, ideal_procent: p.ideal, zapis_procent: p.zapis, prahy } }, odpoved);
      return true;
    }
  });

  window.postMessage({ [TAG + '-pokyn']: 'stav' }, location.origin);   // háček už mohl být připojený dřív
})();
