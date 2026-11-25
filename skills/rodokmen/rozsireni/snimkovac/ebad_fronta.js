// Snímkovač – fronta ZIPů na stránce knihy eBadatelny (…/MatrikaPage/matrikaId/<id>). Varianta B: tlačítko „Do fronty“,
// panel se stavem fronty; když je kniha na řadě, otevře záložku „Popis knihy“, zvýrazní tlačítko „Stáhnout knihu jako ZIP“
// a pípne. Na stažení klikne VŽDY uživatel. Logika fronty je ve workeru (fronta_worker.js).
(() => {
  if (window.__snimkovacFronta) return;
  window.__snimkovacFronta = true;
  // Číslo knihy: z adresy (…/MatrikaPage/matrikaId/<id>), jinak ze stránky – eBadatelna (Wicket) po kliknutí často
  // přepíše adresu na /wicket/page?N nebo MatrikaPage?N bez čísla knihy. Panel se ukáže, až je na stránce kniha
  // (záložka „Popis knihy“ nebo tlačítko ZIP); stránka se dokresluje postupně, proto se čeká (nejvýš 2 min).
  const idZAdresy = () => ((location.href.match(/matrikaId[\/=](\d+)/i) || [])[1]);
  const idZeStranky = () => {
    for (const a of document.querySelectorAll('a[href*="matrikaId"], link[href*="matrikaId"], [data-matrika-id]')) {
      const v = (a.getAttribute('href') || a.getAttribute('data-matrika-id') || '').match(/matrikaId[\/=](\d+)|^(\d+)$/i);
      if (v) return v[1] || v[2];
    }
    return ((document.body && document.body.innerHTML.match(/matrikaId[\/=](\d+)/i)) || [])[1];
  };
  const jeKniha = () => [...document.querySelectorAll('a, li, span, button, input')]
    .some(e => /^(popis knihy|stáhnout knihu jako zip)$/i.test(((e.innerText || e.value || '') + '').replace(/\s+/g, ' ').trim()));
  let pokusu = 0;
  const cekej = setInterval(() => {
    const id = idZAdresy() || (jeKniha() && idZeStranky());
    if (id) { clearInterval(cekej); spust(id); }
    else if (++pokusu > 120) clearInterval(cekej);
  }, 1000);
  function spust(ID) {
  const zivy = () => { try { return !!(chrome.runtime && chrome.runtime.id); } catch (e) { return false; } };
  const posli = z => zivy() ? chrome.runtime.sendMessage(z).catch(() => null) : Promise.resolve(null);
  const text = e => ((e.innerText || e.value || e.textContent || '') + '').replace(/\s+/g, ' ').trim();

  function nazevKnihy() {
    const h = [...document.querySelectorAll('h1, h2, h3, .title, [class*="nazev" i]')].map(text).find(t => t && t.length < 80);
    return h || (document.title || '').trim().slice(0, 80) || 'kniha ' + ID;
  }
  const tlacitkoZip = () => [...document.querySelectorAll('a, button, input[type=button], input[type=submit]')]
    .find(e => /stáhnout knihu jako zip/i.test(text(e)));
  const zalozkaPopis = () => [...document.querySelectorAll('a, li, span, button')]
    .find(e => text(e) === 'Popis knihy' && e.getBoundingClientRect().width > 0);

  // --- panel (stínový DOM, ať mu styly stránky nic nemění) ---
  const box = document.createElement('div');
  box.style.cssText = 'position:fixed;right:12px;bottom:12px;z-index:2147483646';
  const k = box.attachShadow({ mode: 'open' });
  k.innerHTML = `<style>
    :host{all:initial} .p{width:230px;background:#fff;color:#1f2328;border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,.28);
      font:12px/1.35 system-ui,"Segoe UI",sans-serif;overflow:hidden}
    .h{background:#1b5e20;color:#fff;padding:6px 8px;font-weight:600;display:flex;gap:6px;align-items:center}
    .h span{flex:1} .t{padding:8px;display:grid;gap:6px}
    button{all:unset;cursor:pointer;text-align:center;border-radius:6px;padding:5px;font-size:11px;background:#f6f8fa;box-shadow:inset 0 0 0 1px #d0d7de}
    button.hl{background:#1b5e20;color:#fff;box-shadow:none} ol{margin:0;padding-left:18px} li.ja{font-weight:600}
    .z{background:#fff8c5;border:1px solid #d4a72c;border-radius:4px;padding:3px 5px} .m{color:#57606a;font-size:10px}
    .x{all:unset;cursor:pointer;color:#cf222e;margin-left:4px}
  </style><div class="p"><div class="h"><span>Snímkovač – fronta ZIPů</span></div><div class="t">
    <button class="hl" data-pridej>Do fronty</button><div data-zprava></div><ol data-seznam></ol>
    <div style="display:flex;gap:6px"><button data-pokracuj hidden style="flex:1">Pokračovat</button><button data-vycisti style="flex:1">Vyprázdnit</button></div>
    <div class="m">Stahování spouštíš vždy ty kliknutím. Jedno naráz, při chybě fronta stojí.</div></div></div>`;
  document.body.appendChild(box);
  const $ = s => k.querySelector(s);
  // Přesun panelu tažením za zelené záhlaví; poloha se pamatuje
  const hlava = $('.h');
  hlava.style.cursor = 'move'; hlava.title = 'Tažením přesuneš';
  const umisti = (l, t) => {
    box.style.left = Math.max(0, Math.min(innerWidth - 80, l)) + 'px';
    box.style.top = Math.max(0, Math.min(innerHeight - 30, t)) + 'px';
    box.style.right = box.style.bottom = 'auto';
  };
  chrome.storage.local.get('fronta_poloha').then(d => { const p = d.fronta_poloha; if (p) umisti(p.left, p.top); }, () => {});
  let tah = null;
  hlava.addEventListener('pointerdown', e => { tah = { dx: e.clientX - box.offsetLeft, dy: e.clientY - box.offsetTop }; hlava.setPointerCapture(e.pointerId); });
  hlava.addEventListener('pointermove', e => { if (tah) umisti(e.clientX - tah.dx, e.clientY - tah.dy); });
  hlava.addEventListener('pointerup', () => {
    if (!tah) return;
    tah = null;
    if (zivy()) chrome.storage.local.set({ fronta_poloha: { left: box.offsetLeft, top: box.offsetTop } });
  });
  const POPIS = { ceka: 'čeká', 'na-rade': 'na řadě – klikni na Stáhnout', stahuje: 'stahuje', hotovo: 'hotovo ✓', chyba: 'chyba' };

  let fronta = null;
  function kresli(f, zprava) {
    if (f) fronta = f;
    const fr = fronta || { polozky: [] };
    const ja = fr.polozky.find(p => p.id === ID);
    const pb = $('[data-pridej]');
    pb.textContent = ja && ja.stav !== 'hotovo' && ja.stav !== 'chyba' ? `Ve frontě (${POPIS[ja.stav]})` : 'Do fronty';
    pb.disabled = !!ja && ja.stav !== 'hotovo' && ja.stav !== 'chyba';
    const sez = $('[data-seznam]');
    sez.replaceChildren(...fr.polozky.map(p => {
      const li = document.createElement('li');
      if (p.id === ID) li.className = 'ja';
      li.textContent = `${p.nazev || p.id} – ${POPIS[p.stav] || p.stav}${p.stav === 'stahuje' && p.mb ? ` (${p.mb} MB)` : ''}`
        + (p.stav === 'chyba' && p.duvod ? ` (${p.duvod})` : '');
      // odebrat jde i „stahuje“ – když se stahování zaseklo, uvolní se tím fronta (stahování v Chrome to nezruší)
      const x = document.createElement('button'); x.className = 'x'; x.textContent = '×';
      x.title = p.stav === 'stahuje' ? 'Odebrat z fronty (zaseknuté stahování – v Chrome ho zruš přes Ctrl+J)' : 'Odebrat z fronty';
      x.onclick = () => posli({ typ: 'fronta-odeber', id: p.id }).then(r => kresli(r));
      li.append(x);
      return li;
    }));
    const z = $('[data-zprava]');
    const t = zprava || fr.zastaveno || '';
    z.className = t ? 'z' : ''; z.textContent = t;
    $('[data-pokracuj]').hidden = !fr.zastaveno;
  }
  $('[data-pridej]').onclick = () => posli({ typ: 'fronta-pridej', id: ID, nazev: nazevKnihy() }).then(r => r && kresli(r, r.chyba));
  $('[data-vycisti]').onclick = () => posli({ typ: 'fronta-vycisti' }).then(r => kresli(r));
  $('[data-pokracuj]').onclick = () => posli({ typ: 'fronta-pokracuj' }).then(r => kresli(r));

  // Klik uživatele na „Stáhnout knihu jako ZIP“: když už běží jiné stahování, klik zadrží (server by vrátil chybu 500)
  // (předání kliku dál: b.click() má isTrusted = false, tento posluchač ho proto pustí beze změny)
  document.addEventListener('click', e => {
    const b = tlacitkoZip();
    if (!b || !(e.target === b || b.contains(e.target)) || !e.isTrusted) return;
    e.preventDefault(); e.stopImmediatePropagation();
    posli({ typ: 'fronta-klik', id: ID, nazev: nazevKnihy() }).then(r => {
      if (r && r.blokovano) { kresli(r, `Počkej: ještě se stahuje ${r.blokovano}. Server pustí jen jedno stahování.`); return; }
      if (r) kresli(r);
      zvyrazni(false);
      b.click();   // pustit původní akci stránky – stejný prvek, na který uživatel právě klikl
    });
  }, true);

  function zvyrazni(zap) {
    const b = tlacitkoZip();
    if (!b) return;
    b.style.outline = zap ? '4px solid #1b5e20' : '';
    b.style.outlineOffset = zap ? '3px' : '';
    b.style.boxShadow = zap ? '0 0 0 10px rgba(124,179,66,.45)' : '';
    if (zap) b.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }
  function pipni() {
    try {
      const a = new AudioContext(), o = a.createOscillator(), g = a.createGain();
      o.frequency.value = 880; g.gain.value = 0.15; o.connect(g); g.connect(a.destination);
      o.start(); o.frequency.setValueAtTime(660, a.currentTime + 0.18); o.stop(a.currentTime + 0.4);
    } catch (e) { /* zvuk nejde – zůstane oznámení */ }
  }

  chrome.runtime.onMessage.addListener(z => {
    if (!z) return;
    if (z.typ === 'fronta-stav') kresli(z.fronta);
    if (z.typ === 'fronta-na-rade' && z.id === ID) {
      const zal = zalozkaPopis();
      if (zal && !tlacitkoZip()) zal.click();   // jen přepnutí záložky na stránce, nic se nestahuje
      let pokusu = 0;
      const t = setInterval(() => { if (tlacitkoZip() || ++pokusu > 20) { clearInterval(t); zvyrazni(true); } }, 300);
      pipni();
    }
  });
  posli({ typ: 'fronta-stav?' }).then(r => r && kresli(r));
  }   // spust
})();
