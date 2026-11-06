"""Test nasazení na Cloudflare: export vyrobí bránu (web/cloudflare/worker.js) a wrangler.jsonc, brána pustí jen rodinu.

Založí ukázkový projekt v dočasné složce, spustí export s otázkou i pro otevřený web a bránu vyzkouší v Node
s napodobeným env.ASSETS (statické soubory Cloudflare). Na Cloudflare nechodí. Potřebuje Node.js.
Z kořene repozitáře:
  python3 -I tests/web/test_cloudflare.py skills/rodokmen
"""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile

SKILL = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "skills/rodokmen")
vysledky = []


def check(nazev, ok, detail=""):
    vysledky.append(bool(ok))
    print(f"[{'OK ' if ok else 'CHYBA'}] {nazev}{'' if ok else '  ' + str(detail)[:800]}", flush=True)


def jsonc(cesta):
    return json.loads("".join(r for r in open(cesta, encoding="utf-8") if not r.lstrip().startswith("//")))


def export(projekt, prihlaseni, cloudflare=None, *args):
    cesta = os.path.join(projekt, "data", "web.json")
    cfg = json.load(open(cesta, encoding="utf-8"))
    cfg["prihlaseni"] = prihlaseni
    cfg.pop("cloudflare", None)
    if cloudflare is not None:
        cfg["cloudflare"] = cloudflare
    json.dump(cfg, open(cesta, "w", encoding="utf-8"), ensure_ascii=False)
    return subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(projekt, "tools", "export_web.py"), *args],
                          capture_output=True, text=True, cwd=projekt)


# Napodobený Cloudflare: env.ASSETS vrací soubory z dist/ a stejně jako Cloudflare (html_handling auto-trailing-slash)
# přesměruje /prihlaseni.html na /prihlaseni. Výsledky dotazů vypíše jako JSON.
ZKOUSKA = r"""
import worker from %s;
const PRIHLASENI = '<html><script>document.cookie = \'rodokmen=\' + hash</script></html>';
const ASSETS = { async fetch(req) {
  const p = new URL(req.url ?? req).pathname;
  if (p === '/prihlaseni.html') return new Response(null, { status: 307, headers: { location: '/prihlaseni' } });
  if (p === '/prihlaseni') return new Response(PRIHLASENI, { headers: { 'content-type': 'text/html' } });
  if (p === '/nic') return new Response('404 stránka', { status: 404 });
  return new Response('obsah ' + p, { headers: { 'content-type': 'text/html' } });
} };
const vysledky = {};
for (const [klic, cesta, cookie] of %s) {
  const req = new Request('https://rodokmen.ucet.workers.dev' + cesta, { headers: cookie ? { cookie } : {} });
  const res = await worker.fetch(req, { ASSETS });
  vysledky[klic] = { status: res.status, text: await res.text(), robots: res.headers.get('x-robots-tag'),
                     cache: res.headers.get('cache-control'), location: res.headers.get('location') };
}
console.log(JSON.stringify(vysledky));
"""


def zkus(worker, dotazy):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "zkouska.mjs")
        url = "file://" + os.path.abspath(worker).replace(os.sep, "/")
        open(p, "w", encoding="utf-8").write(ZKOUSKA % (json.dumps(url), json.dumps(dotazy)))
        r = subprocess.run(["node", p], capture_output=True, text=True)
        try:
            return json.loads(r.stdout)
        except ValueError:
            return {"chyba": r.stderr[-800:]}


