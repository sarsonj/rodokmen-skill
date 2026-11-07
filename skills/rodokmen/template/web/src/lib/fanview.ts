// Posun a přibližování vějíře předků (stránka /vejir/).
//
// Vějíř je jedno velké SVG se stovkami textů (část z nich po oblouku). Když se při každém pohybu mění viewBox celého
// SVG, prohlížeč přepočítává a kreslí tisíce prvků – to trvá 0,3–1 s a vějíř se seká.
//
// Hardwarová akcelerace funguje jako mapové aplikace – tři vrstvy nad sebou:
//   podklad  – kresba celého vějíře (SVG bez odkazových ploch) v malém rozlišení (BASE_W). Připraví se jednou po načtení
//              ve volné chvíli, kdy uživatel na vějíř nesahá (0,1–1 s práce; po pruzích to nejde – každý pruh stojí
//              skoro tolik co celek, prohlížeč pokaždé zpracuje celé SVG).
//   dlaždice – přesně viditelný výřez v rozlišení obrazovky, ostrý jako vektor při jakémkoli přiblížení. Kreslí se
//              po zastavení (10–100 ms). Při pohybu se nakreslená dlaždice jen posouvá a zvětšuje (CSS transform,
//              grafická karta) a okraje, které odkryje, na chvíli doplní podklad.
//   odkazy   – živé SVG, jehož kresba je jednou provždy vyřazená (display: none), takže zbydou jen průhledné odkazové
//              plochy (klepnutí na jméno, popisky, zvýraznění nalezeného). Těch je málo, takže jejich viewBox jede
//              s pohybem v každém snímku a jména jdou klepnout kdykoli.
// Než je podklad připravený (pár vteřin po načtení), funguje vějíř postaru přes viewBox celého SVG.
//
// Zapnutí: výchozí „auto“ zapne akceleraci jen u velkých vějířů (fanmath.ts, AUTO_MIN_TEXTS) – malý vějíř se
// překresluje rychle sám. Vynutit: v data/web.json  "vejir": { "akcelerace": true | false }, pro vyzkoušení
// v adrese ?akcelerace=1 / 0 / auto. Bez akcelerace se mění viewBox přímo (nejvýš jednou za snímek obrazovky).

import { type Box, type Size, bitmapTransform, clampSource, panned, tileSource, tileTransform, zoomed } from './fanmath';

export type { Box } from './fanmath';

const SETTLE_MS = 120;               // ms po posledním kroku kolečka / posunu (nebo změně velikosti) do ostré dlaždice
const BASE_W = 1024;                 // šířka podkladu v px – víc se nevyplácí: větší plátno se kreslí přes sekundu
                                     // a při prvním zobrazení se dlouho přenáší do grafické karty
const QUIET_MS = 400;                // příprava běží jen po takové chvíli bez pohybu
const LITE_CLASS = 'fan-lite';       // z živého SVG jen odkazové plochy (CSS v global.css)

/** Volná chvíle prohlížeče (Safari nemá requestIdleCallback). */
const idle = () => new Promise<void>((done) =>
  'requestIdleCallback' in window ? window.requestIdleCallback(() => done(), { timeout: 2000 }) : window.setTimeout(done, 50));
const sleep = (ms: number) => new Promise<void>((done) => window.setTimeout(done, ms));
const nextFrame = () => new Promise<void>((done) => requestAnimationFrame(() => requestAnimationFrame(() => done())));

/** Viditelnost vrstvy přes visibility, ne display: skrytá vrstva tak zůstane v grafické kartě a další pohyb
 *  nezačne jejím novým přenosem. */
const showLayer = (el: HTMLElement, on: boolean) => { el.style.visibility = on ? '' : 'hidden'; };

export class FanView {
  readonly home: Box;
  private vb: Box;
  private shown: Box;                // výřez, na který je nastavený viewBox živého SVG
  private art: HTMLImageElement | null = null;   // kresba vějíře jako obrázek (zdroj podkladu i dlaždic)
  private base: HTMLCanvasElement | null = null;
  private tile: HTMLCanvasElement;
  private tileVb: Box | null = null; // výřez, pro který je dlaždice nakreslená
  private moving = false;
  private area: Size;
  private origin: { left: number; top: number } | null = null;   // poloha plochy v okně, platí po dobu jednoho pohybu
  private raf = 0;
  private timer = 0;
  private lastGesture = 0;           // čas posledního kroku kolečka / posunu

