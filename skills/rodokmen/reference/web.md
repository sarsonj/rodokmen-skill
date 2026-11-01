# Rodinný web – stavba, nastavení, zveřejnění

Web je statický (Astro + vyhledávání Pagefind), data bere z `data/` přes `tools/export_web.py`.
Šablona používá Astro 7.3.8; podle `package-lock.json` vyžaduje Astro Node.js `>=22.12.0` a tranzitivní `undici`
8.11.2 `>=22.19.0`. Používej proto Node.js `>=22.19.0` při čisté instalaci i sestavení webu.
Stránky: úvod (lákadlo, statistiky, zajímavosti, mapa, rody, vějíř), příběh, zajímavosti, rody, stránka rodu,
mapa (OpenStreetMap), vějíř přes celou obrazovku s hledáním, seznam předků, zápisy (s výřezem, rámečkem, přepisem
a překladem), stránka osoby, rodiny, „Co hledáme“, výzkumný deník, hledání.

## Příkazy (ve složce `web/`)
| příkaz | co dělá |
|---|---|
| `npm ci` | čistá instalace přesně podle `package-lock.json` |
| `npm run data` | převede data do webu (vždy po změně dat; funkční Python 3 vyhledá `scripts/data.mjs`) |
| `npm run build` | sestaví web do `dist/` |
| `npm run nahled` | data + build + náhled na http://localhost:4321 (Ctrl+C ukončí) |
| `npm run dev` | vývojový režim při úpravách vzhledu |
| `npm run nasadit` | data + build + nahrání na Netlify |

Náhled spouštěj na pozadí a uživateli pošli odkaz. Vzhled si ověř sám (snímek obrazovky přes prohlížeč, je-li k dispozici).

## `data/web.json`
```json
{
 "nazev": "Rodokmen Novákových",
 "popis": "Popis pro vyhledávače a sdílení (web je ale noindex).",
 "zapati": "Dohledáno v digitalizovaných matrikách SOA Zámrsk (portál ARON)",
 "kontakt": {"jmeno": "Petrovi", "email": "petr@example.cz"},
 "prihlaseni": {"uvod": "Tenhle web je jen pro rodinu.", "otazka": "Jak se jmenoval pes u babičky v Holicích?", "odpoved": "Alík"},
 "uvod": {"nadpis": "Lákavý nadpis", "odstavce": ["2–3 věty, které chytí"], "foto": "klic_obrazku_ve_vyrezech", "foto_popis": "…"},
 "pribeh": {"menu": "Příběh Nováků", "rod": 8, "tlacitko": "Přečíst příběh Nováků"},
 "pribehy": [],
 "zajimavosti_na_uvodu": [{"nadpis": "Nejstarší předek", "text": "Kovář Jan, asi 1825."}]
}
```
- `kontakt.jmeno` je ve 3. pádě („Napište Petrovi na …“).
- **Přihlášení:** otázka, na kterou zná odpověď jen rodina (ne snadno dohledatelná na sociálních sítích).
  Odpověď se porovnává bez diakritiky a velkých písmen. Na serveru i v cookie prohlížeče je jen její otisk (SHA-256),
  samotná odpověď se nikam neukládá. Krátkou nebo běžnou odpověď (jméno, obec) ale jde z otisku uhádnout zkoušením,
  proto ať ji uživatel nepoužívá jako heslo jinde. Bez odpovědi nasazení (`npm run nasadit`, `deploy-caprover`)
  skončí chybou; otevřený web jen výslovně přes `"otevreny": true` v `prihlaseni`.
  Je to lehká ochrana proti náhodným návštěvníkům, ne bankovní zabezpečení – citlivé věci na web nepatří.
- `uvod.foto` = klíč obrázku ve `vyrezy/` (ulož přes `vyrez.py`).
- `pribeh`: `menu` a `tlacitko` pojmenuj podle hlavního rodu („Příběh Novákových“), `rod` = číslo rodu (8–15).
  Bez vyplněného `uvod` ukáže úvodní stránka aspoň název a `lead` příběhu. Viz `pribehy.md`.
- `pribehy`: volitelný seznam slugů souborů z `data/pribehy/`, který určuje pořadí příběhů v rozcestníku.
  Prázdný seznam použije všechny soubory v abecedním pořadí; vyplněný seznam musí každý slug obsahovat právě jednou.
  Frontmatter (`title`, `lead`, číselné `rod`) a stránka každého příběhu jsou popsány v `reference/pribehy.md`.
- Šablona `web.json` je prázdná – název nastav hned, jak znáš příjmení výchozí osoby (`kontrola.py` hlásí zbytky ukázky).
- `citlive_schvaleno`: seznam úryvků textu, které uživatel na webu schválil (např. `["oběsil se ve stodole"]`) –
  `kontrola.py` je pak nehlásí jako `CITLIVÉ`. Úryvek musí obsahovat hlášené slovo; když se text změní, hlásí se znovu.

