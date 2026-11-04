// Přihlašovací brána pro Netlify (Edge Function). Soubor edge-functions/brana.js z této šablony
// vyrábí tools/export_web.py – ručně neupravovat. Na web se dostane, kdo má v cookie „rodokmen“ buď otisk
// odpovědi na rodinnou otázku (uloží ho přihlašovací stránka), nebo klíč z osobního odkazu /?k=<klíč>
// (tools/pozvanky.py). Tady jsou jen otisky (SHA-256), ne odpověď ani klíče. Klíč z odkazu brána uloží do cookie
// (HttpOnly) a přesměruje na adresu bez něj. Zrušený odkaz přestane platit po dalším nasazení, i ve starých cookie.
// otisk odpovědi (prázdný = otázka vypnutá) a otisky klíčů z osobních odkazů
const HASH = '{{HASH}}';
const OTISKY = new Set({{OTISKY}});
const ROBOTS = 'noindex, nofollow';
// Neplatnou cookie smazat: zrušený klíč je v cookie HttpOnly a tu by odpověď na otázku z přihlašovací stránky nepřepsala.
const SMAZAT = 'rodokmen=; Max-Age=0; Path=/; HttpOnly; Secure; SameSite=Lax';

async function platnyKlic(klic) {
  if (!klic || OTISKY.size === 0) return false;
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(klic));
  return OTISKY.has(Array.from(new Uint8Array(buf), (b) => b.toString(16).padStart(2, '0')).join(''));
}

async function platnaCookie(cookie) {
  if (!cookie) return false;
  return (HASH !== '' && cookie === HASH) || platnyKlic(cookie);
}

function bezKlice(url) {
  const cil = new URL(url);
  cil.searchParams.delete('k');
  // úvodní lomítka sloučit: z adresy „https://web//cizi.web/?k=…“ by jinak „//cizi.web/“ přesměrovalo na cizí web
  return cil.pathname.replace(/^[\/\\]+/, '/') + cil.search;
}

export default async (request, context) => {
  const url = new URL(request.url);
  const cookie = context.cookies.get('rodokmen');
  const cookieOk = await platnaCookie(cookie);
  if (url.pathname === '/prihlaseni.html') {
    const res = await context.next();
    if (cookie && !cookieOk) res.headers.append('set-cookie', SMAZAT);
    return res;
  }

  if (url.searchParams.has('k')) {
    const klic = url.searchParams.get('k');
    const headers = { location: bezKlice(url), 'cache-control': 'no-store', 'referrer-policy': 'no-referrer', 'x-robots-tag': ROBOTS };
    if (await platnyKlic(klic)) {
      headers['set-cookie'] = `rodokmen=${klic}; Max-Age=31536000; Path=/; HttpOnly; Secure; SameSite=Lax`;
      return new Response(null, { status: 302, headers });
    }
    if (cookieOk) return new Response(null, { status: 302, headers });   // starý odkaz, ale člověk už má platnou cookie
  } else if (cookieOk) {
    const res = await context.next();
    res.headers.set('X-Robots-Tag', ROBOTS);
    return res;
  }

  // Přihlašovací stránka pozná neplatný odkaz podle parametru k v adrese.
  const login = await fetch(new URL('/prihlaseni.html', url));
  const headers = { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store', 'referrer-policy': 'no-referrer', 'x-robots-tag': ROBOTS };
  if (cookie) headers['set-cookie'] = SMAZAT;
  return new Response(await login.text(), { status: 401, headers });
};

export const config = { path: '/*' };
