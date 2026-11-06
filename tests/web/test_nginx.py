"""Test nginx.conf, který z šablony vyrábí tools/export_web.py (nasazení přes Docker/CapRover).

Založí ukázkový projekt v dočasné složce, spustí export s otázkou i pro otevřený web a kontroluje mapu
$cookie_rodokmen: právě jeden `default` (dvojí `default` nginx odmítne, #61). Je-li k dispozici Docker,
ověří konfiguraci i samotným nginx (`nginx -t` v image z web/Dockerfile).
Z kořene repozitáře:
  python3 -I tests/web/test_nginx.py skills/rodokmen
"""
import json, os, re, shutil, subprocess, sys, tempfile

SKILL = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "skills/rodokmen")
vysledky = []


def check(nazev, ok, detail=""):
    vysledky.append(bool(ok))
    print(f"[{'OK ' if ok else 'CHYBA'}] {nazev}{'' if ok else '  ' + str(detail)[:800]}", flush=True)


def mapa(conf):
    m = re.search(r"map \$cookie_rodokmen \$rodokmen_ok \{(.*?)\n\}", conf, re.S)
    return m.group(1) if m else ""


def export(projekt, prihlaseni):
    cesta = os.path.join(projekt, "data", "web.json")
    cfg = json.load(open(cesta, encoding="utf-8"))
    cfg["prihlaseni"] = prihlaseni
    json.dump(cfg, open(cesta, "w", encoding="utf-8"), ensure_ascii=False)
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(projekt, "tools", "export_web.py")],
                       capture_output=True, text=True, cwd=projekt)
    conf = os.path.join(projekt, "web", "nginx.conf")
    return r, (open(conf, encoding="utf-8").read() if os.path.exists(conf) else "")


def docker_image(projekt):
    for radek in open(os.path.join(projekt, "web", "Dockerfile"), encoding="utf-8"):
        if radek.startswith("FROM nginx"):
            return radek.split()[1]


def nginx_t(conf, image):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "default.conf")
        open(p, "w", encoding="utf-8").write(conf)
        r = subprocess.run(["docker", "run", "--rm", "-v", f"{p}:/etc/nginx/conf.d/default.conf:ro", image, "nginx", "-t"],
                           capture_output=True, text=True)
        return r.returncode == 0, r.stderr[-400:]


tmp = tempfile.mkdtemp()
try:
    projekt = os.path.join(tmp, "projekt")
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(SKILL, "tools", "novy_projekt.py"), projekt, "--ukazka"],
                       capture_output=True, text=True)
    check("ukázkový projekt založen", r.returncode == 0, r.stderr)

    r, s_otazkou = export(projekt, {"otazka": "Řemeslo?", "odpoved": "kovář"})
    m = mapa(s_otazkou)
    check("s otázkou: export proběhl", r.returncode == 0, r.stderr)
    check("s otázkou: v mapě default 0 a otisk", m.count("default") == 1 and "default 0;" in m and re.search(r'"[0-9a-f]{64}" 1;', m), m)
    check("s otázkou: map_hash_bucket_size pro 64znakový otisk", "map_hash_bucket_size 128;" in s_otazkou, s_otazkou[:300])

    r, otevreny = export(projekt, {"otevreny": True})
    m = mapa(otevreny)
    check("otevřený web: export proběhl", r.returncode == 0, r.stderr)
    check("otevřený web: v mapě právě jeden default, a to 1", m.count("default") == 1 and "default 1;" in m, m)
    check("otevřený web: v mapě žádný otisk", not re.search(r'"[0-9a-f]{64}"', m), m)

    image = docker_image(projekt)
    check("Dockerfile: nginx:stable-alpine", image == "nginx:stable-alpine", image)
    if shutil.which("docker") and subprocess.run(["docker", "info"], capture_output=True).returncode == 0:
        for nazev, conf in (("s otázkou", s_otazkou), ("otevřený web", otevreny)):
            ok, err = nginx_t(conf, image)
            check(f"nginx -t ({image}): {nazev}", ok, err)
    else:
        print("[–] Docker není k dispozici, nginx -t přeskočeno")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\n{sum(vysledky)} z {len(vysledky)} správně")
sys.exit(0 if all(vysledky) else 1)
