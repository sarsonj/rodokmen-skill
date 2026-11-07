// Výpočty pro posun a přibližování vějíře (bez DOM, aby šly testovat: npm test).

export type Box = { x: number; y: number; w: number; h: number };
export type Size = { width: number; height: number };

export const MAX_ZOOM = 40;          // nejmenší výřez = 1/40 celého vějíře
export const MIN_ZOOM = 1 / 1.2;     // nejvíc oddálit na 120 % celého vějíře

const OFF = new Set(['false', '0', 'no', 'ne', 'off']);
const ON = new Set(['true', '1', 'yes', 'ano', 'on']);
/** Od kolika textů se akcelerace vyplatí. Malý vějíř (5–7 generací, desítky jmen) se překresluje rychle a bitmapy
 *  by jen zabraly paměť a čas při načtení; velký (stovky jmen, textů po oblouku) se bez ní seká. */
export const AUTO_MIN_TEXTS = 300;

/** Akcelerace zapnutá? Adresa ?akcelerace=0/1/auto má přednost před nastavením webu („vejir.akcelerace“ v web.json,
 *  do stránky jako text). true/1/ano/on = vždy, false/0/ne/off = nikdy, cokoli jiného (výchozí „auto“) = podle
 *  velikosti vějíře (počtu textů). */
export function accelerationEnabled(search: string, setting: string | undefined, texts: number): boolean {
  const q = new URLSearchParams(search).get('akcelerace');
  const v = String(q ?? setting ?? '').trim().toLowerCase();
  if (ON.has(v)) return true;
  if (OFF.has(v)) return false;
  return texts >= AUTO_MIN_TEXTS;
}

/** Měřítko (jednotek SVG na 1 px) a odsazení výřezu v ploše – jako SVG s preserveAspectRatio="xMidYMid meet". */
export function fit(v: Box, area: Size) {
  const s = Math.max(v.w / area.width, v.h / area.height);
  return { s, ox: (area.width - v.w / s) / 2, oy: (area.height - v.h / s) / 2 };
}

/** Bod plochy (px od levého horního rohu) → souřadnice SVG. */
export function toSvg(v: Box, area: Size, px: number, py: number) {
  const { s, ox, oy } = fit(v, area);
  return { x: v.x + (px - ox) * s, y: v.y + (py - oy) * s };
}

/** Výřez po přiblížení f-krát (f < 1 oddálí) kolem bodu plochy; zvětšení omezené na MIN_ZOOM..MAX_ZOOM vůči home. */
export function zoomed(v: Box, home: Box, area: Size, f: number, px: number, py: number): Box {
  const p = toSvg(v, area, px, py);
  const w = Math.min(home.w / MIN_ZOOM, Math.max(home.w / MAX_ZOOM, v.w / f));
  const k = w / v.w;
  return { x: p.x - (p.x - v.x) * k, y: p.y - (p.y - v.y) * k, w, h: v.h * k };
}

/** Výřez posunutý o dx, dy px plochy. */
export function panned(v: Box, area: Size, dx: number, dy: number): Box {
  const { s } = fit(v, area);
  return { ...v, x: v.x - dx * s, y: v.y - dy * s };
}

/** CSS transform, který bitmapu celého vějíře (šířka bw px) umístí do plochy jako výřez v. */
export function bitmapTransform(v: Box, home: Box, area: Size, bw: number): string {
  const { s, ox, oy } = fit(v, area);
  const k = home.w / (bw * s);   // CSS px na 1 px bitmapy
  return `translate(${(home.x - v.x) / s + ox}px, ${(home.y - v.y) / s + oy}px) scale(${k})`;
}

/** Krok kolečka → faktor přiblížení: úměrný deltě (touchpad posílá mnoho malých kroků, myš velké),
 *  jeden krok nejvýš ~2,2×. deltaMode 1 = řádky (Firefox), přepočet na px. */
export function wheelFactor(deltaY: number, deltaMode: number): number {
  const d = deltaMode === 1 ? deltaY * 33 : deltaY;
  return Math.exp(-Math.max(-300, Math.min(300, d)) * 0.0026);
}

/** Zdrojový obdélník (v souřadnicích SVG) pro vykreslení celé plochy při výřezu v – i s okraji, které výřez
 *  při jiném poměru stran nepokrývá (drawImage pak kreslí přesně to, co by ukázalo SVG). */
export function tileSource(v: Box, area: Size) {
  const { s, ox, oy } = fit(v, area);
  return { sx: v.x - ox * s, sy: v.y - oy * s, sw: area.width * s, sh: area.height * s };
}

/** CSS transform, který dlaždici vykreslenou pro výřez `drawn` (přes celou plochu) posune a zvětší na výřez v –
 *  při pohybu jede ostrá dlaždice s obrazem, okraje mimo ni doplní podkladová bitmapa. */
export function tileTransform(drawn: Box, v: Box, area: Size): string {
  const a = tileSource(drawn, area), b = tileSource(v, area);
  const sa = a.sw / area.width, sb = b.sw / area.width;   // jednotek SVG na 1 px
  return `translate(${(a.sx - b.sx) / sb}px, ${(a.sy - b.sy) / sb}px) scale(${sa / sb})`;
}

/** Zdrojový obdélník oříznutý na obrázek (0..imgW, 0..imgH) a k němu cílový obdélník: drawImage se zdrojem mimo
 *  obrázek (celý vějíř na široké ploše) některé prohlížeče nekreslí nebo hlásí chybu. Null = nic k nakreslení. */
export function clampSource(src: { sx: number; sy: number; sw: number; sh: number }, imgW: number, imgH: number,
                            dstW: number, dstH: number) {
  const kx = dstW / src.sw, ky = dstH / src.sh;   // cílových px na 1 px zdroje
  const x0 = Math.max(0, src.sx), y0 = Math.max(0, src.sy);
  const x1 = Math.min(imgW, src.sx + src.sw), y1 = Math.min(imgH, src.sy + src.sh);
  if (x1 <= x0 || y1 <= y0) return null;
  return { sx: x0, sy: y0, sw: x1 - x0, sh: y1 - y0,
           dx: (x0 - src.sx) * kx, dy: (y0 - src.sy) * ky, dw: (x1 - x0) * kx, dh: (y1 - y0) * ky };
}
