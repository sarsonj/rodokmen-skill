"""Test filtru titulu v tools/anno.py (ANNO_TITLE, --ztraty) – offline, API ANNO se podvrhne.

Z kořene repozitáře:
  python3 -I tests/anno/test_ztraty.py skills/rodokmen/tools
ANNO filtruje titul parametrem selectedFilters=title:<zkratka> (parametr title= nezná a vrací 0, ověřeno 5. 11. 2026);
víc filtrů naráz se sčítá jako „a zároveň“, proto se tituly hledají po jednom.
"""
import contextlib, io, os, sys

TOOLS = os.path.abspath(sys.argv[1])
sys.path.insert(0, TOOLS)
import anno  # noqa: E402

vysledky = []


def check(nazev, ok, detail=""):
    vysledky.append(bool(ok))
    print(f"[{'OK ' if ok else 'CHYBA'}] {nazev}{'' if ok else '  ' + str(detail)[:600]}", flush=True)


VOLANI = []


def fake_get(path, params):
    VOLANI.append((path, dict(params)))
    if path == "snippet":
        return {"snippetPages": []}
    f = params.get("selectedFilters", "")
    titul = f.split(":", 1)[1] if f.startswith("title:") else None
    docs = {None: ["ANNO_ptb19141013", "ANNO_vlv19160812"], "vll": ["ANNO_vll19150301"],
            "vlv": ["ANNO_vlv19160812"], "nvv": ["ANNO_nvv19141210"]}.get(titul, [])
    return {"totalHits": len(docs), "textQuery": params["text"], "lastHit": len(docs),
            "documents": [{"docId": d, "displayTitle": d, "totalHitsInDoc": 1, "openUrl": "u"} for d in docs]}


anno.get = fake_get


def spust(argv, env=None):
    VOLANI.clear()
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        anno.main(argv, env or {})
    return out.getvalue()


out = spust(['"Hromadko Wenzel"', "1914", "1919"], {"ANNO_TITLE": "vlv"})
p = VOLANI[0][1]
check("ANNO_TITLE posílá selectedFilters=title:vlv", p.get("selectedFilters") == "title:vlv", p)
check("ANNO_TITLE neposílá neznámý parametr title=", "title" not in p, p)
check("výsledek z rejstříku ztrát", "ANNO_vlv19160812" in out, out)

out = spust(['"Hromadko Wenzel"', "1914", "1919"], {"ANNO_TITLE": "vll,nvv"})
filtry = [v[1].get("selectedFilters") for v in VOLANI if v[0] == "complex"]
check("víc titulů v ANNO_TITLE: každý zvlášť", filtry == ["title:vll", "title:nvv"], filtry)
check("víc titulů: výsledky obou", "ANNO_vll19150301" in out and "ANNO_nvv19141210" in out, out)

out = spust(['"Hromadko Wenzel"', "1914", "1919", "--ztraty"])
filtry = [v[1].get("selectedFilters") for v in VOLANI if v[0] == "complex"]
check("--ztraty hledá seznamy, rejstříky i raněné", filtry == ["title:vll", "title:vlv", "title:nvv"], filtry)
check("--ztraty: bez běžných novin", "ANNO_ptb" not in out and "ANNO_vll19150301" in out, out)

out = spust(['"Hromadko Wenzel"', "1914", "1919"])
p = VOLANI[0][1]
check("bez filtru: žádný selectedFilters", "selectedFilters" not in p and "ANNO_ptb19141013" in out, p)

print(f"\n{sum(vysledky)} z {len(vysledky)} správně")
sys.exit(0 if all(vysledky) else 1)
