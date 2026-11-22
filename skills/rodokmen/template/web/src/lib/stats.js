// Statistiky z doložených údajů (site.json). Žijící osoby se nepočítají (living ze zivoty.js).
// Stránka Statistiky se vytvoří a nabídne v menu jen tehdy, když je dost údajů: maStatistiky.
import site from '../data/site.json';
import { people, families, byK } from './data.js';
import { living, parseFact, firstNames } from './zivoty.js';

const all = Object.values(people);
const ok = (p) => p && !living.has(p.slug);

/** Kolik zemřelých osob s doloženým rokem narození je nejméně potřeba, aby se stránka Statistiky vůbec zobrazila. */
export const MIN_OSOB = 15;
/** Kolik údajů musí mít jednotlivá část stránky (třeba věk při svatbě), aby se zobrazila. */
export const MIN_ROW = 5;

/** Rok narození a úmrtí z textu „* 1826“, „1810–1870“, „† před 1743“ – jen přesné roky (ne ≈, ?, před, po, „žil“). */
export function lifeYears(p) {
  const y = (p.years || '').trim();
  const num = (s) => {
    if (!s || /[≈?]|před|po /.test(s)) return null;
    const m = s.match(/\b(\d{4})\b/);
    return m ? Number(m[1]) : null;
  };
  if (y.startsWith('†')) return { b: null, d: num(y) };
  if (y.startsWith('žil')) return { b: null, d: null };
  const [b, d] = y.replace(/^\* /, '').split('–');
  return { b: num(b), d: num(d) };
}

/** Počet zemřelých osob s doloženým rokem narození (základ prahu MIN_OSOB). */
export const nDolozeno = all.filter((p) => ok(p) && lifeYears(p).b !== null).length;
export const maStatistiky = nDolozeno >= MIN_OSOB;

/** Úplné datum narození z faktu „* 3. 5. 1921 …“ (ne křest, ne odhad). */
const fullBirth = (p) => {
  for (const f of p.facts) {
    const r = parseFact(f);
    if (r && r.t === 'b' && r.exact && !r.krest) return r;
  }
  return null;
};
// věk k datu; není-li známý den narození, počítáme jen z roků
const exactAge = (bd, y1, m1, d1) =>
  bd && bd.d && bd.m ? y1 - bd.y - ((m1 || 12) < bd.m || ((m1 || 12) === bd.m && (d1 || 31) < bd.d) ? 1 : 0) : null;

// ---------- povolání ----------
const OCC = [
  ['Sedláci, rolníci, hospodáři', /(sedlák|sedlač|rolník|hospodář|statkář|gruntovník|possessor)/iu],
  ['Chalupníci a čtvrtláníci', /(chalupník|čtvrtláník|půlláník|zahradník)/iu],
  ['Domkáři', /domkář/iu],
  ['Podruzi, nádeníci, čeleď', /(podruh|nádeník|čeledín|služebn|děvečka|pacholek)/iu],
  ['Výměnkáři', /(výměnkář|výminkář)/iu],
  ['Kováři', /kovář/iu],
  ['Tkalci a soukeníci', /(tkadlec|tkalec|tkalcovsk|soukeník|přadlen)/iu],
  ['Krejčí a švadleny', /(krejčí|krejčovsk|švadlen)/iu],
  ['Ševci a koželuzi', /(švec|ševcovsk|koželuh)/iu],
  ['Mlynáři', /mlynář/iu],
  ['Kameníci a zedníci', /(kameník|zedník|zednick)/iu],
  ['Tesaři a truhláři', /(tesař|truhlář|stolař)/iu],
  ['Šenkýři a hostinští', /(šenkýř|hostinsk|hospodsk|krčmář)/iu],
  ['Vojáci', /(voják|vojín|pluk)/iu],
  ['Horníci a dělníci', /(horník|dělník|továrn|hutník)/iu],
  ['Lesníci a hajní', /(lesník|hajný|myslivec|polesn)/iu],
  ['Řezníci a pekaři', /(řezník|pekař)/iu],
  ['Úředníci, rychtáři, učitelé', /(rychtář|písař|učitel|úředník|purkmistr|starosta)/iu],
  ['Šafáři a ovčáci', /(šafář|ovčák|pastýř)/iu],
  ['Železničáři', /(železničář|výpravčí|strojvedoucí|topič)/iu],
];
const notOwn = /^(pomáhal|v domácnosti|sloužil|manželka|syn|dcera|děti|vdova|vdovec|z |ze |otec|matka|bratr|sestra|nemanželsk|kmotr|svědek)/iu;
export function professions() {
  const rows = OCC.map(([name, rx]) => ({ name, rx, people: [] }));
  let known = 0;
  for (const p of all) {
    if (!ok(p)) continue;
    const texts = p.facts.filter((f) => !/^[*†×⚭]/.test(f) && !notOwn.test(f));
    if (!texts.length) continue;
    let hit = false;
    for (const r of rows) if (texts.some((f) => r.rx.test(f))) { r.people.push(p.slug); hit = true; }
    if (hit) known++;
  }
  return { known, rows: rows.filter((r) => r.people.length).sort((a, b) => b.people.length - a.people.length) };
}

