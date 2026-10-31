#!/usr/bin/env python3
"""Hook PreToolUse (Bash, PowerShell, Monitor): zamítne síťová volání mimo wrapper scripts/slusne.py.

Zamítne (textová heuristika, ne neprůstřelná ochrana):
- Python se síťovým importem (soubor, -c, heredoc nebo here-string) spuštěný mimo wrapper,
- curl / wget s adresou mimo localhost, v PowerShellu i Invoke-WebRequest, Invoke-RestMethod a WebClient,
- shellový skript, který volá curl nebo síťový Python, spuštěný mimo wrapper.
Zamítnutí (kód 2) vrátí agentovi přesný návod, jak příkaz spustit přes wrapper. Když hook sám selže, příkaz pustí.
Nastavení v .claude/settings.json projektu (hooks → PreToolUse, matcher "Bash|PowerShell|Monitor").
"""
import json, os, re, sys

sys.dont_write_bytecode = True   # žádné scripts/__pycache__
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from slusne import curl_cile   # noqa: E402  (stejné čtení voleb curl jako ve wrapperu)

PROJEKT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY_CMD = "python -I -X utf8" if os.name == "nt" else "python3 -I"
PY_JMENO = re.compile(r"python[\d.]*|pythonw[\d.]*|py")
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
PS_SIT = {"invoke-webrequest", "iwr", "invoke-restmethod", "irm", "start-bitstransfer"}
PS_NET = re.compile(r"Net\.WebClient|Net\.Http\.HttpClient|Net\.(Http)?WebRequest\]|\.Download(String|File|Data)(Async)?\s*\(", re.I)
LOKAL = re.compile(r"^(https?://)?(localhost|127\.\d+\.\d+\.\d+|\[::1\]|0\.0\.0\.0)(:\d+)?(/|$)", re.I)
SIT_MODULY = {"urllib.request", "urllib3", "http.client", "requests", "httpx", "aiohttp", "socket", "ftplib", "pycurl",
              "websocket", "websockets", "mechanize", "selenium", "playwright"}
PREDPONY = {"then", "do", "else", "elif", "if", "while", "until", "!", "{", "}", "sudo", "nohup", "time", "exec",
            "command", "builtin", "&"}


# ---------- rozklad příkazu ----------
def _heredocy(text):
    """Vyjme těla heredoců (bash): vrací text bez nich a seznam těl."""
    radky, ven, tela, i = text.split("\n"), [], [], 0
    while i < len(radky):
        r = radky[i]
        ven.append(r)
        i += 1
        for m in re.finditer(r"<<(-?)\s*(['\"]?)([A-Za-z_][\w.-]*)\2", r):
            if r[max(0, m.start() - 1):m.start()] == "<":   # <<< here-string
                continue
            telo = []
            while i < len(radky):
                x = radky[i]
                i += 1
                if (x.lstrip("\t") if m.group(1) else x).rstrip("\r") == m.group(3):
                    break
                telo.append(x)
            tela.append("\n".join(telo))
    return "\n".join(ven), tela


def _here_stringy(text):
    """PowerShell @'…'@ a @"…"@: vyjme obsah."""
    tela = []

    def pryc(m):
        tela.append(m.group(2))
        return " __HERE__ "
    return re.sub(r"@(['\"])\r?\n(.*?)\r?\n\1@", pryc, text, flags=re.S), tela


def _konec_zavorky(t, k, ps):
    esc = "`" if ps else "\\"
    hl, q, i = 0, None, k
    while i < len(t):
        c = t[i]
        if q:
            if c == q:
                q = None
            elif c == esc and q == '"':
                i += 1
        elif c == esc:
            i += 1
        elif c in "'\"":
            q = c
        elif c == "(":
            hl += 1
        elif c == ")":
            hl -= 1
            if hl == 0:
                return i
        i += 1
    return len(t)


