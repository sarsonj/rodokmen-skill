// Snímkovač – fronta ZIPů z eBadatelny SOA Praha (varianta B: jen upozorní, stahování spouští uživatel).
// Pomůcka pro ruční práci: knihu do fronty přidá uživatel klikem, stahování spouští VŽDY uživatel klikem na
// „Stáhnout knihu jako ZIP“. Rozšíření jen hlídá konec stahování, připraví další kartu, zvýrazní tlačítko a ozve se.
// Nic nestahuje samo, nečte cookies, nevolá odkazy …-downloadZip, při chybě se fronta zastaví a nic neopakuje.
// Fronta je v chrome.storage.session (zavřením prohlížeče zmizí).
const FRONTA_MAX = 5, FRONTA_PAUZA_MS = 10000, EBAD = 'ebadatelna.soapraha.cz';

async function frontaNacti() {
  const d = await chrome.storage.session.get('fronta');
  return d.fronta || { polozky: [], zastaveno: '' };   // polozka: {id, nazev, tabId, stav: ceka|na-rade|stahuje|hotovo|chyba, dlId, mb, cas}
}
async function frontaUloz(f) {
  await chrome.storage.session.set({ fronta: f });
  const tabs = [...new Set(f.polozky.map(p => p.tabId))];
  for (const t of tabs) chrome.tabs.sendMessage(t, { typ: 'fronta-stav', fronta: f }).catch(() => {});
}
const zEbad = u => { try { return new URL(u).hostname === EBAD; } catch (e) { return false; } };

// Pojistka proti zaseknutí (0.17.4): položka „stahuje“, jejíž stahování v Chrome už neběží (zrušené, ztracené,
// nebo se po kliknutí vůbec nezačalo do 60 s), se uvolní – jinak by fronta i další kliky čekaly navždy.
async function frontaOdblokuj(f) {
  let zmena = false;
  for (const p of f.polozky.filter(x => x.stav === 'stahuje')) {
    let bezi = false;
    if (p.dlId != null) {
      try { const [d] = await chrome.downloads.search({ id: p.dlId }); bezi = !!d && d.state === 'in_progress'; if (d && d.state === 'complete') { p.stav = 'hotovo'; zmena = true; continue; } }
      catch (e) { bezi = false; }
    } else {
      // stahování se nespárovalo – zkusit najít běžící ZIP, který začal po kliknutí
      try {
        const kand = (await chrome.downloads.search({ state: 'in_progress', startedAfter: new Date((p.cas || 0) - 5000).toISOString() }))
          .filter(d => jeZip(d) || zEbad(d.url) || zEbad(d.referrer));
        if (kand.length) { p.dlId = kand[0].id; zmena = true; continue; }
      } catch (e) { /* nic */ }
      bezi = Date.now() - (p.cas || 0) < 60000;   // čeká se, až Chrome stahování založí
    }
    if (!bezi) { p.stav = 'chyba'; p.duvod = p.dlId != null ? 'stahování v Chrome neběží' : 'stahování se nezačalo'; zmena = true; }
  }
  if (zmena) await frontaUloz(f);
  return zmena;
}

// Další kniha na řadě: přepnout na její kartu, ať ji uživatel vidí, a dát vědět. Stahování nespouští.
async function frontaDalsi(f) {
  await frontaOdblokuj(f);
  if (f.zastaveno || f.polozky.some(p => p.stav === 'stahuje' || p.stav === 'na-rade')) return;
  const p = f.polozky.find(x => x.stav === 'ceka');
  if (!p) return;
  p.stav = 'na-rade';
  await frontaUloz(f);
  try {
    const tab = await chrome.tabs.update(p.tabId, { active: true });
    await chrome.windows.update(tab.windowId, { focused: true });
  } catch (e) { /* karta mezitím zavřená – odebere ji onRemoved */ }
  chrome.tabs.sendMessage(p.tabId, { typ: 'fronta-na-rade', id: p.id }).catch(() => {});
  try {
    await chrome.notifications.create('fronta-' + p.id, { type: 'basic', iconUrl: 'ikony/ikona128.png', priority: 2,
      title: 'Snímkovač – další kniha je připravená', message: `${p.nazev || p.id}: klikni na „Stáhnout knihu jako ZIP“.` });
  } catch (e) { /* oznámení nejde – zůstane zvuk a zvýraznění */ }
}

