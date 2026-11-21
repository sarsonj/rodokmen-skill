// Snímkovač – okénko po kliknutí na ikonu. Jedna stavová karta s jedním hlavním tlačítkem; pokročilé věci schované.
const $ = id => document.getElementById(id);
const verze = chrome.runtime.getManifest().version;
$('pata').textContent = `Snímkovač ${verze} · ukládá jen to, co si sám zobrazíš.`;
const zprava = z => new Promise(ok => chrome.runtime.sendMessage(z, r => ok(chrome.runtime.lastError ? null : r)));
const doZalozky = (tabId, z) => new Promise(ok => chrome.tabs.sendMessage(tabId, z, r => ok(chrome.runtime.lastError ? null : r)));
const URO = [
  { id: 'min', nazev: 'Přehled', barva: 'var(--prehled)' },
  { id: 'ideal', nazev: 'Čtení', barva: 'var(--cteni)' },
  { id: 'zapis', nazev: 'Záznam', barva: 'var(--zapis)' }
];

// --- jedno místo pro výsledek, potvrzení přímo v okénku (žádné systémové dialogy) ---
function vysledek(text, druh = 'ok') { const v = $('vysledek'); v.className = 'pruh ' + druh; v.textContent = text; }
function potvrd(text, ano, akce) {
  $('potvrzeniText').textContent = text;
  $('potvrzeniAno').textContent = ano;
  $('potvrzeni').hidden = false;
  $('potvrzeniAno').onclick = () => { $('potvrzeni').hidden = true; akce(); };
  $('potvrzeniNe').onclick = () => { $('potvrzeni').hidden = true; };
}

// --- karta ---
function karta({ nadpis, text = '', pruh = null, souhlas = false, hlavni = null, druhe = null, odkaz = null, urovne = null }) {
  $('kNadpis').textContent = nadpis;
  $('kText').textContent = text;
  $('kText').hidden = !text;
  const p = $('kPruh');
  p.hidden = !pruh;
  if (pruh) { p.className = 'pruh ' + pruh.druh; p.textContent = pruh.text; }
  $('kSouhlas').hidden = !souhlas;
  for (const [id, b] of [['kHlavni', hlavni], ['kDruhe', druhe], ['kOdkaz', odkaz]]) {
    const el = $(id);
    el.hidden = !b;
    if (!b) continue;
    el.textContent = b.text;
    el.onclick = b.akce;
    el.disabled = !!(souhlas && id === 'kHlavni' && !$('kRozumim').checked);
    if (id === 'kDruhe') el.className = b.nebezpecne ? 'nebezpecne' : '';
  }
  if (souhlas) $('kRozumim').onchange = () => { $('kHlavni').disabled = !$('kRozumim').checked; };
  const u = $('kUrovne');
  u.hidden = !urovne;
  if (urovne) u.innerHTML = URO.map(x => `<div class="uroven"><span>${x.nazev}</span><span class="lista"><i style="width:${urovne[x.id] || 0}%;background:${x.barva}"></i></span><b>${urovne[x.id] ?? '–'} %</b></div>`).join('');
}

// --- hlavní stav ---
async function nacti() {
  const s = await zprava({ typ: 'stav' }) || {};
  $('prep').checked = !!s.zap;
  $('tecka').className = 'tecka' + (s.zap ? ' zap' : '');
  $('podhlava').textContent = s.zap ? 'Ukládání zapnuto' : 'Ukládání vypnuto';
  $('pocet').textContent = s.dnes ?? 0;
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!s.zap) {
    return karta({ nadpis: 'Ukládání je vypnuté.', text: 'Nic se neukládá na žádném webu.',
                   hlavni: { text: 'Zapnout ukládání', akce: () => prepni(true) } });
  }
  let u = null;
  try { u = new URL(tab.url); } catch (e) { /* bez adresy */ }
  if (!u || u.protocol !== 'https:') return karta({ nadpis: 'Tady není co ukládat.', text: 'Otevři snímek matriky v archivu.' });
  const host = u.hostname, vestaveny = host === 'ebadatelna.soapraha.cz';
  const weby = (await chrome.storage.local.get('weby')).weby || {};
  if (!vestaveny && !weby[host]) return kartaNepovoleny(tab, host);
  // povolený web: dlaždicový prohlížeč, nebo jeden obrázek
  const [osd, str] = await Promise.all([doZalozky(tab.id, { typ: 'osd-stav' }), doZalozky(tab.id, { typ: 'stranka' })]);
  const prestat = vestaveny ? null : { text: 'Přestat ukládat na tomto webu', akce: () => zprava({ typ: 'zrus-web', host }).then(() => window.close()) };
  if (osd) return kartaDlazdice(tab, host, osd, prestat);
  if (str) {
    const kdy = typeof str.uz === 'string' ? new Date(str.uz) : null;
    return karta({
      nadpis: 'Ukládám, co si zobrazíš.',
      text: str.uz ? `Tento snímek už máš uložený${kdy && !isNaN(kdy) ? ' (' + kdy.toLocaleString('cs-CZ', { day: 'numeric', month: 'numeric', hour: '2-digit', minute: '2-digit' }) + ')' : ''}.` : '',
      pruh: str.ok ? null : { druh: 'chyba', text: 'Nepovedlo se uložit: ' + str.text },
      druhe: { text: 'Uložit znovu', akce: () => doZalozky(tab.id, { typ: 'znovu' }).then(() => window.close()) },
      odkaz: prestat });
  }
  karta({ nadpis: 'Zatím nevidím snímek.', text: 'Otevři snímek matriky. Když tu snímek je a nic se neděje, obnov stránku (F5).', odkaz: prestat });
}

