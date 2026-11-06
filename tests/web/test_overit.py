"""Test kontroly po nasazení (template/web/scripts/overit.mjs): pozná rodinnou bránu, ochranu týmu Netlify a web bez brány.

Z kořene repozitáře:
  python3 -I tests/web/test_overit.py skills/rodokmen
Lokální server napodobí odpovědi webu (rodinná brána 401, přihlášení k Netlify, veřejná stránka 200); overit.mjs
dostane jeho adresu přes --url, takže na Netlify nechodí. Potřebuje Node.js.
"""
import os, shutil, subprocess, sys, tempfile, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

SKILL = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "skills/rodokmen")
SABLONA = os.path.join(SKILL, "template", "web")
BRANA = open(os.path.join(SABLONA, "prihlaseni.sablona.html"), encoding="utf-8").read()
vysledky = []


def check(nazev, ok, detail=""):
    vysledky.append(bool(ok))
    print(f"[{'OK ' if ok else 'CHYBA'}] {nazev}{'' if ok else '  ' + str(detail)[:700]}", flush=True)


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        p = self.path.split("?")[0]
        if p.startswith("/brana"):
            self.odpoved(401, BRANA)
        elif p.startswith("/netlify401"):
            self.odpoved(401, "<html><title>Login Redirect</title><body>Netlify</body></html>")
        elif p.startswith("/netlify"):   # ochrana týmu: přesměrování na přihlášení k Netlify
            self.send_response(302)
            self.send_header("Location", "https://app.netlify.com/login?redirect=1")
            self.end_headers()
        elif p.startswith("/cf429"):
            self.odpoved(429, "error code: 1027")
        elif p.startswith("/cfvyzva"):   # ověřovací stránka Cloudflare (ne naše brána)
            self.odpoved(403, "<html><title>Just a moment...</title><body>cf-chl challenge-platform</body></html>")
        elif p.startswith("/verejny"):
            self.odpoved(200, "<html><title>Rodokmen</title><body>Rodokmen Nováků</body></html>")
        else:
            self.odpoved(404, "nic")

    def odpoved(self, kod, text):
        b = text.encode()
        self.send_response(kod)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *a):
        pass


s = ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=s.serve_forever, daemon=True).start()
A = f"http://127.0.0.1:{s.server_address[1]}"

tmp = tempfile.mkdtemp(prefix="overit_web_")
try:
    web = os.path.join(tmp, "web")
    os.makedirs(os.path.join(web, "scripts"))
    shutil.copy(os.path.join(SABLONA, "scripts", "overit.mjs"), os.path.join(web, "scripts", "overit.mjs"))

    def overit(cesta, brana=True, cloudflare=None):
        edge = os.path.join(web, "netlify", "edge-functions", "brana.js")
        cf = os.path.join(web, "cloudflare", "worker.js")
        if cloudflare is None and os.path.exists(cf):
            os.remove(cf)
        elif cloudflare is not None:
            os.makedirs(os.path.dirname(cf), exist_ok=True)
            open(cf, "w").write("const OTEVRENY = %s;" % cloudflare)
            brana = False
        if brana:
            os.makedirs(os.path.dirname(edge), exist_ok=True)
            open(edge, "w").write("// brana")
        elif os.path.exists(edge):
            os.remove(edge)
        r = subprocess.run(["node", "scripts/overit.mjs", "--url", A + cesta], cwd=web, capture_output=True, text=True,
                           timeout=60)
        return r.returncode, r.stdout + r.stderr

    kod, out = overit("/brana")
    check("rodinná brána: v pořádku (kód 0)", kod == 0 and "rodinnou otázku" in out, out)

    for cesta in ("/netlify", "/netlify401"):
        kod, out = overit(cesta)
        check(f"ochrana týmu Netlify ({cesta}): chyba (kód 1)", kod == 1, out)
        check(f"ochrana týmu Netlify ({cesta}): poradí sso_login i cestu v administraci",
              "sso_login" in out and "Visitor access" in out, out)

    kod, out = overit("/verejny")
    check("brána v projektu, ale web veřejný: chyba", kod == 1 and "bez rodinné otázky" in out, out)

    kod, out = overit("/verejny", brana=False)
    check("web bez přihlášení (bez otázky v nastavení): jen informace, kód 0", kod == 0 and "bez přihlášení" in out, out)

    kod, out = overit("/neni")
    check("nečekaná odpověď (404): chyba s kódem odpovědi", kod == 1 and "404" in out, out)

    kod, out = overit("/verejny", cloudflare="false")
    check("Cloudflare: brána v projektu, ale web veřejný: chyba", kod == 1 and "bez rodinné otázky" in out, out)

    kod, out = overit("/verejny", cloudflare="true")
    check("Cloudflare: otevřený web – jen informace, kód 0", kod == 0 and "bez přihlášení" in out, out)

    kod, out = overit("/cf429", cloudflare="false")
    check("Cloudflare 429: vysvětlí denní limit", kod == 1 and "limit" in out, out)

    kod, out = overit("/cfvyzva", cloudflare="false")
    check("ověřovací stránka Cloudflare: vysvětlí, že to není brána", kod == 1 and "ověřovací" in out, out)

    # bez --url a bez .netlify/state.json: nic neověří, ale nasazení nezastaví
    r = subprocess.run(["node", "scripts/overit.mjs"], cwd=web, capture_output=True, text=True, timeout=60)
    check("bez propojení s Netlify: jen upozornění, kód 0", r.returncode == 0 and "anonymním okně" in r.stdout,
          r.stdout + r.stderr)
finally:
    s.shutdown()
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\n{sum(vysledky)} z {len(vysledky)} správně")
sys.exit(0 if all(vysledky) else 1)
