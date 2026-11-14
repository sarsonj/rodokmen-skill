// Snímkovač – háček pro Matricula Online (data.matricula-online.eu), běží ve světě stránky od document_start.
// Prohlížeč Matriculy (OpenLayers) si celý snímek načte jako obrázek z img.data.matricula-online.eu. Háček si jen
// všimne, že se ten obrázek načetl, a jeho kopii (z paměti prohlížeče, bez dalšího stahování) předá rozšíření.
// Aby nebrzdil prohlížeč: nic nedělá, dokud není Snímkovač zapnutý; kopii dělá až chvíli po načtení (když už
// uživatel listuje dál, snímek přeskočí) a obrázek dekóduje mimo hlavní vlákno (createImageBitmap).
(() => {
  if (location.hostname !== 'data.matricula-online.eu' || window.__snimkovacMatricula) return;
  window.__snimkovacMatricula = true;
  const TAG = 'snimkovac-matricula';
  const VZOR = /^https:\/\/img\.data\.matricula-online\.eu\/image\/([^/?]+)\//;
  const PRODLEVA_MS = 1500;

  let zapnuto = false;          // řekne content.js podle přepínače ZAP/VYP
  let cekajici = null;          // {im, url} – poslední načtený snímek
  let casovac = null, posledni = '';

  const popis = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, 'src');
  Object.defineProperty(HTMLImageElement.prototype, 'src', {
    configurable: true, enumerable: popis.enumerable,
    get() { return popis.get.call(this); },
    set(v) {
      try {
        if (typeof v === 'string' && VZOR.test(v)) {
          const im = this;
          im.addEventListener('load', () => { cekajici = { im, url: v }; naplanuj(); }, { once: true });
        }
      } catch (e) { /* nic */ }
      popis.set.call(this, v);
    }
  });

  window.addEventListener('message', e => {
    if (e.source !== window || !e.data || e.data[TAG + '-pokyn'] !== 'zap') return;
    zapnuto = !!e.data.hodnota;
    if (zapnuto) naplanuj();
  });

  function naplanuj() {
    clearTimeout(casovac);
    if (zapnuto && cekajici) casovac = setTimeout(predej, PRODLEVA_MS);
  }

  function puvodniSoubor(url) {
    let s = '';
    try { s = atob(url.match(VZOR)[1].replace(/-/g, '+').replace(/_/g, '/')); } catch (e) { return ''; }
    try { return decodeURIComponent(s); } catch (e) { return s; }
  }

  function poradi(url) {   // pořadí snímku podle seznamu souborů prohlížeče (nezávisle na adrese stránky)
    try {
      const o = window.dv1 && window.dv1.options;
      const cesta = url.replace(/^https:\/\/img\.data\.matricula-online\.eu/, '').split('?')[0];
      const i = o.files.indexOf(cesta);
      return i < 0 ? null : { snimek: i + 1, stitek: o.labels[i] || '', pocet: o.files.length };
    } catch (e) { return null; }
  }

  async function predej() {
    if (!zapnuto || !cekajici) return;
    const { im, url } = cekajici;
    const cesta = url.split('?')[0];
    if (cesta === posledni) return;   // prohlížeč vkládá tentýž snímek dvakrát
    posledni = cesta;
    try {
      const bmp = await createImageBitmap(im);   // dekódování mimo hlavní vlákno
      const c = new OffscreenCanvas(bmp.width, bmp.height);
      c.getContext('2d').drawImage(bmp, 0, 0);
      bmp.close();
      const blob = await c.convertToBlob({ type: 'image/jpeg', quality: 0.95 });
      window.postMessage({ [TAG]: 'obraz', blob, sirka: c.width, vyska: c.height,
                           puvodni: puvodniSoubor(url), poradi: poradi(url) }, location.origin);
    } catch (e) {
      posledni = '';
      window.postMessage({ [TAG]: 'chyba', zprava: 'obrázek nejde přečíst: ' + e }, location.origin);
    }
  }
})();
