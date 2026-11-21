// Snímkovač – háček pro prohlížeč Zoomify (SOA Třeboň, ve vloženém rámu view.php). Běží ve světě stránky (MAIN),
// jen na webech, které uživatel sám povolil. Nic nestahuje: když se pohled ustálí, vezme z plátna prohlížeče to, co je
// právě vykreslené, a s polohou na snímku to pošle osd.js (stejný protokol jako háček OpenSeadragonu: minimapa,
// ukládání, skládání). Adresy dlaždic jsou u Třeboně zašifrované, proto se nebere dlaždice, ale vykreslený pohled.
(() => {
  if (window.__snimkovacZoomify) return;
  window.__snimkovacZoomify = true;
  const TAG = 'snimkovac-osd';
  const posli = (typ, data) => window.postMessage({ [TAG]: typ, ...data }, location.origin);
  let Z = null, posledniPohled = '', casZmeny = 0, zachyceno = new Set(), pripojeno = false;

  function vp() { return Z && Z.Viewport; }

  function info() {
    return Z && Z.imageW ? { sirka: Z.imageW, vyska: Z.imageH, maxLevel: null, dlazdice: Z.tileW || null, presah: 0 } : null;
  }

  // Pohled: zvětšení (1 = plné rozlišení) a střed v bodech snímku; viditelná oblast prohlížeče v bodech rámu
  // Různé verze Zoomify mají různé metody – zkusit několik cest (Třeboň: calculateCurrentCenterCoordinates/getViewW,
  // starší verze: getX/getY a Z.viewerW/H, nouzově velikost prvku prohlížeče)
  // Bez výjimek: metodu volá jen když existuje (Chrome hlásí i zachycené chyby ve skriptu rozšíření)
  const zavolej = (o, jm) => (o && typeof o[jm] === 'function') ? o[jm]() : undefined;
  const cislo = (...hodnoty) => { for (const v of hodnoty) if (typeof v === 'number' && isFinite(v)) return v; return null; };
  function pohled() {
    const v = vp();
    if (!v || typeof v.getZoom !== 'function') return null;
    const c = zavolej(v, 'calculateCurrentCenterCoordinates') || {};
    const z = cislo(v.getZoom());
    const cx = cislo(c.x, zavolej(v, 'getX'), Z.imageX);
    const cy = cislo(c.y, zavolej(v, 'getY'), Z.imageY);
    const prvek = Z.ViewerDisplay || document.getElementById('oversizeDisplay');
    const rp = prvek && prvek.getBoundingClientRect ? prvek.getBoundingClientRect() : {};
    const W = cislo(zavolej(v, 'getViewW'), Z.viewerW, rp.width);
    const H = cislo(zavolej(v, 'getViewH'), Z.viewerH, rp.height);
    if ([z, cx, cy, W, H].some(x => x === null) || !z) return null;
    return { z, cx, cy, W, H };
  }

  // Bod rámu → bod snímku (stejný vzorec jako v reference/portaly.md, SOA Třeboň)
  const naSnimek = (p, x, y) => ({ x: (x - p.W / 2) / p.z + p.cx, y: (y - p.H / 2) / p.z + p.cy });

  function stav() {
    const p = pohled(), i = info();
    if (!p || !i) return;
    const a = naSnimek(p, 0, 0), b = naSnimek(p, p.W, p.H);
    const pl = [...document.querySelectorAll('canvas')].find(c => /^viewportDisplay\d*$/.test(c.id));
    const rp = pl && pl.getBoundingClientRect();
    const hustota = pl && rp && rp.width ? pl.width / rp.width : 1;
    posli('stav', { info: i, procent: Math.round(p.z * 100), hustota, okno: [p.W, p.H], pohled: [a.x / i.sirka, a.y / i.vyska, b.x / i.sirka, b.y / i.vyska] });
  }

  // Vezme viditelnou část plátna prohlížeče a pošle ji jako „dlaždici“ s polohou na snímku
  function zachyt() {
    const p = pohled(), i = info();
    if (!p || !i) return;
    const platno = [...document.querySelectorAll('canvas')].find(c => /^viewportDisplay\d*$/.test(c.id));
    if (!platno || !platno.width) return ladeni('nenašel jsem plátno prohlížeče');
    // plátno z cizího serveru (AHMP) nejde přečíst → rovnou snímek viditelné části záložky
    try { platno.getContext('2d').getImageData(0, 0, 1, 1); }
    catch (x) { return zachytObrazovku(p, i); }
    const r = platno.getBoundingClientRect();
    if (!r.width || !r.height) return;
    const sx = platno.width / r.width, sy = platno.height / r.height;
    // průnik plátna s viditelnou oblastí prohlížeče (0..W, 0..H v bodech rámu)
    const x0 = Math.max(0, r.left), y0 = Math.max(0, r.top), x1 = Math.min(p.W, r.right), y1 = Math.min(p.H, r.bottom);
    if (x1 - x0 < 20 || y1 - y0 < 20) return;
    const a = naSnimek(p, x0, y0), b = naSnimek(p, x1, y1);
    // jen část, která leží na snímku
    const ix0 = Math.max(0, a.x), iy0 = Math.max(0, a.y), ix1 = Math.min(i.sirka, b.x), iy1 = Math.min(i.vyska, b.y);
    if (ix1 - ix0 < 10 || iy1 - iy0 < 10) return;
    const cssX = (ix0 - p.cx) * p.z + p.W / 2, cssY = (iy0 - p.cy) * p.z + p.H / 2;
    const px = Math.round((cssX - r.left) * sx), py = Math.round((cssY - r.top) * sy);
    const pw = Math.round((ix1 - ix0) * p.z * sx), ph = Math.round((iy1 - iy0) * p.z * sy);
    const skala = Math.min(1, p.z * sx);   // bodů plátna na bod snímku (nad 1 jen zvětšené plné rozlišení)
    const klic = `${Math.round(ix0)}/${Math.round(iy0)}/${Math.round(ix1)}/${Math.round(iy1)}/${skala.toFixed(3)}`;
    try {
      const c = document.createElement('canvas');
      c.width = Math.max(1, Math.round(pw * Math.min(1, 1 / (p.z * sx))));   // nad plné rozlišení nezvětšovat
      c.height = Math.max(1, Math.round(ph * Math.min(1, 1 / (p.z * sy))));
      c.getContext('2d').drawImage(platno, px, py, pw, ph, 0, 0, c.width, c.height);
      c.toBlob(blob => {
        if (!blob) return;
        posli('dlazdice', { info: i, level: Math.round(skala * 1000), x: Math.round(ix0), y: Math.round(iy0), skala,
                            rect: [ix0, iy0, ix1 - ix0, iy1 - iy0], blob, prepsat: zachyceno.has(klic) });
        zachyceno.add(klic);
      }, 'image/jpeg', 0.92);
    } catch (x) {   // plátno nejde přečíst (dlaždice z cizího serveru, např. AHMP) → snímek viditelné části záložky
      zachytObrazovku(p, i);
    }
  }

  // Levý horní roh oblasti prohlížeče v bodech okna: prvek o velikosti pohledu, jinak střed plátna (Zoomify ho centruje)
  function puvodPohledu(p) {
    const platna = [...document.querySelectorAll('canvas')].filter(c => /^viewportDisplay\d*$/.test(c.id));
    const kandidati = [Z && Z.ViewerDisplay, document.getElementById('oversizeDisplay'), ...platna.map(c => c.parentElement)];
    for (const e of kandidati) {
      if (!e || !e.getBoundingClientRect) continue;
      const r = e.getBoundingClientRect();
      if (Math.abs(r.width - p.W) < 3 && Math.abs(r.height - p.H) < 3) return { x: r.left, y: r.top };
    }
    if (!platna.length) return null;
    const r = platna[0].getBoundingClientRect();
    return { x: r.left + r.width / 2 - p.W / 2, y: r.top + r.height / 2 - p.H / 2 };
  }

  // Snímek obrazovky jde jen z hlavní stránky (ne z vloženého rámu); udělá ho rozšíření (captureVisibleTab), nic se nestahuje
  const ladeni = duvod => posli('ladeni', { duvod });

  // Ovládání prohlížeče (lišta s tlačítky, náhled stránky) leží přes obraz a na snímku obrazovky by bylo vidět.
  // Označí prvky, které zasahují do fotografované oblasti a neobsahují plátno s obrazem; osd.js je na dobu focení skryje.
  function oznacPrekryvy([x, y, w, h]) {
    const obraz = [...document.querySelectorAll('canvas')].filter(c => /^(viewportDisplay|viewportBackfillDisplay)\d*$/.test(c.id));
    for (const e of document.querySelectorAll('[data-snimkovac-skryt]')) e.removeAttribute('data-snimkovac-skryt');
    for (const e of document.body.querySelectorAll('*')) {
      if (obraz.some(c => e === c || e.contains(c))) continue;          // obraz a jeho obaly zůstávají
      if (e.closest('[data-snimkovac-mapa]')) continue;                 // minimapu skrývá osd.js sám
      const r = e.getBoundingClientRect();
      if (!r.width || !r.height || r.right <= x || r.left >= x + w || r.bottom <= y || r.top >= y + h) continue;
      e.setAttribute('data-snimkovac-skryt', '1');
    }
  }
  function zachytObrazovku(p, i) {
    if (window.top !== window) return ladeni('prohlížeč je ve vloženém rámu – snímek obrazovky neumím');
    const o = puvodPohledu(p);
    if (!o) return ladeni('nenašel jsem polohu prohlížeče na stránce');
    const vx0 = Math.max(o.x, 0), vy0 = Math.max(o.y, 0), vx1 = Math.min(o.x + p.W, innerWidth), vy1 = Math.min(o.y + p.H, innerHeight);
    const a = naSnimek(p, vx0 - o.x, vy0 - o.y), b = naSnimek(p, vx1 - o.x, vy1 - o.y);
    const ix0 = Math.max(0, a.x), iy0 = Math.max(0, a.y), ix1 = Math.min(i.sirka, b.x), iy1 = Math.min(i.vyska, b.y);
    if (ix1 - ix0 < 10 || iy1 - iy0 < 10) return ladeni('ve viditelné části není snímek');
    const klic = `${Math.round(ix0)}/${Math.round(iy0)}/${Math.round(ix1)}/${Math.round(iy1)}/${p.z.toFixed(3)}`;
    const kx = (ix0 - p.cx) * p.z + p.W / 2 + o.x, ky = (iy0 - p.cy) * p.z + p.H / 2 + o.y;
    oznacPrekryvy([kx, ky, (ix1 - ix0) * p.z, (iy1 - iy0) * p.z]);
    // skutečná hustota obrazu: body plátna prohlížeče na bod stránky (Zoomify kreslí v bodech CSS, ne v bodech
    // obrazovky – při škálování Windows 150 % má snímek obrazovky víc bodů, než kolik obraz skutečně obsahuje)
    const pl = [...document.querySelectorAll('canvas')].find(c => /^viewportDisplay\d*$/.test(c.id));
    const rp = pl && pl.getBoundingClientRect();
    const hustota = pl && rp && rp.width ? pl.width / rp.width : 1;
    posli('zachyt-obrazovku', { info: i, rect: [ix0, iy0, ix1 - ix0, iy1 - iy0], hustota,
                                klient: [kx, ky, (ix1 - ix0) * p.z, (iy1 - iy0) * p.z], okno: [innerWidth, innerHeight],
                                prepsat: zachyceno.has(klic) });
    zachyceno.add(klic);
  }

  // Sledování pohledu (čte jen proměnné prohlížeče, nic nenačítá): po ustálení zachytit, po chvíli ještě jednou
  // (dlaždice se mohou dokreslit později)
  let casovac1 = null, casovac2 = null;
  function hlidej() {
    const p = pohled();
    if (!p) return;
    const k = `${p.z.toFixed(4)}|${Math.round(p.cx)}|${Math.round(p.cy)}|${p.W}|${p.H}`;
    if (k !== posledniPohled) {
      posledniPohled = k;
      casZmeny = Date.now();
      stav();
      clearTimeout(casovac1); clearTimeout(casovac2);
      casovac1 = setTimeout(zachyt, 1500);
      casovac2 = setTimeout(zachyt, 5000);
    }
  }

  function pripoj() {
    if (pripojeno || !window.Z || !window.Z.Viewport || !window.Z.imageW) return false;
    Z = window.Z;
    pripojeno = true;
    posli('pripojeno', {});
    setInterval(hlidej, 400);
    hlidej();
    return true;
  }
  // prohlížeč se načítá postupně – zkoušet nejvýš 2 minuty
  let pokusu = 0;
  const t = setInterval(() => { if (pripoj() || ++pokusu > 240) clearInterval(t); }, 500);

  // Pokyny z osd.js (jen na kliknutí uživatele v popupu)
  window.addEventListener('message', e => {
    if (e.source !== window || !e.data || e.data[TAG + '-pokyn'] === undefined || !Z) return;
    const pk = e.data[TAG + '-pokyn'];
    if (pk === 'stav') { stav(); zachyceno = new Set(); setTimeout(zachyt, 300); }
    if (pk === 'prejdi' && Array.isArray(e.data.vyrez)) {
      const p = pohled(), i = info();
      if (!p || !i) return;
      const [x0, y0, x1, y1] = e.data.vyrez.map((v, n) => v * (n % 2 ? i.vyska : i.sirka));
      // pojistka (0.16.4, AHMP 21. 11.): příliš malý nebo nesmyslný výřez by Zoomify přiblížil daleko za plné rozlišení
      // a kolečko ho pak nevrátí – přiblížení nejvýš 2× plné rozlišení
      if (!(x1 - x0 > 20 && y1 - y0 > 20) || ![x0, y0, x1, y1].every(isFinite)) return;
      const zoom = Math.min(2, p.W / (x1 - x0), p.H / (y1 - y0));
      vp().zoomAndPanToView((x0 + x1) / 2, (y0 + y1) / 2, zoom);
    }
  });
})();
