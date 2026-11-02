"""Regresní sada pro hlídač sítě tools/hlidac_site.py: příkazy, které má zamítnout, a příkazy, které má pustit.

Hlídač se spouští přesně příkazem, který do .claude/settings.json zapíše `novy_projekt.py --hlidac`, a to přes bash
(na Windows Git Bash – výchozí shell hooků) a přes PowerShell (shell hooků na Windows bez Git Bashe), je-li k dispozici.
U zamítnutí kontroluje i to, že odpověď je platné UTF-8 (Claude Code ji tak čte). Hlídač nic nestahuje.
Z kořene repozitáře (přes obal, test obsahuje příkazy s curl):
  python3 -I skills/rodokmen/tools/slusne.py tests/brzda/test_hlidac.py skills/rodokmen
Případy vznikly z testů hooku na Windows (PR #53). Stav 0.6.0 na Windows 11, 2. 11. 2026: přes Git Bash 39 z 59
(zamítnutí v cp1250; `import json, urllib.request` v heredocu i ve skriptu, `bash -c "curl …"` a Monitor projdou);
přes PowerShell 0 z 59 – příkaz hooku se nespustí (chybí &), skončí kódem 1 a pustí všechno.
"""
import json, os, shutil, subprocess, sys, tempfile

SKILL = os.path.abspath(sys.argv[1])          # …/skills/rodokmen (tools/hlidac_site.py, tools/novy_projekt.py)
sys.path.insert(0, os.path.join(SKILL, "tools"))
import novy_projekt                            # noqa: E402 – stejný příkaz hooku, jaký zapisuje --hlidac

PRIKAZ = novy_projekt.HLIDAC
SHELLY = {}
if os.name == "nt" and os.path.isfile(r"C:\Program Files\Git\usr\bin\bash.exe"):
    SHELLY["Git Bash"] = [r"C:\Program Files\Git\usr\bin\bash.exe", "-c", PRIKAZ]
elif shutil.which("bash"):
    SHELLY["bash"] = [shutil.which("bash"), "-c", PRIKAZ]
if shutil.which("pwsh"):
    SHELLY["PowerShell"] = [shutil.which("pwsh"), "-NoProfile", "-Command", PRIKAZ]

POM = tempfile.mkdtemp(prefix="test_hlidac_")
DAVKA = os.path.join(POM, "davka.py").replace("\\", "/")          # spouští nástroj s import slusne → pustit
VLASTNI = os.path.join(POM, "vlastni_sit.py").replace("\\", "/")  # vlastní skript se sítí → zamítnout
with open(DAVKA, "w", encoding="utf-8") as f:
    f.write("import subprocess, sys\nfor n in range(1, 50):\n"
            "    subprocess.run([sys.executable, '-I', 'tools/aron_img.py', '123', str(n), '1', f'pracovni/x{n}.jpg'])\n")
with open(VLASTNI, "w", encoding="utf-8") as f:
    f.write("import json, urllib.request\nprint(1)\n")