def _substituce(text, ps):
    """$( … ) a v bashi `…` nahradí značkou; vrací (text, [vnitřní příkazy])."""
    esc = "`" if ps else "\\"
    ven, uvnitr, q, i, n = [], [], None, 0, len(text)
    while i < n:
        c = text[i]
        if q == "'":
            ven.append(c)
            if c == "'":
                q = None
            i += 1
        elif c == esc and i + 1 < n:
            ven.append(text[i:i + 2])
            i += 2
        elif c == "'" and q is None:
            q = "'"
            ven.append(c)
            i += 1
        elif c == '"':
            q = None if q == '"' else '"'
            ven.append(c)
            i += 1
        elif c == "$" and text.startswith("(", i + 1):
            j = _konec_zavorky(text, i + 1, ps)
            uvnitr.append(text[i + 2:j])
            ven.append(" __SUBST__ ")
            i = j + 1
        elif c == "`" and not ps:
            j = text.find("`", i + 1)
            j = n if j < 0 else j
            uvnitr.append(text[i + 1:j])
            ven.append(" __SUBST__ ")
            i = j + 1
        else:
            ven.append(c)
            i += 1
    return "".join(ven), uvnitr


def _segmenty(text, ps):
    """Jednoduché příkazy (dělí ; & | && || nový řádek a závorky) jako seznamy slov bez uvozovek + surový text."""
    esc = "`" if ps else "\\"
    segs, slova, w, q, raw = [], [], None, None, []
    i, n = 0, len(text)

    def slovo():
        nonlocal w
        if w is not None:
            slova.append(w)
            w = None

    def segment():
        nonlocal slova, raw
        slovo()
        if slova:
            segs.append((slova, "".join(raw).strip()))
        slova, raw = [], []

    while i < n:
        c = text[i]
        if q == "'":
            raw.append(c)
            if c == "'":
                if ps and text.startswith("''", i):
                    w += "'"
                    raw.append("'")
                    i += 2
                    continue
                q = None
            else:
                w += c
            i += 1
            continue
        if q == '"':
            raw.append(c)
            if c == '"':
                q = None
            elif c == esc and i + 1 < n:
                w += text[i + 1]
                raw.append(text[i + 1])
                i += 2
                continue
            else:
                w += c
            i += 1
            continue
        if c in "'\"":
            q = c
            w = w or ""
            raw.append(c)
            i += 1
            continue
        if c == esc and i + 1 < n:
            if text[i + 1] not in "\r\n":
                w = (w or "") + text[i + 1]
            raw.append(text[i:i + 2])
            i += 2
            continue
        if c == "#" and w is None:   # komentář do konce řádku
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        if c == "$" and text.startswith("{", i + 1):   # ${VAR}
            j = text.find("}", i)
            j = n - 1 if j < 0 else j
            w = (w or "") + text[i:j + 1]
            raw.append(text[i:j + 1])
            i = j + 1
            continue
        if c == "&" and ((i > 0 and text[i - 1] in "<>") or text.startswith(">", i + 1)):   # 2>&1, &>soubor
            w = (w or "") + c
            raw.append(c)
            i += 1
            continue
        if c in "\r\n;|&()" or (c in "{}" and (ps or (w is None and (i + 1 >= n or text[i + 1] in " \t\r\n;")))):
            segment()
            i += 1
            continue
        if c in " \t":
            slovo()
            raw.append(c)
            i += 1
            continue
        w = (w or "") + c
        raw.append(c)
        i += 1
    segment()
    return segs


def _prikaz(slova):
    """Index slova, které je příkazem (přeskočí VAR=…, env, timeout, xargs, & …)."""
    i = 0
    while i < len(slova):
        s, ls = slova[i], slova[i].lower()
        if re.match(r"[A-Za-z_]\w*=", s) or ls in PREDPONY:
            i += 1
        elif ls == "env":
            i += 1
            while i < len(slova) and (slova[i].startswith("-") or "=" in slova[i]):
                i += 2 if slova[i] in ("-u", "-C", "-S", "--unset", "--chdir") else 1
        elif ls in ("timeout", "nice", "stdbuf", "xargs"):
            i += 1
            while i < len(slova) and slova[i].startswith("-"):
                i += 2 if slova[i] in ("-n", "-k", "-s", "-I", "-P", "-L", "-d", "-a", "-E", "-o", "-e", "-i") else 1
            if ls == "timeout":
                i += 1
        else:
            return i
    return None


def _jmeno(w):
    n = re.split(r"[\\/]", w)[-1].lower()
    return n[:-4] if n.endswith(".exe") else n


def _cesta(p, ctx):
    p = os.path.expanduser(p)
    if os.name == "nt" and re.match(r"/[A-Za-z]/", p):
        p = p[1] + ":" + p[2:]
    for zaklad in (ctx["cwd"], PROJEKT):
        k = p if os.path.isabs(p) else os.path.join(zaklad, p)
        if os.path.isfile(k):
            return k
    return None


