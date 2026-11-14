// Snímkovač – háček pro dlaždicové prohlížeče OpenSeadragon (MZA Acta Publica aj.). Běží ve světě stránky (MAIN),
// jen na webech, které uživatel sám povolil. Nic nestahuje: bere dlaždice, které prohlížeč už SÁM načetl
// (událost tile-loaded, případně jeho vnitřní mezipaměť), a posílá je přes window.postMessage do osd.js.
// Na pokyn uživatele (tlačítko „Přejít na výřez“) umí přiblížit na zadaný výřez – to je totéž, jako když přiblíží ručně.
(() => {
  if (window.__snimkovacOsd) return;
  window.__snimkovacOsd = true;
  const TAG = 'snimkovac-osd';
  let viewer = null;
  const odeslane = new Set();   // level/x/y už poslané v tomto načtení stránky
  // počítadlo pro denní limity: záznamy o stažení (velikost, zda šlo ze serveru) – zvětšit vyrovnávací paměť záznamů
  try { performance.setResourceTimingBufferSize(50000); } catch (x) { /* nic */ }

  // dokud se nepřipojí osd.js (běží až po načtení stránky), počty se drží tady
  let uiPripojeno = false;
  const cekajici = [];

  // Počítá každé stažení dlaždice ze záznamů prohlížeče (i těch před připojením k prohlížeči snímků).
  // transferSize > 0 = šlo ze serveru, 0 s obsahem = z mezipaměti prohlížeče.
  const JE_DLAZDICE = /cgi-bin\/i_|iipsrv|Deepzoom=|_files\/\d+\/\d+_\d+\.|TileGroup\d|\/tiles?\/|\/full\/[^/]+\/\d+\/default\./i;
  const NENI_DLAZDICE = /\.dzi(\?|$)|\.xml(\?|$)|info\.json|ImageProperties/i;
  try {
    new PerformanceObserver(seznam => {
      for (const e of seznam.getEntries()) {
        if (!JE_DLAZDICE.test(e.name) || NENI_DLAZDICE.test(e.name)) continue;
        const c = { zeServeru: e.transferSize > 0 ? true : (e.decodedBodySize > 0 ? false : null), bajtu: e.transferSize || 0 };
        if (uiPripojeno) posli('nacteno', c); else cekajici.push(c);
      }
    }).observe({ type: 'resource', buffered: true });
  } catch (x) { /* starý prohlížeč */ }

  const posli =(typ, data) => window.postMessage({ [TAG]: typ, ...data }, location.origin);

  function polozka() {
    return viewer && viewer.world && viewer.world.getItemCount() ? viewer.world.getItemAt(0) : null;
  }

  function info() {
    const ti = polozka();
    if (!ti || !ti.source) return null;
    const s = ti.source;
    return { sirka: s.width || (s.dimensions && s.dimensions.x), vyska: s.height || (s.dimensions && s.dimensions.y),
             maxLevel: s.maxLevel, dlazdice: s.tileSize || (s.getTileWidth && s.getTileWidth(s.maxLevel)), presah: s.tileOverlap || 0 };
  }

  // Obrázek dlaždice z události / dlaždice (různé verze OpenSeadragonu)
  function obrazDlazdice(e, tile) {
    let im = (e && (e.image || e.data)) || null;
    if (!im && tile) {
      try { im = tile.getImage ? tile.getImage() : null; } catch (x) { /* nic */ }
      if (!im && tile.cacheImageRecord && tile.cacheImageRecord.getImage) im = tile.cacheImageRecord.getImage();
      if (!im && tile.context2D) im = tile.context2D.canvas;
    }
    if (im && im.canvas && !im.width) im = im.canvas;   // CanvasRenderingContext2D
    return im && (im.naturalWidth || im.width) ? im : null;
  }

  function zpracujDlazdici(tile, im) {
    const ti = polozka();
    if (!ti || !tile || !im) return;
    const k = `${tile.level}/${tile.x}/${tile.y}`;
    if (odeslane.has(k)) return;
    const s = ti.source;
    const skala = s.getLevelScale(tile.level);   // 1 = plné rozlišení
    const tw = s.getTileWidth ? s.getTileWidth(tile.level) : s.tileSize;
    const th = s.getTileHeight ? s.getTileHeight(tile.level) : s.tileSize;
    const ov = s.tileOverlap || 0;
    const w = im.naturalWidth || im.width, h = im.naturalHeight || im.height;
    // Poloha v plném rozlišení (DZI: dlaždice nese přesah na stranách, které nejsou u okraje)
    const rect = [(tile.x * tw - (tile.x > 0 ? ov : 0)) / skala, (tile.y * th - (tile.y > 0 ? ov : 0)) / skala, w / skala, h / skala];
    try {
      const c = document.createElement('canvas');
      c.width = w; c.height = h;
      c.getContext('2d').drawImage(im, 0, 0);
      c.toBlob(b => {
        if (!b) return;
        odeslane.add(k);
        posli('dlazdice', { info: info(), level: tile.level, x: tile.x, y: tile.y, skala, rect, blob: b });
      }, 'image/jpeg', 0.95);
    } catch (x) { /* obrázek z cizího serveru – nejde přečíst */ }
  }

  // Dlaždice, které prohlížeč načetl dřív, než se háček připojil (vnitřní mezipaměť, podle verze)
  function sklidit() {
    const ti = polozka();
    if (!ti) return;
    const tc = ti._tileCache || (viewer.tileCache);
    const seznam = (tc && (tc._tilesLoaded || [])) || [];
    for (const t of seznam) {
      const tile = t.tile || t;
      if (tile && tile.loaded !== false) zpracujDlazdici(tile, obrazDlazdice(null, tile));
    }
  }

  function stav() {
    const ti = polozka();
    if (!ti) return;
    const i = info();
    try {
      const zoom = ti.viewportToImageZoom(viewer.viewport.getZoom(true));
      const r = ti.viewportToImageRectangle(viewer.viewport.getBounds(true));
      const vel = viewer.viewport.getContainerSize();
      posli('stav', { info: i, procent: Math.round(zoom * 100), hustota: window.devicePixelRatio || 1,
                      okno: [vel.x, vel.y], stupne: true, minPixelRatio: viewer.minPixelRatio || 0.5,
                      pohled: [r.x / i.sirka, r.y / i.vyska, (r.x + r.width) / i.sirka, (r.y + r.height) / i.vyska] });
    } catch (x) { /* ještě není připravený */ }
  }

  let casStavu = 0;
  function pripoj(v) {
    if (viewer || !v) return;
    viewer = v;
    v.addHandler('tile-loaded', e => zpracujDlazdici(e.tile, obrazDlazdice(e, e.tile)));
    v.addHandler('tile-load-failed', e => posli('chyba', { zprava: String((e && e.message) || 'dlaždice se nenačetla').slice(0, 120) }));
    v.addHandler('open-failed', e => posli('chyba', { zprava: 'snímek se neotevřel: ' + String((e && e.message) || '').slice(0, 100) }));
    v.addHandler('open', () => { odeslane.clear(); posli('otevreno', {}); setTimeout(() => { stav(); sklidit(); }, 500); });
    v.addHandler('animation-finish', stav);
    v.addHandler('update-viewport', () => { const t = Date.now(); if (t - casStavu > 300) { casStavu = t; stav(); } });
    setTimeout(() => { stav(); sklidit(); }, 500);
    posli('pripojeno', {});
  }

  // Najít prohlížeč: OpenSeadragon neeviduje instance, ale každý prohlížeč neustále volá raiseEvent –
  // první volání nám ho prozradí (funguje i pro prohlížeč schovaný v uzávěru skriptu stránky).
  function oprav(OSD) {
    if (!OSD || !OSD.Viewer || OSD.Viewer.prototype.__snimkovac) return;
    const P = OSD.Viewer.prototype;
    const puvodni = P.raiseEvent;
    P.raiseEvent = function () {
      if (!viewer) pripoj(this);
      return puvodni.apply(this, arguments);
    };
    P.__snimkovac = true;
  }

  if (window.OpenSeadragon) {
    oprav(window.OpenSeadragon);
  } else {
    let hodnota;
    try {
      Object.defineProperty(window, 'OpenSeadragon', {
        configurable: true, enumerable: true,
        get() { return hodnota; },
        set(v) { hodnota = v; queueMicrotask(() => oprav(v)); }
      });
    } catch (x) { /* nejde – zkusíme později */ }
    window.addEventListener('load', () => oprav(window.OpenSeadragon));
  }

  // Pokyny z osd.js (jen na kliknutí uživatele v popupu)
  window.addEventListener('message', e => {
    if (e.source !== window || !e.data || e.data[TAG + '-pokyn'] === undefined) return;
    const p = e.data[TAG + '-pokyn'];
    if (p === 'stav' && !uiPripojeno) { uiPripojeno = true; cekajici.splice(0).forEach(c => posli('nacteno', c)); }
    const ti = polozka();
    if (!ti) return;
    if (p === 'stav') { odeslane.clear(); stav(); sklidit(); }   // osd.js se připojil – poslat i dřívější dlaždice
    if (p === 'prejdi' && Array.isArray(e.data.vyrez)) {
      const i = info();
      const [x0, y0, x1, y1] = e.data.vyrez;
      const OSD = window.OpenSeadragon;
      viewer.viewport.fitBounds(ti.imageToViewportRectangle(new OSD.Rect(x0 * i.sirka, y0 * i.vyska, (x1 - x0) * i.sirka, (y1 - y0) * i.vyska)));
    }
  });
})();
