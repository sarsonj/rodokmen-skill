// Snímkovač – analýza otevřené stránky (spouští se jen tlačítkem v popupu, jednou).
// Funkce se vkládá do stránky (chrome.scripting, world MAIN) a vrací popis: obrázky, plátna, typ prohlížeče snímků,
// vzory adres dlaždic (z toho, co si stránka už SAMA stáhla – Performance API, žádný nový dotaz), čísla snímků
// a robots.txt. Jediný dotaz na server je načtení /robots.txt (jednou, po kliknutí).
// Z adres se odstraňují hodnoty parametrů (mohou v nich být tokeny); cookies se nečtou.
async function snimkovacAnalyza() {
  const bezHodnot = u => {
    try {
      const x = new URL(u, location.href);
      const klice = [...x.searchParams.keys()];
      // dlouhé náhodné úseky cesty bývají přístupové tokeny (MZA: /iipsrv.fcgi/<číslo>/<token>) – zakrýt
      const cesta = x.pathname.replace(/;jsessionid=[^/]*/i, '').split('/')
        .map(s => (s.length >= 16 && /[a-z]/i.test(s) && /\d/.test(s) && !/\./.test(s)) ? '‹token›' : s).join('/');
      return x.origin + cesta +(klice.length ? '?' + klice.map(k => k + '=…').join('&') : '');
    } catch (e) { return String(u).slice(0, 200); }
  };
  const vzor = u => bezHodnot(u).replace(/\d+/g, 'N');

  // --- obrázky a plátna ---
  const obrazky = [...document.images].map(im => {
    const r = im.getBoundingClientRect();
    return { src: bezHodnot(im.currentSrc || im.src), id: im.id || '', trida: String(im.className || '').slice(0, 80),
             prirozene: [im.naturalWidth, im.naturalHeight], zobrazene: [Math.round(r.width), Math.round(r.height)],
             cizi_server: (() => { try { return new URL(im.currentSrc || im.src).origin !== location.origin; } catch (e) { return null; } })() };
  }).filter(o => o.prirozene[0] * o.prirozene[1] > 40000)
    .sort((a, b) => b.prirozene[0] * b.prirozene[1] - a.prirozene[0] * a.prirozene[1]).slice(0, 20);
  const platna = [...document.querySelectorAll('canvas')].map(c => {
    const r = c.getBoundingClientRect();
    let citelne = null;
    try {
      const g = c.width && c.height ? c.getContext('2d') : null;
      if (g) { g.getImageData(0, 0, 1, 1); citelne = true; } else citelne = 'jiny-kontext';
    } catch (x) { citelne = x.name === 'SecurityError' ? false : 'chyba: ' + x.name; }
    return { id: c.id || '', trida: String(c.className || '').slice(0, 80), velikost: [c.width, c.height],
             zobrazene: [Math.round(r.width), Math.round(r.height)], citelne };
  }).slice(0, 10);
  const pozadi = [];
  for (const e of [...document.querySelectorAll('div, span, section')].slice(0, 3000)) {
    const b = getComputedStyle(e).backgroundImage;
    if (b && b.startsWith('url(')) pozadi.push(vzor(b.slice(4, -1).replace(/["']/g, '')));
    if (pozadi.length >= 300) break;
  }

  // --- prohlížeč snímků ---
  const w = window;
  const skripty = [...document.scripts].map(s => s.src).filter(Boolean).map(bezHodnot);
  const prohlizec = {
    OpenSeadragon: !!w.OpenSeadragon, Leaflet: !!(w.L && w.L.map), OpenLayers: !!w.ol,
    Zoomify: !!(w.Z || w.Zoomify) || skripty.some(s => /zoomify/i.test(s)) || !!document.querySelector('[class*="zoomify" i]')
      || performance.getEntriesByType('resource').some(e => /TileGroup\d+\/\d+-\d+-\d+\./i.test(e.name)),
    IIIF: skripty.some(s => /iiif|mirador|universalviewer/i.test(s)) || performance.getEntriesByType('resource').some(e => /\/info\.json(\?|$)/.test(e.name)),
    DeepZoom: performance.getEntriesByType('resource').some(e => /\.dzi(\?|$)|_files\/\d+\//.test(e.name))
  };

  let zoomify = null;
  try {
    if (w.Z && (w.Z.imageW || w.Z.Viewport)) {
      const Z = w.Z;
      zoomify = { imageW: Z.imageW, imageH: Z.imageH, tileW: Z.tileW, tileH: Z.tileH, tierCount: Z.tierCount,
                  imagePath: Z.imagePath ? bezHodnot(String(Z.imagePath)) : null,
                  zoom: Z.Viewport && Z.Viewport.getZoom ? Z.Viewport.getZoom() : null,
                  // které metody a údaje prohlížeč má (různé verze Zoomify se liší) – jen názvy, žádné hodnoty
                  metody_viewport: Z.Viewport ? Object.keys(Z.Viewport).filter(k => typeof Z.Viewport[k] === 'function').slice(0, 300) : [],
                  udaje_Z: Object.keys(Z).filter(k => /^(viewer|image|tile|Viewer|Viewport)/.test(k)).slice(0, 80),
                  stred: (() => { try { const v = Z.Viewport; return v.calculateCurrentCenterCoordinates ? 'calculateCurrentCenterCoordinates' : (v.getX ? 'getX/getY' : 'nevím'); } catch (e) { return String(e).slice(0, 60); } })() };
    }
  } catch (x) { zoomify = { chyba: String(x).slice(0, 100) }; }
  let hlavni = true;
  try { hlavni = window.top === window; } catch (x) { hlavni = false; }

  // --- co si stránka už sama stáhla (vzory adres, hlavně dlaždice) ---
  const zdroje = {};
  for (const e of performance.getEntriesByType('resource')) {
    if (!/\.(jpe?g|png|webp|gif|tiff?|jp2)(\?|$)|tile|image|img|scan|zoom/i.test(e.name)) continue;
    const k = vzor(e.name);
    const z = zdroje[k] || (zdroje[k] = { vzor: k, pocet: 0, priklad: bezHodnot(e.name), bajtu: 0, typ: e.initiatorType,
                                          cizi_server: (() => { try { return new URL(e.name).origin !== location.origin; } catch (x) { return null; } })() });
    z.pocet++;
    z.bajtu += e.transferSize || 0;
  }
  const stazeno = Object.values(zdroje).sort((a, b) => b.pocet - a.pocet).slice(0, 25);

  // --- čísla snímků a název knihy ---
  const vybery = [...document.querySelectorAll('select')].map(s => ({
    id: s.id || '', jmeno: s.name || '', voleb: s.options.length,
    ciselne: [...s.options].every(o => /^\d+$/.test(o.text.trim())),
    vybrano: s.options[s.selectedIndex] ? s.options[s.selectedIndex].text.trim().slice(0, 40) : ''
  })).slice(0, 10);
  const pole = [...document.querySelectorAll('input')].filter(i => /^\d+$/.test(i.value || ''))
    .map(i => ({ id: i.id || '', jmeno: i.name || '', typ: i.type, hodnota: i.value })).slice(0, 10);
  const nadpisy = [...document.querySelectorAll('h1, h2, h3, a, [class*="title" i], [class*="breadcrumb" i]')]
    .filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.top >= 0 && r.top < 150; })
    .map(e => ({ tag: e.tagName.toLowerCase(), text: (e.innerText || '').trim().slice(0, 80) }))
    .filter(o => o.text).slice(0, 25);
  const podminky = [...document.querySelectorAll('a')]
    .filter(a => /podmínk|pravidl|řád|terms|conditions|licenc|ochran|cookies|gdpr|užití/i.test(a.innerText || ''))
    .map(a => ({ text: (a.innerText || '').trim().slice(0, 80), href: bezHodnot(a.href) })).slice(0, 15);

  // --- robots.txt (jediný dotaz na server) ---
  const robots = { adresa: location.origin + '/robots.txt' };
  if (!hlavni) robots.preskoceno = 'vložený rám – robots.txt jen v hlavní stránce';
  else try {
    const r = await fetch('/robots.txt', { credentials: 'omit', cache: 'force-cache' });
    robots.http = r.status;
    if (r.ok) {
      const text = (await r.text()).slice(0, 30000);
      robots.text = text;
      // rozdělení na skupiny: řádky User-agent, pak pravidla
      const skupiny = [];
      let akt = null, posledniUA = false;
      for (const radek of text.split(/\r?\n/)) {
        const m = radek.replace(/#.*/, '').trim().match(/^([A-Za-z-]+)\s*:\s*(.*)$/);
        if (!m) continue;
        const k = m[1].toLowerCase(), v = m[2].trim();
        if (k === 'user-agent') {
          if (!posledniUA) skupiny.push(akt = { agenti: [], pravidla: [], zpozdeni: null });
          akt.agenti.push(v.toLowerCase());
          posledniUA = true;
          continue;
        }
        posledniUA = false;
        if (!akt) continue;
        if (k === 'allow' || k === 'disallow') akt.pravidla.push({ typ: k, cesta: v });
        if (k === 'crawl-delay') akt.zpozdeni = v;
      }
      // Platí pro cestu? (nejdelší shoda vyhrává, Allow při shodě délky; * a $ podle RFC 9309)
      const plati = (pravidla, cesta) => {
        let best = null;
        for (const p of pravidla) {
          if (!p.cesta) continue;
          const re = new RegExp('^' + p.cesta.replace(/[.+?^{}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*').replace(/\\\$$|\$$/, '$'));
          if (re.test(cesta) && (!best || p.cesta.length > best.cesta.length || (p.cesta.length === best.cesta.length && p.typ === 'allow'))) best = p;
        }
        return best ? best.typ === 'disallow' : false;
      };
      const cesta = location.pathname + location.search;
      const vsichni = skupiny.filter(s => s.agenti.includes('*'));
      robots.pro_vsechny = {
        tahle_stranka_zakazana: plati(vsichni.flatMap(s => s.pravidla), cesta),
        zakazano_vse: vsichni.some(s => s.pravidla.some(p => p.typ === 'disallow' && p.cesta === '/')),
        crawl_delay: vsichni.map(s => s.zpozdeni).find(Boolean) || null
      };
      // Zmínění konkrétní roboti, hlavně AI asistenti (Comet = Perplexity)
      const AI = /perplexity|claude|anthropic|gptbot|chatgpt|openai|google-extended|ccbot|bytespider|(^|[^a-z])ai([^a-z]|$)/i;
      robots.jmenovani_roboti = skupiny.filter(s => !s.agenti.includes('*')).map(s => ({
        agenti: s.agenti, ai: s.agenti.some(a => AI.test(a)),
        tahle_stranka_zakazana: plati(s.pravidla, cesta),
        zakazano_vse: s.pravidla.some(p => p.typ === 'disallow' && p.cesta === '/')
      })).slice(0, 40);
    }
  } catch (e) {
    robots.chyba = String(e).slice(0, 200);
  }

  return {
    snimkovac_analyza: 2, cas: new Date().toISOString(), adresa: bezHodnot(location.href), titulek: document.title, hlavni_ram: hlavni, zoomify,
    prohlizec, obrazky, platna, pozadi_vzory: [...new Set(pozadi)].slice(0, 20), stazeno, vybery, pole, nadpisy,
    podminky, skripty: skripty.slice(0, 40), robots
  };
}

// Krátké shrnutí robots.txt pro popup
function snimkovacShrnRobots(r) {
  if (!r || r.chyba) return 'robots.txt: nejde načíst';
  if (r.http !== 200) return `robots.txt: není (HTTP ${r.http}) – žádná pravidla pro roboty`;
  const v = r.pro_vsechny || {};
  let t = 'robots.txt: pro všechny roboty ' + (v.zakazano_vse ? 'ZAKAZUJE celý web' : v.tahle_stranka_zakazana ? 'ZAKAZUJE tuto stránku' : 'tuto stránku nezakazuje');
  if (v.crawl_delay) t += `, žádá ${v.crawl_delay} s mezi dotazy`;
  const ai = (r.jmenovani_roboti || []).filter(s => s.ai && (s.zakazano_vse || s.tahle_stranka_zakazana));
  if (ai.length) t += '; zakazuje AI roboty: ' + ai.flatMap(s => s.agenti).slice(0, 5).join(', ');
  return t + '.';
}