chrome.runtime.onMessage.addListener((z, od, odpoved) => {
  if (!z || !String(z.typ || '').startsWith('fronta-')) return;
  if (!od.tab || !zEbad(od.tab.url || od.url)) return;   // jen ze stránek eBadatelny
  (async () => {
    const f = await frontaNacti();
    const tabId = od.tab.id;
    if (await frontaOdblokuj(f)) await frontaDalsi(f);
    if (z.typ === 'fronta-stav?') return f;
    if (z.typ === 'fronta-pridej') {
      if (f.polozky.some(p => p.id === z.id && p.stav !== 'hotovo' && p.stav !== 'chyba')) return f;
      if (f.polozky.filter(p => p.stav === 'ceka' || p.stav === 'na-rade' || p.stav === 'stahuje').length >= FRONTA_MAX)
        return { ...f, chyba: `Ve frontě může být nejvýš ${FRONTA_MAX} knih.` };
      f.polozky = f.polozky.filter(p => p.id !== z.id);
      f.polozky.push({ id: z.id, nazev: z.nazev || '', tabId, stav: 'ceka', cas: Date.now() });
      await frontaUloz(f);
      await frontaDalsi(f);
      return f;
    }
    if (z.typ === 'fronta-odeber') { f.polozky = f.polozky.filter(p => p.id !== z.id); await frontaUloz(f); await frontaDalsi(f); return f; }
    // Vyprázdnit smaže všechno, i „stahuje“ (běžící stahování v Chrome tím nezruší, jen ho fronta přestane hlídat)
    if (z.typ === 'fronta-vycisti') { f.polozky = []; f.zastaveno = ''; await frontaUloz(f); return f; }
    if (z.typ === 'fronta-pokracuj') { f.zastaveno = ''; await frontaUloz(f); await frontaDalsi(f); return f; }
    if (z.typ === 'fronta-klik') {   // uživatel klikl na „Stáhnout knihu jako ZIP“
      const bezi = f.polozky.find(p => p.stav === 'stahuje');
      if (bezi && bezi.id !== z.id) return { ...f, blokovano: bezi.nazev || bezi.id };   // server pustí jen jedno stahování
      let p = f.polozky.find(x => x.id === z.id);
      if (!p) { p = { id: z.id, nazev: z.nazev || '', tabId, stav: 'ceka', cas: Date.now() }; f.polozky.push(p); }
      p.stav = 'stahuje'; p.cas = Date.now(); p.dlId = null; p.mb = 0;
      await frontaUloz(f);
      return f;
    }
  })().then(odpoved, e => odpoved({ chyba: String(e) }));
  return true;
});

// Stahování ZIPu z eBadatelny (vlastní snímky Snímkovače jsou data: adresy a sem nepatří)
// ZIP může jít i z jiné adresy než ebadatelna.soapraha.cz (přesměrování) – stačí, že je to ZIP a začal do minuty po kliknutí
const jeZip = d => /\.zip$/i.test(d.filename || '') || /zip/i.test(d.mime || '') || /downloadZip/i.test(d.url || '');
chrome.downloads.onCreated.addListener(async d => {
  if (/^(data|blob):/.test(d.url || '') && !zEbad(d.referrer)) return;   // vlastní snímky Snímkovače
  if (!zEbad(d.url) && !zEbad(d.finalUrl) && !zEbad(d.referrer) && !jeZip(d)) return;
  const f = await frontaNacti();
  const p = f.polozky.find(x => x.stav === 'stahuje' && !x.dlId && Date.now() - (x.cas || 0) < 60000);
  if (p) { p.dlId = d.id; await frontaUloz(f); }
});

chrome.downloads.onChanged.addListener(async d => {
  if (!d.state && !d.bytesReceived) return;
  const f = await frontaNacti();
  const p = f.polozky.find(x => x.dlId === d.id);
  if (!p) return;
  if (d.bytesReceived) p.mb = Math.round(d.bytesReceived.current / 1048576);
  if (d.state && d.state.current === 'complete') {
    p.stav = 'hotovo';
    await frontaUloz(f);
    setTimeout(async () => frontaDalsi(await frontaNacti()), FRONTA_PAUZA_MS);   // pauza mezi knihami
    return;
  }
  if (d.state && d.state.current === 'interrupted') {
    p.stav = 'chyba';
    f.zastaveno = `Stahování ${p.nazev || p.id} selhalo (${(d.error && d.error.current) || 'přerušeno'}) – fronta stojí.`;
    await frontaUloz(f);
    try {
      await chrome.notifications.create('fronta-chyba', { type: 'basic', iconUrl: 'ikony/ikona128.png', priority: 2,
        title: 'Snímkovač – stahování selhalo', message: f.zastaveno + ' Pokračuj tlačítkem ve frontě, až budeš chtít.' });
    } catch (e) { /* nic */ }
    return;
  }
  await frontaUloz(f);
});

chrome.tabs.onRemoved.addListener(async tabId => {
  const f = await frontaNacti();
  const zbyle = f.polozky.filter(p => p.tabId !== tabId || p.stav === 'stahuje');   // běžící stahování doběhne i bez karty
  if (zbyle.length === f.polozky.length) return;
  f.polozky = zbyle;
  await frontaUloz(f);
  await frontaDalsi(f);
});
