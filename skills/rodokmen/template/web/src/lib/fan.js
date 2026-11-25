// Vějíř předků kreslený v prohlížeči – přepis tools/fan_chart.py (webová varianta), ale od libovolné osoby.
// Vstup: osoby jako {k, name, years, st, href}; rootK = Kekulého číslo osoby uprostřed (1 = výchozí osoba webu).
// Barvy zůstávají podle absolutního čísla (rod se pozná stejně jako ve velkém vějíři); prstence jsou relativní.

const RINGS = [[0, 240], [240, 440], [440, 650], [650, 880], [880, 1100], [1100, 1380],
  [1380, 1640], [1640, 1870], [1870, 2010], [2010, 2130], [2130, 2240]];   // jako tools/fan_chart.py
const R = RINGS[RINGS.length - 1][1];
const W = 2 * (R + 20), CX = R + 20, CY = R + 20;
const BASE = { 8: '#EFB45F', 9: '#F09A78', 10: '#E58AA6', 11: '#B99AE0', 12: '#86B8E8', 13: '#6FCBB9', 14: '#9CD17A', 15: '#D3D46A' };
const LIGHT = { 3: 0.0, 4: 0.18, 5: 0.32, 6: 0.44, 7: 0.55, 8: 0.64, 9: 0.72, 10: 0.78, 11: 0.82, 12: 0.85, 13: 0.87, 14: 0.89 };
const SIDE_COL = { 0: '#E9DFCF', 1: '#D6E2EC' };
const EMPTY = '#ECE8E0';
const MINF = { 5: 15, 6: 13, 7: 11, 8: 9.5, 9: 8.5, 10: 7.5 };
const MAXF = { 5: 26, 6: 22, 7: 18, 8: 14, 9: 11, 10: 9 };
const MAXG = RINGS.length - 1;

const gen = (k) => 31 - Math.clz32(k);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
const rad = (a) => (a * Math.PI) / 180;
const pt = (r, a) => [CX + r * Math.sin(rad(a)), CY - r * Math.cos(rad(a))];
const f1 = (n) => n.toFixed(1);

function mix(hex, t) {
  const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  return '#' + c.map((v) => Math.round(v + (255 - v) * t).toString(16).padStart(2, '0')).join('').toUpperCase();
}

function sector(r0, r1, a0, a1) {
  const large = a1 - a0 > 180 ? 1 : 0;
  const [x0, y0] = pt(r1, a0), [x1, y1] = pt(r1, a1), [x2, y2] = pt(r0, a1), [x3, y3] = pt(r0, a0);
  return `M${f1(x0)},${f1(y0)} A${r1},${r1} 0 ${large} 1 ${f1(x1)},${f1(y1)} L${f1(x2)},${f1(y2)} A${r0},${r0} 0 ${large} 0 ${f1(x3)},${f1(y3)} Z`;
}

/** Barva podle absolutního čísla předka (jako fan_chart.py). */
function fill(k, p) {
  const g = gen(k);
  if (!p || p.st === 'unk') return EMPTY;
  if (g === 0) return '#5B4A3A';
  if (g <= 2) return SIDE_COL[(k >> (g - 1)) & 1];
  const c = mix(BASE[k >> (g - 3)], LIGHT[Math.min(g, 14)] ?? 0.9);
  return p.st === 'prob' || p.st === 'mh' ? mix(c, 0.45) : c;
}

const fit = (text, avail, fmax, fmin) => Math.max(fmin, Math.min(fmax, avail / (0.56 * Math.max(text.length, 1))));

/**
 * @param {Record<number, {name:string, years:string, st:string, href:string}>} byK  osoby podle absolutního čísla
 * @param {number} rootK  osoba uprostřed
 * @param {Record<number,string>} lineNames  názvy rodů pro 3. prstenec (jen když rootK = 1)
 */
