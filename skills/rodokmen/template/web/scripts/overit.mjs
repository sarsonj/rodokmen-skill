// Kontrola po nasazení (`npm run nasadit` ji spouští na konci, ručně `node scripts/overit.mjs`):
// otevře web bez přihlášení jako cizí návštěvník a pozná, jestli ho chrání rodinná otázka.
// Nový web na Netlify bývá „Private“ (ochrana týmu) – rodina pak místo otázky vidí přihlášení k Netlify
// a majitel si toho nevšimne, protože je u Netlify přihlášený.
// Adresu a stav ochrany zjistí přes netlify-cli (web propojený v .netlify/state.json); --url <adresa> = jen otevřít adresu.
import { npxSync } from "./npx.mjs";
import { existsSync, readFileSync } from "node:fs";

const BRANA = /document\.cookie\s*=\s*'rodokmen=/;   // přihlašovací stránka (prihlaseni.html z tools/export_web.py)
// export vyrobí bránu Netlify jen s otázkou v nastavení; bránu Cloudflare vždy, u otevřeného webu s OTEVRENY = true
const maBranu = existsSync("netlify/edge-functions/brana.js") ||
  (existsSync("cloudflare/worker.js") && !/OTEVRENY = true/.test(readFileSync("cloudflare/worker.js", "utf8")));
const a = process.argv.slice(2);
let url = a[a.indexOf("--url") + 1] && a.includes("--url") ? a[a.indexOf("--url") + 1] : null;
let siteId = null;

function konec(kod, ...radky) {
  console.log(radky.join("\n"));
  process.exit(kod);
}

function ochranaTymu() {
  const id = siteId || "<site_id z web/.netlify/state.json>";
  konec(1,
    "CHYBA: web chrání přihlášení k Netlify (ochrana týmu, „Private“) – rodina místo rodinné otázky uvidí přihlášení k Netlify.",
    "Vypnutí (mění nastavení účtu uživatele – nejdřív se ho zeptej):",
    `  npx -y netlify-cli@latest api updateSite --data '{"site_id":"${id}","body":{"sso_login":false}}'`,
    "  (Windows PowerShell/cmd: JSON v uvozovkách \"…\" s \\\" uvnitř.)",
    "Nebo v administraci webu: Project configuration → Access & security → Visitor access → Project visibility →",
    "  Edit visibility → Public (Production i Deploy Preview) → Save. Web pak chrání rodinná otázka.",
    "Potom znovu: node scripts/overit.mjs");
}

if (!url && !existsSync(".netlify/state.json") && existsSync(".wrangler/adresa.txt")) {
  url = readFileSync(".wrangler/adresa.txt", "utf8").trim();   // uloží ji scripts/nasadit_cloudflare.mjs
}

if (!url) {
  try {
    siteId = JSON.parse(readFileSync(".netlify/state.json", "utf8")).siteId;
  } catch {}
  if (!siteId) {
    konec(0, "Kontrola přeskočena: složka není propojená s webem na Netlify (.netlify/state.json).",
      "Otevři adresu webu v anonymním okně – musí se ukázat rodinná otázka.");
  }
  const r = npxSync(["-y", "netlify-cli@latest", "api", "getSite", "--data", JSON.stringify({ site_id: siteId })],
    { encoding: "utf8" });
  let site = null;
  try {
    site = JSON.parse(r.stdout.slice(r.stdout.indexOf("{")));
  } catch {}
  if (!site) {
    konec(0, "Kontrola přeskočena: údaje o webu z Netlify nejdou načíst (netlify-cli api getSite).",
      "Otevři adresu webu v anonymním okně – musí se ukázat rodinná otázka.");
  }
  if (site.sso_login) ochranaTymu();
  url = site.ssl_url || site.url;
}

