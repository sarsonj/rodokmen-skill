// `npm run data`: spustí ../tools/export_web.py prvním funkčním Pythonem 3.
// macOS/Linux: python3; Windows: python nebo py -3 („python3“ tam bývá jen nefunkční alias z Microsoft Store).
// -X utf8: s -I se proměnná PYTHONUTF8 ignoruje, na Windows by jinak výstup a soubory byly v cp1250.
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

// Astro 7 potřebuje Node ≥ 22.12 – říct to hned a srozumitelně, ne až chybou při `astro build`.
const [maj, min] = process.versions.node.split(".").map(Number);
if (maj < 22 || (maj === 22 && min < 12)) {
  console.error(`CHYBA: web potřebuje Node 22.12 nebo novější, tady je ${process.versions.node}. Nainstaluj aktuální ` +
    "Node LTS (macOS: brew install node, Windows: winget install OpenJS.NodeJS.LTS, pak restart Claude Code) a spusť znovu.");
  process.exit(1);
}

const script = fileURLToPath(new URL("../../tools/export_web.py", import.meta.url));
const candidates = process.platform === "win32"
  ? [["python"], ["py", "-3"], ["python3"]]
  : [["python3"], ["python"]];

for (const [cmd, ...pre] of candidates) {
  const probe = spawnSync(cmd, [...pre, "-c", "import sys; sys.exit(sys.version_info < (3, 9))"], { stdio: "ignore" });
  if (probe.status !== 0) continue;
  const run = spawnSync(cmd, [...pre, "-I", "-X", "utf8", script, ...process.argv.slice(2)], { stdio: "inherit" });
  process.exit(run.status ?? 1);
}
console.error("Nenašel jsem Python 3.9+ (python3, python ani py -3). Nainstalujte ho (python.org) a zkuste to znovu.");
process.exit(1);
