# Rodinný web – stavba, nastavení, zveřejnění

Web je statický (Astro + vyhledávání Pagefind), data bere z `data/` přes `tools/export_web.py`.
Stránky: úvod (lákadlo, statistiky, zajímavosti, mapa, rody, vějíř), příběh, zajímavosti, rody, stránka rodu,
mapa (OpenStreetMap), vějíř přes celou obrazovku s hledáním, seznam předků, zápisy (s výřezem, rámečkem, přepisem
a překladem), stránka osoby, rodiny, „Co hledáme“, výzkumný deník, hledání.

## Příkazy (ve složce `web/`)
| příkaz | co dělá |
|---|---|
| `npm install` | jednou na začátku (stáhne knihovny, ~1 minuta) |
| `npm run data` | převede data do webu (vždy po změně dat; `scripts/data.mjs` si sám najde funkční Python 3) |
| `npm run build` | sestaví web do `dist/` |
| `npm run nahled` | data + build + náhled na http://localhost:4321 (Ctrl+C ukončí) |
| `npm run dev` | vývojový režim při úpravách vzhledu |
| `npm run nasadit-cloudflare` | data + build + nahrání na Cloudflare (výchozí) + kontrola |
| `npm run nasadit` | data + build + nahrání na Netlify + kontrola |
| `npm run overit` | kontrola nasazeného webu bez přihlášení (rodinná otázka × ochrana týmu Netlify / stránka Cloudflare) |

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
 "zajimavosti_na_uvodu": [{"nadpis": "Nejstarší předek", "text": "Kovář Jan, asi 1825."}]
}
```
- `kontakt.jmeno` je ve 3. pádě („Napište Petrovi na …“).
- **Přihlášení:** otázka, na kterou zná odpověď jen rodina (ne snadno dohledatelná na sociálních sítích).
  Odpověď se porovnává bez diakritiky a velkých písmen a musí obsahovat písmena nebo číslice z latinky (azbuka
  a samotné symboly nejdou). Na serveru i v cookie prohlížeče je jen její otisk (SHA-256),
  samotná odpověď se nikam neukládá. Krátkou nebo běžnou odpověď (jméno, obec) ale jde z otisku uhádnout zkoušením,
  proto ať ji uživatel nepoužívá jako heslo jinde. Bez odpovědi nasazení (`npm run nasadit-cloudflare`, `nasadit`, `deploy-caprover`)
  skončí chybou; otevřený web jen výslovně přes `"otevreny": true` v `prihlaseni`.
  Je to lehká ochrana proti náhodným návštěvníkům, ne bankovní zabezpečení – citlivé věci na web nepatří.
- `uvod.foto` = klíč obrázku ve `vyrezy/` (ulož přes `vyrez.py`).
- `pribeh`: `menu` a `tlacitko` pojmenuj podle hlavního rodu („Příběh Novákových“), `rod` = číslo rodu (8–15).
  Bez vyplněného `uvod` ukáže úvodní stránka aspoň název a `lead` příběhu. Viz `pribehy.md`.
- Šablona `web.json` je prázdná – název nastav hned, jak znáš příjmení výchozí osoby (`kontrola.py` hlásí zbytky ukázky).
- `citlive_schvaleno`: seznam úryvků textu, které uživatel na webu schválil (např. `["oběsil se ve stodole"]`) –
  `kontrola.py` je pak nehlásí jako `CITLIVÉ`. Úryvek musí obsahovat hlášené slovo; když se text změní, hlásí se znovu.

## Zveřejnění na Cloudflare (výchozí, zdarma)
Nasazování i přenos jsou zdarma bez limitu; brána běží před každým souborem a to se počítá do 100 000 požadavků denně
(stránka webu je asi 20–40 požadavků → tisíce zobrazení denně; po vyčerpání vrací web do půlnoci UTC chybu 429).
1. **Účet:** nemá-li uživatel účet Cloudflare, ať si ho **nejdřív** založí na dash.cloudflare.com (zdarma, stačí e-mail)
   a potvrdí e-mail z pošty – registrace se do dvou minut přihlášení nevejde. Až je v dashboardu přihlášený, pokračuj.
2. **Přihlášení:** spusť sám na pozadí `cd web && npx -y wrangler@4 login` – otevře prohlížeč. Řekni uživateli:
   „Otevře se stránka Cloudflare – klikni na **Allow**, máš na to asi 2 minuty.“ Ověření: `npx -y wrangler@4 whoami`.
   - **„Application authorization failed / Authentication error, please login“:** prohlížeč není u Cloudflare přihlášený
     (typicky hned po registraci, nebo jiné okno/anonymní okno). „Retry authorization“ nepomůže, když login mezitím
     vypršel. Ať se uživatel v tom prohlížeči přihlásí na dash.cloudflare.com, pak spusť `wrangler login` znovu
     (nový odkaz). Odkaz bez otevření prohlížeče: `npx -y wrangler@4 login --browser=false`.
   - „Timed out waiting for authorization code“ = vypršely 2 minuty, spusť login znovu.
3. **Adresa webu:** web poběží na `https://rodokmen.<název>.workers.dev` (`rodokmen` = název webu na účtu, `<název>` =
   subdoména účtu). Vymysli 2–3 názvy podle rodu (malá písmena
   bez diakritiky, pomlčky: `novakovi`, `novakovi-holice`, `rod-novaku`), ověř je
   `cd web && node scripts/nasadit_cloudflare.mjs --volno novakovi novakovi-holice rod-novaku` (ptá se DNS Cloudflare,
   adresu tím „nevyplašíš“) a uživateli nabídni jen volné. Vybraný zapiš do `data/web.json` jako
   `"cloudflare": {"nazev": "novakovi"}`. Název je subdoména celého účtu Cloudflare (založí se při prvním nasazení,
   změnit jde jen v administraci); kdyby byl přece obsazený, nasazení zkusí variantu s číslem a řekne ji.
   **Má-li uživatel účet Cloudflare už dřív**, použije se jeho stávající subdoména a název z `web.json` se nepoužije –
   adresu pak řekne až nasazení. Subdoména je na účtu jen jedna a přes API ji změnit nejde (jen v administraci).
   **Druhý rodokmen na stejném účtu** potřebuje jiný název webu, jinak by první web přepsal: zeptej se na něj (např.
   `rodokmen-dvorakovi`), zapiš `"cloudflare": {"web": "rodokmen-dvorakovi"}` a ukaž celou adresu
   `https://rodokmen-dvorakovi.<subdoména>.workers.dev`. Nasazení to samo hlídá: když web s tím názvem na účtu už je
   a z téhle složky se ještě nenasazoval, skončí s radou (tentýž projekt z jiného počítače: `node scripts/nasadit_cloudflare.mjs --prepsat`).