// Nová subdoména workers.dev se šíří několik minut. Kdyby se počítač zeptal moc brzy, zapamatuje si
// „neexistuje“ a web pak chvíli nevidí – proto nejdřív čekáme přes DNS Cloudflare (DoH), ne přes počítač.
async function cekejNaDns(host) {
  for (let i = 0; i < 36; i++) {
    try {
      const r = await fetch(`https://cloudflare-dns.com/dns-query?name=${host}&type=A`, { headers: { accept: "application/dns-json" } });
      if ((await r.json()).Answer?.length) return true;
    } catch {}
    if (i === 0) console.log("Čekám, až se nová adresa rozšíří (může trvat pár minut)…");
    await new Promise((ok) => setTimeout(ok, 5000));
  }
  return false;
}
const host = new URL(url).hostname;
if (host.endsWith(".workers.dev") && !(await cekejNaDns(host))) {
  konec(0, `Adresa ${url} se ještě šíří. Za pár minut ji otevři v anonymním okně nebo spusť: npm run overit`);
}

let res, text;
for (let pokus = 0; pokus < 3; pokus++) {   // hned po nasazení může web pár sekund chybět
  try {
    res = await fetch(url, { redirect: "manual", headers: { "cache-control": "no-cache" } });
    text = await res.text();
    if (res.status !== 404 || pokus === 2) break;
  } catch (e) {
    if (pokus === 2 && e.cause?.code === "ENOTFOUND" && host.endsWith(".workers.dev")) {
      konec(0, `Web je nahraný, ale tento počítač adresu ${url} ještě nezná (nová adresa se šíří).`,
        "Počítač nebo router si „neexistuje“ může pamatovat až 30 minut. Pak ji otevři v anonymním okně",
        "nebo spusť: npm run overit (hned to jde třeba v telefonu přes mobilní data).");
    }
    if (pokus === 2) konec(1, `CHYBA: web ${url} nejde otevřít (${e.cause?.code || e.message}).`);
  }
  await new Promise((ok) => setTimeout(ok, 5000));
}

const kam = res.headers.get("location") || "";
if (BRANA.test(text)) {
  konec(0, `V pořádku: ${url} bez přihlášení ukáže rodinnou otázku.`);
}
if ((res.status >= 300 && res.status < 400 && /netlify\.com/.test(kam)) ||
    ((res.status === 401 || res.status === 403) && /netlify|login/i.test(text))) {
  ochranaTymu();
}
if (res.status === 429) {
  konec(1, `CHYBA: ${url} vrátil 429 – vyčerpaný denní limit Cloudflare zdarma (100 000 požadavků, obnoví se o půlnoci UTC).`,
    "Brána web dál chrání, jen se teď nikdo nedostane dovnitř. Kdyby se to opakovalo, zvaž placený tarif nebo menší výřezy.");
}
if ((res.status === 403 || res.status === 503) && /cf-chl|challenge-platform|Just a moment/i.test(text)) {
  konec(1, `CHYBA: ${url} ukázal ověřovací stránku Cloudflare (ochrana proti robotům), ne rodinnou otázku.`,
    "Otevři adresu v anonymním okně prohlížeče. Safari s blokátorem obsahu ji zobrazí jako prázdnou stránku 403 –",
    "zkus jiný prohlížeč. Pokud se otázka v prohlížeči ukáže, je web v pořádku.");
}
if (res.status === 200) {
  if (maBranu) {
    konec(1, `CHYBA: ${url} se otevře bez rodinné otázky, ačkoli ji nastavení webu má.`,
      "Brána se nenasadila – nasazuj jen přes `npm run nasadit` / `npm run nasadit-cloudflare`, ne přetažením složky (Netlify Drop).");
  }
  konec(0, `Pozor: ${url} je bez přihlášení (v data/web.json není rodinná otázka) – vidí ho kdokoli.`);
}
konec(1, `CHYBA: ${url} vrátil nečekanou odpověď ${res.status}${kam ? " → " + kam : ""}. Otevři ho v anonymním okně a zkontroluj.`);
