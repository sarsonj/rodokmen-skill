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
ok(sdileni.rozsah_svazku({"svazek": "N Holice 1880–1900, sign. 12"}) == {"N": "1880–1900"}, "rozsah z názvu")
ok(sdileni.rozsah_svazku({"svazek": "Matrika zemřelých 1784-1830"}) == {"Z": "1784–1830"}, "rozsah z názvu, druh slovem")
ok(sdileni.rozsah_svazku({"svazek": "N 1800–1820, O 1800–1830"}) == {}, "víc druhů = bez rozsahu")
ok(sdileni.rozsah_svazku({"svazek": "Kožlany 21, Matrika oddaných"}) == {}, "bez let = bez rozsahu")
ok(sdileni.rozsah_svazku({"roky": {"N": "1900–1905", "X": "1"}, "svazek": "Z 1700–1710"}) == {"N": "1900–1905"}, "pole roky má přednost")

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

# ---------- hledání podle jména (bez sítě: index podstrčený místo json_z / stahni) ----------
ok(sdileni.kmen("Červenková") == "červenk" and sdileni.kmen("Veselý") == "vesel" and sdileni.kmen("Wick") == "wick", "kmen příjmení")
ok({"prihod", "przihod", "przyhod"} <= set(sdileni.tvary("příhod")), "starý pravopis")
ok(sdileni.shoduje(["przihoda"], sdileni.tvary("příhod")) == "przihoda", "shoda starého tvaru")
ok(sdileni.shoduje(["musel"], ["musil"]) is None, "očima přesně")
ok(sdileni.shoduje(["przihoga"], sdileni.tvary("příhod"), ocr=True) == "przihoga", "OCR s odchylkou")
ok(sdileni.kniha_indexu_jinde("https://aron.vychodoceskearchivy.cz/apu/1A6D0B5C-5f05-41fe") == "vca/1a6d0b5c", "ARON klíč indexu")
ok(sdileni.kniha_indexu_jinde("https://www.mza.cz/actapublica/matrika/detail/7122") == "mza/7122", "MZA klíč indexu")

KNIHY = [{"id": "vca/1a6d0b5c", "nazev": "Choceň N 1725–1785", "farnost": "Choceň", "obsah": "", "url": "u1", "ocr_stran": 2,
          "ocr_cteni": [{"soubor": "ocr-pero.tsv"}]},
         {"id": "portafontium/x-01", "nazev": "Jinde 01", "farnost": "Jinde", "obsah": "", "url": "u2", "ocr_stran": 0}]
PRECTENO = [[0, "300", "1755-01-27", "N", "Choceň", "dítě: Alžběta; otec: Tomáš Przihoda", "", "vysoká", "Někdo 2026-11-01", ""],
            [0, "321", "1759-01-17", "N", "Choceň", "dítě: Dorota; otec: Jan Walach", "", "vysoká", "Jiný 2026-11-02", ""],
            [1, "5", "1800-01-01", "N", "Jinde", "dítě: Jan; otec: Josef Příhoda", "", "vysoká", "X 2026-11-03", ""]]
OCR = "snimek\tsoubor\tstrana\tradek\ttext\n319\tf\tL\t11\tbarne, Przihöda\n320\tf\tL\t12\tnic tu není\n"
sdileni.json_z = lambda url: KNIHY if url.endswith("knihy.json") else PRECTENO if url.endswith("precteno.json") else None
sdileni.stahni = lambda url, max_stari=0: OCR if url.endswith("ocr-pero.tsv") else None
json.dump({"ch": {"url": "https://aron.vychodoceskearchivy.cz/apu/1a6d0b5c-5f05"}}, open("data/svazky.json", "w"))
json.dump([{"klic": "a1755", "svazek": "ch", "snimek": 300, "druh": "N", "datum": "27. 1. 1755"}], open("data/zaznamy.json", "w"))
json.dump({"Choceň": {"re": "Choc(eň|ni|ně)", "lat": 50, "lon": 16}}, open("data/mista.json", "w", encoding="utf-8"), ensure_ascii=False)
open("data/osoby.py", "w", encoding="utf-8").write('P = {1: dict(n="Petr Novák", note="Žijící – údaje jen základní."), '
                                                    '4: dict(n="Tomáš Příhoda", f=["* 1731 Choceň"])}\nSIDE = []\n')
import io, contextlib  # noqa: E402
out = io.StringIO()
with contextlib.redirect_stdout(out):
    sdileni.hledej(["Příhoda"])
t = out.getvalue()
ok("z knih a obcí projektu 1" in t and "vca/1a6d0b5c sn. 300" in t and "portafontium/x-01" in t, "hledej: projekt celý, jinde počet\n" + t)
out = io.StringIO()
with contextlib.redirect_stdout(out):
    sdileni.shody()
t = out.getvalue()
ok("4 Tomáš Příhoda" in t and "sn. 300" not in t and "OCR vca/1a6d0b5c: sn. 319" in t and "Novák" not in t,
   "shody: bez zápisu projektu a žijících, OCR jen snímek\n" + t)

print("\n".join(chyby) or "sdileni: vše v pořádku")
sys.exit(1 if chyby else 0)
