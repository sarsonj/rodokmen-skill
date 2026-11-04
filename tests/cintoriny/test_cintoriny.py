"""Testy tools/cintoriny.py (výpis hledání po stránkách, karta hrobu, převod dat).

Z kořene repozitáře:
  python3 -I tests/cintoriny/test_cintoriny.py
  (Windows: python -I -X utf8 tests/cintoriny/test_cintoriny.py)
Nic nestahuje: odpovědi portálu cintoriny.sk jsou vepsané v testu, get() se nahradí.
"""
import importlib.util, os, sys, tempfile, unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest import mock

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "skills", "rodokmen", "tools")
os.environ.setdefault("SLUSNE_STAV", tempfile.mkdtemp(prefix="cintoriny_slusne_"))   # brzda při importu nesahá na skutečný stav
sys.path.insert(0, TOOLS)
spec = importlib.util.spec_from_file_location("cintoriny", os.path.join(TOOLS, "cintoriny.py"))
cintoriny = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cintoriny)

# Zkrácené odpovědi portálu cintoriny.sk (tvar z 4. 11. 2026).
STRANA1 = (
    '<input type="hidden" id="searchPayload" value="surname=Izso" /><div>Počet záznamov: 3</div>\n<ul>'
    '<li><div>SK VÚC: Bratislavský</div><ul><li><div>Okres: Bratislava</div><ul>'
    '<li><div>Obec/mesto: Bratislava - Petržalka</div><ul><li><div>Cintorín:  <a data-cemetery-id="68">Cintorín Petržalka</a></div>'
    '<div class="people" style="margin-left:-55px">'
    '<div class="name-column colspan "><a data-grave-id="68002334" data-deceased-id="554130587">Izsof Jozef</a></div>'
    '<div class="break-word">*&nbsp;07.05.1903</div><div class="break-word">†&nbsp;01.01.1974</div><div>70&nbsp;r.</div>'
    '<div class="name-column colspan "><a data-grave-id="68002334" data-deceased-id="554130588">Izsofová Viktória</a></div>'
    '<div class="break-word">*&nbsp;03.01.1903</div><div class="break-word">†&nbsp;28.06.1992</div><div>89&nbsp;r.</div>'
    '</div></li></ul></li></ul></li></ul></li></ul>\n'
    '<div class="more-rows" data-from-id="473243032" data-shown-so-far="2">... viac údajov (2/2)</div>'
)
STRANA2 = (
    '<div class="people" style="margin-left:5px"></div><div>Cintorín:  <a data-cemetery-id="1379">Strašnice</a></div>'
    '<div class="people"><div class="name-column colspan "><a data-grave-id="1379000001" data-deceased-id="1">Izsó Anna</a></div>'
    '<div>*&nbsp;neuvedený</div><div>†&nbsp;neuvedený</div><div></div></div>'
)
KARTA = (
    '<div class="col">Sektor: <span>13</span></div><div class="col">Rad: <span>-</span></div>'
    '<div class="col grave-numbers"><span>Číslo: </span><span>163</span></div>'
    '<div class="col col-md-4 mobile-hide">Špecifikácia: <span>Hrobové miesto</span></div>'
    '<div class="col col-md-3 mobile-hide">Typ: <span>jednohrob</span></div>'
    '<input id="karta-hrob-starecislo" value="XIII-159" type="text" readonly/>'
    '<tbody id="zosnuly-zoznam"><tr class=""><td><span class="fake-link" data-grave-id="68002334" data-deceased-id="554130587">Izsof</span></td>'
    '<td>Jozef</td><td></td><td>07.05.1903</td><td>01.01.1974</td><td>70</td><td>01.01.1974</td><td></td></tr></tbody>'
)
DETAIL = '<input id="karta-zosnuly-miestonarodenia" value="Kajal" type="text" readonly/>'


class HledatTests(unittest.TestCase):
    def test_parses_people_cemeteries_and_follows_pages(self):
        dotazy = []

        def fake_get(path, data=None, binary=False):
            dotazy.append(data)
            return STRANA1 if len(dotazy) == 1 else STRANA2

        out = StringIO()
        with mock.patch.object(cintoriny, "get", fake_get), redirect_stdout(out):
            cintoriny.hledat({"surname": "Izso"}, 2)
        radky = out.getvalue().splitlines()
        self.assertEqual(radky[0], "Izsof Jozef | * 07.05.1903 | † 01.01.1974 | 70 r. | "
                                   "Cintorín Petržalka (Bratislava - Petržalka) | hrob 68:68002334")
        self.assertIn("| Strašnice | hrob 1379:1379000001", radky[2])
        self.assertEqual(dotazy[1], {"surname": "Izso", "subsetFrom": "473243032", "shownSoFar": "2"})

    def test_converts_dates(self):
        self.assertEqual(cintoriny.datum("1903", False), "1903-01-01")
        self.assertEqual(cintoriny.datum("1903", True), "1903-12-31")
        self.assertEqual(cintoriny.datum("7. 5. 1903", False), "1903-05-07")


class HrobTests(unittest.TestCase):
    def test_prints_grave_card_with_details(self):
        def fake_get(path, data=None, binary=False):
            return KARTA if "GetCard" in path else DETAIL

        out = StringIO()
        with mock.patch.object(cintoriny, "get", fake_get), redirect_stdout(out):
            cintoriny.hrob("68:68002334")
        text = out.getvalue()
        self.assertIn("sektor 13, řada -, číslo 163 (Hrobové miesto, jednohrob)", text)
        self.assertIn("Dřívější číslo hrobu: XIII-159", text)
        self.assertIn("- Jozef Izsof | * 07.05.1903 | † 01.01.1974 | 70 r. | uložen 01.01.1974 | místo narození Kajal", text)
        self.assertIn("zástupné", text)


if __name__ == "__main__":
    unittest.main()