export function renderFan(byK, rootK = 1, lineNames = {}) {
  const g0 = gen(rootK);
  const rel = (k) => { const d = gen(k) - g0; return (1 << d) | (k - (rootK << d)); };
  const abs = (r) => { const d = gen(r); return (rootK << d) | (r - (1 << d)); };
  const known = Object.keys(byK).map(Number).filter((k) => k >= rootK && gen(k) - g0 <= MAXG && (k >> (gen(k) - g0)) === rootK);
  const slots = new Set(known.map(rel));
  for (const k of known) for (const c of [2 * k, 2 * k + 1]) if (gen(c) - g0 <= MAXG) slots.add(rel(c));
  const paths = [], defs = [], texts = [], links = [];
  for (const r of [...slots].sort((a, b) => a - b)) {
    const k = abs(r), g = gen(r), p = byK[k];
    const [r0, r1] = RINGS[g];
    const n = 1 << g, i = r - n, span = 360 / n;
    const [a0, a1] = g === 0 ? [0, 360] : [180 + i * span, 180 + (i + 1) * span];
    const col = g === 0 ? '#5B4A3A' : fill(k, p);
    paths.push(g === 0
      ? `<circle cx="${CX}" cy="${CY}" r="${r1}" fill="${p ? col : EMPTY}" stroke="#fff" stroke-width="3"/>`
      : `<path d="${sector(r0, r1, a0, a1)}" fill="${col}" stroke="#FBF8F2" stroke-width="${g < 6 ? 3 : 1.6}"/>`);
    if (!p) continue;
    const name = p.name, yrs = p.years || '', st = p.st;
    if (p.href) {
      const shape = g === 0 ? `<circle cx="${CX}" cy="${CY}" r="${r1}"/>` : `<path d="${sector(r0, r1, a0, a1)}"/>`;
      links.push(`<a href="${esc(p.href)}" data-k="${k}"><title>${esc(name)} ${esc(yrs)}</title>${shape}</a>`);
    }
    const style = st === 'unk' ? 'font-style="italic" fill="#8A8278"' : st === 'prob' || st === 'mh' ? 'font-style="italic" fill="#2B2620"' : 'fill="#1F1A15"';
    if (g === 0) {
      texts.push(`<text x="${CX}" y="${CY - 8}" text-anchor="middle" font-size="44" font-weight="700" fill="#FFF8EE">${esc(name)}</text>`);
      texts.push(`<text x="${CX}" y="${CY + 46}" text-anchor="middle" font-size="34" fill="#F1E3CF">${esc(yrs)}</text>`);
      continue;
    }
    const am = (a0 + a1) / 2, rm = (r0 + r1) / 2;
    if (g <= 4) {
      const lines = [];
      if (g === 3 && rootK === 1 && lineNames[k]) lines.push([lineNames[k].toUpperCase(), 21, 'font-weight="700" letter-spacing="4" fill="#5A4632"']);
      lines.push([name, { 1: 40, 2: 34, 3: 30, 4: 27 }[g], `font-weight="600" ${style}`]);
      if (yrs) lines.push([yrs, { 1: 30, 2: 27, 3: 24, 4: 22 }[g], style]);
      const gap = lines.map(([, s]) => s * 1.25), total = gap.reduce((a, b) => a + b, 0);
      const bottom = am % 360 > 90 && am % 360 < 270;
      let cur = rm + total / 2;
      let order = lines.map(([t, s, a], j) => { cur -= gap[j]; return [t, s, a, cur + gap[j] * 0.28]; });
      if (bottom) { const radii = order.map((o) => o[3]).reverse(); order = order.map(([t, s, a], j) => [t, s, a, radii[j] + s * 0.55]); }
      order.forEach(([t, s, a, rr], j) => {
        const pid = `fp${k}_${j}`, pad = Math.min(3, (a1 - a0) * 0.04), b0 = a0 + pad, b1 = a1 - pad;
        s = Math.min(s, (rad(b1 - b0) * rr) / (0.56 * Math.max(t.length, 1)));
        const lg = b1 - b0 > 180 ? 1 : 0;
        const [xa, ya] = pt(rr, bottom ? b1 : b0), [xb, yb] = pt(rr, bottom ? b0 : b1);
        defs.push(`<path id="${pid}" d="M${f1(xa)},${f1(ya)} A${f1(rr)},${f1(rr)} 0 ${lg} ${bottom ? 0 : 1} ${f1(xb)},${f1(yb)}" fill="none"/>`);
        texts.push(`<text font-size="${f1(s)}" ${a}><textPath href="#${pid}" startOffset="50%" text-anchor="middle">${esc(t)}</textPath></text>`);
      });
    } else {
      const depth = r1 - r0 - 22, arc = rad(a1 - a0) * rm;
      let fa = fit(name, depth, MAXF[g], MINF[g]);
      const fb = yrs ? fit(yrs, depth, MAXF[g] * 0.85, MINF[g] * 0.9) : 0;
      const two = yrs && arc >= (fa + fb) * 1.15;
      if (!two) fa = Math.min(fa, arc / 1.25);
      const rot = am % 360 < 180 ? am - 90 : am + 90;
      const [x, y] = pt(rm, am);
      const tw = `transform="translate(${f1(x)},${f1(y)}) rotate(${rot.toFixed(2)})"`;
      if (two) {
        const h = (fa + fb) * 1.08;
        texts.push(`<g ${tw}><text y="${f1(-h / 2 + fa * 0.85)}" text-anchor="middle" font-size="${f1(fa)}" font-weight="600" ${style}>${esc(name)}</text><text y="${f1(h / 2 - fb * 0.15)}" text-anchor="middle" font-size="${f1(fb)}" ${style}>${esc(yrs)}</text></g>`);
      } else {
        texts.push(`<g ${tw}><text y="${f1(fa * 0.35)}" text-anchor="middle" font-size="${f1(fa)}" font-weight="600" ${style}>${esc(name)}</text></g>`);
      }
    }
  }
  // výřez jen na obsazené prstence (vějíř od mladší osoby by jinak byl malý uprostřed)
  const maxG = Math.max(0, ...[...slots].map(gen));
  const rr = RINGS[maxG][1] + 30;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${CX - rr} ${CY - rr} ${2 * rr} ${2 * rr}" font-family="Helvetica Neue, Helvetica, Arial, sans-serif" class="fan">`
    + `<defs>${defs.join('')}</defs>${paths.join('')}${texts.join('')}<g class="fan-links">${links.join('')}</g></svg>`;
}
