#!/usr/bin/env python3
"""Založí nový projekt rodokmenu ze šablony skillu.

Použití: python3 <skill>/tools/novy_projekt.py <cílová složka> [--ukazka] [--hlidac | --bez-hlidace]
  --ukazka        nakopíruje i vymyšlená ukázková data (rodina Novákových), aby šel web hned vyzkoušet
  --hlidac        zapne hlídač sítě (hook v .claude/settings.json, tools/hlidac_site.py): zamítne příkazy,
                  které jdou na web archivu mimo brzdu tools/slusne.py; --bez-hlidace ho vypne
       python3 <skill>/tools/novy_projekt.py <složka projektu> --vyreseno <soubor> [--vyreseno <soubor> …]
  --vyreseno      po ručním převzetí změn šablony (soubor „ke kontrole“, např. web/src/pages/index.astro) uloží
                  novou verzi šablony jako základ; soubor v projektu nezmění a další aktualizace ho už nehlásí

Vytvoří: data/ (prázdné kostry nebo ukázka), web/ (Astro web), tools/ (kopie nástrojů),
vyrezy/, zdroje/, dokumenty/, pracovni/, CLAUDE.md, .gitignore, .gitattributes (konce řádků LF i na Windows)
a .claude/launch.json (náhled v Claude desktop). Do .claude/settings.json doplní zákaz přímého curl/wget
(stahování z archivů jde přes brzdu tools/slusne.py); ostatní nastavení v souboru nechá beze změny.
Existující data nepřepisuje.
Do .skill_sablona/ uloží kopii šablony web/ a tools/, ze které projekt vznikl (patří do gitu s projektem).
Aktualizace staršího projektu (znovu spustit na stejnou složku) rozhodne o každém souboru web/ a tools/ podle
tří verzí (uložená šablona, projekt, nová šablona): neupravený soubor přepíše, vlastní úpravu nechá, když se šablona
nezměnila, a jinak sloučí po řádcích (git merge-file). Při konfliktu, bez gitu, u souboru přidaného projektem
i šablonou a u souboru smazaného v projektu, který šablona změnila, soubor nechá a novou verzi uloží do
pracovni/zaloha_<datum>/nova_sablona/ (u konfliktu sloučení s gitem i návrh se značkami) a zapíše ji do
.skill_sablona/cekajici.json; hlásí ho, dokud ho nevyřešíte (--vyreseno uloží jako základ právě tento návrh).
Soubor, který šablona už nemá, nemaže: hlásí ho, dokud ho nesmažete ručně a nespustíte --vyreseno. Odkazy (symlink,
junction) mimo projekt a na místě záloh, složku místo souboru a cesty lišící se jen velikostí písmen ohlásí a přeskočí.
Projekt bez .skill_sablona/ (ze starší verze) přepíše a původní verze změněných souborů uloží do
pracovni/zaloha_<datum>/puvodni/.
"""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile, time
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def copy(src, out):
    if os.path.islink(out):   # nepsat přes symlink mimo projekt
        os.remove(out)
    shutil.copy2(src, out)


SKIP = ("node_modules", "dist", ".astro", "__pycache__")
SABLONA = ".skill_sablona"   # kopie šablony, ze které projekt vznikl (základ pro tříčestnou aktualizaci)
CEKAJICI = "cekajici.json"   # v .skill_sablona/: návrhy z konfliktů, které čekají na --vyreseno
VZDY_SABLONA = {"web/package-lock.json"}   # mění ho npm install, ne uživatel: neslučovat, vzít nový (starý do zálohy)
NEROZLISUJE = os.name == "nt" or sys.platform == "darwin"   # disk běžně nerozlišuje velikost písmen


def copy_tree(src, dst):
    """Zkopíruje chybějící soubory."""
    for base, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SKIP]
        rel = os.path.relpath(base, src)
        os.makedirs(os.path.join(dst, rel), exist_ok=True)
        for f in files:
            new, out = os.path.join(base, f), os.path.join(dst, rel, f)
            if not os.path.lexists(out):
                copy(new, out)


def soubory(src):
    """Relativní cesty souborů šablony (bez závislostí a buildu)."""
    for base, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            yield os.path.relpath(os.path.join(base, f), src)


def cti(p):
    with open(p, "rb") as f:
        return f.read()


def zapis(p, data, mode_z=None):
    if os.path.islink(p):   # nepsat přes symlink mimo projekt
        os.remove(p)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(data)
    if mode_z:
        shutil.copymode(mode_z, p)