Z, P = "zamítnout", "pustit"
PRIPADY = [
    # Bash – zamítnout
    ("Bash", "python -I -X utf8 -c \"import urllib.request; urllib.request.urlopen('https://aron.vychodoceskearchivy.cz')\"", Z),
    ("Bash", "python -I -X utf8 - <<'EOF'\nimport json, urllib.request\nprint(1)\nEOF", Z),
    ("Bash", "python -I -X utf8 - <<'EOF'\nimport urllib.request  # Plaňany, Všeruby\nEOF", Z),
    ("Bash", "curl -s https://katalog.ahmp.cz/pragapublica/ -o pracovni/x.html", Z),
    ("Bash", 'for i in 1 2 3; do curl -s "https://example.cz/api?p=$i"; done', Z),
    ("Bash", "x=$(curl -s https://example.com) && echo $x", Z),
    ("Bash", "wget https://example.com/a.jpg", Z),
    ("Bash", 'bash -c "curl -s https://example.com"', Z),
    ("Bash", f"python -I -X utf8 {VLASTNI}", Z),
    ("Bash", 'curl -s "https://www.portafontium.eu/register/soap-pn?q=Plaňany"', Z),
    ("Bash", "curl -s https://rodokmen.svamberk.net/", Z),
    ("Monitor", "while true; do curl -s https://example.com/stav; sleep 1; done", Z),
    # Bash – pustit (nástroje se brzdí samy, obal, localhost, vlastní web)
    ("Bash", 'python -I -X utf8 tools/aron_search.py "Holice"', P),
    ("Bash", 'bash tools/ahmp_search.sh "Švamberk"', P),
    ("Bash", "./tools/ahmp_search.sh Holice", P),
    ("Bash", 'cd pracovni && python -I -X utf8 ../tools/kramerius.py "Švamberk" 1', P),
    ("Bash", "timeout 60 python -I -X utf8 tools/mista.py", P),
    ("Bash", f"python -I -X utf8 {DAVKA}", P),
    ("Bash", f"python -I -X utf8 tools/slusne.py {VLASTNI}", P),
    ("Bash", "python -I -X utf8 tools/slusne.py - <<'EOF'\nimport urllib.request\nEOF", P),
    ("Bash", 'python -I -X utf8 tools/slusne.py bash tools/ahmp_search.sh "Plaňany"', P),
    ("Bash", "python -I -X utf8 tools/slusne.py curl -s https://example.com", P),
    ("Bash", "curl -s https://rodokmen-adelka.netlify.app/", P),
    ("Bash", "curl -s http://localhost:4321/", P),
    ("Bash", "curl --version", P),
    ("Bash", "python -I -X utf8 tools/zapis.py data/zaznamy.json klic pracovni/x.json", P),
    ("Bash", "python -I -X utf8 tools/kontrola.py", P),
    ("Bash", "python -I -X utf8 tools/export_web.py", P),
    ("Bash", "grep -n urllib tools/aron_img.py && cat tools/ahmp_search.sh", P),
    ("Bash", "git commit -m \"$(cat <<'EOF'\nUse curl https://x.cz and python tools/aron_img.py, it's fine\nEOF\n)\"", P),
    ("Bash", "python -I -X utf8 - <<'EOF'\nimport json\nprint(json.dumps({}))\nEOF", P),
    ("Bash", "cd web && npm run data", P),
    ("Bash", 'echo "curl https://example.com" >> pracovni/poznamka.txt', P),
    ("Bash", 'echo "Plaňany, Všeruby, Dolní Bělá" > pracovni/x.txt', P),
    ("Bash", "python -m http.server 8000", P),
    ("Bash", "gh api repos/sarsonj/rodokmen-skill/commits --jq '.[0].sha'", P),
    ("Bash", "magick x.jpg -resize 50% y.jpg 2>&1 && python -I -X utf8 tools/vyrez.py a.jpg klic 0,0,1,1", P),
    # PowerShell – zamítnout
    ("PowerShell", "Invoke-WebRequest https://aron.vychodoceskearchivy.cz/api/aron -OutFile x.json", Z),
    ("PowerShell", "iwr $url -OutFile x.jpg", Z),
    ("PowerShell", "curl.exe -s https://example.com", Z),
    ("PowerShell", '(New-Object System.Net.WebClient).DownloadString("https://example.com")', Z),
    ("PowerShell", '1..3 | ForEach-Object { Invoke-RestMethod "https://example.cz/api?p=$_" }', Z),
    ("PowerShell", "@'\nimport urllib.request\nprint(1)\n'@ | python -I -X utf8 -", Z),
    ("PowerShell", 'Invoke-WebRequest "https://www.portafontium.eu/?q=Plaňany"', Z),
    ("PowerShell", f"python -I -X utf8 {VLASTNI}", Z),
    # PowerShell – pustit
    ("PowerShell", 'python -I -X utf8 tools\\aron_search.py "Holice"', P),
    ("PowerShell", 'bash tools/ahmp_search.sh "Holice"', P),
    ("PowerShell", '& "C:\\Program Files\\Git\\bin\\bash.exe" tools/matricula_dl.sh "https://img.data.matricula-online.eu/x" x.jpg', P),
    ("PowerShell", 'python -I -X utf8 tools/slusne.py tools\\aron_search.py "Holice"', P),
    ("PowerShell", "python -I -X utf8 tools/slusne.py curl -s https://example.com", P),
    ("PowerShell", 'python -I -X utf8 tools/slusne.py bash tools/ahmp_search.sh "Holice"', P),
    ("PowerShell", "Invoke-WebRequest http://localhost:4321/ -UseBasicParsing", P),
    ("PowerShell", "Get-Content tools\\aron_img.py | Select-String urllib", P),
    ("PowerShell", "python -I -X utf8 tools\\kontrola.py", P),
    ("PowerShell", "@'\nimport json\n'@ | python -I -X utf8 -", P),
    ("PowerShell", "git log --oneline -3", P),
    ("PowerShell", "Invoke-WebRequest https://rodokmen-adelka.netlify.app/ -UseBasicParsing", P),
    ("PowerShell", "python -m http.server 8000", P),
    ("PowerShell", "git commit -m 'Use curl https://x.cz'", P),
]

vse_ok = True
for shell, argv in SHELLY.items():
    spravne, chyby = 0, []
    for nastroj, prikaz, cekam in PRIPADY:
        vstup = json.dumps({"tool_name": nastroj, "tool_input": {"command": prikaz}, "cwd": SKILL,
                            "hook_event_name": "PreToolUse"}, ensure_ascii=False).encode("utf-8")
        r = subprocess.run(argv, input=vstup, capture_output=True, env={**os.environ, "CLAUDE_PROJECT_DIR": SKILL})
        try:
            out, utf8 = r.stdout.decode("utf-8"), True
        except UnicodeDecodeError:
            out, utf8 = r.stdout.decode("cp1250", "replace"), False
        try:
            rozhodnuti = json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out.strip() else "allow"
        except (ValueError, KeyError):
            rozhodnuti = "?"
        vysl = Z if rozhodnuti == "deny" else P
        ok = vysl == cekam and (utf8 or vysl == P) and r.returncode in (0, 2)
        spravne += ok
        if not ok:
            pozn = [f"kód {r.returncode}"] if r.returncode not in (0, 2) else []
            if not utf8:
                pozn.append("odpověď není UTF-8")
            chyby.append(f"  [CHYBA] {nastroj:10} čekám {cekam}, je {vysl}: {prikaz.splitlines()[0][:70]}"
                         + (f"  ({'; '.join(pozn)})" if pozn else ""))
    vse_ok &= spravne == len(PRIPADY)
    print(f"== hlídač přes {shell}: {spravne} z {len(PRIPADY)} správně")
    print("\n".join(chyby))
if not SHELLY:
    print("Nenašel jsem bash ani pwsh – nic netestováno.")
sys.exit(0 if vse_ok and SHELLY else 1)
