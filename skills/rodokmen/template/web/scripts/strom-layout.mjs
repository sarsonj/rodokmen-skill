// Layout of the whole family graph for the page /strom/ (Strom).
// Reads src/generated/strom.json (from strom.py), lays it out with Graphviz dot (WebAssembly, runs in Node at build time)
// and writes src/generated/strom_layout.json: card centres in px and family junctions (couple -> children).
//
// Couples are laid out as one unit (a record node with one field per person: husband, wife, a second wife…), so
// spouses always sit side by side. Edges go from the parents' unit to the child's field.
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { Graphviz } from "@hpcc-js/wasm-graphviz";

const IN = fileURLToPath(new URL("../src/generated/strom.json", import.meta.url));
const OUT = fileURLToPath(new URL("../src/generated/strom_layout.json", import.meta.url));
const CARD = { w: 210, h: 66 };            // px, must match the card size in strom.astro
const GAP = 22;                           // px between spouses inside a unit
const DPI = 72;

const data = JSON.parse(readFileSync(IN, "utf8"));
const q = (s) => '"' + String(s).replace(/"/g, '\\"') + '"';

// Lays out one variant of the graph (all people, or the direct line only).
function compute(nodes, graphviz) {
const isAnc = (id) => !!nodes[id].page;
// the starting person and their siblings count as one family: same edge weights, so siblings sit side by side under the parents
const own = new Set([data.root, ...(nodes[data.root]?.parents ?? []).flatMap((p) => nodes[p]?.children ?? [])]);
const isMain = (id) => isAnc(id) || own.has(id);

// --- units: connected components of the spouse relation, ordered as a chain (wife – husband – second wife) ---------
const unitOf = {}, units = [];
for (const id of Object.keys(nodes)) {
  if (unitOf[id] !== undefined) continue;
  const comp = [], stack = [id];
  while (stack.length) {
    const x = stack.pop();
    if (comp.includes(x)) continue;
    comp.push(x);
    for (const s of nodes[x].spouses) if (nodes[s]) stack.push(s);
  }
  let order;
  if (comp.length === 1) order = comp;
  else if (comp.length === 2) order = comp.sort((a, b) => (nodes[a].sex === "M" ? 0 : 1) - (nodes[b].sex === "M" ? 0 : 1));
  else {
    // a chain: start at an end (a person with one spouse), prefer the end whose partner keeps an ancestor on the left
    const ends = comp.filter((x) => nodes[x].spouses.filter((s) => comp.includes(s)).length === 1);
    let start = ends.find((e) => !isAnc(e)) ?? ends[0] ?? comp[0];   // a second spouse goes on the outer side
    order = [start];
    while (order.length < comp.length) {
      const next = nodes[order.at(-1)].spouses.find((s) => comp.includes(s) && !order.includes(s));
      if (!next) { order.push(...comp.filter((x) => !order.includes(x))); break; }
      order.push(next);
    }
  }
  const u = { id: "u" + units.length, members: order };
  order.forEach((m) => (unitOf[m] = units.length));
  units.push(u);
}

// --- families: distinct parent sets of children, plus childless couples ------------------------------------------
const fams = new Map();
const famOf = (parents) => {
  const key = [...parents].sort().join("|");
  if (!fams.has(key)) fams.set(key, { id: "f" + fams.size, parents, children: [] });
  return fams.get(key);
};
for (const n of Object.values(nodes)) if (n.parents.length) famOf(n.parents.slice(0, 2)).children.push(n.id);
for (const n of Object.values(nodes)) for (const s of n.spouses) famOf([n.id, s]);

// --- generations and left-to-right order ---------------------------------------------------------------------------
// Ancestors by their Kekulé number (father's side left, mother's right), side relatives next to their anchor:
// siblings of a man to the left of his couple, of a woman to the right, children under their parents.
const gen = {}, frac = {};
const byBirth = (a, b) => (parseInt((nodes[a].years.match(/\d{4}/) || ["9999"])[0]) - parseInt((nodes[b].years.match(/\d{4}/) || ["9999"])[0]));
for (const n of Object.values(nodes)) {
  if (!n.k) continue;
  const g = Math.floor(Math.log2(n.k));
  gen[n.id] = g;
  frac[n.id] = (n.k - 2 ** g + 0.5) / 2 ** g;
}
for (let changed = true; changed; ) {
  changed = false;
  for (const n of Object.values(nodes)) {
    if (gen[n.id] !== undefined) continue;
    const sp = n.spouses.find((s) => gen[s] !== undefined);
    const sibs = [...new Set(n.parents.flatMap((p) => nodes[p]?.children ?? []))];
    const anc = sibs.find((c) => c !== n.id && nodes[c].k && gen[c] !== undefined);
    const par = n.parents.find((p) => gen[p] !== undefined);
    const ch = n.children.find((c) => gen[c] !== undefined);
    if (sp) { gen[n.id] = gen[sp]; frac[n.id] = frac[sp]; }
    else if (anc) {
      const g = gen[anc], side = sibs.filter((c) => !nodes[c].k).sort(byBirth), i = side.indexOf(n.id);
      // tiny offsets: the sibling stays right next to its anchor, so whole side branches keep together
      gen[n.id] = g;
      frac[n.id] = nodes[anc].k % 2 === 0
        ? frac[anc] - 1e-3 * (side.length - i) / (side.length + 1)
        : frac[anc] + 1e-3 * (i + 1) / (side.length + 1);
    } else if (par) {
      const kids = nodes[par].children.slice().sort(byBirth);
      gen[n.id] = gen[par] - 1;
      frac[n.id] = frac[par] + 1e-6 * kids.indexOf(n.id);
    } else if (ch) { gen[n.id] = gen[ch] + 1; frac[n.id] = frac[ch]; }
    else continue;
    changed = true;
  }
}
const ufrac = (u) => {
  const a = u.members.filter((m) => nodes[m].k);
  const ms = a.length ? a : u.members;
  return ms.reduce((t, m) => t + (frac[m] ?? 0.5), 0) / ms.length;
};
const ugen = (u) => gen[u.members.find((m) => nodes[m].k) ?? u.members[0]] ?? 0;
const rows = new Map();
for (const u of units) {
  const g = ugen(u);
  if (!rows.has(g)) rows.set(g, []);
  rows.get(g).push(u);
}
for (const r of rows.values()) r.sort((a, b) => ufrac(a) - ufrac(b));

// --- dot graph ------------------------------------------------------------------------------------------------------
const fieldW = CARD.w + GAP;
const lines = [
  "digraph G {",
  `graph [rankdir=TB, nodesep=0.3, ranksep=0.85, splines=false, newrank=true];`,
  `node [shape=record, fixedsize=true, height=${CARD.h / DPI}];`,
  `edge [arrowhead=none];`,
];
for (const u of units) {
  const label = u.members.map((_, i) => `<p${i}>`).join("|");
  lines.push(`${q(u.id)} [label=${q(label)}, width=${(u.members.length * fieldW) / DPI}];`);
}
const port = (id) => `${q(units[unitOf[id]].id)}:p${units[unitOf[id]].members.indexOf(id)}`;
for (const f of fams.values()) {
  const ps = f.parents.filter((p) => nodes[p]);
  if (!ps.length) continue;
  const pu = units[unitOf[ps[0]]];
  // tail: the unit's bottom centre for a plain couple, otherwise the parent's own field
  const tail = ps.length === 2 && pu.members.length === 2 ? `${q(pu.id)}:s` : `${port(ps[0])}:s`;
  for (const c of f.children) {
    const w = isMain(c) && ps.every(isMain) ? 60 : 4;
    lines.push(`${tail} -> ${port(c)}:n [weight=${w}];`);
  }
}
for (const r of rows.values()) {
  if (r.length > 1) lines.push(`{ rank=same; ${r.map((u) => q(u.id)).join(" -> ")} [style=invis, weight=1]; }`);
  else lines.push(`{ rank=same; ${q(r[0].id)}; }`);
}
lines.push("}");

const plain = graphviz.layout(lines.join("\n"), "plain", "dot");

let height = 0, width = 0;
const upos = {};
for (const line of plain.split("\n")) {
  const g = line.match(/^graph \S+ (\S+) (\S+)/);
  if (g) { width = +g[1] * DPI; height = +g[2] * DPI; continue; }
  const m = line.match(/^node ("(?:[^"\\]|\\.)*"|\S+) (\S+) (\S+) (\S+)/);
  if (m) {
    const name = m[1].startsWith('"') ? m[1].slice(1, -1) : m[1];
    upos[name] = { x: +m[2] * DPI, y: height - +m[3] * DPI, w: +m[4] * DPI };
  }
}

const pos = {};
for (const u of units) {
  const p = upos[u.id];
  const left = p.x - (u.members.length * fieldW) / 2;
  u.members.forEach((m, i) => (pos[m] = { x: Math.round(left + (i + 0.5) * fieldW), y: Math.round(p.y) }));
}
const famsOut = [...fams.values()].map((f) => {
  const ps = f.parents.filter((p) => pos[p]);
  const j = ps.length === 2 ? { x: Math.round((pos[ps[0]].x + pos[ps[1]].x) / 2), y: pos[ps[0]].y } : { x: null, y: null };
  return { ...f, parents: ps, ...j };
});

console.log(`strom_layout.json: ${Object.keys(nodes).length} osob, ${units.length} jednotek, ${fams.size} rodin, ${Math.round(width)}×${Math.round(height)} px`);
return { width: Math.round(width), height: Math.round(height), pos, fams: famsOut };
}

// Direct line only: ancestors plus the siblings of the starting person (own family), relations restricted to them.
function directLine(nodes, root) {
  const keep = new Set(Object.keys(nodes).filter((id) => nodes[id].page));
  for (const p of nodes[root]?.parents ?? []) for (const c of nodes[p]?.children ?? []) keep.add(c);
  const only = (ids) => ids.filter((i) => keep.has(i));
  return Object.fromEntries([...keep].map((id) => [id, { ...nodes[id], parents: only(nodes[id].parents),
    spouses: only(nodes[id].spouses), children: only(nodes[id].children) }]));
}

const graphviz = await Graphviz.load();
const full = compute(data.nodes, graphviz);
const core = compute(directLine(data.nodes, data.root), graphviz);
writeFileSync(OUT, JSON.stringify({ card: CARD, root: data.root, full, core }));