## Zveřejnění na Netlify (výchozí, zdarma)
1. Uživatel si založí účet na netlify.com (stačí přihlášení přes Google/GitHub) – udělá sám.
2. Přihlášení CLI (otevře prohlížeč) – dej uživateli: `! cd web && npx -y netlify-cli@latest login`.
   Když `!` nejde (cloudové prostředí): `npx -y netlify-cli@latest login --request "Rodokmen"` vypíše odkaz a číslo
   lístku – uživatel odkaz otevře a schválí, pak `npx -y netlify-cli@latest login --check <lístek>`.
3. Založení webu a propojení složky (interaktivní, jednou) – dej uživateli:
   `! cd web && npx -y netlify-cli@latest sites:create` (zvolí tým a název → adresa `https://<název>.netlify.app`),
   případně `npx netlify-cli link`, pokud web už existuje. Je-li uživatel už přihlášený, jde web založit i bez dotazů
   (můžeš spustit sám): `cd web && npx -y netlify-cli@latest sites:create --name <název> --account-slug <tým>`.
   **Windows:** když `!` běží ve Windows PowerShellu 5.1 (`&&` tam nefunguje a `npx` blokuje Execution Policy), ať uživatel
   otevře PowerShell 7 nebo Příkazový řádek, přejde do složky `web` a spustí `npx -y netlify-cli@latest login` (a `sites:create`).
4. Nasazení: `cd web && npm run nasadit` (můžeš spustit sám; vypíše adresu webu).
5. Ověř: otevři adresu **v anonymním okně** → musí se ukázat rodinná přihlašovací otázka; po správné odpovědi web.
   Ukáže-li se místo ní přihlášení k Netlify (401, „Login Redirect“), zdědil web ochranu týmu („Team protection“).
   Uživatel ji vypne v administraci webu: Project configuration → Access & security → Visitor access. Web pak chrání
   rodinná otázka – proto znovu ověř v anonymním okně, že se ukáže.
   Přihlášení zajišťuje Netlify Edge Function `web/netlify/edge-functions/brana.js` (generuje ji export).
Další aktualizace = jen `npm run nasadit`. Vlastní doménu lze nastavit v administraci Netlify.

**Pozor:** „Netlify Drop“ (přetažení složky v prohlížeči) neumí Edge Functions → web by byl bez přihlášení. Nepoužívat.

## Náhled v Claude desktop
Projekt má `.claude/launch.json` – náhled webu v Claude desktop spustí `npm --prefix web run dev` (port 4321). Data se
předtím musí vyexportovat (`cd web && npm run data`). Když náhled nenaběhne (třeba na Windows, kde je `npm` jako `npm.cmd`),
zkus v `launch.json` `"runtimeExecutable": "node"` a `"runtimeArgs": ["web/node_modules/astro/bin/astro.mjs", "dev", "--root", "web"]`
(Astro 7 má spouštěč `astro.mjs`, ne `astro.js`). Server běží jen na tomto počítači – nepřidávej `--host`.

## Vlastní server (pokročilé)
- Docker: `web/Dockerfile` (build Astro → nginx s `nginx.conf` z `nginx.sablona.conf`). Před buildem image vždy `npm run data`.
- CapRover: `npm run deploy-caprover` (vyžaduje nainstalovaný a přihlášený `caprover` CLI).

## Úpravy vzhledu
Styly `web/src/styles/global.css` (barvy v `:root`), rozložení `web/src/layouts/Base.astro`, stránky `web/src/pages/`.
Barvy rodů jsou v `tools/export_web.py` (`LINE_COLORS`) a `tools/fan_chart.py` (`BASE`). Upravuj jen na přání uživatele
a po úpravě zkontroluj web na mobilu i počítači.

## Vějíř jako plakát
`python3 -I tools/fan_chart.py vystupy/` → SVG a HTML (a PNG, je-li nainstalovaný Google Chrome, na Windows i Microsoft Edge) k tisku.

## Aktualizace staršího projektu
Znovu spusť `python3 -I SKILL_DIR/tools/novy_projekt.py <složka projektu>`. Data (`data/`, výřezy) zůstanou, `tools/` se přepíše
a soubory ve `web/`, které se liší od nové šablony, taky – staré verze uloží do `pracovni/zaloha_web_<datum>/` a vypíše jejich seznam.
Upravoval-li jsi s uživatelem vzhled (styly, stránky), převezmi úpravy ze zálohy (porovnej soubory) a ověř web. Pak ve `web/`
se stejnou verzí Node.js `>=22.19.0` pro instalaci i build spusť `npm ci`, `npm run data` a `npm run build`.
`package-lock.json` zachovej; `npm ci` z něj provede čistou instalaci. Starou šablonu přihlášení `export_web.py` odmítne s výzvou k aktualizaci.
