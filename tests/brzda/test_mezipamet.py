"""Test mezipaměti obrázků (tools/cache.py přes brzdu tools/slusne.py): ukládá se jen celý obrázek.

Z kořene repozitáře (lokální server na 127.0.0.2 – localhost brzda nebrzdí, na macOS alias na lo0 nebo Docker):
  python3 -I skills/rodokmen/tools/slusne.py tests/brzda/test_mezipamet.py skills/rodokmen/tools
Mezipaměť a stav brzdy jsou v dočasné složce (RODOKMEN_SNIMKY, SLUSNE_STAV). Nic nestahuje z internetu.
"""
import os, socket, subprocess, sys, tempfile, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

TOOLS = os.path.abspath(sys.argv[1])
sys.path.insert(0, TOOLS)
import cache  # noqa: E402

JPG = b"\xff\xd8\xff\xe0" + bytes(range(256)) * 40 + b"\xff\xd9"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 3000 + b"\x00\x00\x00\x00IEND\xaeB`\x82"
GIF = b"GIF89a" + b"\x01" * 3000 + b";"
WEBP = b"RIFF" + (3000 + 4).to_bytes(4, "little") + b"WEBP" + b"\x00" * 3000
HITS = {}


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def do_GET(self):
        p = self.path.split("?")[0]
        HITS[p] = HITS.get(p, 0) + 1
        telo = {"/cely.jpg": JPG, "/kratky.jpg": JPG[:2000], "/delka.jpg": JPG, "/stary.jpg": JPG}[p]
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        if p == "/delka.jpg":
            self.send_header("Content-Length", str(len(telo) + 500))   # server slíbil víc, než poslal
        elif p != "/kratky.jpg":   # zkrácený bez délky: spojení se zavře uprostřed
            self.send_header("Content-Length", str(len(telo)))
        self.end_headers()
        self.wfile.write(telo)

    def log_message(self, *a):
        pass


vysledky = []


def check(nazev, ok, detail=""):
    vysledky.append(ok)
    print(f"[{'OK ' if ok else 'CHYBA'}] {nazev} {detail}", flush=True)


# 1) kontrola konce v paměti
for jmeno, data in (("JPEG", JPG), ("PNG", PNG), ("GIF", GIF), ("WebP", WEBP)):
    check(f"{jmeno} celý", cache.cely(data))
    check(f"{jmeno} zkrácený", not cache.cely(data[:len(data) // 2]))
check("JPEG s výplní za koncem", cache.cely(JPG + b"\x00" * 100))
check("nesedí Content-Length", not cache.cely(JPG, len(JPG) + 1))
check("HTML není obrázek", not cache.cely(b"<html>zablokovano</html>"))

# 2) přes brzdu s lokálním serverem
s = ThreadingHTTPServer(("127.0.0.2", 0), H)
threading.Thread(target=s.serve_forever, daemon=True).start()
A = f"http://127.0.0.2:{s.server_address[1]}"
tmp = tempfile.mkdtemp(prefix="mezipamet_")
env = {**os.environ, "RODOKMEN_SNIMKY": os.path.join(tmp, "snimky"), "SLUSNE_STAV": os.path.join(tmp, "stav")}
KLIENT = os.path.join(tmp, "klient.py")
with open(KLIENT, "w", encoding="utf-8") as f:
    f.write(f"import sys; sys.path.insert(0, {TOOLS!r}); import slusne\n"
            "import http.client, urllib.request\n"
            "for u in sys.argv[1:]:\n"
            "    try:\n        n = len(urllib.request.urlopen(u, timeout=10).read())\n"
            "    except http.client.IncompleteRead:\n        n = 'IncompleteRead'\n"
            "    print(u.rsplit('/', 1)[-1], n, flush=True)\n")

# zkrácený snímek uložený starší verzí (0.7.0) – má se smazat a stáhnout znovu
os.environ["RODOKMEN_SNIMKY"] = env["RODOKMEN_SNIMKY"]
cache.KOREN = env["RODOKMEN_SNIMKY"]
stary = cache.cesta(cache.klic_url(A + "/stary.jpg")) + ".jpg"
os.makedirs(os.path.dirname(stary), exist_ok=True)
open(stary, "wb").write(JPG[:2000])

for kolo in (1, 2):
    r = subprocess.run([sys.executable, "-I", KLIENT] + [A + p for p in ("/cely.jpg", "/kratky.jpg", "/delka.jpg",
                                                                         "/stary.jpg")],
                       env=env, capture_output=True, text=True, timeout=120)
    if r.returncode:
        print(r.stdout, r.stderr)
check("celý snímek: z archivu jen jednou", HITS.get("/cely.jpg") == 1, HITS)
check("zkrácený bez délky: neuložen, stahuje se znovu", HITS.get("/kratky.jpg") == 2)
check("nesedí délka: neuložen", HITS.get("/delka.jpg") == 2)
check("zkrácený uložený dřív: smazán a stažen znovu (pak už z disku)", HITS.get("/stary.jpg") == 1
      and cache.cely_soubor(stary))
s.shutdown()

print(f"\n{sum(vysledky)} z {len(vysledky)} správně")
sys.exit(0 if all(vysledky) else 1)
