# Příprava počítače a projektu (Fáze 0)

Čti při zakládání projektu nebo když nějaký nástroj chybí či padá na instalaci.

## Nástroje
Zkontroluj: `python3 --version` (≥ 3.9), `node --version` (≥ 20), `magick -version` (ImageMagick 7; je-li jen verze 6
s příkazem `convert`, nástroje ji mimo Windows použijí samy), `git --version`.
Co chybí, pomoz nainstalovat. Instalace systémových věcí nech uživatele potvrdit; interaktivní příkazy mu dej
s předponou `!`, ať je spustí sám.
- **macOS:** Homebrew `brew install python node imagemagick git`.
- **Windows:** winget nebo instalátory z python.org, nodejs.org, imagemagick.org. **winget vždy s plnými přepínači**,
  jinak spadne na otázce ke zdroji msstore („Error reading input in prompt“):
  `winget install --id <balík> --source winget --accept-source-agreements --accept-package-agreements`
  (balíky `Python.Python.3.12` + `--scope user`, `OpenJS.NodeJS.LTS`, `ImageMagick.ImageMagick`, `Git.Git`).

## macOS: https a certifikáty
Ověř: `python3 -I -c "import urllib.request; urllib.request.urlopen('https://aron.vychodoceskearchivy.cz')"`.
Python z python.org po instalaci nemá certifikáty (`CERTIFICATE_VERIFY_FAILED`) – ať uživatel spustí
`Install Certificates.command` ve složce `/Applications/Python 3.x/`, nebo použij Python z Homebrew (`/opt/homebrew/bin/python3`).

## Windows
- **Python:** `python3` tam bývá jen nefunkční alias z Microsoft Store („Python nebyl nalezen“) – zkontroluj
  `python --version` (případně `py -3 --version`) a ve všech příkazech skillu místo `python3 -I` používej
  `python -I -X utf8` (funguje-li jen launcher, tak `py -3 -I -X utf8`). `-I` ignoruje proměnnou `PYTHONUTF8`; bez
  `-X utf8` je výstup do roury nebo souboru v cp1250 – čeština se rozbije a některé nástroje spadnou na znacích jako „→“.
- Zkontroluj, **který** Python to je (`which -a python`) – může být přibalený k jinému programu (Inkscape, GIMP…) a nemít
  certifikáty. Ověř https: `python -I -c "import urllib.request; urllib.request.urlopen('https://aron.vychodoceskearchivy.cz')"`.
  Při `CERTIFICATE_VERIFY_FAILED` nainstaluj běžný Python (winget výše) a volej ho plnou cestou
  `"$LOCALAPPDATA/Programs/Python/Python312/python.exe"` (do PATH se dostane až po restartu Claude Code).
- **ImageMagick:** `winget install --id ImageMagick.ImageMagick --source winget --accept-source-agreements --accept-package-agreements`;
  do PATH se dostane až po restartu Claude Code (do té doby před příkazy `export PATH="/c/Program Files/ImageMagick-7…:$PATH"`
  s přesnou složkou z `C:\Program Files`). **Nikdy `convert`** (systémový nástroj Windows), vždy `magick`.
- Skripty `.sh` spouštěj přes Git Bash (`bash tools/…`). Delší jednorázové skripty v Pythonu nepiš jako heredoc
  (`python - <<EOF`), v Git Bash občas spadnou na „unexpected EOF“ – zapiš je do souboru v `pracovni/` a spusť.
- Tato pravidla zapiš hned po založení projektu do jeho `CLAUDE.md`, ať platí i příště, a dej je do zadání pomocníkům
  (další pasti při práci: `matriky.md` → Technické pasti (Windows)).

## Prohlížeč pro Clauda
Potřebuješ ho pro archivy, které nástroje nepouštějí (SOA Praha, MZA Brno, SOA Třeboň, ZA Opava, hledání v SOA
Litoměřice). Když předci žili tam a nemáš nástroje `mcp__…playwright…`, nabídni doplněk Playwright:
`/plugin install playwright@claude-plugins-official` (dej ho uživateli s `!` jako
`claude plugin install playwright@claude-plugins-official`), pak restart Claude Code. Jinou možností je Claude in Chrome
(`/chrome`); postupy v `portaly.md` jsou vyzkoušené hlavně s Playwrightem (snímek obrazovky do souboru).
Bez prohlížeče ať uživatel posílá snímky obrazovky.

## Založení projektu
1. Zeptej se, kde má projekt být (navrhni `~/Rodokmen`), a založ ho: `python3 -I SKILL_DIR/tools/novy_projekt.py <složka>`.
   Chce-li uživatel nejdřív vidět, jak web vypadá, založ vedle ukázku: `… novy_projekt.py ~/Rodokmen-ukazka --ukazka`,
   pak `cd web && npm install && npm run nahled` (na pozadí) a pošli mu odkaz http://localhost:4321.
2. Zeptej se, jestli zapnout **hlídač sítě** (`… novy_projekt.py <složka> --hlidac`, vypnutí `--bez-hlidace`).
   Vysvětli jednou větou: archivy blokují IP adresu po sérii rychlých dotazů. Hlídač je malý skript v projektu
   (`tools/hlidac_site.py`), který před každým příkazem zkontroluje, že stahování jde přes brzdu, a jinak ho zamítne.
   Sám nic nestahuje. Bez něj platí jen pravidla brzdy a zákaz přímého `curl`/`wget` v `.claude/settings.json`.
3. V projektu `git init` a první uložení (git = historie změn, kdyby se něco pokazilo). Doporuč pokračovat v Claude Code
   **z této složky** (soubor `CLAUDE.md` v ní zajistí, že příště navážeš).
4. Vyplň v `data/STAV.md` sekci „Pro koho“ a v `data/web.json` název webu („Rodokmen Novákových“), jakmile znáš
   příjmení výchozí osoby (šablona je prázdná).
