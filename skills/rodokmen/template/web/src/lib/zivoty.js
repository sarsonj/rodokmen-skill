// Údaje o životě osob odvozené z textů „faktů“ (* narození, † úmrtí, × sňatek), společné pro stránky Jména a Kalendář.
// Fakta jsou volný text zapsaný člověkem; tady se čtou jen začátky vět a nic se nedomýšlí.
import { people, lineByK } from './data.js';

/** Rok sestavení webu (pro odhad, kdo ještě může žít). */
export const NOW = new Date().getFullYear();

/** Rozbor jednoho faktu: { t: 'b'|'d'|'m', y, m?, d?, exact, uncertain, krest, approx, before } nebo null. */
export function parseFact(f) {
  let s = f.trim();
  const lead = s.match(/^(\d)\.\s*(?=[×⚭])/);        // „1. × 7. 5. 1793 …“
  if (lead) s = s.slice(lead[0].length);
  const sym = s[0];
  if (!'*†×⚭'.includes(sym)) return null;
  const t = sym === '*' ? 'b' : sym === '†' ? 'd' : 'm';
  let rest = s.slice(1).trim();
  let krest = false;
  const pre = rest.match(/^\(pokřtěn\)\s*/);
  if (pre) { krest = true; rest = rest.slice(pre[0].length); }
  rest = rest.replace(/^\(\d\.\)\s*/, '').replace(/^\(\?\)\s*/, '');
  const mod = rest.match(/^(před|po|asi|snad|kolem|≈)\s*/i);
  if (mod) rest = rest.slice(mod[0].length);
  const dm = rest.match(/^(?:(\d{1,2})\.\s*(\d{1,2})\.\s*)?(\d{4})\b(?!\s*\/)/);
  if (!dm) return null;
  const after = rest.slice(dm[0].length);
  const r = { t, y: +dm[3], exact: false, uncertain: false, krest, approx: false, before: false };
  const w = mod ? mod[1].toLowerCase() : '';
  r.approx = w === 'asi' || w === '≈' || w === 'kolem';
  r.before = w === 'před' || w === 'po';
  if (w === 'snad') r.uncertain = true;
  if (dm[1]) {
    const d = +dm[1], m = +dm[2];
    if (d >= 1 && d <= 31 && m >= 1 && m <= 12) { r.d = d; r.m = m; r.exact = !mod || w === 'snad'; }
  }
  const head = after.slice(0, 70);
  if (/\(\?\)|pravděpodobn|nejist|\bsnad\b/i.test(head)) r.uncertain = true;
  if (t === 'b') {
    const kr = after.match(/\(křest([^)]*)\)/);
    if (kr && !/\d/.test(kr[1])) r.krest = true;          // datum je datum křtu; „(křest 5. 3. Těnovice)“ znamená, že datum je narození
  }
  return r;
}

/** Žije, nebo by mohla žít? V takovém případě se osoba na těchto stránkách nezobrazuje. */
export function isLiving(p) {
  if (/^Žijící/i.test(p.note || '')) return true;
  if (p.st === 'fam' && /^\*\s*\d{4}\s*$/.test(p.y || '') && !p.facts.some((f) => f.startsWith('†'))) {
    const y = +p.y.match(/\d{4}/)[0];
    if (y > NOW - 110) return true;
  }
  const hasDeath = p.facts.some((f) => f.startsWith('†')) || /[–†]/.test(p.y || '');
  const by = birthYearGuess(p);
  return !hasDeath && by !== null && by > NOW - 110;
}

function birthYearGuess(p) {
  for (const f of p.facts) {
    const r = parseFact(f);
    if (r && r.t === 'b') return r.y;
  }
  const m = (p.y || '').match(/\d{4}/);
  return m ? +m[0] : null;
}

/** Slugy osob, které žijí nebo by mohly žít – ty se na stránkách Jména a Kalendář nezobrazují. */
export const living = new Set(Object.values(people).filter(isLiving).map((p) => p.slug));

// ---------- časová osa ----------

const facts = Object.fromEntries(Object.values(people).map((p) => [p.slug, p.facts.map((f) => ({ ...parseFact(f), text: f })).filter((r) => r.t)]));

function fromY(y) {
  // rok narození a úmrtí z pole `y` (opravdu jen první výskyt; pole bývá ošklivé: „* 1746* 24. 2. 1746“)
  const r = { b: null, bq: null, d: null, dq: null };
  y = (y || '').trim();
  const ys = y.match(/\d{4}/g);
  if (!ys) return r;
  const head = y.split('–');
  if (y.startsWith('†')) { r.d = +ys[0]; r.dq = /před/.test(y.split('†')[1] || '') ? 'before' : 'exact'; return r; }
  if (y.startsWith('*')) { r.b = +ys[0]; r.bq = /\*\s*(asi|≈)/.test(y.slice(0, 12)) ? 'approx' : 'exact'; return r; }
  if (y.startsWith('–') || y.startsWith('? ')) { r.d = +ys[ys.length - 1]; r.dq = /před/.test(y) ? 'before' : 'exact'; return r; }
  r.b = +ys[0]; r.bq = /^(asi|≈)/.test(y) ? 'approx' : 'exact';
  if (ys.length > 1 && head.length > 1) {
    r.d = +ys[ys.length - 1];
    r.dq = /před/.test(head[1]) ? 'before' : /(asi|≈|\?)/.test(head[1]) ? 'approx' : 'exact';
  }
  return r;
}

