#!/usr/bin/env python3
"""Testy tools/folio.py (folio/strana → snímek).
Spuštění z kořene repa:
  python3 -I tests/folio/test_folio.py skills/rodokmen/tools
"""
import os, subprocess, sys
NASTROJ = os.path.join(sys.argv[1] if len(sys.argv) > 1 else "skills/rodokmen/tools", "folio.py")
ok = celkem = 0


def spust(*a):
    r = subprocess.run([sys.executable, "-I", NASTROJ, *a], capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout + r.stderr


def check(nazev, podminka, vystup=""):
    global ok, celkem
    celkem += 1
    ok += bool(podminka)
    print(("OK   " if podminka else "CHYBA"), nazev, "" if podminka else "\n" + vystup)


# dvoustrany: snímek 10 = 1v/2r … posun mezi oddíly se mění (vlepený list mezi 20r a 30r)
k, o = spust("10=1v", "20=10v", "31=20v", "15r", "25v")
check("interpolace v úseku (posun se mezi body mění)", k == 0 and "folio 15r → snímek ≈ 25" in o, o)
check("za posledním bodem prodlouží poslední úsek", "folio 25v → snímek ≈ 36 (mezi 36 a 37)" in o and "mimo známé body" in o, o)
k, o = spust("10=1r", "30=21r", "11r")
check("lineárně mezi body (1 snímek = 1 list)", "snímek ≈ 20" in o, o)
k, o = spust("10=1r", "30=21r", "40r")
check("mimo body prodlouží a upozorní", "snímek ≈ 49" in o and "mimo známé body" in o, o)
k, o = spust("10=5r", "7r")
check("jedna dvojice = dvoustrana s upozorněním", "snímek ≈ 12" in o and "jen jedna dvojice" in o, o)
k, o = spust("--pagina", "5=12", "15=32", "22")
check("paginace", "pagina 22 → snímek ≈ 10" in o, o)
k, o = spust("--pagina", "5=12v", "22")
check("paginace bez r/v", k != 0 and "nerozumím" in o, o)
k, o = spust("10=5r", "8=7r", "6r")
check("snímky jdou proti foliím – varování", "POZOR" in o, o)
k, o = spust("10=5r", "12=5r", "6r")
check("totéž folio u dvou snímků – chyba", k != 0 and "u dvou snímků" in o, o)
k, o = spust("abc")
check("nesmysl – srozumitelná hláška", k != 0 and "nerozumím" in o, o)
print(f"\n{ok} z {celkem} v pořádku")
sys.exit(0 if ok == celkem else 1)
