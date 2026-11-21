// Snímkovač – fronta ZIPů z eBadatelny SOA Praha (rozšíření jen upozorní, stahování spouští uživatel).
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

// Další kniha na řadě: přepnout na její kartu, ať ji uživatel vidí, a dát vědět. Stahování nespouští.
async function frontaDalsi(f) {
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
    if (z.typ === 'fronta-vycisti') { f.polozky = f.polozky.filter(p => p.stav === 'stahuje'); f.zastaveno = ''; await frontaUloz(f); return f; }
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
chrome.downloads.onCreated.addListener(async d => {
  if (!zEbad(d.url) && !zEbad(d.finalUrl) && !zEbad(d.referrer)) return;
  const f = await frontaNacti();
  const p = f.polozky.find(x => x.stav === 'stahuje' && !x.dlId);
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
