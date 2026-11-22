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