4. **Nasazení:** `cd web && npm run nasadit-cloudflare` (spusť sám). Vypíše adresu a sám spustí kontrolu
   `scripts/overit.mjs`. U nové adresy kontrola počká, až se rozšíří (pár minut); když ji počítač ještě nezná, řekne to
   a skončí bez chyby – pak ověř později `npm run overit`. Do té doby adresu v prohlížeči neotvírej: počítač nebo
   router by si zapamatoval, že neexistuje, a až 30 minut by ji neviděl (jinde, třeba v telefonu na mobilních datech,
   web už jede). Řekni to uživateli, ať se nelekne.
5. Ověř i sám v anonymním okně: rodinná otázka, po správné odpovědi web.
   Bránu (`web/cloudflare/worker.js`) a `web/wrangler.jsonc` vyrábí export – ručně neupravovat. Brána musí běžet
   před každým souborem (`run_worker_first`), jinak by šly stránky a fotky stáhnout bez přihlášení.
Další aktualizace = jen `npm run nasadit-cloudflare`.

**Pasti:**
- „You need to verify your email address to use Workers“ (403) u nového účtu: Cloudflare chce ověřený e-mail – ověření
  v dashboardu (pruh nahoře / My Profile), potvrdit odkaz v poště, nasadit znovu (subdoména už zůstane založená).
- Safari s blokátorem obsahu ukáže místo ověřovací stránky Cloudflare prázdnou stránku 403 – zkus jiný prohlížeč
  (kontrola to pozná).
- Nepoužívej `wrangler pages project create/deploy` ani „Import a repository“ v administraci – založí jiný typ projektu,
  případně sám přepíše `astro.config`/`package.json`. Nasazuj jen přes `npm run nasadit-cloudflare`.
- V cloudovém prostředí (claude.ai), kde se přihlášení přes prohlížeč nevrátí do terminálu, použij Netlify (`login --request`).