function kartaNepovoleny(tab, host) {
  const stav = stavWebu(host), w = najdiWeb(host);
  const povolit = async () => {
    const ok = await chrome.permissions.request({ origins: [`https://${host}/*`] });   // jediný dotaz prohlížeče
    if (!ok) return vysledek('Prohlížeč povolení nedal.', 'chyba');
    await zprava({ typ: 'povol-web', host, potvrzeno: true, tabId: tab.id });
    window.close();
  };
  if (stav === 'povoleno') return karta({ nadpis: `${host}: zatím neukládám.`, text: 'Archiv pasivní ukládání dovoluje.' + (w && w.pozn ? ' ' + w.pozn : ''),
                                          hlavni: { text: 'Ukládat na tomto webu', akce: povolit } });
  if (stav === 'zakazano') return karta({ nadpis: `${host}: zatím neukládám.`, pruh: { druh: 'chyba', text: 'Tento archiv nástroje zakazuje.' },
                                          souhlas: true, druhe: { text: 'Přesto ukládat', akce: () => $('kRozumim').checked && povolit() } });
  karta({ nadpis: `${host}: zatím neukládám.`,
          text: 'Pravidla tohoto archivu nemáme ověřená.' + (w && w.pozn ? ' ' + w.pozn : ' Než ho zapneš, mrkni na jeho podmínky užití.'),
          souhlas: true, hlavni: { text: 'Ukládat na tomto webu', akce: povolit } });
}

async function kartaDlazdice(tab, host, s, prestat) {
  const maVse = await chrome.permissions.contains({ origins: ['<all_urls>'] });
  const uloz = () => doZalozky(tab.id, { typ: 'osd-uloz', vyrez: false }).then(r =>
    r && r.ok ? vysledek(`Uloženo: ${r.soubor}`) : vysledek('Nepovedlo se uložit: ' + ((r && r.chyba) || '?'), 'chyba'));
  let pruh = null, hlavni = { text: 'Uložit teď', akce: uloz }, druhe = null;
  if (s.chyba && s.potrebujePovoleni && !maVse) {
    // otevřením okénka už prohlížeč focení na této stránce povolil (activeTab) a panel fotí znovu
    pruh = { druh: 'pozor', text: 'Tady stránku fotím z obrazovky. Teď jsem vyfotil, ale po načtení další stránky budeš muset kliknout znovu – nebo povol focení jednou provždy.' };
    hlavni = { text: 'Povolit focení', akce: povolFoceni };
    druhe = { text: 'Klikat pokaždé', akce: () => window.close() };
  } else if (s.chyba) {
    pruh = { druh: 'chyba', text: s.chyba };
  } else if (s.fotim && !maVse) {
    pruh = { druh: 'pozor', text: 'Tady stránku fotím z obrazovky. Po každém načtení stránky klikni na ikonu (Alt+S), nebo povol focení jednou provždy v Pokročilých.' };
  }
  karta({ nadpis: 'Skládám stránku z toho, co vidíš.',
          text: `Snímek ${s.popis && s.popis.snimek || '?'} · detail ${s.detail ?? s.procent ?? '?'} %` + (s.ulozeno ? ` · uloženo ${s.ulozeno}` : ''),
          urovne: s.pokryti, pruh, hlavni, druhe, odkaz: prestat });
  // pokročilé pro dlaždicové prohlížeče
  $('pDlazdice').hidden = false;
  $('pPrejdiBlok').hidden = false;
  $('pFoceni').hidden = !s.fotim || maVse;
  $('pVyrez').onclick = () => doZalozky(tab.id, { typ: 'osd-uloz', vyrez: true }).then(r =>
    r && r.ok ? vysledek(`Uloženo: ${r.soubor}`) : vysledek('Nepovedlo se uložit: ' + ((r && r.chyba) || '?'), 'chyba'));
  $('pSmaz').onclick = () => potvrd('Smazat rozpracovanou stránku? Uložené soubory zůstanou.', 'Smazat', () =>
    doZalozky(tab.id, { typ: 'osd-smaz' }).then(r => r && r.ok ? vysledek('Rozpracovaná stránka smazána') : vysledek('Nepovedlo se: ' + ((r && r.chyba) || '?'), 'chyba')));
  $('osdprejdi').onclick = () => {
    const v = $('osdkam').value.split(/[,;\s]+/).map(Number);
    if (v.length !== 4 || v.some(x => isNaN(x) || x < 0 || x > 1) || v[2] <= v[0] || v[3] <= v[1]) return vysledek('Zadej čtyři čísla od 0 do 1', 'chyba');
    doZalozky(tab.id, { typ: 'osd-prejdi', vyrez: v }).then(() => window.close());
  };
}