  constructor(private stage: HTMLElement, private svg: SVGSVGElement, accelerate: boolean) {
    const v = svg.viewBox.baseVal;
    this.home = { x: v.x, y: v.y, w: v.width, h: v.height };
    this.vb = { ...this.home };
    this.shown = { ...this.home };
    this.tile = document.createElement('canvas');
    this.tile.className = 'fan-bitmap';
    const r = stage.getBoundingClientRect();
    this.area = { width: r.width, height: r.height };
    // velikost plochy se čte jen při změně; překreslí se jako po pohybu (při tažení okraje okna ne v každém snímku)
    new ResizeObserver(([e]) => {
      this.area = { width: e.contentRect.width, height: e.contentRect.height };
      this.schedule();
    }).observe(stage);
    if (accelerate) this.prepare().catch((err) => {
      console.warn('Vějíř: hardwarová akcelerace vypnuta, kresbu se nepodařilo připravit.', err);
    });
  }

  /** Přiblížit (f > 1) / oddálit (f < 1) kolem bodu v souřadnicích okna; bez bodu kolem středu. */
  zoomAt(f: number, clientX?: number, clientY?: number) {
    const o = this.measure();
    const px = clientX === undefined ? this.area.width / 2 : clientX - o.left;
    const py = clientY === undefined ? this.area.height / 2 : clientY - o.top;
    this.vb = zoomed(this.vb, this.home, this.area, f, px, py);
    this.schedule();
  }

  /** Posunout o dx, dy pixelů obrazovky. */
  panBy(dx: number, dy: number) {
    this.vb = panned(this.vb, this.area, dx, dy);
    this.schedule();
  }

  /** Nastavit výřez hned, bez animace (hledání, tlačítko Celý). */
  show(box: Box) {
    this.vb = { ...box };
    cancelAnimationFrame(this.raf);
    this.raf = 0;
    this.settle();
  }

  reset() { this.show(this.home); }

  // --- vnitřek ---

  /** Poloha plochy v okně (pro bod pod kurzorem). Čte se na začátku pohybu – plocha se mezi pohyby může posunout
   *  i beze změny velikosti (zalomení lišty nad ní), a to ResizeObserver nehlásí. Během pohybu se nemění. */
  private measure() {
    if (!this.origin) {
      const r = this.stage.getBoundingClientRect();
      this.origin = { left: r.left, top: r.top };
    }
    return this.origin;
  }

  private schedule() {
    this.lastGesture = performance.now();
    if (!this.raf) this.raf = requestAnimationFrame(() => { this.raf = 0; this.frame(); });
  }

  /** Jeden snímek pohybu: podklad a nakreslená dlaždice se jen přetransformují, odkazy dostanou nový viewBox. */
  private frame() {
    this.setViewBox(this.vb);   // bez akcelerace (nebo ještě nepřipraveno) to stačí – mění se celé SVG
    if (this.base) {
      this.base.style.transform = bitmapTransform(this.vb, this.home, this.area, this.base.width);
      if (this.tileVb) this.tile.style.transform = tileTransform(this.tileVb, this.vb, this.area);
      if (!this.moving) {
        this.moving = true;
        showLayer(this.base, true);
      }
    }
    clearTimeout(this.timer);
    this.timer = window.setTimeout(() => this.settle(), SETTLE_MS);
  }

  /** Klid: ostrá dlaždice přesně pro výřez. */
  private settle() {
    clearTimeout(this.timer);
    this.origin = null;
    this.setViewBox(this.vb);
    if (!this.base) return;
    try {
      this.drawTile();
    } catch (err) {   // plátno se nepovedlo (málo paměti): zpátky na obyčejné SVG, ať vějíř funguje dál
      console.warn('Vějíř: hardwarová akcelerace vypnuta, dlaždici se nepodařilo nakreslit.', err);
      this.disable();
      return;
    }
    // v jednom snímku: nová dlaždice na místě a podklad pryč (nic nebliká)
    this.tile.style.transform = '';
    showLayer(this.base, false);
    this.moving = false;
  }