## Zveřejnění na Netlify (druhá možnost)
Pro uživatele, kteří už web na Netlify mají. Bezplatný účet vystačí jen na asi 20 nasazení měsíčně (viz kredity níže).
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
   **Nový web bývá „Private“ (ochrana týmu)** – rodina by místo rodinné otázky viděla přihlášení k Netlify a majitel to
   nepozná (je přihlášený). Řekni to uživateli předem; kontrola po nasazení (krok 4) ji pozná. Vypni ji se souhlasem uživatele:
   `npx -y netlify-cli@latest api updateSite --data '{"site_id":"<siteId z web/.netlify/state.json>","body":{"sso_login":false}}'`
   (v administraci: Project configuration → Access & security → Visitor access → Project visibility → Edit visibility → Public).
4. Nasazení: `cd web && npm run nasadit` (můžeš spustit sám; vypíše adresu webu). Na konci se sama spustí kontrola
   `scripts/overit.mjs` (ručně `npm run overit`): otevře web bez přihlášení a pozná rodinnou otázku, ochranu týmu Netlify
   (vypíše, jak ji vypnout) i web bez brány. Skončí-li chybou, oprav to a spusť `npm run overit` znovu.
5. Ověř i sám: otevři adresu **v anonymním okně** → rodinná otázka, po správné odpovědi web.
   Přihlášení zajišťuje Netlify Edge Function `web/netlify/edge-functions/brana.js` (generuje ji export).
Další aktualizace = jen `npm run nasadit`. Vlastní doménu lze nastavit v administraci Netlify.

**Kredity Netlify (bezplatný účet):** 300 kreditů měsíčně, nepřevádějí se. Každé nasazení stojí 15 (nepovedené nic),
1 GB přenosu 20 → asi 20 nasazení měsíčně, nebo méně, když rodina stahuje velké výřezy ze `zdroje/`. Po vyčerpání
Netlify nasazování pozastaví a `npm run nasadit` skončí „Forbidden“ – to jsou vyčerpané kredity, ne chyba webu
(stav kreditů je v administraci Netlify). Proto nasazuj na pokyn uživatele nebo jednou na konci sezení, mezitím jen
náhled. Řekni to uživateli hned při prvním zveřejnění.

**Pozor:** „Netlify Drop“ (přetažení složky v prohlížeči) neumí Edge Functions → web by byl bez přihlášení. Nepoužívat.

## Náhled v Claude desktop
Projekt má `.claude/launch.json` – náhled webu v Claude desktop spustí `npm --prefix web run dev` (port 4321). Data se
předtím musí vyexportovat (`cd web && npm run data`). Když náhled nenaběhne (třeba na Windows, kde je `npm` jako `npm.cmd`),
zkus v `launch.json` `"runtimeExecutable": "node"` a `"runtimeArgs": ["web/node_modules/astro/bin/astro.mjs", "dev", "--root", "web"]`
(Astro 7 má spouštěč `astro.mjs`, ne `astro.js`). Server běží jen na tomto počítači – nepřidávej `--host`.

## Vlastní server (pokročilé)
- Docker: `web/Dockerfile` (build Astro → nginx s `nginx.conf` z `nginx.sablona.conf`). Před buildem image vždy `npm run data`.
  Bez Node.js na počítači: `python3 -I tools/export_web.py --nasazeni`, pak `docker build` ve `web/` (Astro se sestaví v image).
- Přestavba nechává na disku starý image bez tagu (stovky MB). Po `docker build` smaž jen starý image tohoto webu:
  ```
  OLD=$(docker images -q rodokmen-web:latest); docker build -t rodokmen-web .
  docker rm -f rodokmen-web; docker run -d --name rodokmen-web --restart unless-stopped -p 8080:80 rodokmen-web
  [ -n "$OLD" ] && [ "$OLD" != "$(docker images -q rodokmen-web:latest)" ] && docker image rm "$OLD"
  ```
  `docker system/image/builder prune` nepoužívej – platí pro celý server a smaže i věci jiných projektů.
- Web počítá s během v kořeni domény (odkazy, cookie přihlášení i hledání od `/`) – za reverse proxy mu dej
  subdoménu (`rodokmen.server.cz`), ne podadresář (`server.cz/rodokmen/`).