def lf(data):
    """Konce řádků LF – CRLF z gitu na Windows se nepočítá jako úprava (binární soubory beze změny)."""
    return data if b"\0" in data else data.replace(b"\r\n", b"\n")


def sloucit(nase, zaklad, nova):
    """Sloučí po řádcích přes `git merge-file`. Vrátí (výsledek, bez konfliktu); bez gitu nebo při chybě (None, False)."""
    git = shutil.which("git")
    if not git:
        return None, False
    d = tempfile.mkdtemp(prefix="slouceni_")
    try:
        cesty = [os.path.join(d, n) for n in ("projekt", "puvodni_sablona", "nova_sablona")]
        for p, data in zip(cesty, (nase, zaklad, nova)):
            zapis(p, data)
        r = subprocess.run([git, "merge-file", "-p", "-L", "projekt", "-L", "puvodni_sablona", "-L", "nova_sablona",
                            *cesty], capture_output=True)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    if not 0 <= r.returncode <= 127:   # chyba (např. binární soubor); 1–127 = počet konfliktů
        return None, False
    return r.stdout, r.returncode == 0


def mimo(dst, *cesty):
    """Vede některá cesta přes odkaz (symlink, junction) mimo projekt? Poslední článek se nepočítá – symlink na místě
    souboru zapis() jen nahradí. Takovou cestu ohlásí a volající ji přeskočí."""
    koren = os.path.normcase(os.path.realpath(dst)) + os.sep
    for p in cesty:
        real = os.path.join(os.path.realpath(os.path.dirname(p)), os.path.basename(p))
        if not os.path.normcase(real).startswith(koren):
            print(f"POZOR: {p} vede mimo projekt (odkaz) – přeskakuji.")
            return True
    return False


def nova_verze(new):
    data = cti(new)
    return data.replace(b"\r\n", b"\n") if new.endswith(".sh") else data   # skill z Windows (core.autocrlf) má CRLF


def zalohuj(dst, p, data=None, z=None):
    """Zapíše do zálohy data, nebo kopii souboru z. Ne přes odkaz či složku na místě zálohy a ne mimo projekt."""
    if os.path.islink(p) or os.path.isdir(p):   # isdir chytí i junction (islink ji v Pythonu 3.9 nepozná)
        print(f"POZOR: na místě zálohy {p} je odkaz nebo složka – zálohu nezapíšu.")
        return False
    if mimo(dst, os.path.realpath(p)):
        return False
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if z:
        shutil.copy2(z, p)
    else:
        zapis(p, data)
    return True


def kolize(dst, p):
    """Je na místě souboru složka, nebo je některá nadřazená složka v projektu soubor?"""
    if os.path.isdir(p) and not os.path.islink(p):
        return True
    d = os.path.dirname(p)
    while len(d) > len(dst):
        if os.path.lexists(d) and not os.path.isdir(d):
            return True
        d = os.path.dirname(d)
    return False


