# Rodinný web – stavba, nastavení, zveřejnění

Web je statický (Astro + vyhledávání Pagefind), data bere z `data/` přes `tools/export_web.py`.
Stránky: úvod (lákadlo, statistiky, zajímavosti, mapa, rody, vějíř), příběh, zajímavosti, rody, stránka rodu,
mapa (OpenStreetMap), vějíř přes celou obrazovku s hledáním, seznam předků, zápisy (s výřezem, rámečkem, přepisem
a překladem), stránka osoby, rodiny, „Co hledáme“, výzkumný deník, hledání.

## Příkazy (ve složce `web/`)
| příkaz | co dělá |
|---|---|
| `npm install` | jednou na začátku (stáhne knihovny, ~1 minuta) |
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
- Šablona `web.json` je prázdná – název nastav hned, jak znáš příjmení výchozí osoby (`kontrola.py` hlásí zbytky ukázky).
- `puvodni_jmena`: `true` = jména osob na webu a ve vějíři v původních tvarech ze zápisů (pole `zap` v `osoby.py`,
  „Catharina Nowakin / Kateřina Nováková“). Výchozí je dnešní spisovná podoba; původní tvar je pak jen řádkem na stránce osoby.
- `citlive_schvaleno`: seznam úryvků textu, které uživatel na webu schválil (např. `["oběsil se ve stodole"]`) –
  `kontrola.py` je pak nehlásí jako `CITLIVÉ`. Úryvek musí obsahovat hlášené slovo; když se text změní, hlásí se znovu.

## Stránky Statistiky a Domy
- **Statistiky** (`/statistiky/`, `tools/statistiky.py`): povolání, věk dožití a při sňatku, měsíce svateb, generační
  odstup, místa narození, křestní jména, víra, zápisy podle druhu a archivu. Počítá se jen z faktů přímých předků –
  čím jednotnější zápis faktů (`* 12. 3. 1873 Obec čp. 5`, `× …`, `† …`, řemeslo samostatně), tím lepší čísla.
- **Domy** (`/domy/`, `tools/domy_export.py`): mapa domů předků z výstupu skillu stare-adresy (viz `data.md` → `domy/`).
  Podklad ČÚZK (mapa / letecký snímek), domy shluknuté podle obcí, barva podle rodu, v okénku lidé, kteří v domě
  žili (přímí předci první, boční příbuzní s odkazem na kartičku u předka), výřez skici a jedna věta o jistotě polohy.
  Na stránkách osob a zápisů jsou odkazy na domy. Výřezy skic na veřejném webu jen s citací archivu (podmínky
  v návodu stare-adresy).

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
Další aktualizace = jen `npm run nasadit`. Tarif zdarma má měsíční kredity a každé nasazení je spotřebovává –
nenasazuj po každé drobné změně, ale až na požádání uživatele (třeba po skončení kola hledání). Vlastní doménu lze nastavit v administraci Netlify.

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
