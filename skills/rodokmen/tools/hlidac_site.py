#!/usr/bin/env python3
"""Hlídač síťových příkazů (volitelný hook PreToolUse v .claude/settings.json projektu).

Zapíná se příkazem `novy_projekt.py <projekt> --hlidac`, vypíná `--bez-hlidace`.
Než Claude spustí příkaz v Bash nebo PowerShellu, hlídač zkontroluje, jestli nejde na web archivu mimo brzdu
(tools/slusne.py): curl/wget s adresou, Python skript se síťovým importem, shellový skript s curl, v PowerShellu
Invoke-WebRequest a podobně. Takový příkaz zamítne a Claudovi napíše, jak ho spustit přes brzdu.
Sám nic nestahuje a nikam nic neposílá. Je to textová heuristika, ne neprůstřelná ochrana.
Při jakékoli vlastní chybě příkaz pustí – rozbitý hlídač nesmí zablokovat práci.
"""
import json, os, re, sys

CMD = r"(?:^|[;&|(\n`]|\$\(|\b(?:then|do|else|exec|env|time|nohup|xargs|sudo)\s)\s*"
CURL = re.compile(CMD + r"(curl|wget)(?:\.exe)?(?=\s|$)", re.I)
PYTHON = re.compile(CMD + r"(?:\S*/)?(?:python3?|py)(?:\.exe)?(?:\s+-3)?(?=\s|$)", re.I)
SHELL = re.compile(CMD + r"(?:(?:bash|sh|zsh)\s+|\./)(\S+\.sh)\b")
SIT_PY = re.compile(r"^\s*(?:import|from)\s+(?:requests|httpx|aiohttp|urllib3|pycurl|socket|urllib\.request|http\.client)\b"
                    r"|^\s*from\s+urllib\s+import\s+.*\brequest\b|urllib\.request\.|urlopen\(", re.M)
PS = re.compile(r"\b(Invoke-WebRequest|Invoke-RestMethod|iwr|irm|curl\.exe|wget|Start-BitsTransfer|Net\.WebClient|"
                r"HttpClient|DownloadString|DownloadFile)\b", re.I)
URL = re.compile(r"https?://([^/\s\"'`:;)]+)", re.I)
VOLNE = ("localhost", "127.0.0.1", "0.0.0.0", "netlify.app", "netlify.com", "github.com", "githubusercontent.com",
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


def posoudit(tool, cmd, cwd):
    """Vrátí důvod zamítnutí, nebo None (pustit)."""
    if tool == "PowerShell":
        if PS.search(cmd) and "slusne.py" not in cmd and not jen_volne(cmd):
            return "PowerShell stahuje z webu mimo brzdu"
        tool = "Bash"   # python a curl.exe v PowerShellu posoudit stejně
    if tool != "Bash":
        return None
    for m in CURL.finditer(cmd):
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
            if SIT_PY.search(obsah):
                return f"Python skript {args[0]} používá síť"
        if SIT_PY.search(cmd):                   # python -c "…" nebo heredoc s kódem v příkazu
            return "Python se síťovým importem přímo v příkazu"
    for m in SHELL.finditer(cmd):
        obsah = cist(m.group(1), cwd)
        if "slusne.py" not in obsah and CURL.search(obsah) and not jen_volne(obsah):
            return f"shellový skript {m.group(1)} volá curl/wget"
    return None


def main():
    try:
        vstup = json.load(sys.stdin)
        tool = vstup.get("tool_name", "")
        cmd = (vstup.get("tool_input") or {}).get("command", "") or ""
        duvod = posoudit(tool, cmd, vstup.get("cwd") or os.getcwd())
    except Exception:          # rozbitý hlídač příkaz pustí
        return 0
    if duvod:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "deny",
            "permissionDecisionReason": f"Hlídač sítě: {duvod}.\n{RADA}"}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