/** Řádky časové osy (bez žijících). Chybějící roky se odhadnou z dětí, sňatku a rodičů – takové pruhy na ose bledou. */
export function timelineRows() {
  const list = Object.values(people).filter((p) => !living.has(p.slug));
  const info = {};
  for (const p of list) {
    const fy = fromY(p.y);
    const o = { b: fy.b, bq: fy.bq, d: fy.d, dq: fy.dq, m: [] };
    for (const r of facts[p.slug]) {
      if (r.t === 'b' && !o.fromFactB) { o.b = r.y; o.bq = r.approx || r.before || r.uncertain ? 'approx' : 'exact'; o.fromFactB = true; }
      else if (r.t === 'd' && !o.fromFactD) { o.d = r.y; o.dq = r.before ? 'before' : r.approx ? 'approx' : 'exact'; o.fromFactD = true; }
      else if (r.t === 'm') o.m.push(r.y);
    }
    o.m = [...new Set(o.m)].sort((a, b) => a - b);
    info[p.slug] = o;
  }
  const birthOf = (s) => info[s]?.b ?? null;
  // odhady od nejbližších generací k nejstarším, ať děti jsou odhadnuté dřív než rodiče
  for (const p of [...list].sort((a, b) => a.gen - b.gen || a.k - b.k)) {
    const o = info[p.slug];
    if (o.b === null) {
      const cands = [];
      const kids = p.children.map(birthOf).filter((x) => x !== null);
      if (kids.length) cands.push(Math.min(...kids) - (p.sex === 'M' ? 30 : 27));
      if (o.m.length) cands.push(o.m[0] - (p.sex === 'M' ? 27 : 23));
      const par = [p.father, p.mother].map(birthOf).filter((x) => x !== null);
      if (par.length) cands.push(Math.max(...par) + 30);
      const spb = p.spouse ? birthOf(p.spouse) : null;
      if (spb !== null) cands.push(spb);
      if (cands.length) { o.b = Math.round(cands.reduce((a, b) => a + b, 0) / cands.length); o.bq = 'est'; }
    }
  }
  const rows = [];
  for (const p of list) {
    const o = info[p.slug];
    if (o.b === null && o.d === null) continue;
    if (o.b === null) { o.b = o.d - 55; o.bq = 'est'; }
    if (o.d === null) {
      const kids = p.children.map(birthOf).filter((x) => x !== null);
      const last = Math.max(o.b + 55, ...(kids.length ? [Math.max(...kids) + 5] : []), ...(o.m.length ? [o.m[o.m.length - 1] + 10] : []));
      o.d = Math.min(last, NOW); o.dq = 'est';
    }
    if (o.d < o.b) o.d = o.b + 1;
    const spread = (q) => (q === 'est' ? 12 : q === 'approx' ? 4 : q === 'before' ? 8 : 0);
    const x0 = o.b - spread(o.bq), x1 = o.d + spread(o.dq);
    const w = Math.max(1, x1 - x0);
    const line = p.line ? lineByK[p.line] : null;
    rows.push({
      s: p.slug, n: p.name, k: p.k, g: p.gen, b: o.b, bq: o.bq, d: o.d, dq: o.dq, x0, x1,
      sl: +(spread(o.bq) / w).toFixed(3) || 0, sr: +(spread(o.dq) / w).toFixed(3) || 0,
      m: o.m.filter((y) => y >= o.b && y <= o.d + 1), c: line ? line.color : '#9aa3ad', l: line ? line.name : 'Nejbližší rodina',
      y: p.years || '', st: p.st,
    });
  }
  rows.sort((a, b) => a.b - b.b || a.k - b.k);
  return rows;
}

// ---------- jména ----------

/** Křestní jména osoby (bez příjmení, závorek, otazníků; dvojité jméno = dvě jména). */
export function firstNames(p) {
  let n = p.name.replace(/\([^)]*\)/g, ' ').replace(/\s+/g, ' ').trim();
  n = n.replace(/\b(st|ml)\.?$/, '').trim();
  const toks = n.split(' ').filter(Boolean);
  if (!toks.length) return [];
  if (/^otec|^matka|neuveden/i.test(n)) return [];
  if (n.includes(' / ') && !/\S+ \/ \S+ \S+/.test(n)) return toks.filter((x) => x !== '/');   // „Markéta / Mariana“ – dvě podoby jména, příjmení není
  if (toks.length === 1) return toks;           // jen křestní jméno (bez rodného příjmení)
  return toks.slice(0, -1);
}

/** Čísla rodů, do kterých osoba patří (i přes „také“ – předek v rodokmenu vícekrát); null = nejbližší rodina mimo rody. */
export function personLines(p) {
  const ks = [p.line, ...(p.also || []).map((a) => a.line)].filter((k) => k != null);
  return [...new Set(ks.length ? ks : [null])];
}

/** Je na časové ose aspoň jeden předek (s alespoň jedním známým rokem)? Jen pak má smysl stránka a položka v menu. */
export const maCasovouOsu = timelineRows().length > 0;
