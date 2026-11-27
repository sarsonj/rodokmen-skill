"""Test odhadu pohlaví podle křestního jména v tools/kontrola.py (kontrola prohozeného otce a matky).

Z kořene repozitáře:
  python3 -I tests/kontrola/test_pohlavi.py skills/rodokmen/tools/kontrola.py
"""
import importlib.util, os, sys

spec = importlib.util.spec_from_file_location("kontrola", os.path.abspath(sys.argv[1]))
k = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k)

PRIPADY = [
    ("Anna Nováková", True), ("Marie", True), ("Kateřina Dvořáková (?)", True), ("Elisabeth Weber", True),
    ("Jan Novák", False), ("Jiří", False), ("Matěj Píček", False), ("Nikola Tesla", False), ("Kuba Novák", False),
    ("otec neuveden", None), ("matka neuvedena", None), ("N. N.", None), ("", None), ("? Novák", None),
]
chyby = [(j, ocek, k.vypada_na_zenu(j)) for j, ocek in PRIPADY if k.vypada_na_zenu(j) is not ocek]
for j, ocek, dost in chyby:
    print(f"CHYBA {j!r}: čekáno {ocek}, je {dost}")
print(f"{len(PRIPADY) - len(chyby)} z {len(PRIPADY)} v pořádku")
sys.exit(1 if chyby else 0)