// ---------- sňatky ----------
/** Datum sňatku z řádků „× 20. 6. 1919 …“ rodiny: { y, m?, d? } – jen přesné roky (ne „asi“, „před“, „po“). */
function marriageDate(lines) {
  let best = null;
  for (const l of lines || []) {
    const r = parseFact(l);
    if (!r || r.t !== 'm' || r.approx || r.before) continue;
    if (r.exact) return r;
    best ??= r;
  }
  return best;
}
export function marriages() {
  const out = [];
  for (const f of Object.values(families)) {
    const fa = people[f.father], mo = people[f.mother];
    if (!fa || !mo || !ok(fa) || !ok(mo)) continue;
    out.push({ fam: f, date: marriageDate(f.marriage), father: fa, mother: mo });
  }
  return out;
}
export function ageAtMarriage() {
  const rows = { M: [], F: [] };
  for (const m of marriages()) {
    if (!m.date) continue;
    for (const [p, sex] of [[m.father, 'M'], [m.mother, 'F']]) {
      const ly = lifeYears(p);
      if (ly.b === null) continue;
      let age = m.date.y - ly.b;
      const ex = exactAge(fullBirth(p), m.date.y, m.date.m, m.date.d);
      if (ex !== null) age = ex;
      if (age >= 14 && age <= 80) rows[sex].push({ age, p });
    }
  }
  return rows;
}
export function weddingMonths() {
  const mon = Array(12).fill(0), wd = Array(7).fill(0), who = Array.from({ length: 12 }, () => []);
  const wdWho = Array.from({ length: 7 }, () => []);
  let n = 0;
  for (const m of marriages()) {
    if (!m.date || !m.date.m || !m.date.d) continue;
    mon[m.date.m - 1]++;
    who[m.date.m - 1].push(m.father.slug);
    const w = (new Date(m.date.y, m.date.m - 1, m.date.d).getDay() + 6) % 7;
    wd[w]++;
    wdWho[w].push(m.father.slug);
    n++;
  }
  return { n, mon, wd, who, wdWho };
}
export function spouseGap() {
  const gaps = [];
  for (const m of marriages()) {
    const a = lifeYears(m.father).b, b = lifeYears(m.mother).b;
    if (a !== null && b !== null) gaps.push({ gap: b - a, m });
  }
  return gaps;
}