def _cti(p, ctx):
    k = _cesta(p, ctx)
    if not k:
        return None
    try:
        with open(k, encoding="utf-8", errors="replace") as f:
            return f.read(300_000)
    except OSError:
        return None


# ---------- co je síť ----------
def _sitovy_kod(kod, ctx, hloubka=0):
    for m in re.finditer(r"\bimport\s+([\w.]+(?:\s+as\s+\w+)?(?:\s*,\s*[\w.]+(?:\s+as\s+\w+)?)*)", kod):
        for jm in m.group(1).split(","):
            jm = jm.split()[0]
            if jm in SIT_MODULY or jm.split(".")[0] in SIT_MODULY - {"urllib.request", "http.client"}:
                return True
    for m in re.finditer(r"\bfrom\s+([\w.]+)\s+import\s+([\w\s,()*]+)", kod):
        mod, co = m.group(1), m.group(2)
        if mod in SIT_MODULY or mod.split(".")[0] in SIT_MODULY - {"urllib.request", "http.client"} \
                or (mod == "urllib" and re.search(r"\brequest\b", co)) or (mod == "http" and re.search(r"\bclient\b", co)):
            return True
    if re.search(r"\burlopen\s*\(|\burllib\.request\.|__import__\(\s*['\"](urllib\.request|requests|http\.client|socket|urllib3|httpx)", kod):
        return True
    if re.search(r"\b(subprocess|os\.system|os\.popen|Popen)\b", kod) and re.search(r"""['"\[\s](curl|wget)(\.exe)?['"\s,]""", kod):
        return True
    if hloubka == 0:   # skript spouští jiný skript (subprocess s tools/x.py, x.sh)
        for p in set(re.findall(r"""['"]([^'"\s]+\.(?:py|sh))['"]""", kod)):
            obsah = _cti(p, ctx)
            if obsah and (_sitovy_kod(obsah, ctx, 1) if p.endswith(".py") else analyzuj(obsah, False, ctx["cwd"], 3)):
                return True
    return False


def _sitova_adresa(a):
    if "$" in a or "__SUBST__" in a:   # proměnná – cíl neznáme
        return True
    if re.search(r"(https?|ftps?)://", a, re.I):
        return not LOKAL.match(a)
    return bool(re.match(r"[\w-]+(\.[\w-]+)+(:\d+)?/", a)) and not LOKAL.match(a)


# ---------- kontrola jednoho příkazu ----------
def _wrap(ctx):
    w = os.path.join(PROJEKT, "scripts", "slusne.py")
    if os.path.normcase(os.path.abspath(ctx["cwd"])) == os.path.normcase(PROJEKT):
        return "scripts/slusne.py"
    return w.replace("\\", "/")


def _navrh_python(raw, ctx):
    m = re.search(r"""(?:^|(?<=[\s&]))(?:"[^"]*python[^"]*"|'[^']*python[^']*'|\S*python[\d.]*(?:\.exe)?|py(?:\.exe)?)"""
                  r"""((?:\s+-(?:X\s*\S+|W\s*\S+|[A-Za-z0-9]+))*?)(?=\s+(?:-c\b|-\s|-$|[^-\s]))""", raw, re.I)
    if not m:
        return None
    return raw[:m.end()] + " " + _wrap(ctx) + raw[m.end():]


def _navrh_pred(raw, slovo, ctx):
    i = raw.find(slovo)
    if i < 0 or _jmeno(slovo) == "wget":   # wget má jiné volby než curl – návrh by byl špatně
        return None
    return raw[:i] + f"{PY_CMD} {_wrap(ctx)} " + raw[i:]


