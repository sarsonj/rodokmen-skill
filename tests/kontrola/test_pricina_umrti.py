"""Příčina úmrtí: kontrola dat, export a zapojení do kontroly citlivých textů.

Z kořene repozitáře: python3 -I tests/kontrola/test_pricina_umrti.py
Pouze smyšlené zápisy v dočasném projektu, nic se nestahuje.
"""
import datetime
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[2] / "skills" / "rodokmen"
UVEDENA = dict(stav="uvedena", puvodni="Altersschwäche", cesky="stařecká slabost", jistota="doc")


class PricinaUmrti(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="rodokmen_pricina_")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "data").mkdir()
        (self.root / "tools").mkdir()
        for name in ("kontrola.py", "export_web.py"):
            shutil.copyfile(SKILL / "tools" / name, self.root / "tools" / name)
        (self.root / "data" / "osoby.py").write_text(
            'P = {1: dict(n="Jan Novák", y="1800–1870", st="fam", f=[], r=[])}\n', encoding="utf-8")

    def record(self, **fields):
        return dict(klic="umrti_jan_1870", druh="Z", datum="1870", nazev="Úmrtí Jana Nováka",
                    shrnuti="Smyšlený zápis pro test.", ukazka=True, **fields)

    def write_json(self, name, value):
        (self.root / "data" / name).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def check(self, record, config=None):
        self.write_json("zaznamy.json", [record])
        self.write_json("web.json", config or {})
        return subprocess.run([sys.executable, "-I", "-X", "utf8", str(self.root / "tools" / "kontrola.py")],
                              capture_output=True, text=True, encoding="utf-8")

    def assert_invalid(self, cause, kind="Z"):
        record = self.record(pricina_umrti=cause)
        record["druh"] = kind
        result = self.check(record)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("CHYBA:", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_starsi_zapis_bez_pole(self):
        record = self.record()
        record.pop("ukazka")
        result = self.check(record)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("příčina úmrtí", result.stdout)

    def test_vsechny_stavy_a_nejiste_cteni(self):
        causes = [UVEDENA, dict(UVEDENA, jistota="prob", puvodni="Altersschwäche (?)"),
                  dict(stav="necitelna", puvodni="Al[…]", poznamka="Poškozený sloupec."),
                  dict(stav="necitelna"), dict(stav="nevyplnena"), dict(stav="bez_rubriky")]
        for cause in causes:
            with self.subTest(cause=cause):
                result = self.check(self.record(pricina_umrti=cause))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_neplatny_objekt_nebo_stav(self):
        for cause in (None, [], "neznámá", 12, False, {}, dict(stav="neznamy"), dict(stav=[])):
            with self.subTest(cause=cause):
                self.assert_invalid(cause)
        for kind in ("N", "O", "I", "S", "J"):
            with self.subTest(kind=kind):
                self.assert_invalid(UVEDENA, kind)

    def test_uvedena_potrebuje_text_a_jistotu(self):
        for field in ("puvodni", "cesky", "jistota"):
            cause = {k: v for k, v in UVEDENA.items() if k != field}
            with self.subTest(missing=field):
                self.assert_invalid(cause)
            for value in ("", "  ", None, 42, []):
                with self.subTest(field=field, value=value):
                    self.assert_invalid(dict(UVEDENA, **{field: value}))
        self.assert_invalid(dict(UVEDENA, jistota="jista"))
        self.assert_invalid(dict(UVEDENA, poznamka=[]))

    def test_chybejici_pricina_nema_preklad(self):
        for state in ("necitelna", "nevyplnena", "bez_rubriky"):
            with self.subTest(state=state):
                self.assert_invalid(dict(stav=state, cesky="stařecká slabost"))
        for state in ("nevyplnena", "bez_rubriky"):
            with self.subTest(state=state):
                self.assert_invalid(dict(stav=state, puvodni="Altersschwäche"))

    def test_export_zachova_original_i_chybejici_stavy(self):
        causes = [dict(UVEDENA, jistota="prob", puvodni='Al[…] <zkouška> & "text"'),
                  dict(stav="necitelna", puvodni="Al[…]"), dict(stav="nevyplnena"), dict(stav="bez_rubriky")]
        records = [dict(self.record(pricina_umrti=c), klic=f"umrti_{i}") for i, c in enumerate(causes)]
        records.append(self.record())
        self.write_json("zaznamy.json", records)
        before = (self.root / "data" / "zaznamy.json").read_bytes()
        exporter = runpy.run_path(str(self.root / "tools" / "export_web.py"))
        rows = exporter["record_rows"]()
        self.assertEqual([r["cause"] for r in rows], causes + [None])
        self.assertEqual((self.root / "data" / "zaznamy.json").read_bytes(), before)

    def test_novodoba_pricina_projde_kontrolou_citlivych_textu(self):
        cause = dict(UVEDENA, cesky="rakovina")
        record = self.record(pricina_umrti=cause)
        record["datum"] = str(datetime.date.today().year - 10)
        result = self.check(record)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("CITLIVÉ (příčina úmrtí umrti_jan_1870)", result.stdout)
        result = self.check(record, {"citlive_schvaleno": ["rakovina"]})
        self.assertNotIn("CITLIVÉ", result.stdout)
        record["datum"] = "1800"
        self.assertNotIn("CITLIVÉ", self.check(record).stdout)


if __name__ == "__main__":
    unittest.main()