tmp = tempfile.mkdtemp()
try:
    projekt = os.path.join(tmp, "projekt")
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(SKILL, "tools", "novy_projekt.py"), projekt, "--ukazka"],
                       capture_output=True, text=True)
    check("ukázkový projekt založen", r.returncode == 0, r.stderr)
    web = os.path.join(projekt, "web")
    worker = os.path.join(web, "cloudflare", "worker.js")
    wrangler = os.path.join(web, "wrangler.jsonc")

    # --- s rodinnou otázkou ---
    r = export(projekt, {"otazka": "Řemeslo?", "odpoved": "kovář"})
    check("s otázkou: export proběhl", r.returncode == 0, r.stderr)
    otisk = hashlib.sha256("rodokmen:kovar".encode()).hexdigest()
    obsah = open(worker, encoding="utf-8").read() if os.path.exists(worker) else ""
    check("brána cloudflare/worker.js s otiskem odpovědi", otisk in obsah and "{{" not in obsah, obsah[:300])

    cfg = {}
    try:
        cfg = jsonc(wrangler)
    except (OSError, ValueError) as e:
        cfg = {"chyba": str(e)}
    a = cfg.get("assets") or {}
    check("wrangler.jsonc: výchozí název rodokmen, brána jako main", cfg.get("name") == "rodokmen" and cfg.get("main") == "cloudflare/worker.js", cfg)
    check("wrangler.jsonc: soubory z dist/ přes ASSETS", a.get("directory") == "./dist" and a.get("binding") == "ASSETS", a)
    check("wrangler.jsonc: brána běží před každým souborem (run_worker_first)", a.get("run_worker_first") is True, a)
    check("wrangler.jsonc: chybějící stránka = 404.html", a.get("not_found_handling") == "404-page", a)
    check("wrangler.jsonc: workers.dev ano, preview URL ne", cfg.get("workers_dev") is True and cfg.get("preview_urls") is False, cfg)
    check("wrangler.jsonc: compatibility_date", re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(cfg.get("compatibility_date", ""))), cfg)

    c = f"rodokmen={otisk}"
    v = zkus(worker, [["bez", "/", None], ["spatna", "/", "rodokmen=abc"], ["dobra", "/", c],
                      ["vic", "/osoba/jan/", "jine=1; " + c + "; dalsi=2"], ["obrazek", "/img/x.jpg", None],
                      ["obrazek_ok", "/img/x.jpg", c], ["prihlaseni", "/prihlaseni", None],
                      ["prihlaseni_html", "/prihlaseni.html", None], ["nic", "/nic", c]])
    check("node: brána jde spustit", "chyba" not in v, v.get("chyba"))
    if "chyba" not in v:
        check("bez cookie: 401 s přihlašovací stránkou", v["bez"]["status"] == 401 and "rodokmen=" in v["bez"]["text"], v["bez"])
        check("bez cookie: noindex a no-store", v["bez"]["robots"] == "noindex, nofollow" and "no-store" in (v["bez"]["cache"] or ""), v["bez"])
        check("špatná cookie: 401", v["spatna"]["status"] == 401, v["spatna"])
        check("správná cookie: stránka webu", v["dobra"]["status"] == 200 and v["dobra"]["text"] == "obsah /", v["dobra"])
        check("správná cookie: noindex", v["dobra"]["robots"] == "noindex, nofollow", v["dobra"])
        check("cookie mezi jinými cookies", v["vic"]["status"] == 200, v["vic"])
        check("obrázek bez cookie: 401 (ne soubor)", v["obrazek"]["status"] == 401 and "obsah" not in v["obrazek"]["text"], v["obrazek"])
        check("obrázek se cookie: soubor", v["obrazek_ok"]["text"] == "obsah /img/x.jpg", v["obrazek_ok"])
        check("přihlašovací stránka bez cookie dostupná", v["prihlaseni"]["status"] == 200 and "rodokmen=" in v["prihlaseni"]["text"], v["prihlaseni"])
        check("/prihlaseni.html bez cookie projde (přesměrování Cloudflare)", v["prihlaseni_html"]["status"] in (200, 307, 308), v["prihlaseni_html"])
        check("chybějící stránka se cookie: 404", v["nic"]["status"] == 404, v["nic"])

    # --- název subdomény (cloudflare.nazev) ---
    r = export(projekt, {"otazka": "Řemeslo?", "odpoved": "kovář"}, {"nazev": "novakovi"})
    cfg = jsonc(wrangler) if r.returncode == 0 and os.path.exists(wrangler) else {}
    check("platný cloudflare.nazev projde, Worker se dál jmenuje rodokmen", cfg.get("name") == "rodokmen", (r.stderr, cfg))
    r = export(projekt, {"otazka": "Řemeslo?", "odpoved": "kovář"}, {"nazev": "Rod.Nováků"})
    check("neplatný název: export skončí srozumitelnou chybou", r.returncode != 0 and "cloudflare" in (r.stdout + r.stderr).lower(), (r.returncode, r.stdout[-300:], r.stderr[-300:]))

    # --- odpověď bez písmen a číslic z latinky (azbuka, symboly) ---
    r = export(projekt, {"otazka": "Kde?", "odpoved": "Москва"}, None, "--nasazeni")
    out = r.stdout + r.stderr
    check("odpověď v azbuce: nasazení odmítne a vysvětlí proč (latinka)", r.returncode != 0 and "latink" in out, out[-300:])

    # --- otevřený web ---
    r = export(projekt, {"otevreny": True})
    check("otevřený web: export proběhl", r.returncode == 0, r.stderr)
    v = zkus(worker, [["bez", "/", None], ["obrazek", "/img/x.jpg", None]])
    check("otevřený web: bez cookie stránka i obrázek", v.get("bez", {}).get("status") == 200 and v.get("obrazek", {}).get("text") == "obsah /img/x.jpg", v)

    # --- kontrola volného názvu (--volno): DNS Cloudflare přes DoH, tady napodobené lokálním serverem ---
    import threading
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
    from urllib.parse import urlparse, parse_qs
    DOTAZY = []

    class Doh(BaseHTTPRequestHandler):
        def do_GET(self):
            jmeno = parse_qs(urlparse(self.path).query).get("name", [""])[0]
            DOTAZY.append(jmeno)
            obsazene = jmeno.endswith(".novakovi.workers.dev")
            b = json.dumps({"Status": 0, "Answer": [{"data": "104.21.12.93"}]} if obsazene else {"Status": 3}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/dns-json")
            self.end_headers()
            self.wfile.write(b)

        def log_message(self, *a):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), Doh)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    env = dict(os.environ, RODOKMEN_DOH=f"http://127.0.0.1:{srv.server_address[1]}/dns-query")

    def volno(*jmena):
        r = subprocess.run(["node", "scripts/nasadit_cloudflare.mjs", "--volno", *jmena], cwd=web, env=env,
                           capture_output=True, text=True, timeout=60)
        return r.returncode, r.stdout + r.stderr

    kod, out = volno("novakovi")
    check("--volno: obsazený název pozná (kód 1)", kod == 1 and "obsazen" in out, out)
    check("--volno: ptá se na *.název.workers.dev", any(d.endswith(".novakovi.workers.dev") for d in DOTAZY), DOTAZY)
    kod, out = volno("novakovi-holice")
    check("--volno: volný název (kód 0)", kod == 0 and "voln" in out, out)
    kod, out = volno("novakovi", "rod-novaku")
    check("--volno: víc názvů – vypíše každý", "novakovi" in out and "rod-novaku" in out and kod == 0, out)
    kod, out = volno("Rod.Nováků")
    check("--volno: neplatný název odmítne", kod == 2 and "nejde" in out, out)
    srv.shutdown()
    r = subprocess.run(["node", "scripts/nasadit_cloudflare.mjs", "--zkouska"], cwd=web, capture_output=True, text=True, timeout=60)
    check("neznámý přepínač: skončí hned (kód 2), nic nenasazuje", r.returncode == 2 and "wrangler" not in r.stdout.lower(), r.stdout + r.stderr)

    # --- skripty a git ---
    pkg = json.load(open(os.path.join(web, "package.json"), encoding="utf-8"))
    s = pkg["scripts"].get("nasadit-cloudflare", "")
    check("package.json: nasadit-cloudflare (data --nasazeni, build, nasazení, kontrola)",
          "--nasazeni" in s and "build" in s and "cloudflare" in s, s)
    gi = open(os.path.join(projekt, ".gitignore"), encoding="utf-8").read()
    check(".gitignore: vygenerovaná brána, wrangler.jsonc a .wrangler/",
          all(x in gi for x in ("web/cloudflare/worker.js", "web/wrangler.jsonc", "web/.wrangler/")), gi[-300:])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\n{sum(vysledky)} z {len(vysledky)} správně")
sys.exit(0 if all(vysledky) else 1)