- **Jen přes https** (reverse proxy s Let's Encrypt, DSM, CapRover to umí): přihlašovací stránka počítá otisk odpovědi
  v prohlížeči a ten to přes obyčejné http (mimo localhost) nedovolí – přihlášení by nefungovalo.
- CapRover: `npm run deploy-caprover` (vyžaduje nainstalovaný a přihlášený `caprover` CLI).

## Úpravy vzhledu
Styly `web/src/styles/global.css` (barvy v `:root`), rozložení `web/src/layouts/Base.astro`, stránky `web/src/pages/`.
Barvy rodů jsou v `tools/export_web.py` (`LINE_COLORS`) a `tools/fan_chart.py` (`BASE`). Upravuj jen na přání uživatele
a po úpravě zkontroluj web na mobilu i počítači.

## Vějíř jako plakát
`python3 -I tools/fan_chart.py vystupy/` → SVG a HTML (a PNG, je-li nainstalovaný Google Chrome, na Windows i Microsoft Edge) k tisku.

## Aktualizace staršího projektu
Znovu spusť `python3 -I SKILL_DIR/tools/novy_projekt.py <složka projektu>`. Data (`data/`, výřezy) zůstanou. Projekt má
v `.skill_sablona/` kopii šablony `web/` a `tools/`, ze které vznikl (commitovat s projektem), a skript podle ní rozhodne
o každém souboru a vypíše seznam:
- **Přepsáno**: soubor projekt neupravoval, nahradila ho nová verze.
- **Ponecháno**: vlastní úprava, šablona se nezměnila.
- **Sloučeno**: změnila se úprava i šablona, každá jinde; `git merge-file` je spojil. Ověř, že soubor dává smysl.
- **Ke kontrole**: úprava i šablona změnily stejná místa, chybí `git`, soubor přidal projekt i nová šablona, nebo ho
  projekt smazal a šablona změnila. Soubor zůstal, jak byl; nová verze je v `pracovni/zaloha_<datum>/nova_sablona/`
  (u konfliktu sloučení, kdy je `git`, vedle i návrh se značkami `<<<<<<<` jako `.konflikt`). Převezmi změny šablony
  ručně a pak spusť `python3 -I SKILL_DIR/tools/novy_projekt.py <složka projektu> --vyreseno web/src/…` (volbu lze
  opakovat). Jako základ uloží přesně ten návrh, který je v záloze (zapamatovaný v `.skill_sablona/cekajici.json`),
  takže pozdější změny šablony přijdou při další aktualizaci; soubor v projektu nezmění. Bez záznamu uloží aktuální
  verzi šablony a řekne to. Do té doby se soubor hlásí při každé aktualizaci. Do ke kontrole patří i složka na místě
  souboru (nebo naopak) a na Windows a macOS cesty, které se liší jen velikostí písmen; ty skript nezmění.
- **Smazáno v projektu**: soubor projekt smazal a šablona ho nezměnila, zůstane smazaný.
- **Šablona už nemá**: soubor zůstal (skript nic nemaže) a hlásí se při každé aktualizaci. Zkontroluj, jestli ho web
  ještě potřebuje; případně ho smaž ručně a spusť `--vyreseno` s jeho cestou.
- **Přepsáno, původní verze v záloze**: projekt ze starší verze bez `.skill_sablona/`. Upravené soubory nahradila nová
  verze a původní jsou v `pracovni/zaloha_<datum>/puvodni/`; vlastní úpravy z nich převezmi (porovnej soubory).

Odkaz (symlink, junction) ve `web/`, `tools/`, `.skill_sablona/` nebo `pracovni/`, který vede mimo projekt, a odkaz
nebo složku na místě zálohy skript odmítne s hláškou POZOR a soubory za nimi přeskočí (bez zálohy nic nepřepíše).

`web/package-lock.json` (mění ho `npm install`) se neslučuje: změnila-li ho šablona, vezme se nový a starý jde do zálohy.

**Po aktualizaci projdi výpis s uživatelem** (skript řeší jen mechanické případy):
1. **Ke kontrole:** porovnej, co změnila šablona (`.skill_sablona/<soubor>` proti `nova_sablona/<soubor>` v záloze)
   a co projekt (`.skill_sablona/<soubor>` proti souboru v projektu). Uživateli řekni jednou dvěma větami, co je nového
   a co je jeho úprava, navrhni sloučení a po souhlasu ho udělej a spusť `--vyreseno`.
2. **Přepsáno, původní verze v záloze:** porovnej `puvodni/<soubor>` s novou verzí. Jsou-li v ní vlastní úpravy
   (ne jen starší stav šablony), nabídni jejich převzetí do nové verze.
3. **Sloučeno:** prohlédni výsledek (`git diff`), jestli dává smysl.
4. Ve `web/` `npm install`, `npm run data` a `npm run build`, pak `python3 -I tools/kontrola.py`.
Starou šablonu přihlášení `export_web.py` odmítne s výzvou k aktualizaci.