async function povolFoceni() {
  // Chrome dovolí trvale fotit záložku jen s přístupem ke všem webům; Snímkovač dál fotí jen povolené archivy
  const ok = await chrome.permissions.request({ origins: ['<all_urls>'] });
  vysledek(ok ? 'Focení povoleno natrvalo' : 'Focení zůstává na klik', ok ? 'ok' : 'pozor');
  if (ok) nacti();
}

async function prepni(zap) { await zprava({ typ: 'zap', hodnota: zap }); nacti(); }
$('prep').onchange = () => prepni($('prep').checked);

// --- pokročilé (společné) ---
(async () => {
  const p = { min: 25, ideal: 50, zapis: 75, ...((await chrome.storage.local.get('prahy')).prahy || {}) };
  $('pmin').value = p.min; $('pideal').value = p.ideal; $('pzapis').value = p.zapis;
  const ulozPrahy = () => chrome.storage.local.set({ prahy: { min: +$('pmin').value || 25, ideal: +$('pideal').value || 50, zapis: +$('pzapis').value || 75 } });
  for (const id of ['pmin', 'pideal', 'pzapis']) $(id).onchange = ulozPrahy;
})();
$('pFoceni').onclick = povolFoceni;
$('pZapomen').onclick = () => potvrd('Zapomenout, co už je uložené? Snímky se při dalším zobrazení uloží znovu, soubory na disku zůstanou.', 'Zapomenout',
  () => zprava({ typ: 'zapomen' }).then(() => vysledek('Zapomenuto – snímky se při dalším zobrazení uloží znovu')));
const den = new Date().toLocaleDateString('sv-SE');
zprava({ typ: 'pocitadlo-vse' }).then(async vse => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  let host = ''; try { host = new URL(tab.url).hostname; } catch (e) { /* nic */ }
  const z = vse && vse[den] && vse[den][host];
  if (z) $('pPocitadlo').textContent = `Dnes na ${host} od ${z.prvni || '?'}: ${z.snimku} snímků, ${z.zeServeru} dlaždic ze serveru `
    + `(${(z.bajtu / 1048576).toFixed(1)} MB), ${z.zMezipameti} z mezipaměti` + (z.chyby ? `, nenačteno ${z.chyby} (server dlaždici nevrátil – když přibývá a snímky jsou bílé, přestaň)` : ', bez chyb')
    + (z.zruseno ? `, ${z.zruseno} zrušil prohlížeč archivu sám (v pořádku)` : '') + '.';
  $('pStatistika').onclick = () => chrome.downloads.download({
    url: 'data:application/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(vse || {}, null, 2)),
    filename: `rodokmen-snimky/_analyza/pocitadlo_${den}.json`, conflictAction: 'overwrite', saveAs: false
  }).then(() => vysledek('Statistika uložena do Stažené / rodokmen-snimky / _analyza'));
});

// --- analýza stránky (jedno kliknutí = jedno projití stránky + jedno načtení robots.txt) ---
$('analyza').onclick = async () => {
  vysledek('Analyzuji…', 'pozor');
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  try {
    let vysledky;
    try {   // všechny rámy (prohlížeč snímků bývá ve vloženém rámu); rámy cizích webů prohlížeč nepustí
      vysledky = await chrome.scripting.executeScript({ target: { tabId: tab.id, allFrames: true }, world: 'MAIN', func: snimkovacAnalyza });
    } catch (x) {
      vysledky = await chrome.scripting.executeScript({ target: { tabId: tab.id }, world: 'MAIN', func: snimkovacAnalyza });
    }
    const hlavni = vysledky.find(v => v.frameId === 0) || vysledky[0];
    const z = hlavni && hlavni.result;
    if (!z) throw new Error('stránka nevrátila výsledek');
    z.ramce = vysledky.filter(v => v !== hlavni && v.result).map(v => v.result);
    const host = new URL(tab.url).hostname.replace(/[^a-z0-9.-]/gi, '_');
    const cas = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    z.weby_js_stav = stavWebu(new URL(tab.url).hostname);
    await chrome.downloads.download({
      url: 'data:application/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(z, null, 2)),
      filename: `rodokmen-snimky/_analyza/${host}_${cas}.json`, conflictAction: 'uniquify', saveAs: false
    });
    const typy = new Set();
    for (const r of [z, ...z.ramce]) for (const [k, ano] of Object.entries(r.prohlizec || {})) if (ano) typy.add(k);
    const typ = [...typy].join(', ') || (z.obrazky.length ? 'jeden obrázek' : 'nic nenalezeno');
    const zamcene = [z, ...z.ramce].some(r => (r.platna || []).some(c => c.citelne === false));
    vysledek(`Analýza uložena do _analyza. Prohlížeč: ${typ}.` + (zamcene ? ' Obraz je z cizího serveru – budu fotit obrazovku.' : '')
      + ` ${snimkovacShrnRobots(z.robots)}`);
  } catch (e) {
    vysledek('Analýza se nepovedla: ' + e.message, 'chyba');
  }
};

nacti();
