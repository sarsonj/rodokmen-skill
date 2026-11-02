// `node scripts/podcesta.mjs /rodokmen/sarka`: přepíše hotový dist/ pro provoz v podadresáři za reverse proxy.
// Web používá odkazy od kořene („/osoba/…“); proxy prefix odřízne, prohlížeč ho ale v odkazech potřebuje.
// ponytail: textové nahrazení v buildu místo Astro `base` – šablona skillu tak zůstává beze změny.
import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const base = (process.argv[2] || "").replace(/\/+$/, "");
if (!/^\/[\w\-/]+$/.test(base)) {
  console.error("Použití: node scripts/podcesta.mjs /rodokmen/jmeno");
  process.exit(1);
}

const rules = [
  [/\b(href|src|action)=(["'])\/(?![\/])/g, `$1=$2${base}/`],
  [/url\((["']?)\/(?![\/])/g, `url($1${base}/`],
  // odkazy v datech předaných skriptům přes atributy (mapa: JSON se jmény a odkazy)
  [/&quot;\/(?=[a-z_])/g, `&quot;${base}/`],
  // přihlašovací stránka: cookie jen pro tento web, návrat na jeho úvod
  [/Path=\/;/g, `Path=${base}/;`],
  [/path === '\/prihlaseni\.html' \? '\/'/g, `path === '${base}/prihlaseni.html' ? '${base}/'`],
  // vyhledávání: výsledky z indexu jsou od kořene
  [/new PagefindUI\(\{/g, `new PagefindUI({ baseUrl: '${base}/', bundlePath: '${base}/pagefind/',`],
];

let changed = 0;
const walk = (dir) => {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) walk(p);
    else if (/\.(html|js|mjs|css|svg)$/.test(e.name) && !p.includes("pagefind")) {
      const before = readFileSync(p, "utf8");
      const after = rules.reduce((t, [re, to]) => t.replace(re, to), before);
      if (after !== before) { writeFileSync(p, after); changed++; }
    }
  }
};
walk(new URL("../dist", import.meta.url).pathname.replace(/^\/(\w:)/, "$1"));
console.log(`podcesta ${base}: upraveno ${changed} souborů`);
