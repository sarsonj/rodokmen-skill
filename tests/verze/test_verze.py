"""Test kontroly verze (tools/verze.py) a pojistky proti aktualizaci projektu starším skillem (novy_projekt.py).

GitHub napodobí lokální server (RODOKMEN_VERZE_URL), mezipaměť je v dočasné složce (RODOKMEN_CACHE) – do sítě nechodí.
Z kořene repozitáře:
  python3 -I tests/verze/test_verze.py skills/rodokmen
"""
import json, os, shutil, subprocess, sys, tempfile, threading, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

SKILL = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "skills/rodokmen")
vysledky = []


def check(nazev, ok, detail=""):
    vysledky.append(bool(ok))
    print(f"[{'OK ' if ok else 'CHYBA'}] {nazev}{'' if ok else '  ' + str(detail)[:700]}", flush=True)


STAV = {"tag": "v0.9.0", "dotazy": 0, "kod": 200}


class GH(BaseHTTPRequestHandler):
    def do_GET(self):
        STAV["dotazy"] += 1
        b = json.dumps({"tag_name": STAV["tag"]}).encode()
        self.send_response(STAV["kod"])
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b if STAV["kod"] == 200 else b"{}")

    def log_message(self, *a):
        pass


srv = ThreadingHTTPServer(("127.0.0.1", 0), GH)
threading.Thread(target=srv.serve_forever, daemon=True).start()
tmp = tempfile.mkdtemp(prefix="verze_")
cache = os.path.join(tmp, "cache")
ENV = dict(os.environ, RODOKMEN_VERZE_URL=f"http://127.0.0.1:{srv.server_address[1]}/latest", RODOKMEN_CACHE=cache)


def falesny_skill(verze, plugin=False):
    s = os.path.join(tmp, "plugins", "cache", "rodokmen-skill", "rodokmen", verze, "skills", "rodokmen") if plugin \
        else os.path.join(tmp, "skills", f"rodokmen_{verze}")
    os.makedirs(os.path.join(s, "tools"), exist_ok=True)
    shutil.copy(os.path.join(SKILL, "tools", "verze.py"), os.path.join(s, "tools", "verze.py"))
    open(os.path.join(s, "VERZE"), "w").write(verze + "\n")
    return s


def projekt(verze):
    p = os.path.join(tmp, f"projekt_{verze}")
    os.makedirs(p, exist_ok=True)
    open(os.path.join(p, ".skill_verze"), "w").write(verze + "\n")
    return p


def verze(skill, proj=None, env=None):
    args = [sys.executable, "-I", os.path.join(skill, "tools", "verze.py")] + ([proj] if proj else [])
    r = subprocess.run(args, capture_output=True, text=True, env=env or ENV, timeout=60)
    return r.returncode, r.stdout + r.stderr


