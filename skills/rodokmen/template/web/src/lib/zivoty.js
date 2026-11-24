// Údaje o životě osob odvozené z textů „faktů“ (* narození, † úmrtí, × sňatek), společné pro stránky Jména a Kalendář.
// Fakta jsou volný text zapsaný člověkem; tady se čtou jen začátky vět a nic se nedomýšlí.
import { people } from './data.js';

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

// ---------- kalendář ----------

const facts = Object.fromEntries(Object.values(people).map((p) => [p.slug, p.facts.map((f) => ({ ...parseFact(f), text: f })).filter((r) => r.t)]));

const ORDER = { narozeni: 0, krest: 1, svatba: 2, umrti: 3 };

/** Kalendář: události s přesným dnem a měsícem. Žijící osoby (ani sňatky s nimi) nejsou. */
export function calendarEvents() {
  const out = [];
  const seen = new Map();   // svatba zapsaná u obou manželů se spojí
  for (const p of Object.values(people)) {
    if (living.has(p.slug)) continue;
    for (const r of facts[p.slug]) {
      if (!r.exact) continue;
      const e = { m: r.m, d: r.d, y: r.y, q: +r.uncertain };
      if (r.t === 'b') out.push({ ...e, k: r.krest ? 'krest' : 'narozeni', p: [p.slug] });
      else if (r.t === 'd') out.push({ ...e, k: 'umrti', p: [p.slug] });
      else {
        const sp = p.spouse ? people[p.spouse] : null;
        const nm = sp ? sp.name.replace(/\s*\(\?\)\s*$/, '') : null;
        const named = nm && r.text.includes(nm);
        if (named && living.has(sp.slug)) continue;
        const numbered = /^\d\.\s*[×⚭]|^[×⚭]\s*\(\d\.\)/.test(r.text);
        const ps = named && !numbered ? [p.slug, sp.slug] : [p.slug];
        const key = `${r.y}-${r.m}-${r.d}|${[...ps].sort().join('+')}`;
        if (seen.has(key)) continue;
        seen.set(key, true);
        out.push({ ...e, k: 'svatba', p: ps });
      }
    }
  }
  // svatba zapsaná u obou manželů, ale bez jména manžela/manželky v textu: spojit podle vazby manžel – manželka
  for (const e of out) {
    if (e.k !== 'svatba' || e.p.length !== 1 || e.merged) continue;
    const sp = people[e.p[0]].spouse;
    const o = out.find((x) => x !== e && x.k === 'svatba' && x.p.length === 1 && x.p[0] === sp && x.y === e.y && x.m === e.m && x.d === e.d);
    if (o) { e.p = [e.p[0], sp]; o.drop = true; }
  }
  for (let i = out.length - 1; i >= 0; i--) if (out[i].drop) out.splice(i, 1);
  // osamělý záznam svatby skrýt, je-li ten samý člověk už ve spojeném záznamu téhož dne
  const full = out.filter((e) => e.k === 'svatba' && e.p.length > 1);
  return out
    .filter((e) => !(e.k === 'svatba' && e.p.length === 1 && full.some((f) => f.y === e.y && f.m === e.m && f.d === e.d && f.p.includes(e.p[0]))))
    .filter((e) => e.p.every((s) => !living.has(s)))
    .sort((a, b) => a.m - b.m || a.d - b.d || ORDER[a.k] - ORDER[b.k] || a.y - b.y);
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
