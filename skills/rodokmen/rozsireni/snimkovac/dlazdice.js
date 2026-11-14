// Snímkovač – úložiště dlaždic (IndexedDB rozšíření) a skládání snímku. Načítá ho worker.js (importScripts).
// Dlaždice zůstávají mezi návštěvami, takže se snímek doskládává; nic se neposílá na internet.
const DB_JMENO = 'snimkovac', DB_VERZE = 1;
let _db = null;

function db() {
  if (_db) return Promise.resolve(_db);
  return new Promise((ok, chyba) => {
    const r = indexedDB.open(DB_JMENO, DB_VERZE);
    r.onupgradeneeded = () => {
      const d = r.result;
      const t = d.createObjectStore('dlazdice', { keyPath: ['obraz', 'level', 'x', 'y'] });
      t.createIndex('obraz', 'obraz');
      d.createObjectStore('obrazy', { keyPath: 'obraz' });
    };
    r.onsuccess = () => { _db = r.result; ok(_db); };
    r.onerror = () => chyba(r.error);
  });
}

function tx(store, rezim, fn) {
  return db().then(d => new Promise((ok, chyba) => {
    const t = d.transaction(store, rezim);
    const vysledek = fn(t.objectStore(store));
    t.oncomplete = () => ok(vysledek && 'result' in vysledek ? vysledek.result : vysledek);
    t.onerror = () => chyba(t.error);
  }));
}

async function dataUrlNaBlob(u) {
  return (await fetch(u)).blob();   // data: URL – žádná síť
}

// Uloží dlaždici, pokud ještě není. Vrací {nova: true/false}.
async function ulozDlazdici(z) {
  const klic = [z.obraz, z.level, z.x, z.y];
  const je = await tx('dlazdice', 'readonly', s => s.getKey(klic));
  if (je !== undefined && !z.prepsat) return { nova: false };
  const blob = await dataUrlNaBlob(z.data);
  await tx('dlazdice', 'readwrite', s => s.put({ obraz: z.obraz, level: z.level, x: z.x, y: z.y, skala: z.skala, rect: z.rect, blob }));
  await tx('obrazy', 'readwrite', s => s.put({ obraz: z.obraz, popis: z.popis, posledni: new Date().toISOString() }));
  return { nova: je === undefined };
}

// Smaže všechny uložené dlaždice jednoho snímku (např. záběry s chybou). Vrací počet.
async function smazDlazdice(obraz) {
  const klice = (await tx('dlazdice', 'readonly', s => s.index('obraz').getAllKeys(obraz))) || [];
  await tx('dlazdice', 'readwrite', s => { for (const k of klice) s.delete(k); });
  return klice.length;
}

async function seznamDlazdic(obraz) {
  const vse = await tx('dlazdice', 'readonly', s => s.index('obraz').getAll(obraz));
  return (vse || []).map(d => ({ skala: d.skala, rect: d.rect }));
}

// Poskládá snímek (nebo výřez – zlomky [x0,y0,x1,y1]) v nejlepší uložené škále a stáhne ho s .json.
async function slozSnimek(z, stahni, bezpecne) {
  const vse = (await tx('dlazdice', 'readonly', s => s.index('obraz').getAll(z.obraz))) || [];
  if (!vse.length) return { ok: false, chyba: 'pro tento snímek zatím nejsou uložené žádné dlaždice' };
  const p = z.popis;
  const [vx0, vy0, vx1, vy1] = z.vyrez || [0, 0, 1, 1];
  const ox = vx0 * p.sirka, oy = vy0 * p.vyska, ow = (vx1 - vx0) * p.sirka, oh = (vy1 - vy0) * p.vyska;
  // výstupní škála = nejlepší dlaždice zasahující do výřezu (nejvýš plné rozlišení)
  const zasah = vse.filter(d => d.rect[0] < ox + ow && d.rect[0] + d.rect[2] > ox && d.rect[1] < oy + oh && d.rect[1] + d.rect[3] > oy);
  if (!zasah.length) return { ok: false, chyba: 've výřezu nejsou uložené dlaždice' };
  const skala = Math.min(1, Math.max(...zasah.map(d => d.skala)));
  const W = Math.max(1, Math.round(ow * skala)), H = Math.max(1, Math.round(oh * skala));
  if (W * H > 16e7) return { ok: false, chyba: 'snímek je na poskládání příliš velký' };
  const c = new OffscreenCanvas(W, H);
  const g = c.getContext('2d');
  g.fillStyle = '#ffffff';
  g.fillRect(0, 0, W, H);
  zasah.sort((a, b) => a.skala - b.skala);   // hrubé dlaždice dospodu, jemné navrch
  for (const d of zasah) {
    const bmp = await createImageBitmap(d.blob);
    g.drawImage(bmp, (d.rect[0] - ox) * skala, (d.rect[1] - oy) * skala, d.rect[2] * skala, d.rect[3] * skala);
    bmp.close();
  }
  const jpg = await c.convertToBlob({ type: 'image/jpeg', quality: 0.92 });
  const dataUrl = await new Promise(ok => { const f = new FileReader(); f.onload = () => ok(f.result); f.readAsDataURL(jpg); });
  const slozka = `rodokmen-snimky/${bezpecne(p.kniha) || bezpecne(p.matrikaId)}`;
  const zaklad = `${bezpecne(String(p.matrikaId))}_${bezpecne(String(p.snimek))}`
    + (z.vyrez ? '_vyrez_' + z.vyrez.map(v => v.toFixed(3)).join('_') : '');
  const meta = {
    druh: 'osd', host: p.host, matrikaId: p.matrikaId, snimek: p.snimek, obraz: p.obraz, kniha: p.kniha, adresa: p.adresa,
    cas: new Date().toISOString(), sirka: W, vyska: H, skala: Math.round(skala * 1000) / 1000,
    plne_rozliseni: [p.sirka, p.vyska], vyrez: z.vyrez || null, pokryti: z.pokryti, dlazdic: zasah.length,
    uzivatel_zobrazil: true, poznamka: 'poskládáno z dlaždic, které prohlížeč sám načetl; místa bez dlaždic jsou bílá'
  };
  await stahni(dataUrl, `${slozka}/${zaklad}.jpg`);
  await stahni('data:application/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(meta, null, 2)), `${slozka}/${zaklad}.json`);
  return { ok: true, soubor: `${slozka}/${zaklad}.jpg`, sirka: W, vyska: H };
}
