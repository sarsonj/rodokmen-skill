// Kontrola po nasazení (`npm run nasadit` ji spouští na konci, ručně `node scripts/overit.mjs`):
// otevře web bez přihlášení jako cizí návštěvník a pozná, jestli ho chrání rodinná otázka.
// Nový web na Netlify bývá „Private“ (ochrana týmu) – rodina pak místo otázky vidí přihlášení k Netlify
// a majitel si toho nevšimne, protože je u Netlify přihlášený.
// Adresu a stav ochrany zjistí přes netlify-cli (web propojený v .netlify/state.json); --url <adresa> = jen otevřít adresu.
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";

const BRANA = /document\.cookie\s*=\s*'rodokmen=/;   // přihlašovací stránka (prihlaseni.html z tools/export_web.py)
const maBranu = existsSync("netlify/edge-functions/brana.js");   // export ji vyrobí, jen když je v nastavení otázka
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

if (!url) {
  try {
    siteId = JSON.parse(readFileSync(".netlify/state.json", "utf8")).siteId;
  } catch {}
  if (!siteId) {
    konec(0, "Kontrola přeskočena: složka není propojená s webem na Netlify (.netlify/state.json).",
      "Otevři adresu webu v anonymním okně – musí se ukázat rodinná otázka.");
  }
  const r = spawnSync("npx", ["-y", "netlify-cli@latest", "api", "getSite", "--data", JSON.stringify({ site_id: siteId })],
    { encoding: "utf8", shell: process.platform === "win32" });
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

let res, text;
for (let pokus = 0; pokus < 3; pokus++) {   // hned po nasazení může web pár sekund chybět
  try {
    res = await fetch(url, { redirect: "manual", headers: { "cache-control": "no-cache" } });
    text = await res.text();
    if (res.status !== 404 || pokus === 2) break;
  } catch (e) {
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
if (res.status === 200) {
  if (maBranu) {
    konec(1, `CHYBA: ${url} se otevře bez rodinné otázky, ačkoli ji nastavení webu má.`,
      "Brána (Edge Function) se nenasadila – nasazuj jen přes `npm run nasadit`, ne přetažením složky (Netlify Drop).");
  }
  konec(0, `Pozor: ${url} je bez přihlášení (v data/web.json není rodinná otázka) – vidí ho kdokoli.`);
}
konec(1, `CHYBA: ${url} vrátil nečekanou odpověď ${res.status}${kam ? " → " + kam : ""}. Otevři ho v anonymním okně a zkontroluj.`);
