// Testy výpočtů vějíře: npm test  (Node ≥ 22.18 spouští TypeScript přímo)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  accelerationEnabled, AUTO_MIN_TEXTS, bitmapTransform, clampSource, fit, MAX_ZOOM, MIN_ZOOM, panned, tileSource, tileTransform,
  toSvg, wheelFactor, zoomed,
} from './fanmath.ts';

const home = { x: 0, y: 0, w: 4880, h: 4880 };
const wide = { width: 1600, height: 800 };   // širší než vysoká plocha – vějíř je na výšku, po stranách okraj
const close = (a: number, b: number, eps = 1e-6) => assert.ok(Math.abs(a - b) < eps, `${a} ≠ ${b}`);

test('přepínač akcelerace: adresa má přednost, pak nastavení webu, jinak podle velikosti vějíře', () => {
  const big = AUTO_MIN_TEXTS, small = 60;   // 60 textů ≈ vějíř s 5 generacemi
  assert.equal(accelerationEnabled('', undefined, big), true);
  assert.equal(accelerationEnabled('', undefined, small), false);
  assert.equal(accelerationEnabled('', 'auto', small), false);
  assert.equal(accelerationEnabled('', 'true', small), true);
  assert.equal(accelerationEnabled('', 'false', big), false);
  for (const off of ['0', 'ne', 'off', 'False', ' no ']) assert.equal(accelerationEnabled('', off, big), false, off);
  assert.equal(accelerationEnabled('?akcelerace=1', 'false', small), true);
  assert.equal(accelerationEnabled('?akcelerace=0', 'true', big), false);
  assert.equal(accelerationEnabled('?akcelerace=auto', 'true', small), false);
  assert.equal(accelerationEnabled('?akcelerace=nesmysl', 'true', small), false);   // neznámá hodnota = auto
});

test('fit centruje výřez jako preserveAspectRatio meet', () => {
  const { s, ox, oy } = fit(home, wide);
  close(s, 4880 / 800);
  close(oy, 0);
  close(ox, (1600 - 800) / 2);
});

test('toSvg: střed plochy je střed výřezu, okraj vějíře je okraj výřezu', () => {
  const c = toSvg(home, wide, 800, 400);
  close(c.x, 2440); close(c.y, 2440);
  const leftEdge = toSvg(home, wide, 400, 0);
  close(leftEdge.x, 0); close(leftEdge.y, 0);
});

test('přiblížení drží bod pod kurzorem na místě', () => {
  const px = 1100, py = 300;
  const before = toSvg(home, wide, px, py);
  const v = zoomed(home, home, wide, 2, px, py);
  const after = toSvg(v, wide, px, py);
  close(after.x, before.x, 1e-6); close(after.y, before.y, 1e-6);
  close(v.w, home.w / 2);
});

test('přiblížení a oddálení jsou omezené', () => {
  let v = home;
  for (let i = 0; i < 100; i++) v = zoomed(v, home, wide, 2, 800, 400);
  close(v.w, home.w / MAX_ZOOM);
  for (let i = 0; i < 100; i++) v = zoomed(v, home, wide, 0.5, 800, 400);
  close(v.w, home.w / MIN_ZOOM);
});

test('posun o N px posune výřez o N px v měřítku', () => {
  const v = panned(home, wide, 100, -50);
  const { s } = fit(home, wide);
  close(v.x, -100 * s); close(v.y, 50 * s); close(v.w, home.w);
});

test('transformace bitmapy: celý vějíř v celé ploše', () => {
  const t = bitmapTransform(home, home, wide, 4096);
  const m = /translate\(([-\d.e]+)px, ([-\d.e]+)px\) scale\(([-\d.e]+)\)/.exec(t);
  assert.ok(m, t);
  close(Number(m![1]), 400); close(Number(m![2]), 0); close(Number(m![3]), 800 / 4096);
});

test('kolečko: směr, symetrie a omezení kroku', () => {
  assert.ok(wheelFactor(-100, 0) > 1);
  assert.ok(wheelFactor(100, 0) < 1);
  close(wheelFactor(-100, 0) * wheelFactor(100, 0), 1);
  close(wheelFactor(-3, 1), wheelFactor(-99, 0));
  close(wheelFactor(-10000, 0), wheelFactor(-300, 0));
});

test('dlaždice klidového stavu pokrývá celou plochu včetně okrajů', () => {
  const t = tileSource(home, wide);
  close(t.sh, 4880); close(t.sw, 9760); close(t.sx, -2440); close(t.sy, 0);
  const v = zoomed(home, home, wide, 8, 300, 200);
  const z = tileSource(v, wide);
  const corner = toSvg(v, wide, 0, 0);
  close(z.sx, corner.x); close(z.sy, corner.y);
});

test('dlaždice při pohybu: bez změny výřezu žádný posun, po posunu o N px posun o N px', () => {
  const m = (t: string) => /translate\(([-\d.e]+)px, ([-\d.e]+)px\) scale\(([-\d.e]+)\)/.exec(t)!.slice(1).map(Number);
  const [x0, y0, k0] = m(tileTransform(home, home, wide));
  close(x0, 0); close(y0, 0); close(k0, 1);
  const [x1, y1, k1] = m(tileTransform(home, panned(home, wide, 120, -30), wide));
  close(x1, 120); close(y1, -30); close(k1, 1);
  const z = zoomed(home, home, wide, 2, 800, 400);   // 2× kolem středu: dlaždice 2× větší, střed na místě
  const [x2, y2, k2] = m(tileTransform(home, z, wide));
  close(k2, 2); close(800 * k2 + x2, 800); close(400 * k2 + y2, 400);
});

test('oříznutí zdroje dlaždice na obrázek', () => {
  // celý vějíř 4880×4880 na ploše 2× širší: zdroj −2440..7320, cíl 1600 px → obrázek padne doprostřed
  const c = clampSource({ sx: -2440, sy: 0, sw: 9760, sh: 4880 }, 4880, 4880, 1600, 800)!;
  close(c.sx, 0); close(c.sw, 4880); close(c.dx, 400); close(c.dw, 800); close(c.dy, 0); close(c.dh, 800);
  const inside = clampSource({ sx: 100, sy: 200, sw: 300, sh: 150 }, 4880, 4880, 600, 300)!;
  close(inside.sx, 100); close(inside.dx, 0); close(inside.dw, 600);
  assert.equal(clampSource({ sx: 5000, sy: 0, sw: 100, sh: 100 }, 4880, 4880, 100, 100), null);
});