def _python(slova, k, raw, ctx):
    i, kod, skript, vstup = k + 1, None, None, None
    while i < len(slova):
        a = slova[i]
        if a in ("-X", "-W"):
            i += 2
            continue
        if a == "-c":
            kod = slova[i + 1] if i + 1 < len(slova) else ""
            break
        if a == "-m":
            return None
        if a == "-":
            break
        if re.match(r"\d*[<>]", a):   # přesměrování
            if a == "<" and i + 1 < len(slova):
                vstup = slova[i + 1]
            elif a.startswith("<") and not a.startswith("<<"):
                vstup = a[1:]
            i += 2 if a in ("<", ">", ">>", "2>", "1>", "2>>") else 1
            continue
        if a.startswith("-") and len(a) > 1:
            i += 1
            continue
        skript = a
        break
    if skript and os.path.basename(skript.replace("\\", "/")) == "slusne.py":
        return None
    if skript:
        obsah = _cti(skript, ctx)
        if not (obsah and _sitovy_kod(obsah, ctx)):
            return None
        duvod = f"Python skript {skript} chodí na síť"
    elif kod is not None:
        if not _sitovy_kod(kod, ctx):
            return None
        duvod = "python -c se síťovým importem"
    else:   # kód ze vstupu: heredoc, here-string, roura, < soubor
        texty = [ctx["cely"]] + ([_cti(vstup, ctx) or ""] if vstup else [])
        if not any(_sitovy_kod(t, ctx) for t in texty):
            return None
        duvod = "Python ze vstupu (heredoc / here-string) se síťovým importem"
    return duvod, _navrh_python(raw, ctx)


def _skript(cesta_nebo_text, je_text, ps, ctx):
    text = cesta_nebo_text if je_text else _cti(cesta_nebo_text, ctx)
    return bool(text) and bool(analyzuj(text, ps, ctx["cwd"], ctx["hloubka"] + 1))


def _zkontroluj(slova, k, raw, ctx):
    w0, args = slova[k], slova[k + 1:]
    jm, ps = _jmeno(w0), ctx["ps"]
    if PY_JMENO.fullmatch(jm):
        return _python(slova, k, raw, ctx)
    if jm.endswith(".py"):   # ./skript.py
        obsah = _cti(w0, ctx)
        if obsah and _sitovy_kod(obsah, ctx):
            return f"Python skript {w0} chodí na síť", f"{PY_CMD} {_wrap(ctx)} {raw[raw.find(w0):]}"
        return None
    if jm in ("curl", "wget"):
        if not args or any(a in ("--version", "-V", "--help", "-h", "--manual", "-M") for a in args):
            return None
        cile = curl_cile(args) if jm == "curl" else [a for a in args if not a.startswith("-")]
        if jm == "wget" and any(a in ("-i", "--input-file") or a.startswith("--input-file=") for a in args):
            return "wget -i (hromadné stahování)", None
        if any(_sitova_adresa(c) for c in cile) or any(re.search(r"(https?|ftps?)://", a) and not LOKAL.match(a) for a in args):
            return f"{w0} mimo wrapper", _navrh_pred(raw, w0, ctx)
        return None
    if ps and jm in PS_SIT:
        if any(_sitova_adresa(a) for a in args) or not any("://" in a for a in args):
            return f"{w0} (stahování z PowerShellu)", None
        return None
    if jm in SHELLS or jm in ("source", "."):
        i = 0
        while i < len(args):
            a = args[i]
            if a == "-c":
                if _skript(args[i + 1] if i + 1 < len(args) else "", True, False, ctx):
                    return f"{w0} -c volá síť (curl / Python)", _navrh_pred(raw, w0, ctx)
                return None
            if a in ("-o", "+o", "-O", "+O"):
                i += 2
                continue
            if a.startswith(("-", "+")):
                i += 1
                continue
            if _skript(a, False, ps and jm == ".", ctx):   # „. skript.ps1“ v PowerShellu
                return f"skript {a} volá síť (curl / Python)", _navrh_pred(raw, w0, ctx) if jm in SHELLS else None
            return None
        if ctx["hd"] and any(_skript(t, True, False, ctx) for t in ctx["hd"]):   # bash <<EOF
            return f"{w0} s heredocem volá síť", None
        return None
    if jm.endswith(".sh"):   # ./tools/x.sh
        if _skript(w0, False, False, ctx):
            return f"skript {w0} volá síť (curl / Python)", f"{PY_CMD} {_wrap(ctx)} bash {raw[raw.find(w0):]}"
        return None
    if jm in ("powershell", "pwsh"):
        for i, a in enumerate(args):
            la = a.lower()
            if la in ("-c", "-command", "-encodedcommand", "-ec", "-e"):
                if la in ("-encodedcommand", "-ec", "-e"):
                    return "powershell -EncodedCommand (nejde zkontrolovat)", None
                if _skript(" ".join(args[i + 1:]), True, True, ctx):
                    return f"{w0} -Command stahuje", None
                return None
            if la in ("-f", "-file") and i + 1 < len(args):
                return (f"skript {args[i + 1]} stahuje", None) if _skript(args[i + 1], False, True, ctx) else None
        return None
    if jm.endswith(".ps1"):
        return (f"skript {w0} stahuje", None) if _skript(w0, False, True, ctx) else None
    if jm == "cmd":
        for i, a in enumerate(args):
            if a.lower() in ("/c", "/k"):
                return (f"cmd {a} stahuje", None) if _skript(" ".join(args[i + 1:]), True, False, ctx) else None
    return None


