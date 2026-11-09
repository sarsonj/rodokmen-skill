// Spuštění `npx …` bez shellu, aby argumenty s mezerou nebo uvozovkami (cesta „C:\Users\Jan Novák\…“, JSON)
// došly beze změny i na Windows. Node má npx jako skript npx-cli.js vedle sebe: na Windows
// <node.exe>\..\node_modules\npm\bin\npx-cli.js, jinde <bin>/../lib/node_modules/npm/bin/npx-cli.js.
// Když ho nenajdeme (neobvyklá instalace), použijeme dosavadní cestu přes shell (na Windows `npx.cmd`).
import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";

const bin = dirname(process.execPath);
const cli = [join(bin, "node_modules", "npm", "bin", "npx-cli.js"), join(bin, "..", "lib", "node_modules", "npm", "bin", "npx-cli.js")]
  .find((p) => existsSync(p));
const win = process.platform === "win32";

function prikaz(args) {
  return cli ? [process.execPath, [cli, ...args], {}] : ["npx", args, { shell: win }];
}

export function npxSync(args, options = {}) {
  const [cmd, a, extra] = prikaz(args);
  return spawnSync(cmd, a, { ...options, ...extra });
}

export function npxSpawn(args, options = {}) {
  const [cmd, a, extra] = prikaz(args);
  return spawn(cmd, a, { ...options, ...extra });
}
