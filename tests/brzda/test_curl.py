#!/usr/bin/env python3
"""Brzda u `slusne.py curl …`: adresa bez https://, víc adres, rozsahy [..]/{..} a vlastní -w.

Nic nestahuje: místo curlu běží podvržený skript (SLUSNE_CURL), který jen zapíše argumenty a podle -w vypíše
stavový kód z FAKE_KOD. Stav brzdy je v dočasné složce (SLUSNE_STAV).

    python3 -I tests/brzda/test_curl.py skills/rodokmen/tools/slusne.py
"""
import json, os, subprocess, sys, tempfile

SLUSNE = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "skills/rodokmen/tools/slusne.py")
TMP = tempfile.mkdtemp(prefix="test_curl_")
FAKE = os.path.join(TMP, "fakecurl.py")
LOG = os.path.join(TMP, "log")
with open(FAKE, "w", encoding="utf-8") as f:
    f.write(r'''import sys, os, json
a = sys.argv[1:]
if a == ["--version"]:
    print("curl 8.5.0 (fake)"); sys.exit(0)
open(os.environ["FAKE_LOG"], "a", encoding="utf-8").write(json.dumps(a) + "\n")
w = None
for i, x in enumerate(a):
    if x in ("-w", "--write-out"): w = a[i + 1]
url = next((x for x in a if "://" in x), "")
if w:
    w = w.replace("%{http_code}", os.environ.get("FAKE_KOD", "200")).replace("%{url_effective}", url)
    for i, part in enumerate(w.split("%{stderr}")):
        (sys.stdout if i == 0 else sys.stderr).write(part)
''')
if os.name == "nt":
    CURL = os.path.join(TMP, "fakecurl.cmd")
    open(CURL, "w").write(f'@"{sys.executable}" "{FAKE}" %*\n')
else:
    CURL = os.path.join(TMP, "fakecurl")
    open(CURL, "w").write(f'#!/bin/sh\nexec "{sys.executable}" "{FAKE}" "$@"\n')
    os.chmod(CURL, 0o755)

vysledky = []


def curl(*args, kod="200", stav="a"):
    open(LOG, "w").close()
    env = dict(os.environ, SLUSNE_CURL=CURL, SLUSNE_STAV=os.path.join(TMP, "stav_" + stav), FAKE_LOG=LOG, FAKE_KOD=kod)
    p = subprocess.run([sys.executable, "-I", SLUSNE, "curl", *args], capture_output=True, text=True, encoding="utf-8",
                       env=env)
    volani = [json.loads(r) for r in open(LOG, encoding="utf-8").read().splitlines()]
    return p.returncode, p.stdout, p.stderr, volani


def over(nazev, podminka, info=""):
    vysledky.append(podminka)
    print(f"[{'OK ' if podminka else 'CHYBA'}] {nazev} {info}")


k, out, err, v = curl("-s", "www.mza.cz/actapublica/matrika/detail/1")
over("adresa bez https:// na zakázaný web se zastaví", k == 3 and not v and "MZA" in err, f"kód {k}")

k, out, err, v = curl("-s", "-O", "https://img.example.cz/a.jpg", "-O", "https://img.example.cz/b.jpg")
over("dvě adresy v jednom curl odmítne", k == 2 and not v, f"kód {k}")

k, out, err, v = curl("-s", "-O", "https://img.example.cz/img[1-200].jpg")
over("rozsah [1-200] odmítne", k == 2 and not v, f"kód {k}")

k, out, err, v = curl("-s", "-O", "https://img.example.cz/{a,b}.jpg")
over("rozsah {a,b} odmítne", k == 2 and not v, f"kód {k}")

k, out, err, v = curl("-sg", "-o", "x.jpg", "https://img.example.cz/a[1].jpg")
over("s -g závorku pustí", k == 0 and len(v) == 1, f"kód {k}")

k, out, err, v = curl("-s", "-o", "out.jpg", "https://img.example.cz/x.jpg")
over("hodnota -o („out.jpg“) není druhá adresa", k == 0 and len(v) == 1, f"kód {k}")

k, out, err, v = curl("-sSLo", "pracovni/x.jpg", "https://img.example.cz/x.jpg")
over("sloučené -sSLo bere další argument jako soubor", k == 0 and len(v) == 1, f"kód {k}")

k, out, err, v = curl("-s", "-o", "x.jpg", "-w", "%{http_code}", "https://digi.archives.cz/da/x", kod="429", stav="b")
over("vlastní -w: výstup uživateli zůstane", out == "429", repr(out))
over("vlastní -w: 429 web zastaví", k == 3 and "zastaven" in err, f"kód {k}")
k2, _, err2, v2 = curl("-s", "https://digi.archives.cz/da/y", stav="b")
over("po 429 další dotaz neodejde", k2 == 3 and not v2, f"kód {k2}")

print(f"\n{sum(vysledky)} z {len(vysledky)} testů prošlo")
sys.exit(0 if all(vysledky) else 1)
