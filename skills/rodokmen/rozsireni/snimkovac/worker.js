// Snímkovač – service worker: dostane snímek od content scriptu a uloží ho do Stažené/rodokmen-snimky/.
// Neodesílá nic na internet.
importScripts('weby.js', 'dlazdice.js');
const SLOZKA = 'rodokmen-snimky';

function dnes() {
  return new Date().toISOString().slice(0, 10);
}

function bezpecne(s) {
  return (s || '').replace(/[\\/:*?"<>|\u0000-\u001f]/g, ' ').replace(/\s+/g, ' ').trim().replace(/[. ]+$/, '').slice(0, 60);
}

async function nastav() {
  const d = await chrome.storage.local.get(['zap', 'dnes', 'videno']);
  return { zap: d.zap !== false, dnes: d.dnes || { datum: dnes(), pocet: 0 }, videno: d.videno || {} };
}

async function odznak(zap, pocet) {
  await chrome.action.setBadgeText({ text: zap ? String(pocet || '') : 'VYP' });
  await chrome.action.setBadgeBackgroundColor({ color: zap ? '#2e7d32' : '#888888' });
}

// Ukládání bez bubliny stahování prohlížeče (oprávnění downloads.ui): na dobu ukládání se bublina vypne a pak
// zase zapne. Soubory se ukládají stejně a jsou vidět v seznamu stahování (Ctrl+J); oznámení ukáže Snímkovač sám.
let bezBubliny = 0, casBubliny = null;
async function bublina(zapnout) {
  if (!chrome.downloads.setUiOptions) return;   // starší prohlížeč – bublina zůstane
  try { await chrome.downloads.setUiOptions({ enabled: zapnout }); } catch (e) { /* nepodporováno */ }
}
function hotovoStahovani(id) {   // počká na dokončení (nebo nejvýš 15 s)
  return new Promise(ok => {
    const konec = () => { chrome.downloads.onChanged.removeListener(posluchac); clearTimeout(t); ok(); };
    const posluchac = d => { if (d.id === id && d.state && d.state.current !== 'in_progress') konec(); };
    const t = setTimeout(konec, 15000);
    chrome.downloads.onChanged.addListener(posluchac);
  });
}
bublina(true);   // pojistka: kdyby worker skončil uprostřed ukládání, bublina se nesmí ztratit natrvalo
async function stahni(url, filename) {
  bezBubliny++;
  clearTimeout(casBubliny);
  await bublina(false);
  try {
    const id = await new Promise((ok, chyba) => {
      chrome.downloads.download({ url, filename, conflictAction: 'overwrite', saveAs: false }, id => {
        if (chrome.runtime.lastError || id === undefined) chyba(new Error(chrome.runtime.lastError?.message || 'chyba stahování'));
        else ok(id);
      });
    });
    await hotovoStahovani(id);
    return id;
  } finally {
    bezBubliny--;
    if (!bezBubliny) casBubliny = setTimeout(() => { if (!bezBubliny) bublina(true); }, 1500);
  }
}

// Je odesílatel eBadatelna, nebo web, který uživatel sám povolil?
async function odesilatelPovolen(odesilatel) {
  let host;
  try { host = new URL(odesilatel.url).hostname; } catch (e) { return false; }
  if (host === 'ebadatelna.soapraha.cz') return true;
  const d = await chrome.storage.local.get('weby');
  return !!(d.weby && d.weby[host]);
}

async function registrujWeb(host) {
  const id = 'web_' + host;
  try { await chrome.scripting.unregisterContentScripts({ ids: [id, id + '_osd'] }); } catch (e) { /* nebylo */ }
  await chrome.scripting.registerContentScripts([
    { id, matches: [`https://${host}/*`], js: ['content.js', 'osd.js'], runAt: 'document_idle', allFrames: true, persistAcrossSessions: true },
    // háček pro dlaždicové prohlížeče musí být ve světě stránky a dřív než OpenSeadragon
    // háčky prohlížečů snímků (OpenSeadragon dřív než se načte, Zoomify si na prohlížeč počká) – i ve vložených rámech
    { id: id + '_osd', matches: [`https://${host}/*`], js: ['osd_hook.js', 'zoomify_hook.js', 'matricula_hook.js'], runAt: 'document_start', world: 'MAIN',
      allFrames: true, persistAcrossSessions: true }
  ]);
}

// Chrome při obnovení (aktualizaci) rozšíření dynamicky registrované skripty smaže – povolené weby zaregistrovat znovu
async function obnovRegistrace() {
  const weby = (await chrome.storage.local.get('weby')).weby || {};
  const hotovo = [];
  for (const host of Object.keys(weby)) {
    if (!(await chrome.permissions.contains({ origins: [`https://${host}/*`] }))) continue;   // oprávnění odebráno
    try { await registrujWeb(host); hotovo.push(host); } catch (e) { console.warn('Snímkovač: registrace', host, e); }
  }
  return hotovo;
}

async function povolWeb(host, potvrzeno, tabId) {
  if (!/^[a-z0-9.-]+$/i.test(host || '')) return { ok: false, chyba: 'neplatný web' };
  // Cokoli mimo ověřeně povolené weby chce výslovné potvrzení uživatele (popup ho vyžádá před voláním)
  if (stavWebu(host) !== 'povoleno' && !potvrzeno) return { ok: false, chyba: 'chybí potvrzení' };
  await registrujWeb(host);
  const d = await chrome.storage.local.get('weby');
  const weby = d.weby || {};
  weby[host] = { od: new Date().toISOString(), potvrzeno: !!potvrzeno, stav: stavWebu(host) };
  await chrome.storage.local.set({ weby });
  if (tabId) {
    await chrome.scripting.executeScript({ target: { tabId, allFrames: true }, files: ['osd_hook.js', 'zoomify_hook.js', 'matricula_hook.js'], world: 'MAIN' });
    await chrome.scripting.executeScript({ target: { tabId, allFrames: true }, files: ['content.js', 'osd.js'] });
  }
  return { ok: true };
}

async function zrusWeb(host) {
  try { await chrome.scripting.unregisterContentScripts({ ids: ['web_' + host, 'web_' + host + '_osd'] }); } catch (e) { /* nebylo */ }
  const d = await chrome.storage.local.get('weby');
  const weby = d.weby || {};
  delete weby[host];
  await chrome.storage.local.set({ weby });
  try { await chrome.permissions.remove({ origins: [`https://${host}/*`] }); } catch (e) { /* nic */ }
  return { ok: true };
}

// Počítadlo pro denní limity archivů: {datum: {web: {snimku, dlazdice, zeServeru, zMezipameti, bajtu, chyby, …}}}
let frontaPocitadla = Promise.resolve();
function zapocitej(host, data) {
  frontaPocitadla = frontaPocitadla.then(async () => {
    const den = new Date().toLocaleDateString('sv-SE');   // RRRR-MM-DD místního času
    const d = (await chrome.storage.local.get('pocitadlo')).pocitadlo || {};
    d[den] = d[den] || {};
    const z = d[den][host] = d[den][host] ||
      { snimku: 0, otisky: [], dlazdice: 0, zeServeru: 0, zMezipameti: 0, nevime: 0, bajtu: 0, chyby: 0, zpravy: [], prvni: null, posledni: null, prvniChyba: null };
    if (data) {
      const ted = new Date().toLocaleTimeString('cs-CZ');
      for (const k of data.snimky || []) {
        const o = String([...k].reduce((h, c) => (Math.imul(h, 31) + c.charCodeAt(0)) | 0, 7));
        if (!z.otisky.includes(o)) { z.otisky.push(o); z.snimku++; }
      }
      for (const k of ['dlazdice', 'zeServeru', 'zMezipameti', 'nevime', 'bajtu', 'chyby']) z[k] += data[k] || 0;
      if (data.dlazdice || data.chyby) { z.prvni = z.prvni || ted; z.posledni = ted; }
      if (data.chyby && !z.prvniChyba) z.prvniChyba = { cas: ted, poSnimcich: z.snimku, poDlazdicichZeServeru: z.zeServeru, zprava: (data.zpravy || [])[0] || '' };
      z.zpravy = [...z.zpravy, ...(data.zpravy || [])].slice(-20);
      for (const k of Object.keys(d).sort().slice(0, -60)) delete d[k];   // nejvýš 60 dní
      await chrome.storage.local.set({ pocitadlo: d });
    }
    const { otisky, ...bezOtisku } = z;
    return { ...bezOtisku, den };
  });
  return frontaPocitadla;
}

// Fronta, aby dvě zprávy naráz nepřepsaly počítadlo
let fronta = Promise.resolve();

async function uloz(zprava) {
  const s = await nastav();
  if (!s.zap) return { ulozeno: false, duvod: 'vypnuto' };
  const m = zprava.meta;
  const klic = `${m.druh}_${m.matrikaId}_${m.snimek}`;
  if (s.videno[klic] && !zprava.znovu) return { ulozeno: false, duvod: 'uz-ulozeno', kdy: s.videno[klic] };
  const kniha = bezpecne(m.kniha) || (m.druh === 'web' ? bezpecne(m.matrikaId) : `kniha ${m.matrikaId}`);
  const zaklad = `${SLOZKA}/${kniha}/${m.matrikaId}_${m.snimek}`;
  await stahni(zprava.dataUrl, `${zaklad}.jpg`);
  await stahni('data:application/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(m, null, 2)), `${zaklad}.json`);
  s.videno[klic] = m.cas;
  if (s.dnes.datum !== dnes()) s.dnes = { datum: dnes(), pocet: 0 };
  s.dnes.pocet += 1;
  await chrome.storage.local.set({ videno: s.videno, dnes: s.dnes });
  await odznak(true, s.dnes.pocet);
  return { ulozeno: true };
}

chrome.runtime.onMessage.addListener((zprava, odesilatel, odpoved) => {
  if (zprava && zprava.typ === 'uloz') {
    fronta = fronta.then(async () => {
      if (!(await odesilatelPovolen(odesilatel))) return { ulozeno: false, duvod: 'web-neni-povolen' };
      return uloz(zprava);
    }).then(odpoved, e => odpoved({ ulozeno: false, chyba: String(e) }));
    return true;
  }
  // Dlaždicové prohlížeče: ukládání dlaždic (jen když je ukládání zapnuté), seznam, poskládání
  if (zprava && zprava.typ === 'osd-dlazdice') {
    (async () => {
      if (!(await odesilatelPovolen(odesilatel))) return { nova: false };
      if (!(await nastav()).zap) return { nova: false };
      return ulozDlazdici(zprava);
    })().then(odpoved, e => odpoved({ nova: false, chyba: String(e) }));
    return true;
  }
  if (zprava && zprava.typ === 'pocitadlo') {
    (async () => {
      if (!(await odesilatelPovolen(odesilatel))) return null;
      return zapocitej(zprava.host, zprava.data);
    })().then(odpoved, () => odpoved(null));
    return true;
  }
  if (zprava && zprava.typ === 'pocitadlo-vse' && !odesilatel.tab) {
    chrome.storage.local.get('pocitadlo').then(d => odpoved(d.pocitadlo || {}));
    return true;
  }
  // Prohlížeč s nečitelným plátnem (AHMP): vyfotit viditelnou část záložky a vyříznout z ní stránku snímku.
  // Jen pro aktivní záložku povoleného webu, jen při zapnutém ukládání; nic se nestahuje.
  if (zprava && zprava.typ === 'zachyt-obrazovku') {
    (async () => {
      if (!(await odesilatelPovolen(odesilatel))) return { chyba: 'Tento web není povolený' };
      if (!(await nastav()).zap) return { chyba: 'Ukládání je vypnuté – zapni ho v okénku Snímkovače' };
      const tab = odesilatel.tab;
      if (!tab || !tab.active) return { chyba: 'Záložka není vpředu, nefotím' };
      let url;
      try { url = await chrome.tabs.captureVisibleTab(tab.windowId, { format: 'png' }); }
      catch (e) { return { chyba: 'Focení není povoleno – klikni na ikonu Snímkovače (Alt+S)', povoleni: true }; }
      const bmp = await createImageBitmap(await (await fetch(url)).blob());
      const k = bmp.width / zprava.okno[0];   // body snímku obrazovky na bod CSS (škálování Windows)
      const [x, y, w, h] = zprava.klient;
      // výstup jen v hustotě, kterou obraz prohlížeče skutečně má (víc bodů by bylo jen roztažené)
      const d = Math.min(k, zprava.hustota > 0 ? zprava.hustota : k);
      let ow = Math.round(w * d), oh = Math.round(h * d), skala = ow / zprava.rect[2];
      if (skala > 1) { ow = Math.round(zprava.rect[2]); oh = Math.round(zprava.rect[3]); skala = 1; }   // nad plné rozlišení nezvětšovat
      const c = new OffscreenCanvas(Math.max(1, ow), Math.max(1, oh));
      c.getContext('2d').drawImage(bmp, x * k, y * k, w * k, h * k, 0, 0, c.width, c.height);
      bmp.close();
      const blob = await c.convertToBlob({ type: 'image/jpeg', quality: 0.92 });
      const dataUrl = await new Promise(ok => { const f = new FileReader(); f.onload = () => ok(f.result); f.readAsDataURL(blob); });
      return { dataUrl, skala: Math.round(skala * 1000) / 1000 };
    })().then(odpoved, e => odpoved({ chyba: String(e) }));
    return true;
  }
  if (zprava && zprava.typ === 'osd-smaz-obraz') {
    (async () => {
      if (!(await odesilatelPovolen(odesilatel))) return { ok: false, chyba: 'web není povolen' };
      return { ok: true, pocet: await smazDlazdice(zprava.obraz) };
    })().then(odpoved, e => odpoved({ ok: false, chyba: String(e) }));
    return true;
  }
  if (zprava && zprava.typ === 'osd-seznam') {
    seznamDlazdic(zprava.obraz).then(d => odpoved({ dlazdice: d }), e => odpoved({ dlazdice: [], chyba: String(e) }));
    return true;
  }
  if (zprava && zprava.typ === 'osd-sloz') {
    slozSnimek(zprava, stahni, bezpecne).then(odpoved, e => odpoved({ ok: false, chyba: String(e) }));
    return true;
  }
  // Povolení / zrušení povolení dalšího webu (z popupu; oprávnění prohlížeče už uživatel potvrdil tam)
  if (zprava && zprava.typ === 'povol-web' && !odesilatel.tab) {  // jen z popupu, ne z webu
    povolWeb(zprava.host, zprava.potvrzeno, zprava.tabId).then(odpoved, e => odpoved({ ok: false, chyba: String(e) }));
    return true;
  }
  if (zprava && zprava.typ === 'zrus-web' && !odesilatel.tab) {
    zrusWeb(zprava.host).then(odpoved, e => odpoved({ ok: false, chyba: String(e) }));
    return true;
  }
  if (zprava && zprava.typ === 'zapomen' && !odesilatel.tab) {   // jen z popupu
    chrome.storage.local.set({ videno: {} }).then(() => odpoved({ ok: true }));
    return true;
  }
  if (zprava && zprava.typ === 'stav') {
    nastav().then(s => odpoved({ zap: s.zap, dnes: s.dnes.datum === dnes() ? s.dnes.pocet : 0 }));
    return true;
  }
  if (zprava && zprava.typ === 'zap') {
    chrome.storage.local.set({ zap: !!zprava.hodnota }).then(async () => {
      const s = await nastav();
      await odznak(s.zap, s.dnes.datum === dnes() ? s.dnes.pocet : 0);
      odpoved({ zap: s.zap });
    });
    return true;
  }
});

chrome.runtime.onInstalled.addListener(async () => {
  await obnovRegistrace();
  const s = await nastav();
  await odznak(s.zap, s.dnes.datum === dnes() ? s.dnes.pocet : 0);
});
chrome.runtime.onStartup.addListener(() => { obnovRegistrace(); });