// ---------- rodiče a děti ----------
export function parentAge() {
  const rows = { M: [], F: [] };
  for (const p of all) {
    if (!ok(p)) continue;
    const cb = lifeYears(p).b;
    if (cb === null) continue;
    for (const [par, sex] of [[people[p.father], 'M'], [people[p.mother], 'F']]) {
      if (!par) continue;
      const pb = lifeYears(par).b;
      if (pb === null) continue;
      const a = cb - pb;
      if (a >= 14 && a <= 70) rows[sex].push({ age: a, p: par });
    }
  }
  return rows;
}
/** Počet dětí z faktu „děti: Jan 1820, Marie 1822“ (počítají se jména s rokem; od dvou dětí výš). */
export function childrenCounts() {
  const rows = [];
  for (const p of all) {
    if (!ok(p)) continue;
    for (const f of p.facts) {
      const m = f.match(/děti[^:]*:\s*(.+)$/iu);
      if (!m) continue;
      const n = m[1].split(/,\s*/).filter((x) => /\d{4}/.test(x)).length;
      if (n >= 2) { rows.push({ n, p }); break; }
    }
  }
  return rows;
}

// ---------- délka života ----------
export function lifespans() {
  const rows = { M: [], F: [] };
  for (const p of all) {
    if (!ok(p)) continue;
    const ly = lifeYears(p);
    if (ly.b === null || ly.d === null || ly.d < ly.b) continue;
    rows[p.sex === 'F' ? 'F' : 'M'].push({ age: ly.d - ly.b, p });
  }
  return rows;
}

// ---------- jména ----------
/** Kolikrát syn dostal jméno po otci a dcera po matce (první křestní jméno). */
export function nameAfterParent() {
  let sons = 0, same = 0, daus = 0, sameD = 0;
  const first = (p) => firstNames(p)[0];
  for (const p of all) {
    if (!ok(p) || !first(p)) continue;
    const par = p.sex === 'F' ? people[p.mother] : people[p.father];
    if (!ok(par) || !first(par)) continue;
    if (p.sex === 'F') { daus++; if (first(par) === first(p)) sameD++; }
    else { sons++; if (first(par) === first(p)) same++; }
  }
  return { sons, same, daus, sameD };
}

// ---------- obce ----------
export function villages() {
  const rows = [];
  for (const pl of site.places) {
    if (pl.hypothesis) continue;
    const slugs = new Set(pl.lines.flatMap((l) => l.people).filter((s) => ok(people[s])));
    if (slugs.size) rows.push({ name: pl.name, n: slugs.size, years: pl.years, lines: pl.lines.length });
  }
  return rows.sort((a, b) => b.n - a.n);
}

// ---------- domy (jen pokud je v projektu stránka Domy – domy.json vyrábí tools/export_domy.py) ----------
const domyFile = import.meta.glob('../data/domy.json', { eager: true });
const domy = Object.values(domyFile)[0]?.default ?? [];
export const maDomy = domy.length > 0;
export function houses() {
  return domy.map((h) => {
    const ppl = Object.keys(h.people).map((s) => people[s]).filter(ok);
    const slugs = new Set(ppl.map((p) => p.slug));
    // dům zůstal v rodině: rodič i dítě s tímto číslem
    const inherited = ppl.filter((p) => slugs.has(p.father) || slugs.has(p.mother)).length;
    const ys = h.facts.filter((f) => slugs.has(f.person)).map((f) => f.year).filter(Boolean);
    return { h, n: ppl.length, inherited, from: Math.min(...ys), to: Math.max(...ys), span: ys.length ? Math.max(...ys) - Math.min(...ys) : 0 };
  });
}

// ---------- kolik předků známe ----------
export function knowledge(maxGen) {
  const rows = [];
  for (let g = 1; g <= maxGen; g++) {
    const row = { g, total: 2 ** g, doc: 0, prob: 0, fam: 0, mh: 0, unk: 0, twice: 0, missing: 0 };
    for (let k = 2 ** g; k < 2 ** (g + 1); k++) {
      const p = byK[k];
      if (!p) { row.missing++; continue; }
      if (p.k !== k) { row.twice++; continue; }
      row[['doc', 'prob', 'fam', 'mh'].includes(p.st) ? p.st : 'unk']++;
    }
    rows.push(row);
  }
  return rows;
}
