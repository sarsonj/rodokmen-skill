// Přihlašovací brána pro Cloudflare (Worker se statickými soubory). Soubor cloudflare/worker.js z této šablony
// vyrábí tools/export_web.py – ručně neupravovat. Odpověď na rodinnou otázku tu není, jen její otisk (SHA-256),
// který přihlašovací stránka uloží do cookie. wrangler.jsonc má run_worker_first: true, takže brána stojí
// před každým souborem webu (bez toho by Cloudflare vydával stránky a obrázky mimo bránu).
const HASH = '{{HASH}}';
const OTEVRENY = {{OTEVRENY}};
const ROBOTS = 'noindex, nofollow';

function cookie(request, nazev) {
  for (const cast of (request.headers.get('cookie') || '').split(';')) {
    const i = cast.indexOf('=');
    if (i > 0 && cast.slice(0, i).trim() === nazev) return cast.slice(i + 1).trim();
  }
  return null;
}

async function soubor(request, env, extra = {}) {
  const res = await env.ASSETS.fetch(request);
  const out = new Response(res.body, res);
  out.headers.set('X-Robots-Tag', ROBOTS);
  for (const [k, v] of Object.entries(extra)) out.headers.set(k, v);
  return out;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === '/prihlaseni' || url.pathname === '/prihlaseni.html') {
      return soubor(request, env, { 'Cache-Control': 'no-store' });
    }
    if (OTEVRENY || (HASH && cookie(request, 'rodokmen') === HASH)) return soubor(request, env);
    // Cloudflare vydává /prihlaseni.html jako /prihlaseni (přesměrování) – stránku si vezmeme rovnou.
    const login = await env.ASSETS.fetch(new Request(new URL('/prihlaseni', url)));
    return new Response(await login.text(), {
      status: 401,
      headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store', 'x-robots-tag': ROBOTS },
    });
  },
};
