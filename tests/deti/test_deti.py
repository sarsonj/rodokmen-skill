"""Test tools/deti.py, zapis.py fakt a varování o faktu „děti“ v kontrola.py.

Z kořene repozitáře:
  python3 -I tests/deti/test_deti.py skills/rodokmen/tools
  (Windows: python -I -X utf8 …)
Postaví dočasný projekt s vymyšlenou rodinou, zkopíruje do něj nástroje a pustí je. Nic nestahuje.
"""
import json, os, shutil, subprocess, sys, tempfile

TOOLS = os.path.abspath(sys.argv[1])
PY = [sys.executable, "-I", "-X", "utf8"]
VYSLEDKY = []
OSOBY = """P = {
 1: dict(n='Martin Test', y='* 1990', st='doc', f=[], r=[], note='Žijící'),
 2: dict(n='Otec Test', y='1960', st='doc', f=[], r=[], note='Žijící'),
 3: dict(n='Matka Test', y='1962', st='doc', f=[], r=[]),
 4: dict(n='Karel Hora', y='1900–1970', st='doc', f=[], r=['k_krest']),
 5: dict(n='Marie Kosová', y='1903–1980', st='doc', f=[], r=[]),
 8: dict(n='Václav Hora', y='1870–1940', st='doc', f=['kovář'], r=[]),
 9: dict(n='Anna Nová', y='1875–1950', st='doc', f=[], r=[]),
}
SIDE = [
 dict(k=4, n='Josef Hora (1902–1960)', t='Bratr.', r=[]),
 dict(k=4, n='Anna Horová', t='Sestra, jen křest.', r=['k_krest_anna']),
 dict(k=4, n='Eva Horová', t='Sestra, rok neznámý.', r=[]),
 dict(k=4, n='Jiří Hora (* 2010)', t='Žijící.', r=[]),
]
SAME = {}
"""


def ma(nazev, ok, detail=""):
    VYSLEDKY.append(ok)
    print(("OK  " if ok else "CHYBA ") + nazev + ("" if ok else f"\n    {detail}"))


tmp = tempfile.mkdtemp(prefix="deti_")
try:
    os.makedirs(os.path.join(tmp, "tools"))
    os.makedirs(os.path.join(tmp, "data"))
    for n in ("deti.py", "zapis.py", "kontrola.py"):
        shutil.copy(os.path.join(TOOLS, n), os.path.join(tmp, "tools", n))
    with open(os.path.join(tmp, "data", "osoby.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write(OSOBY)
    zaz = [dict(klic="k_krest", druh="N", datum="3. 3. 1900", nazev="Křest", shrnuti="", odkaz=""),
           dict(klic="k_krest_anna", druh="N", datum="1. 1. 1905", nazev="Křest", shrnuti="", odkaz="")]
    with open(os.path.join(tmp, "data", "zaznamy.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(zaz, f, ensure_ascii=False, indent=1)

    def spust(nastroj, *args):
        r = subprocess.run(PY + [os.path.join("tools", nastroj), *args], cwd=tmp, capture_output=True, text=True, encoding="utf-8")
        return r.returncode, r.stdout + r.stderr

    def osoby():
        return open(os.path.join(tmp, "data", "osoby.py"), encoding="utf-8").read()

    rc, out = spust("deti.py", "Václav")
    ma("návrh: dítě v linii + sourozenci, rok z křtu, bez žijících a bez roku",
       rc == 0 and "děti: Karel 1900, Josef 1902, Anna 1905" in out and "Eva: bez roku" in out and "Jiří: žijící" in out, out)
    ma("návrh nic nezapíše", osoby() == OSOBY)
    rc, out = spust("deti.py", "9", "--zapsat")
    ma("--zapsat zapíše otci", rc == 0 and "'kovář', 'děti: Karel 1900, Josef 1902, Anna 1905'" in osoby().replace('"', "'"), out + osoby())
    rc, out = spust("deti.py", "--vse", "--zapsat")
    ma("--vse přeskočí pár, který fakt má", rc == 0 and "Zapsáno: 0" in out, out)
    rc, out = spust("zapis.py", "fakt", "99", "x")
    ma("fakt neznámé osobě selže", rc != 0)
    rc, out = spust("kontrola.py")
    ma("kontrola: správný tvar bez varování", "děti" not in out, out)
    spust("zapis.py", "fakt", "5", "děti Karel 1900")
    spust("zapis.py", "fakt", "3", "děti: Karel, Marie 1922")
    rc, out = spust("kontrola.py")
    ma("kontrola varuje před špatným tvarem", "nemá tvar" in out and "bez jména nebo roku" in out, out)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
sys.exit(0 if all(VYSLEDKY) else 1)