  private drawTile() {
    const dpr = window.devicePixelRatio || 1;
    const W = Math.round(this.area.width * dpr), H = Math.round(this.area.height * dpr);
    if (!W || !H) return;
    if (this.tile.width !== W || this.tile.height !== H) { this.tile.width = W; this.tile.height = H; }
    this.tile.style.width = `${this.area.width}px`;    // vždy: přiblížení prohlížeče mění plochu i dpr naráz
    this.tile.style.height = `${this.area.height}px`;
    const ctx = this.tile.getContext('2d');
    if (!ctx) throw new Error('plátno dlaždice se nepodařilo vytvořit');
    ctx.clearRect(0, 0, W, H);
    // souřadnice SVG → pixely obrázku (obrázek má rozměr home.w × home.h, začíná v home.x, home.y)
    const src = tileSource(this.vb, this.area);
    const c = clampSource({ ...src, sx: src.sx - this.home.x, sy: src.sy - this.home.y }, this.home.w, this.home.h, W, H);
    if (c) ctx.drawImage(this.art!, c.sx, c.sy, c.sw, c.sh, c.dx, c.dy, c.dw, c.dh);   // SVG se kreslí jako vektor
    this.tileVb = { ...this.vb };
  }

  private setViewBox(v: Box) {
    if (v.x === this.shown.x && v.y === this.shown.y && v.w === this.shown.w && v.h === this.shown.h) return;
    this.svg.setAttribute('viewBox', `${v.x} ${v.y} ${v.w} ${v.h}`);
    this.shown = { ...v };
  }

  /** Vypnout akceleraci za běhu: vrátit kresbu živého SVG, plátna pryč. */
  private disable() {
    this.svg.classList.remove(LITE_CLASS);
    this.base?.remove();
    this.tile.remove();
    this.base = null;
    this.art = null;
    this.tileVb = null;
    this.moving = false;
  }

  /** Kresba jako obrázek a z ní podklad (ve volné chvíli); pak zapnutí akcelerace. */
  private async prepare() {
    const clone = this.svg.cloneNode(true) as SVGSVGElement;
    clone.setAttribute('viewBox', `${this.home.x} ${this.home.y} ${this.home.w} ${this.home.h}`);
    clone.setAttribute('width', String(this.home.w));
    clone.setAttribute('height', String(this.home.h));
    clone.removeAttribute('class');
    clone.querySelectorAll('.fan-links').forEach((g) => g.remove());   // odkazy a zvýraznění kreslí živé SVG
    await this.quiet();
    const art = await loadSvg(clone);
    const base = document.createElement('canvas');
    base.width = BASE_W;
    base.height = Math.round(BASE_W * this.home.h / this.home.w);
    const ctx = base.getContext('2d');
    if (!ctx) throw new Error('plátno podkladu se nepodařilo vytvořit (málo paměti)');
    await this.quiet();
    ctx.drawImage(art, 0, 0, base.width, base.height);
    base.className = 'fan-bitmap';
    base.style.opacity = '0';   // jednou neviditelně zobrazit: první zobrazení plátna ho přenáší do grafické karty
    this.stage.prepend(base);   // vrstvy odspodu: podklad, dlaždice, živé SVG s odkazy
    this.svg.before(this.tile);
    await this.quiet();
    await nextFrame();
    showLayer(base, false);
    base.style.opacity = '';
    // zapnout: kresba živého SVG se vyřadí (jednou provždy), vidět bude dlaždice
    this.art = art;
    this.base = base;
    this.svg.classList.add(LITE_CLASS);
    if (!this.moving) this.settle();
  }

  /** Počkat na volnou chvíli, kdy uživatel na vějíř chvíli nesahá. */
  private async quiet() {
    for (;;) {
      await idle();
      const wait = QUIET_MS - (performance.now() - this.lastGesture);
      if (wait <= 0) return;
      await sleep(wait);
    }
  }
}

/** SVG jako obrázek. onload, ne img.decode(): decode() u SVG v některých prohlížečích (starší WebKit) selže
 *  nebo skončí předčasně. Adresa blob: se neuvolňuje – obrázek se kreslí znovu při každé dlaždici. */
function loadSvg(svg: SVGSVGElement): Promise<HTMLImageElement> {
  const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)], { type: 'image/svg+xml' }));
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('SVG se nenačetlo jako obrázek')); };
    img.src = url;
  });
}
