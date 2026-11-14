#!/usr/bin/env python3
"""Hlídač síťových příkazů (volitelný hook PreToolUse v .claude/settings.json a .devin/hooks.v1.json projektu).

Zapíná se příkazem `novy_projekt.py <projekt> --hlidac`, vypíná `--bez-hlidace`.
Než Claude spustí příkaz v Bash nebo PowerShellu, hlídač zkontroluje, jestli nejde na web archivu mimo brzdu
(tools/slusne.py): curl/wget s adresou, Python skript se síťovým importem, shellový skript s curl, v PowerShellu
Invoke-WebRequest a podobně. Takový příkaz zamítne a Claudovi napíše, jak ho spustit přes brzdu.
Sám nic nestahuje a nikam nic neposílá. Je to textová heuristika, ne neprůstřelná ochrana.
Při jakékoli vlastní chybě příkaz pustí – rozbitý hlídač nesmí zablokovat práci.
"""
import json, os, re, sys

CMD = r"(?:^|[;&|(\n`]|\$\(|\b(?:then|do|else|exec|env|time|nohup|xargs|sudo)\s|\b(?:bash|sh|zsh)\s+-c\s+[\"']|\beval\s+[\"']?)\s*"
CURL = re.compile(CMD + r"(curl|wget)(?:\.exe)?(?=\s|$)", re.I)
PYTHON = re.compile(CMD + r"(?:\S*/)?(?:python3?|py)(?:\.exe)?(?:\s+-3)?(?=\s|$)", re.I)
SHELL = re.compile(CMD + r"(?:(?:bash|sh|zsh)\s+|\./)(\S+\.sh)\b")
SIT_MOD = r"(?:requests|httpx|aiohttp|urllib3|pycurl|socket|urllib\.request|http\.client)\b"
ZAC = r"(?:^|[;\"'])\s*"   # začátek řádku, příkazu za středníkem nebo kódu v python -c "…"


def _sit_py(zac):
    return re.compile(zac + r"from\s+" + SIT_MOD +
                      "|" + zac + r"import\s+(?:[\w.]+(?:\s+as\s+\w+)?\s*,\s*)*" + SIT_MOD +   # i „import json, urllib.request“
                      "|" + zac + r"from\s+urllib\s+import\s+.*\brequest\b|urllib\.request\.|urlopen\(", re.M)


SIT_PY = _sit_py(ZAC)
SIT_PY_RADEK = _sit_py(r"(?:^|;)\s*")   # kód v heredocu: import jen na začátku řádku, ne „import http.client“ v řetězci
HEREDOC = re.compile(r"<<-?\s*['\"]?\w+|@['\"]\s*\n")   # bash <<EOF, PowerShell @' … '@
PS = re.compile(r"\b(Invoke-WebRequest|Invoke-RestMethod|iwr|irm|curl\.exe|wget|Start-BitsTransfer|Net\.WebClient|"
                r"HttpClient|DownloadString|DownloadFile)\b", re.I)
URL = re.compile(r"https?://([^/\s\"'`:;)]+)", re.I)
VOLNE = ("localhost", "127.0.0.1", "0.0.0.0", "netlify.app", "netlify.com", "workers.dev", "cloudflare.com", "github.com", "githubusercontent.com",
         "npmjs.org", "pypi.org", "pythonhosted.org")
RADA = ("Síť na weby archivů jen přes brzdu proti zablokování (tools/slusne.py), i u pomocníků:\n"
        "  python3 -I tools/slusne.py curl …            místo curl/wget\n"
        "  python3 -I tools/slusne.py pracovni/x.py …   místo python3 pracovni/x.py (skript se síťí)\n"
        "  python3 -I tools/slusne.py bash pracovni/x.sh …\n"
        "Nástroje v tools/ brzdu mají samy, spouštěj je normálně. Brzdu neobcházej (jiný příkaz, prohlížeč).")


def volny(host):
    host = host.lower().rstrip(".")
    return any(host == v or host.endswith("." + v) for v in VOLNE)


def jen_volne(text):
    hosts = URL.findall(text)
    return bool(hosts) and all(volny(h) for h in hosts)


def cist(path, cwd):
    try:
        with open(os.path.join(cwd, os.path.expanduser(path)), encoding="utf-8", errors="replace") as f:
            return f.read(500_000)
    except OSError:
        return ""


RETEZEC = re.compile(r'"(?:[^"\\]|\\.)*"|\'[^\']*\'')
SPUSTI_RETEZEC = re.compile(r"(?:-c|\beval)\s*$")
HEREDOC_TELO = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n(.*?)^\s*\1\s*$", re.S | re.M)
PY_C = re.compile(r"""^((?:\s+-[IuBEsSOqvbdx]+|\s+-X\s+\S+|\s+-W\s+\S+)*)\s+-c\s*("(?:[^"\\]|\\.)*"|'[^']*'|\S+)""")


