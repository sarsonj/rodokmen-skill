"""Test dobových map: položka "druh": "mapa" v data/dokumenty.json → site.json „maps“ (stránka rodu, okénko mapy předků).

Založí ukázkový projekt v dočasné složce, přidá vymyšlenou mapu s obrázkem a spustí export (bez sítě).
Z kořene repozitáře:
  python3 -I tests/web/test_mapy.py skills/rodokmen
  (Windows: python -I -X utf8 …)
"""
import json, os, shutil, subprocess, sys, tempfile

SKILL = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "skills/rodokmen")
vysledky = []


def check(nazev, ok, detail=""):
    vysledky.append(bool(ok))
    print(f"[{'OK ' if ok else 'CHYBA'}] {nazev}{'' if ok else '  ' + str(detail)[:800]}", flush=True)


tmp = tempfile.mkdtemp()
try:
    projekt = os.path.join(tmp, "projekt")
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(SKILL, "tools", "novy_projekt.py"), projekt, "--ukazka"],
                       capture_output=True, text=True)
    check("ukázkový projekt založen", r.returncode == 0, r.stderr)

    docs = [{"img": "mapa_lhota_1841", "druh": "mapa", "rod": 8, "osoby": [18], "misto": "Holice", "rok": 1841,
             "popis": "Zakroužkované čp. 12.", "zdroj": "Indikační skica (vymyšlená)", "odkaz": "https://example.org/skica"},
            {"img": "mapa_bez_obrazku", "druh": "mapa", "rod": [9], "popis": "Obrázek chybí."},
            {"img": "mapa_bez_rodu", "druh": "mapa", "rod": [99, "8"], "osoby": [2], "popis": "Rod 99 není, otec rod nemá."},
            {"img": "foto_svatba", "popis": "Svatba.", "osoby": [8]}]
    json.dump(docs, open(os.path.join(projekt, "data", "dokumenty.json"), "w", encoding="utf-8"), ensure_ascii=False)
    os.makedirs(os.path.join(projekt, "vyrezy"), exist_ok=True)
    jpg = os.path.join(SKILL, "template", "ukazka_vyrezy", "ukazka_krest_jan_novak_1890.jpg")
    for img in ("mapa_lhota_1841", "mapa_bez_rodu", "foto_svatba"):
        shutil.copy(jpg, os.path.join(projekt, "vyrezy", img + ".jpg"))

    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(projekt, "tools", "export_web.py")],
                       capture_output=True, encoding="utf-8", errors="replace", cwd=projekt)
    check("export proběhl", r.returncode == 0, r.stderr)
    site = json.load(open(os.path.join(projekt, "web", "src", "data", "site.json"), encoding="utf-8"))
    maps = site.get("maps", [])
    check("mapa s obrázkem v „maps“, bez obrázku ne", [m["img"] for m in maps] == ["mapa_lhota_1841", "mapa_bez_rodu"], maps)
    check("mapa bez rodu: prázdné rody a POZOR v exportu",
          [m["lines"] for m in maps if m["img"] == "mapa_bez_rodu"] == [[]] and "mapa_bez_rodu nepatří" in r.stdout, r.stdout[-400:])
    m = maps[0] if maps else {}
    check("rody z „rod“ (číslo) i z osob", m.get("lines") == [8, 9], m)
    check("obec, rok, zdroj a odkaz", (m.get("place"), m.get("year"), m.get("url")) == ("Holice", 1841, "https://example.org/skica"), m)
    check("mapa není mezi dokumenty, fotka ano", [d["img"] for d in site["docs"]] == ["foto_svatba"], site["docs"])
    check("obrázek mapy zkopírován na web",
          os.path.exists(os.path.join(projekt, "web", "public", "img", "mapa_lhota_1841.jpg")))
    check("obec mapy je mezi místy mapy předků", any(p["name"] == "Holice" for p in site["places"]),
          [p["name"] for p in site["places"]])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\n{sum(vysledky)} z {len(vysledky)} v pořádku")
sys.exit(0 if all(vysledky) else 1)