def analyzuj(text, ps, cwd, hloubka=0):
    """Seznam problémů (důvod, navržený příkaz nebo None)."""
    if hloubka > 3 or not text.strip():
        return []
    text, hd = _here_stringy(text) if ps else _heredocy(text)
    text2, uvnitr = _substituce(text, ps)
    problemy = []
    for u in uvnitr:
        problemy += analyzuj(u, ps, cwd, hloubka + 1)
    if ps and PS_NET.search(text):
        problemy.append(("PowerShell stahuje přes .NET (WebClient / HttpClient)", None))
    ctx = {"cwd": cwd, "ps": ps, "hd": hd, "cely": text + "\n" + "\n".join(hd), "hloubka": hloubka}
    for slova, raw in _segmenty(text2, ps):
        k = _prikaz(slova)
        if k is None:
            continue
        if slova[k].lower() in ("cd", "pushd", "chdir", "set-location", "sl", "push-location"):   # cesty dál relativně k nové složce
            cil = next((s for s in slova[k + 1:] if not s.startswith("-")), None)
            if cil:
                cil = os.path.expanduser(cil[1] + ":" + cil[2:] if os.name == "nt" and re.match(r"/[A-Za-z]/", cil) else cil)
                cil = cil if os.path.isabs(cil) else os.path.join(ctx["cwd"], cil)
                if os.path.isdir(cil):
                    ctx["cwd"] = os.path.normpath(cil)
            continue
        p = _zkontroluj(slova, k, raw, ctx)
        if p:
            problemy.append(p)
    return problemy


def zprava(problemy, ctx):
    w = _wrap(ctx)
    radky = ["Zamítnuto pojistkou proti zablokování archivů (scripts/slusne_hook.py).",
             "Důvod: " + "; ".join(dict.fromkeys(d for d, _ in problemy)) + ".",
             "Síťové nástroje a skripty spouštěj přes wrapper, který hlídá rychlost dotazů (1 dotaz za 2 s, dlaždice",
             "10 za s, po HTTP 429/503 stop na 30 minut pro všechny procesy)."]
    navrhy = [n for _, n in problemy if n]
    if navrhy:
        radky += ["Spusť místo toho:"] + [f"  {n}" for n in dict.fromkeys(navrhy)]
    radky += ["Tvary příkazů:",
              f"  {PY_CMD} {w} tools/<nástroj>.py …          (i vlastní skript, např. pracovni/x.py)",
              f"  {PY_CMD} {w} - <<'EOF' … EOF               (kód z heredocu; v PowerShellu @'…'@ | {PY_CMD} {w} -)",
              f"  {PY_CMD} {w} curl …                        (místo curl, wget, Invoke-WebRequest)",
              f"  {PY_CMD} {w} bash tools/ahmp_search.sh …   (shellové skripty)",
              "Když wrapper ohlásí zablokovaný web (kód 75), nic na něj neposílej, nezkoušej to znovu a pokračuj jinou prací.",
              "V prohlížeči (JavaScript) platí totéž ručně: nejvýš 1 dotaz za 2 s, žádné Promise.all na dotazy."]
    return "\n".join(radky) + "\n"


def main():
    try:
        data = json.load(sys.stdin)
        prikaz = (data.get("tool_input") or {}).get("command") or ""
        if not prikaz:
            return 0
        ctx = {"cwd": data.get("cwd") or os.getcwd()}
        problemy = analyzuj(prikaz, data.get("tool_name") == "PowerShell", ctx["cwd"])
    except Exception as e:   # heuristika selhala – nepřekážet
        sys.stderr.write(f"slusne_hook: vnitřní chyba ({e!r}), příkaz puštěn\n")
        return 0
    if not problemy:
        return 0
    sys.stderr.write(zprava(problemy, ctx))
    return 2


if __name__ == "__main__":
    sys.exit(main())
