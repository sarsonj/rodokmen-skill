// Nahrání hotového webu (dist/) na Cloudflare – spouští ho `npm run nasadit-cloudflare` po exportu a buildu.
// wrangler.jsonc a bránu cloudflare/worker.js vyrábí tools/export_web.py. Po nahrání spustí kontrolu
// scripts/overit.mjs na adrese, kterou wrangler vypíše (https://rodokmen.<subdoména>.workers.dev).
//
// Subdoména workers.dev: nový účet ji nemá. Wrangler spuštěný z Claude ji zaregistruje sám, název ale bere
// z package.json (u všech „rodokmen-web“ – obsazené). Proto ho spouštíme ze složky .wrangler/subdomena,
// kde package.json nese název z data/web.json (cloudflare.nazev); když je obsazený, zkusíme ho s číslem.
import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

if (!existsSync("wrangler.jsonc") || !existsSync("cloudflare/worker.js")) {
  console.error("CHYBA: chybí wrangler.jsonc nebo cloudflare/worker.js – spusť `npm run nasadit-cloudflare` (vyrobí je export).");
  process.exit(1);
}

function slug(t) {
  return String(t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 50).replace(/-+$/, "");
}

let web = {};
try {
  web = JSON.parse(readFileSync("../data/web.json", "utf8"));
} catch {}
const zaklad = slug(web.cloudflare?.nazev) || slug(web.nazev) || "rodokmen";
const navrhy = [zaklad, ...[0, 1, 2].map(() => `${zaklad}-${Math.floor(1000 + Math.random() * 9000)}`)];

const win = process.platform === "win32";
const config = resolve("wrangler.jsonc");

function nasad(subdomena) {
  const slozka = resolve(".wrangler", "subdomena");
  mkdirSync(slozka, { recursive: true });
  writeFileSync(resolve(slozka, "package.json"), JSON.stringify({ name: subdomena, private: true }) + "\n");
  return new Promise((hotovo) => {
    let text = "";
    const p = spawn("npx", ["-y", "wrangler@4", "deploy", "--config", config],
      { cwd: slozka, shell: win, stdio: ["inherit", "pipe", "pipe"] });
    p.stdout.on("data", (d) => { process.stdout.write(d); text += d; });
    p.stderr.on("data", (d) => { process.stderr.write(d); text += d; });
    p.on("close", (kod) => hotovo({ kod, text }));
  });
}

let vystup;
for (const subdomena of navrhy) {
  vystup = await nasad(subdomena);
  if (vystup.kod === 0 || !/Could not automatically register/i.test(vystup.text)) break;
  console.log(`\nSubdoména „${subdomena}.workers.dev“ je obsazená, zkouším jinou…\n`);
}

if (vystup.kod !== 0) {
  if (/not (logged in|authenticated)|wrangler login/i.test(vystup.text)) {
    console.error("\nNejsi přihlášený ke Cloudflare: `npx -y wrangler@4 login` (souhlas v prohlížeči do 2 minut), pak znovu.");
  } else if (/workers\/onboarding/.test(vystup.text)) {
    console.error("\nSubdoménu workers.dev se nepodařilo založit. Zvol ji jednou ručně na odkazu výše (Workers → onboarding)",
      "a spusť nasazení znovu – nebo dej do data/web.json jiný cloudflare.nazev.");
  }
  process.exit(vystup.kod ?? 1);
}

const adresa = (vystup.text.match(/https:\/\/[a-z0-9.-]+\.workers\.dev/i) || [])[0];
if (!adresa) {
  console.log("Nahráno. Adresu webu jsem ve výstupu nenašel – zkontroluj ji: node scripts/overit.mjs --url <adresa>");
  process.exit(0);
}
writeFileSync(resolve(".wrangler", "adresa.txt"), adresa + "\n");   // pro pozdější `npm run overit`
console.log(`\nWeb je nahraný: ${adresa}`);
const r = spawnSync("node", ["scripts/overit.mjs", "--url", adresa], { stdio: "inherit" });
process.exit(r.status ?? 1);