def nacti_cekajici(dst):
    """Konflikty čekající na --vyreseno: cesta → otisk (sha256) a záloha návrhu šablony, který uživatel dostal."""
    try:
        with open(os.path.join(dst, SABLONA, CEKAJICI), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def uloz_cekajici(dst, cek):
    p = os.path.join(dst, SABLONA, CEKAJICI)
    if mimo(dst, p):
        return
    if cek:
        zapis(p, (json.dumps(cek, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    elif os.path.isfile(p):
        os.remove(p)


def navrh(dst, cek, jmeno, nova_zal, nova):
    """Konflikt: novou verzi uloží do zálohy a zapamatuje si ji pro --vyreseno."""
    if zalohuj(dst, nova_zal, nova):
        cek[jmeno] = {"sha256": hashlib.sha256(nova).hexdigest(),
                      "zaloha": os.path.relpath(nova_zal, dst).replace(os.sep, "/")}


def aktualizuj(src, dst, cast, jmena, zaloha, vysl, stary, cek):
    """Aktualizuje dst/cast podle tří verzí: původní šablona (dst/.skill_sablona/cast), projekt a nová šablona
    (soubory `jmena` ze src). Soubory, které nová šablona už nemá, jen hlásí. Uloženou šablonu posune jen tam, kde se
    nová verze do projektu dostala; návrhy z konfliktů zapíše do cek. stary=True: projekt bez .skill_sablona/.
    Výsledek přidá do vysl[kategorie]."""
    puvodni = os.path.join(dst, SABLONA, cast)
    if mimo(dst, os.path.join(puvodni, "x"), os.path.join(dst, cast, "x")):   # celá složka je odkaz ven
        return
    skupiny = {}
    for rel in sorted(set(jmena) | set(soubory(puvodni) if os.path.isdir(puvodni) else ())):
        skupiny.setdefault(rel.lower() if NEROZLISUJE else rel, []).append(rel)
    for varianty in skupiny.values():
        if len(varianty) > 1:   # liší se jen velikostí písmen – na tomto disku je to jeden soubor: nic nezapisovat
            vysl["konflikt"].append(", ".join(cast + "/" + v.replace(os.sep, "/") for v in varianty)
                                    + " (liší se jen velikostí písmen)")
            continue
        rel = varianty[0]
        new, out, puv = os.path.join(src, rel), os.path.join(dst, cast, rel), os.path.join(puvodni, rel)
        nova_zal = os.path.join(zaloha, "nova_sablona", cast, rel)   # při konfliktu sem nová verze, projekt zůstane
        puvz = os.path.join(zaloha, "puvodni", cast, rel)
        jmeno = cast + "/" + rel.replace(os.sep, "/")
        if mimo(dst, out, puv, nova_zal, puvz):
            continue
        nova = nova_verze(new) if rel in jmena else None
        if kolize(dst, out) or kolize(dst, puv):
            print(f"POZOR: {jmeno} – v projektu je složka místo souboru (nebo naopak), přeskakuji.")
            vysl["konflikt" if nova is not None else "odstraneno"].append(jmeno + " (složka místo souboru)")
            continue
        cek.pop(jmeno, None)
        nase = lf(cti(out)) if os.path.isfile(out) and not os.path.islink(out) else None
        zaklad = lf(cti(puv)) if os.path.isfile(puv) else None
        if (jmeno in VZDY_SABLONA and nova is not None and nase is not None and zaklad is not None
                and nase not in (zaklad, lf(nova)) and zaklad != lf(nova)):   # změnil ho npm i šablona
            if not zalohuj(dst, puvz, z=out):   # bez zálohy nepřepisovat
                vysl["konflikt"].append(jmeno + " (zálohu nešlo zapsat, soubor zůstal)")
                continue
            zapis(out, nova, new)
            zapis(puv, nova, new)
            vysl["prepsano"].append(jmeno + " (generuje npm, starý v záloze puvodni/)")
            continue
        if nova is None:   # šablona soubor odstranila: nic nemazat, hlásit, dokud ho --vyreseno nepřevezme
            if os.path.lexists(out):
                vysl["odstraneno"].append(jmeno)
            continue
        if os.path.islink(out) or (nase is None and zaklad is None):   # symlink jen přepsat; nový soubor doplnit
            if os.path.lexists(out):
                vysl["prepsano"].append(jmeno)
            zapis(out, nova, new)
        elif nase is None:   # smazaný v projektu
            if zaklad == lf(nova):
                vysl["smazano"].append(jmeno)
                continue
            navrh(dst, cek, jmeno, nova_zal, nova)
            vysl["konflikt"].append(jmeno + " (smazáno v projektu)")
            continue
        elif nase == lf(nova):
            pass
        elif nase == zaklad:   # bez vlastních úprav
            vysl["prepsano"].append(jmeno)
            zapis(out, nova, new)
        elif zaklad == lf(nova):   # šablona beze změny
            vysl["ponechano"].append(jmeno)
            continue
        elif zaklad is None and stary:   # projekt ze starší verze bez uložené šablony: přepsat, starou verzi zazálohovat
            if not zalohuj(dst, puvz, z=out):   # bez zálohy nepřepisovat
                vysl["konflikt"].append(jmeno + " (zálohu nešlo zapsat, soubor zůstal)")
                continue
            zapis(out, nova, new)
            vysl["zalohovano"].append(jmeno)
        elif zaklad is None:   # soubor přidal projekt i nová šablona
            navrh(dst, cek, jmeno, nova_zal, nova)
            vysl["konflikt"].append(jmeno + " (nový v šabloně i v projektu)")
            continue
        else:
            sloucene, ok = sloucit(nase, zaklad, lf(nova))
            if not ok:
                navrh(dst, cek, jmeno, nova_zal, nova)
                if sloucene is not None:
                    zalohuj(dst, nova_zal + ".konflikt", sloucene)   # s gitem i návrh se značkami konfliktů
                vysl["konflikt"].append(jmeno)
                continue
            zapis(out, sloucene)
            vysl["slouceno"].append(jmeno)
        if zaklad != lf(nova) or not os.path.isfile(puv):   # nová verze je v projektu: posunout uloženou šablonu
            zapis(puv, nova, new)


def vyresit(dst, cesta):
    """--vyreseno: uloží jako základ návrh šablony, který uživatel u konfliktu dostal (záznam v cekajici.json), bez
    záznamu aktuální verzi šablony; soubor v projektu nechá. Nemá-li soubor šablona, základ smaže a soubor patří
    jen projektu. Vrátí False, když není co vyřešit."""
    if not os.path.isdir(os.path.join(dst, SABLONA)):
        print(f"POZOR: projekt nemá {SABLONA}/ – nejdřív ho aktualizujte (spusťte skript bez --vyreseno).")
        return False
    rel = os.path.normpath(os.path.relpath(cesta, dst) if os.path.isabs(cesta) else cesta).replace(os.sep, "/")
    cast, _, zbytek = rel.partition("/")
    src = {"web": os.path.join(SKILL, "template", "web"), "tools": os.path.join(SKILL, "tools")}.get(cast)
    if not src or not zbytek:
        print(f"POZOR: {cesta} – zadejte cestu ve web/ nebo tools/ projektu (např. web/src/pages/index.astro).")
        return False
    new, puv = os.path.join(src, zbytek), os.path.join(dst, SABLONA, cast, zbytek)
    if mimo(dst, puv) or kolize(dst, puv):
        print(f"POZOR: {rel} – základ nejde zapsat (odkaz ven nebo složka místo souboru).")
        return False
    if cast == "web":
        v_sablone = os.path.isfile(new) and not set(zbytek.split("/")) & set(SKIP)
    else:
        v_sablone = os.path.isfile(new) and "/" not in zbytek and zbytek.endswith((".py", ".sh")) and zbytek != "novy_projekt.py"
    cek = nacti_cekajici(dst)
    zaznam = cek.get(rel)
    if isinstance(zaznam, dict):
        z = os.path.join(dst, str(zaznam.get("zaloha", "")))
        data = cti(z) if os.path.isfile(z) and not mimo(dst, os.path.realpath(z)) else None
        if data is None or hashlib.sha256(data).hexdigest() != zaznam.get("sha256"):
            print(f"POZOR: {rel} – uložený návrh {zaznam.get('zaloha')} chybí nebo se změnil; nevyřešeno. Spusťte"
                  " aktualizaci znovu (uloží nový návrh) a pak --vyreseno.")
            return False
        zapis(puv, data)
        del cek[rel]
        uloz_cekajici(dst, cek)
        print(f"Vyřešeno: {rel} – jako základ je uložený návrh {zaznam['zaloha']}, soubor v projektu zůstal beze změny.")
    elif v_sablone:
        zapis(puv, nova_verze(new), new)
        print(f"Vyřešeno: {rel} – návrh z konfliktu není zaznamenaný, jako základ je uložená aktuální verze šablony;"
              " soubor v projektu zůstal beze změny.")
    elif os.path.isfile(puv):
        os.remove(puv)
        print(f"Vyřešeno: {rel} – šablona ho už nemá, soubor v projektu zůstal a patří jen projektu.")
    else:
        print(f"POZOR: {rel} není v šabloně ani v {SABLONA}/ – není co vyřešit.")
        return False
    return True


SIT_ZAKAZ = ["Bash(curl:*)", "Bash(wget:*)"]   # stahování z archivů jen přes tools/slusne.py (curl přes něj jde)
# Hlídač spustit, jen když soubor existuje: chybějící skript by Python ukončil kódem 2 a ten by zablokoval každý příkaz.
# mimo Windows ne cestu s číslem verze (po aktualizaci Pythonu by zmizela); na Windows lomítka (projdou Git Bash i cmd)
KOD = ("import os,runpy;p=os.path.join(os.environ.get('CLAUDE_PROJECT_DIR','.'),'tools','hlidac_site.py');"
       "os.path.isfile(p) and runpy.run_path(p,run_name='__main__')")
PY = sys.executable.replace("\\", "/") if os.name == "nt" else "python3"
HLIDAC = f'"{PY}" -I -c "{KOD}"'   # tvar se shellem (macOS, Linux)
MATCHER = "Bash|PowerShell|Monitor"   # Monitor spouští příkaz v bashi stejně jako Bash


def _python_windows():
    """Python pro hook na Windows: vždy plná cesta k Pythonu, kterým běží aktualizace. Hooky Claude Code mají jiný PATH
    a „python“ tam může vést na nefunkční zástupce z Microsoft Store – hlídač by se tiše nespustil. Projekt sdílený
    přes OneDrive na dvou počítačích opraví aktualizace spuštěná na druhém počítači (hook se pokaždé přepíše)."""
    return sys.executable


def hook_hlidace():
    """Hook hlídače. Na Windows bez shellu (command + args): hooky tam běží v Git Bashi, nebo v PowerShellu, když
    Git Bash chybí – a tam by příkaz s uvozovkami byl chyba syntaxe a Claude Code by pak zamítal každý příkaz."""
    if os.name == "nt":
        return {"type": "command", "command": _python_windows(), "args": ["-I", "-X", "utf8", "-c", KOD], "timeout": 10}
    return {"type": "command", "command": HLIDAC, "timeout": 10}


def nastaveni(dst, hlidac):
    """Doplní do .claude/settings.json zákaz curl/wget; hlidac=True/False zapne/vypne hook, None nechá, jak je."""
    path = os.path.join(dst, ".claude", "settings.json")
    data = {}
    if os.path.exists(path):
        try:
            data = json.load(open(path, encoding="utf-8"))
        except ValueError:
            print(f"POZOR: {path} není platný JSON – nastavení brzdy jsem nedoplnil. Oprav ho a spusť znovu.")
            return
    puvodni = json.dumps(data, sort_keys=True)
    deny = data.setdefault("permissions", {}).setdefault("deny", [])
    deny += [r for r in SIT_ZAKAZ if r not in deny]
    pre = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
    nase = [h for h in pre if "hlidac_site.py" in json.dumps(h)]
    for h in nase:   # aktualizace projektu: hook obnovit (cesta k Pythonu i tvar se mohly změnit)
        h["matcher"] = MATCHER
        h["hooks"] = [hook_hlidace()]
    if hlidac is True and not nase:
        pre.append({"matcher": MATCHER, "hooks": [hook_hlidace()]})
    elif hlidac is False:
        pre[:] = [h for h in pre if h not in nase]
    if not pre:
        del data["hooks"]["PreToolUse"]
    if not data["hooks"]:
        del data["hooks"]
    if json.dumps(data, sort_keys=True) != puvodni:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
    zapnuty = any("hlidac_site.py" in json.dumps(h) for h in data.get("hooks", {}).get("PreToolUse", []))
    print("Hlídač sítě:", "zapnutý" if zapnuty else "vypnutý (zapnout: --hlidac)")


def _verze(text):
    m = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", (text or "").strip())
    return tuple(int(x) for x in m.groups()) if m else None


def zkontroluj_verzi(dst):
    """Projekt založený novějším skillem neaktualizovat starší kopií skillu – vrátilo by ho to ke staré verzi."""
    try:
        with open(os.path.join(dst, ".skill_verze"), encoding="utf-8") as f:
            projekt = f.read().strip()
        with open(os.path.join(SKILL, "VERZE"), encoding="utf-8") as f:
            skill = f.read().strip()
    except OSError:
        return
    p, s = _verze(projekt), _verze(skill)
    if p and s and p > s:
        sys.exit(f"CHYBA: projekt je z verze skillu {projekt}, tento skill je starší ({skill}). Aktualizace by projekt vrátila\n"
                 "ke starší verzi, proto nic neměním. Aktualizujte nejdřív skill (README, část Instalace) a pak to zkuste znovu.")


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        sys.exit(__doc__)
    dst = os.path.abspath(os.path.expanduser(sys.argv[1]))
    if "--vyreseno" in sys.argv:   # jen označit ručně vyřešené soubory, nic dalšího
        cesty = [sys.argv[i + 1] for i, a in enumerate(sys.argv[:-1]) if a == "--vyreseno"]
        if not cesty:
            sys.exit(__doc__)
        sys.exit(0 if all([vyresit(dst, c) for c in cesty]) else 1)
    zkontroluj_verzi(dst)
    demo = "--ukazka" in sys.argv
    os.makedirs(dst, exist_ok=True)
    copy_tree(os.path.join(SKILL, "template", "ukazka" if demo else "data"), os.path.join(dst, "data"))
    if demo:
        for sub in ("vyrezy", "zdroje"):
            src = os.path.join(SKILL, "template", "ukazka_" + sub)
            if os.path.isdir(src):
                copy_tree(src, os.path.join(dst, sub))
    zaloha = os.path.join(dst, "pracovni", "zaloha_" + time.strftime("%Y%m%d-%H%M%S"))
    vysl = {k: [] for k in ("prepsano", "zalohovano", "slouceno", "ponechano", "smazano", "odstraneno", "konflikt")}
    stary = not os.path.isdir(os.path.join(dst, SABLONA))   # projekt ze starší verze (nebo nový)
    cek = nacti_cekajici(dst)
    sablona_webu = os.path.join(SKILL, "template", "web")
    aktualizuj(sablona_webu, dst, "web", sorted(soubory(sablona_webu)), zaloha, vysl, stary, cek)
    tools = os.path.join(dst, "tools")
    os.makedirs(tools, exist_ok=True)
    nastroje = sorted(f for f in os.listdir(os.path.join(SKILL, "tools"))
                      if f.endswith((".py", ".sh")) and f != "novy_projekt.py")
    aktualizuj(os.path.join(SKILL, "tools"), dst, "tools", nastroje, zaloha, vysl, stary, cek)
    uloz_cekajici(dst, cek)
    for f in nastroje:   # i ponechaný vlastní .sh s CRLF: Git Bash by skript nespustil
        p = os.path.join(tools, f)
        if f.endswith(".sh") and os.path.isfile(p) and not os.path.islink(p) and not mimo(dst, p):
            data = cti(p)
            if b"\r\n" in data:
                zapis(p, data.replace(b"\r\n", b"\n"))
    for d in ("vyrezy", "zdroje", "dokumenty", "pracovni"):
        os.makedirs(os.path.join(dst, d), exist_ok=True)
    os.makedirs(os.path.join(dst, ".claude"), exist_ok=True)
    for name in ("CLAUDE.md", ".gitignore", ".gitattributes", "poznamky_pro_skill.md", os.path.join(".claude", "launch.json")):
        out = os.path.join(dst, name)
        if not os.path.lexists(out):
            copy(os.path.join(SKILL, "template", name), out)
    nastaveni(dst, True if "--hlidac" in sys.argv else False if "--bez-hlidace" in sys.argv else None)
    with open(os.path.join(dst, ".skill_verze"), "w", encoding="utf-8") as f:   # SKILL.md podle něj nabídne aktualizaci
        f.write(open(os.path.join(SKILL, "VERZE"), encoding="utf-8").read())
    print("Projekt připraven:", dst)
    for k, popis in (("prepsano", "Přepsáno novou verzí (bez vlastních úprav)"),
                     ("zalohovano", "Přepsáno, původní verze je v " + os.path.join(zaloha, "puvodni")
                      + " (projekt neměl uloženou šablonu – vlastní úpravy převezměte ze zálohy)"),
                     ("slouceno", "Sloučeno (vlastní úpravy i změny šablony)"),
                     ("ponechano", "Ponecháno (vlastní úpravy, šablona beze změny)"),
                     ("smazano", "Smazáno v projektu, ponecháno smazané (šablona beze změny)"),
                     ("odstraneno", "Šablona už nemá – zkontrolujte, případně smažte ručně a spusťte --vyreseno"),
                     ("konflikt", "Ke kontrole (soubor zůstal beze změny, nová verze je v "
                      + os.path.join(zaloha, "nova_sablona") + "; u konfliktu sloučení s gitem vedle i návrh se"
                      " značkami jako .konflikt)")):
        if vysl[k]:
            print(f"{popis}, {len(vysl[k])}:")
            for f in vysl[k]:
                print("  " + f)
    if vysl["konflikt"] or vysl["odstraneno"]:
        print("Hlásí se při každé aktualizaci, dokud je nevyřešíte. Po ručním převzetí změn spusťte:\n"
              f"  python3 -I {os.path.abspath(__file__)} {dst} --vyreseno <soubor> [--vyreseno <soubor> …]")
    if any(f.startswith("web/") for k in ("prepsano", "zalohovano", "slouceno") for f in vysl[k]):
        print("Ve web/ pak `npm install` a `npm run data`.")


if __name__ == "__main__":
    main()
