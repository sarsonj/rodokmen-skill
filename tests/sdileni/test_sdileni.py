"""Test tools/sdileni.py bez sítě: rozpoznání knih z adres, odhad snímku, body a zápisy z dat projektu, fronta bodů.

    python3 -I tests/sdileni/test_sdileni.py
"""
import json, os, sys, tempfile

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "skills", "rodokmen", "tools")
projekt = tempfile.mkdtemp(prefix="sdileni_test_")
os.chdir(projekt)
os.makedirs("data")
sys.path.insert(0, TOOLS)
import sdileni  # noqa: E402

chyby = []


def ok(podminka, popis):
    if not podminka:
        chyby.append(popis)


ok(sdileni.kniha_z_url("https://www.portafontium.eu/register/soap-pn/kozlany-22") == ("soa-plzen", "portafontium", "kozlany-22"), "Porta fontium")
ok(sdileni.kniha_z_url("https://www.portafontium.eu/iipimage/30074619/kralovice-okresni-urad-10_1970-o")[2] == "kralovice-okresni-urad-10", "PF snímek")
ok(sdileni.kniha_z_url("https://ebadatelna.soapraha.cz/pages/MatrikaPage/matrikaId/4888") == ("soa-praha", "soapraha", "4888"), "eBadatelna")
ok(sdileni.kniha_z_url("https://ebadatelna.soapraha.cz/d/11973/15")[2] == "11973", "eBadatelna /d/")
ok(sdileni.kniha_z_url("https://katalog.ahmp.cz/pragapublica/permalink?xid=144286C6CCB648968F0C7879316827D0") == (None, "ahmp", "144286c6"), "AHMP")
ok(sdileni.kniha_z_url("https://aron.vychodoceskearchivy.cz/apu/abc") is None, "ARON zatím ne")

body = [{"scan": 10, "year": 1800}, {"scan": 30, "year": 1810}, {"scan": 40, "year": 1812, "year_to": 1813}]
ok(sdileni.odhad(body, 1805) == (20, "odhad mezi sn. 10 (1800) a 30 (1810)"), "interpolace")
ok(sdileni.odhad(body, 1813)[0] == 40, "přímo z bodu (year_to)")
ok(sdileni.odhad(body, 1700) is None, "mimo rozsah")
ok(sdileni.slug("Nová Ves u Plzně") == "nova-ves-u-plzne", "slug")

json.dump({"pf_k22": {"url": "https://www.portafontium.eu/register/soap-pn/kozlany-22", "svazek": "Kožlany 22, Matrika zemřelých"},
           "aron_x": {"url": "https://aron.vychodoceskearchivy.cz/apu/x"}}, open("data/svazky.json", "w"))
json.dump([{"klic": "stary", "svazek": "pf_k22", "snimek": 74, "druh": "Z", "datum": "17. 1. 1918", "shrnuti": "…"},
           {"klic": "mlady", "svazek": "pf_k22", "snimek": 140, "druh": "Z", "datum": "3. 2. 1960", "shrnuti": "…"},
           {"klic": "aron", "svazek": "aron_x", "snimek": 5, "druh": "N", "datum": "1. 1. 1800", "shrnuti": "…"}], open("data/zaznamy.json", "w"))
json.dump({"stary": {"orig": "…", "cs": "…"}, "mlady": {"orig": "…", "cs": "…"}}, open("data/prepisy.json", "w"))
b, z, mimo, klic = sdileni.nove()
ok(len(b) == 2 and {x["year"] for x in b} == {1918, 1960}, "body ze všech zápisů podporované knihy")
ok([x["klic"] for x in z] == ["stary"], "do indexu jen zápis starší lhůty")
ok(mimo == {"aron_x"}, "nepodporovaný archiv")
sdileni.bod("pf_k22", "3", "rok=1900", "druh=Z", "rejstrik=A–C")
b2, _, _, _ = sdileni.nove()
ok(len(b2) == 3 and any(x.get("type") == "iZ" and x.get("letters") == "A–C" for x in b2), "bod z fronty, rejstřík = iZ")
n = sdileni.nastaveni()
n["odeslano"]["body"] = [klic(x) for x in b2]
n["odeslano"]["zapisy"] = ["stary"]
b3, z3, _, _ = sdileni.nove(n)
ok(not b3 and not z3, "odeslané se znovu nenabízí")

print("\n".join(chyby) or "sdileni: vše v pořádku")
sys.exit(1 if chyby else 0)
