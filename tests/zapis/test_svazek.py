"""Test: příkaz „svazek“ nástrojů archivů změní v data/svazky.json jen svou položku (přes zapis.py), zbytek souboru
nechá doslova – dřív ho přepsal celý vlastním json.dump (jiné odsazení a pořadí = celý soubor změněný v historii).

Z kořene repozitáře:
  python3 -I tests/zapis/test_svazek.py skills/rodokmen/tools
Na archiv nechodí: popis knihy Porta fontium se nahradí pevnými daty.
"""
import contextlib, io, json, os, sys, tempfile

TOOLS = os.path.abspath(sys.argv[1])
sys.path.insert(0, TOOLS)
import portafontium as pf  # noqa: E402
import zapis  # noqa: E402

vysledky = []


def check(nazev, ok, detail=""):
    vysledky.append(bool(ok))
    print(f"[{'OK ' if ok else 'CHYBA'}] {nazev}{'' if ok else '  ' + str(detail)[:600]}", flush=True)


tmp = tempfile.mkdtemp(prefix="rodokmen_zapis_")
os.makedirs(os.path.join(tmp, "data"))
zapis.ROOT = tmp
cesta = os.path.join(tmp, "data", "svazky.json")
# vlastní formát uživatele: odsazení 2, ručně psaná položka – nástroj ho nesmí přeformátovat
puvodni = ('{\n  "abc12345": {"archiv": "SOA Zámrsk", "portal": "ARON", "svazek": "N Horní Lhota 1800–1850"},\n'
           '  "rucni": {\n    "archiv": "Jiný archiv",\n    "svazek": "O Dolní Lhota"\n  }\n}\n')
open(cesta, "w", encoding="utf-8", newline="\n").write(puvodni)

pf.info = lambda kniha: (kniha, {"Signatura": "1", "Typ": "N", "Místo": "Horní Lhota"}, [1, 2, 3], None)

out = io.StringIO()
with contextlib.redirect_stdout(out):
    pf.svazek("horni-lhota-01", jen_vypsat=True)
check("„vypis“ nic nezapíše", open(cesta, encoding="utf-8").read() == puvodni)
check("„vypis“ ukáže položku", "pf_horni-lhota-01" in out.getvalue() and '"snimku": 3' in out.getvalue(), out.getvalue())

with contextlib.redirect_stdout(io.StringIO()):
    pf.svazek("horni-lhota-01")
text = open(cesta, encoding="utf-8").read()
data = json.loads(text)
check("položka přidána", data.get("pf_horni-lhota-01", {}).get("snimku") == 3, data)
check("ostatní položky doslova beze změny", text.startswith(puvodni.rstrip()[:-2].rstrip()), text)

# opakované volání položku nahradí, nezdvojí
pf.info = lambda kniha: (kniha, {"Signatura": "1", "Typ": "N", "Místo": "Horní Lhota"}, [1, 2, 3, 4], None)
with contextlib.redirect_stdout(io.StringIO()):
    pf.svazek("horni-lhota-01")
text2 = open(cesta, encoding="utf-8").read()
check("opakované volání položku nahradí", text2.count("pf_horni-lhota-01") == 1 and json.loads(text2)["pf_horni-lhota-01"]["snimku"] == 4, text2)
check("ruční položka pořád ve vlastním formátu", '"rucni": {\n    "archiv": "Jiný archiv"' in text2, text2)

print(f"\n{sum(vysledky)} z {len(vysledky)} v pořádku")
sys.exit(0 if all(vysledky) else 1)
