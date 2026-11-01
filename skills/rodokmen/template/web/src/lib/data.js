// Data exported from the research repo by tools/export_web.py (re-run `npm run data` after changes).
import site from '../data/site.json';

export const { people, families, lines, stats, issues, hypotheses, docs, config } = site;
/** Osoby mimo přímou linii (data/osoby.py RODINA) pro stromový graf. */
export const others = site.others ?? [];
/** Počet rodů slovem pro nadpisy („Osm rodů“). */
export const linesTitle = (n) => (['Žádný rod', 'Jeden rod', 'Dva rody', 'Tři rody', 'Čtyři rody', 'Pět rodů', 'Šest rodů', 'Sedm rodů', 'Osm rodů'][n] ?? `${n} rodů`);
export const root = people[site.root];
export const records = Object.fromEntries(site.records.map((r) => [r.key, r]));
export const recordList = site.records;
export const byK = Object.fromEntries([
  ...Object.values(people).map((p) => [p.k, p]),
  ...Object.entries(site.aliases ?? {}).map(([k, slug]) => [Number(k), people[slug]]),
]);
export const lineByK = Object.fromEntries(Object.values(lines).map((l) => [l.k, l]));

export const href = {
  person: (slug) => `/osoba/${slug}/`,
  family: (id) => `/rodina/${id}/`,
  line: (slug) => `/rod/${slug}/`,
  record: (key) => `/zdroj/${key}/`,
};

/** Sortable number from dates like "12. 5. 1811", "3/1867", "12/1790", "1797". */
export function dateKey(date) {
  const y = (date.match(/\d{4}/) || ['9999'])[0];
  const parts = date.replace(y, '').match(/\d+/g) || [];
  const [d, m] = parts.length >= 2 ? [parts[0], parts[1]] : [0, parts[0] || 0];
  return Number(y) * 10000 + Number(m) * 100 + Number(d);
}

export const genName = (g) =>
  ['výchozí osoba', 'rodiče', 'prarodiče', 'praprarodiče'][g] ?? `${g}. generace (${'pra'.repeat(g - 1)}rodiče)`;

export const statusClass = (st) => ({ doc: 'st-doc', prob: 'st-prob', fam: 'st-fam', mh: 'st-mh' })[st] ?? 'st-unk';