try:
    if not os.path.exists(os.path.join(SKILL, "tools", "verze.py")):
        check("tools/verze.py existuje", False)
        raise SystemExit

    # 1) GitHub novější než nainstalovaný skill
    kod, out = verze(falesny_skill("0.8.2", plugin=True), projekt("0.8.2"))
    check("GitHub novější: kód 0", kod == 0, out)
    check("GitHub novější, plugin: řekne verzi a poradí claude plugin update", "0.9.0" in out and "plugin update" in out and "NOVA_VERZE_SKILLU" in out, out)
    kod, out = verze(falesny_skill("0.8.2"), projekt("0.8.2"))
    check("GitHub novější, ručně nakopírovaný skill: neradí claude plugin, ale novou složku z GitHubu",
          "NOVA_VERZE_SKILLU" in out and "claude plugin" not in out and "github.com/sarsonj/rodokmen-skill" in out, out)
    check("GitHub novější: projekt z GitHubu neaktualizuje (žádný git clone)", "clone" not in out, out)
    check("mezipaměť zapsaná", os.path.exists(os.path.join(cache, "rodokmen_verze.json")), os.listdir(tmp))

    # 2) do 24 hodin se GitHubu znovu neptá
    pred = STAV["dotazy"]
    kod, out = verze(falesny_skill("0.8.2"), projekt("0.8.2"))
    check("do 24 h: z mezipaměti, bez dotazu na GitHub", STAV["dotazy"] == pred and "0.9.0" in out, (STAV, out))

    # 3) po 24 hodinách znovu
    c = os.path.join(cache, "rodokmen_verze.json")
    d = json.load(open(c))
    d["cas"] = time.time() - 25 * 3600
    json.dump(d, open(c, "w"))
    STAV["tag"] = "v0.10.0"
    kod, out = verze(falesny_skill("0.9.0"), projekt("0.9.0"))
    check("po 24 h: zeptá se znovu", STAV["dotazy"] == pred + 1, STAV)
    check("0.10.0 je novější než 0.9.0 (čísla, ne text)", "0.10.0" in out and "NOVA_VERZE_SKILLU" in out, out)

    # 4) GitHub nedostupný: nic nespadne, porovná aspoň projekt a skill
    shutil.rmtree(cache)
    STAV["kod"] = 500
    kod, out = verze(falesny_skill("0.9.0"), projekt("0.8.2"))
    check("GitHub nedostupný: kód 0 a nabídne aktualizaci projektu", kod == 0 and "AKTUALIZUJ_PROJEKT" in out, out)
    env = dict(ENV, RODOKMEN_VERZE_URL="http://127.0.0.1:9/nic")
    kod, out = verze(falesny_skill("0.9.0"), projekt("0.9.0"), env)
    check("bez sítě: kód 0, aktuální podle místních verzí", kod == 0 and "AKTUALNI" in out, out)
    STAV["kod"] = 200
    STAV["tag"] = "v0.9.0"

    # 5) skill novější než projekt
    shutil.rmtree(cache, ignore_errors=True)
    kod, out = verze(falesny_skill("0.9.0"), projekt("0.8.2"))
    check("skill novější než projekt: nabídne novy_projekt.py", "AKTUALIZUJ_PROJEKT" in out and "novy_projekt.py" in out, out)

    # 6) projekt novější než skill (stará kopie skillu)
    kod, out = verze(falesny_skill("0.9.0"), projekt("0.9.1"))
    check("projekt novější než skill: varuje, projekt neaktualizovat", "PROJEKT_NOVEJSI" in out and "AKTUALIZUJ_PROJEKT" not in out, out)

    # 7) vše stejné
    kod, out = verze(falesny_skill("0.9.0"), projekt("0.9.0"))
    check("vše aktuální", "AKTUALNI" in out and "NOVA_VERZE" not in out, out)

    # 8) projekt bez .skill_verze (starší než 0.4) = aktualizovat
    p = os.path.join(tmp, "projekt_bez")
    os.makedirs(p)
    kod, out = verze(falesny_skill("0.9.0"), p)
    check("projekt bez .skill_verze: nabídne aktualizaci", "AKTUALIZUJ_PROJEKT" in out, out)

    # 9) bez projektu: jen skill × GitHub
    kod, out = verze(falesny_skill("0.9.0"))
    check("bez projektu: jen skill a GitHub", kod == 0 and "AKTUALNI" in out, out)

    # 10) kopie verze.py v tools/ projektu: najde nainstalovaný skill (registr pluginů / ~/.claude/skills), jinak nehlásí AKTUALNI
    shutil.rmtree(cache, ignore_errors=True)
    cfg = os.path.join(tmp, "claude_cfg")
    pr = projekt("0.9.0")
    os.makedirs(os.path.join(pr, "tools"), exist_ok=True)
    shutil.copy(os.path.join(SKILL, "tools", "verze.py"), os.path.join(pr, "tools", "verze.py"))
    env = dict(ENV, CLAUDE_CONFIG_DIR=cfg)
    kopie = os.path.join(pr, "tools", "verze.py")

    def z_projektu():
        r = subprocess.run([sys.executable, "-I", kopie, pr], capture_output=True, text=True, env=env, timeout=60)
        return r.stdout + r.stderr

    os.makedirs(cfg, exist_ok=True)
    out = z_projektu()
    check("kopie v projektu, skill nenalezen: nehlásí AKTUALNI", "AKTUALNI" not in out and "SKILL_NEZJISTEN" in out, out)
    def plugin(verze, scope, projekt_path=None):
        ip = os.path.join(cfg, "plugins", "cache", "rodokmen-skill", "rodokmen", verze)
        os.makedirs(os.path.join(ip, "skills", "rodokmen"), exist_ok=True)
        open(os.path.join(ip, "skills", "rodokmen", "VERZE"), "w").write(verze + "\n")
        z = {"scope": scope, "installPath": ip, "version": verze}
        if projekt_path:
            z["projectPath"] = projekt_path
        return z
    reg = {"version": 2, "plugins": {"rodokmen@rodokmen-skill": [plugin("0.5.0", "local", "/jiny/projekt"),
                                                                plugin("0.8.2", "user")]}}
    json.dump(reg, open(os.path.join(cfg, "plugins", "installed_plugins.json"), "w"))
    out = z_projektu()
    check("kopie v projektu: najde plugin (rozsah user, ne cizí projekt) → 0.8.2 < GitHub",
          "0.8.2" in out and "NOVA_VERZE_SKILLU" in out and "claude plugin" in out, out)
    reg["plugins"]["rodokmen@rodokmen-skill"].append(plugin("0.9.0", "project", pr))
    json.dump(reg, open(os.path.join(cfg, "plugins", "installed_plugins.json"), "w"))
    out = z_projektu()
    check("kopie v projektu: plugin pro tento projekt má přednost", "Skill (nainstalovaný): 0.9.0" in out and "AKTUALNI" in out, out)
    os.remove(os.path.join(cfg, "plugins", "installed_plugins.json"))
    os.makedirs(os.path.join(cfg, "skills", "rodokmen"), exist_ok=True)
    open(os.path.join(cfg, "skills", "rodokmen", "VERZE"), "w").write("0.8.2\n")
    out = z_projektu()
    check("kopie v projektu: najde ručně nakopírovaný ~/.claude/skills/rodokmen", "0.8.2" in out and "NOVA_VERZE_SKILLU" in out
          and "claude plugin" not in out, out)

    # 11) novy_projekt.py: starší skill projekt neaktualizuje
    proj = os.path.join(tmp, "skutecny")
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(SKILL, "tools", "novy_projekt.py"), proj],
                       capture_output=True, text=True)
    check("projekt založen", r.returncode == 0, r.stderr)
    open(os.path.join(proj, ".skill_verze"), "w").write("99.0.0\n")
    exp = os.path.join(proj, "tools", "export_web.py")
    open(exp, "a").write("# vlastni uprava\n")
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(SKILL, "tools", "novy_projekt.py"), proj],
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    check("novy_projekt: projekt novější než skill → odmítne (kód ≠ 0)", r.returncode != 0 and "99.0.0" in out, out[-400:])
    check("novy_projekt: při odmítnutí nic nezmění", open(exp).read().endswith("# vlastni uprava\n")
          and open(os.path.join(proj, ".skill_verze")).read().strip() == "99.0.0", "")
finally:
    srv.shutdown()
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\n{sum(vysledky)} z {len(vysledky)} správně")
sys.exit(0 if all(vysledky) else 1)
