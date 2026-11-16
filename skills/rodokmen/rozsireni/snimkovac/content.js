// Snímkovač – content script. Běží na eBadatelně SOA Praha a na webech, které uživatel sám povolil v popupu.
// Jen PASIVNĚ: když stránka sama načte snímek, nakreslí se z něj kopie do canvasu a pošle se ke stažení na lokální
// disk. Žádná další síťová komunikace, žádné listování ani předbíhání.
(() => {
  if (window.__snimkovac) return;   // skript se mohl vložit podruhé (registrace + okamžité vložení)
  window.__snimkovac = true;

  let posledniSrc = null;   // adresa obrázku, který už jsme zpracovali (nebo zpracováváme)
  let casovac = null;
  let stavStranky = { ok: true, text: '' };   // pro popup: varování

  const JE_EBAD = location.hostname === 'ebadatelna.soapraha.cz';
  const JE_MATR = location.hostname === 'data.matricula-online.eu';
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
  function odpoj() { clearTimeout(casovac); pozorovatel.disconnect(); }


  // --- adaptér Matricula Online: celý snímek předá háček matricula_hook.js (svět stránky) ----------------------
  // Adresa knihy /<jazyk>/<země>/<diecéze>/<farnost>/<signatura>/?pg=N
  let posledniMatr = null;
  function knihaMatriculy() {
    const c = location.pathname.split('/').filter(Boolean).map(s => { try { return decodeURIComponent(s); } catch (e) { return s; } });
    if (c.length < 5) return null;
    const [, , dieceze, farnost, signatura] = c;
    const casti = (document.title || '').split('|').map(s => s.trim());
    const nazevFarnosti = casti[1] || farnost;
    return { id: `${farnost}_${signatura}`, dieceze, farnost, signatura, kniha: `Matricula ${nazevFarnosti} ${signatura}`,
             druhKnihy: (casti[0] || '').split(' - ')[0] };
  }
  async function ulozMatriculu(d, znovu) {
    if (!zivy()) return;
    const k = knihaMatriculy();
    if (!k) { stavStranky = { ok: false, text: 'neznámá adresa knihy – neukládám' }; return; }
    const pg = parseInt(new URLSearchParams(location.search).get('pg'), 10) || null;
    const snimek = (d.poradi && d.poradi.snimek) || pg;
    if (!snimek) { stavStranky = { ok: false, text: 'neznámé číslo snímku – neukládám' }; return; }
    stavStranky = { ok: true, text: '' };
    const dataUrl = await new Promise(ok => { const r = new FileReader(); r.onload = () => ok(r.result); r.readAsDataURL(d.blob); });
    const meta = {
      adresa: `${location.origin}${location.pathname}?pg=${snimek}`, obrazek: d.puvodni || '', druh: 'matricula', host: location.hostname,
      matrikaId: k.id, snimek, stitek: (d.poradi && d.poradi.stitek) || '', snimku_v_knize: (d.poradi && d.poradi.pocet) || null,
      kniha: k.kniha, druh_knihy: k.druhKnihy, dieceze: k.dieceze, farnost: k.farnost, signatura: k.signatura,
      pg_v_adrese: pg, cas: new Date().toISOString(), sirka: d.sirka, vyska: d.vyska, uzivatel_zobrazil: true,
      licence: 'CC BY-NC-ND 2.0 (Matricula Online) – jen nekomerčně, při zveřejnění uvést zdroj a informovat archiv'
    };
    if (znovu) meta.ulozeno_znovu = true;
    try {
      const r = await chrome.runtime.sendMessage({ typ: 'uloz', dataUrl, meta, znovu: !!znovu });
      if (r && r.duvod === 'uz-ulozeno') { stavStranky = { ok: true, text: '', uz: r.kdy || true }; oznameni(`Snímek ${snimek} už máš uložený`, 'info'); }
      else if (r && r.ulozeno) oznameni(`${znovu ? 'Uloženo znovu' : 'Uloženo'} – snímek ${snimek}${meta.stitek ? ' (' + meta.stitek + ')' : ''}`, 'ok');
      else if (r && r.duvod === 'vypnuto') oznameni('Ukládání je vypnuté', 'pozor');
      else if (r && r.chyba) oznameni('Nepovedlo se uložit – zkus to znovu', 'chyba');
    } catch (e) { console.warn('Snímkovač: zpráva se nepodařila', e); }
  }
  if (JE_MATR) {
    window.addEventListener('message', e => {
      if (e.source !== window || !e.data || !e.data['snimkovac-matricula']) return;
      if (e.data['snimkovac-matricula'] === 'chyba') { stavStranky = { ok: false, text: e.data.zprava }; return; }
      posledniMatr = e.data;
      setTimeout(() => ulozMatriculu(e.data, false), 300);   // ať se stihne přepsat ?pg= v adrese
    });
    // háčku říct, jestli je ukládání zapnuté (vypnutý Snímkovač na stránce nic nedělá)
    const rekniZap = z => window.postMessage({ 'snimkovac-matricula-pokyn': 'zap', hodnota: z !== false }, location.origin);
    chrome.storage.local.get('zap').then(d => rekniZap(d.zap));
    chrome.storage.onChanged.addListener(z => { if (z.zap && zivy()) rekniZap(z.zap.newValue); });
  }

  // --- adaptér eBadatelna SOA Praha ---------------------------------------------------------------------------
  // Adresa PŘÍSNĚ /d/<matrikaId>/<snímek> nebo /a/<archivalieId>/<snímek> (nic dalšího, ani mezery)
  function zAdresyEbad() {
    const m = location.pathname.match(/^\/(d|a)\/(\d+)\/(\d+)\/?$/);
    return m ? { druh: m[1], id: m[2], snimek: parseInt(m[3], 10) } : null;
  }

  // Číslo snímku, které ukazuje prohlížeč eBadatelny (select v dolní liště: ≥5 číselných voleb). null = nenalezeno.
  function cisloZPrehlizece() {
    for (const s of document.querySelectorAll('select')) {
      const volby = [...s.options];
      if (volby.length < 5 || !volby.every(o => /^\d+$/.test(o.text.trim()))) continue;
      const o = s.options[s.selectedIndex];
      if (o) return parseInt(o.text.trim(), 10);
    }
    return null;
  }

  // Název knihy z horní lišty („Benešov 49“); záloha nadpisy a titulek
  function nazevKnihyEbad() {
    const odkazy = [...document.querySelectorAll('a')]
      .map(e => ({ t: (e.innerText || '').trim(), r: e.getBoundingClientRect() }))
      .filter(o => o.r.width > 0 && o.r.top >= 0 && o.r.top < 120 && o.t.length < 60 && /^\S.*\s\d+$/.test(o.t))
      .sort((a, b) => a.r.left - b.r.left);
    if (odkazy.length) return odkazy[0].t;
    const kandidati = [];
    document.querySelectorAll('h1, h2, h3, [class*="title" i], [class*="header" i], [class*="breadcrumb" i]')
      .forEach(e => kandidati.push((e.innerText || '').trim()));
    kandidati.push(document.title || '');
    for (const t of kandidati) {
      if (!t || t.length > 200) continue;
      const casti = t.split(/\s*[\/›»>]\s*/).map(s => s.trim()).filter(Boolean);
      if (casti.length > 1) return casti[casti.length - 1];
    }
    return '';
  }

  // --- obecný adaptér: jeden velký <img> (neumí dlaždicové prohlížeče) -----------------------------------------
  function hash(s) {   // krátký stabilní otisk adresy obrázku (FNV-1a)
    let h = 0x811c9dc5;
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
    return h.toString(16).padStart(8, '0');
  }

  function nejvetsiObrazek() {
    let best = null, plocha = 0;
    for (const im of document.images) {
      if (!im.complete || im.naturalWidth < 1200) continue;
      const r = im.getBoundingClientRect();
      if (r.width < 50 || r.height < 50) continue;
      const p = im.naturalWidth * im.naturalHeight;
      if (p > plocha) { best = im; plocha = p; }
    }
    return best;
  }

  // --- společná část -------------------------------------------------------------------------------------------
  chrome.runtime.onMessage.addListener((z, od, odpoved) => {
    if (z && z.typ === 'stranka') odpoved(stavStranky);
    if (z && z.typ === 'znovu') {   // z popupu: uložit aktuální snímek znovu
      posledniSrc = null;
      ulozitAktualni(true).then(() => odpoved({ ok: true }));
      return true;
    }
  });

  async function ulozitAktualni(znovu) {
    if (!zivy()) return;
    if (JE_MATR) {
      if (znovu && posledniMatr) await ulozMatriculu(posledniMatr, true);
      else if (!posledniMatr) stavStranky = { ok: false, text: 'snímek zatím nezachycen – po zapnutí obnov stránku (F5)' };
      return;
    }
    let im, a, kniha;
    if (JE_EBAD) {
      im = document.getElementById('scanImage');
      if (!im) return;
      a = zAdresyEbad();
      if (!a) {
        stavStranky = { ok: false, text: 'neplatná adresa – neukládám' };
        return;
      }
      const zPrehlizece = cisloZPrehlizece();
      if (zPrehlizece !== null && zPrehlizece !== a.snimek) {
        stavStranky = { ok: false, text: `nesouhlasí číslo snímku (adresa ${a.snimek}, prohlížeč ${zPrehlizece}) – neukládám` };
        console.warn('Snímkovač:', stavStranky.text);
        return;
      }
      kniha = nazevKnihyEbad();
    } else {
      im = nejvetsiObrazek();
      if (!im) return;
      const s = (im.currentSrc || im.src || '').split(';jsessionid=')[0];
      a = { druh: 'web', id: location.hostname, snimek: hash(s) };
      kniha = (document.title || '').trim().slice(0, 80);
    }
    stavStranky = { ok: true, text: '' };
    if (!im.complete || !im.naturalWidth) return;   // ještě se načítá; zavolá se znovu po události load
    const src = (im.currentSrc || im.src || '').split(';jsessionid=')[0];
    if (!src || (src === posledniSrc && !znovu)) return;
    posledniSrc = src;
    let blob;
    try {
      const c = document.createElement('canvas');
      c.width = im.naturalWidth;
      c.height = im.naturalHeight;
      c.getContext('2d').drawImage(im, 0, 0);
      blob = await new Promise(ok => c.toBlob(ok, 'image/jpeg', 0.92));
    } catch (e) {
      stavStranky = { ok: false, text: 'obrázek nejde přečíst (pochází z jiného serveru)' };
      console.warn('Snímkovač: obrázek nejde přečíst (canvas)', e);
      return;
    }
    if (!blob) return;
    const dataUrl = await new Promise(ok => {
      const r = new FileReader();
      r.onload = () => ok(r.result);
      r.readAsDataURL(blob);
    });
    const meta = {
      adresa: location.origin + location.pathname,
      obrazek: src.split('?')[0],
      druh: a.druh,
      matrikaId: a.id,
      snimek: a.snimek,
      kniha,
      cas: new Date().toISOString(),
      sirka: im.naturalWidth,
      vyska: im.naturalHeight,
      uzivatel_zobrazil: true
    };
    if (znovu) meta.ulozeno_znovu = true;
    if (!JE_EBAD) meta.obrazek = src;   // u obecného webu je adresa obrázku jediný klíč k jeho nalezení
    try {
      const r = await chrome.runtime.sendMessage({ typ: 'uloz', dataUrl, meta, znovu: !!znovu });
      if (r && r.duvod === 'uz-ulozeno') {
        stavStranky = { ok: true, text: '', uz: r.kdy || true };
        oznameni(`Snímek ${a.snimek} už máš uložený`, 'info');
      } else if (r && r.ulozeno) oznameni(`${znovu ? 'Uloženo znovu' : 'Uloženo'} – snímek ${a.snimek}`, 'ok');
      else if (r && r.chyba) oznameni('Nepovedlo se uložit – zkus to znovu', 'chyba');
    } catch (e) {
      console.warn('Snímkovač: zpráva se nepodařila', e);
    }
  }

  // Krátké oznámení vpravo dole na 2,5 s (jen na obrazovce, nic se neodesílá)
  // barevná tečka: zelená = hotovo, modrá = informace, žlutá = čeká na tebe, červená = chyba
  const TECKY = { ok: '#2da44e', info: '#54aeff', pozor: '#d29922', chyba: '#cf222e' };
  function oznameni(text, druh = 'ok') {
    const d = document.createElement('div');
    const t = document.createElement('span');
    t.style.cssText = `display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:8px;background:${TECKY[druh] || TECKY.ok}`;
    d.append(t, document.createTextNode(text));
    d.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:2147483647;padding:8px 14px;border-radius:8px;'
      + 'background:#24292f;color:#fff;font:13px/1.3 system-ui,"Segoe UI",sans-serif;box-shadow:0 4px 14px rgba(0,0,0,.3);'
      + 'pointer-events:none;transition:opacity .4s';
    document.body.appendChild(d);
    setTimeout(() => { d.style.opacity = '0'; }, 2100);
    setTimeout(() => d.remove(), 2600);
  }

  // Krátká prodleva, aby se stihla přepsat adresa stránky i hlavička (stránka je jednostránková aplikace).
  function naplanovat() {
    clearTimeout(casovac);
    casovac = setTimeout(ulozitAktualni, 800);
  }

  document.addEventListener('load', e => {
    if (e.target && (JE_EBAD ? e.target.id === 'scanImage' : e.target.tagName === 'IMG')) naplanovat();
  }, true);

  const pozorovatel = new MutationObserver(() => naplanovat());
  pozorovatel.observe(document.documentElement, {
    subtree: true, childList: true, attributes: true, attributeFilter: ['src']
  });

  naplanovat();   // snímek už může být načtený, než se skript spustil
})();