def bez_textu(cmd):
    """Příkaz s vymazaným obsahem textů v uvozovkách („git commit -m "…; curl …"“ nic nespouští) – kromě textů,
    které se opravdu spustí: za `-c` (bash/sh -c) či `eval` a s `$(…)` nebo `…` uvnitř uvozovek."""
    def nahrad(m):
        t = m.group(0)
        if SPUSTI_RETEZEC.search(cmd[:m.start()]) or (t[0] == '"' and ("$(" in t or "`" in t)):
            return t
        return t[0] + " " * (len(t) - 2) + t[-1]
    return RETEZEC.sub(nahrad, cmd)


def python_kod(cmd, od):
    """Kód, který Python spuštěný na pozici `od` opravdu vykoná: text za -c (jen přepínače Pythonu před ním)
    a těla heredoců v příkazu (i heredoc, který skript teprve zapisuje – soubor ještě neexistuje)."""
    m = PY_C.match(cmd[od:])
    return ([m.group(2).strip("\"'")] if m else []), [t for _, t in HEREDOC_TELO.findall(cmd)]


def posoudit(tool, cmd, cwd):
    """Vrátí důvod zamítnutí, nebo None (pustit)."""
    ps = tool in ("PowerShell", "exec")   # "exec" (Devin) může na Windows bez Git Bashe jet v PowerShellu
    if tool in ("Monitor", "exec"):   # Monitor spouští v bashi jako Bash; "exec" je shellový nástroj Devinu
        tool = "Bash"
    if ps:
        if PS.search(cmd) and "slusne.py" not in cmd and not jen_volne(cmd):
            return "PowerShell stahuje z webu mimo brzdu"
        tool = "Bash"   # python a curl.exe v PowerShellu posoudit stejně
    if tool != "Bash":
        return None
    holy = bez_textu(cmd)   # curl/wget/skript jen tam, kde se opravdu spouští, ne v textu v uvozovkách
    for m in CURL.finditer(holy):
        zbytek = re.split(r"[;&|\n]", cmd[m.end():], maxsplit=1)[0]
        if (URL.search(zbytek) or "$" in zbytek) and not jen_volne(zbytek):
            return f"{m.group(1)} přímo na web"
    for m in PYTHON.finditer(cmd):
        zbytek = re.split(r"[;&|]", cmd[m.end():], maxsplit=1)[0].split()
        args = [a for a in zbytek if a not in ("-I", "-u", "-X", "utf8", "-B", "-E", "-s")]
        if args and args[0].strip("\"'").endswith("slusne.py"):
            continue
        if args and args[0] == "-m":
            continue
        if args and args[0].strip("\"'").endswith(".py"):
            obsah = cist(args[0].strip("\"'"), cwd)
            if "import slusne" in obsah:          # nástroje v tools/ se brzdí samy
                continue
            if SIT_PY.search(obsah) and not jen_volne(obsah):   # síť jen na povolené weby (verze.py → GitHub) projde
                return f"Python skript {args[0]} používá síť"
        c_kod, heredocy = python_kod(cmd, m.end())   # jen kód, který Python opravdu spustí, ne zbytek příkazu
        if args and args[0] == "-" and not heredocy:   # kód rourou („echo … | python -“): posoudit celý příkaz
            c_kod.append(cmd)
        if any(SIT_PY.search(k) and not jen_volne(k) for k in c_kod) or \
                any(SIT_PY_RADEK.search(t) and not jen_volne(t) for t in heredocy):
            return "Python se síťovým importem přímo v příkazu"
    for m in SHELL.finditer(holy):
        obsah = cist(m.group(1), cwd)
        if "slusne.py" not in obsah and CURL.search(obsah) and not jen_volne(obsah):
            return f"shellový skript {m.group(1)} volá curl/wget"
    return None


def main():
    try:
        if hasattr(sys.stdin, "reconfigure"):   # Claude Code posílá UTF-8; na Windows by se četl v cp1250
            sys.stdin.reconfigure(encoding="utf-8-sig")
        vstup = json.load(sys.stdin)
        tool = vstup.get("tool_name", "")
        cmd = (vstup.get("tool_input") or {}).get("command", "") or ""
        duvod = posoudit(tool, cmd, vstup.get("cwd") or os.getcwd())   # payload Devinu "cwd" nemusí mít
    except Exception:          # rozbitý hlídač příkaz pustí
        return 0
    if duvod:   # oba formáty: Claude Code čte "permissionDecision" v hookSpecificOutput, Devin "decision"/"reason"
        print(json.dumps({"decision": "block", "reason": f"Hlídač sítě: {duvod}.\n{RADA}",
                          "hookSpecificOutput": {
                              "hookEventName": "PreToolUse", "permissionDecision": "deny",
                              "permissionDecisionReason": f"Hlídač sítě: {duvod}.\n{RADA}"}}))   # \uXXXX: čeština projde i v cp1250
    return 0


if __name__ == "__main__":
    sys.exit(main())
