"""Test chronologického řazení údajů o osobě (chrono_facts v tools/export_web.py).

Z kořene repozitáře, testovaný export je argument:
  python3 -I tests/web/test_chrono.py skills/rodokmen/tools/export_web.py
  (Windows: python -I -X utf8 …)
Funkci vytáhne ze zdrojového kódu (je vnořená v main) a pustí na vymyšlených údajích. Jen standardní knihovna.
"""
import ast, re, sys

src = open(sys.argv[1], encoding="utf-8").read()
fn = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "chrono_facts")
ns = {"re": re}
exec(compile(ast.Module(body=[fn], type_ignores=[]), "chrono_facts", "exec"), ns)
chrono = ns["chrono_facts"]

PRIPADY = [
    ("úmrtí na konci, narození na začátku",
     ["† 2. 4. 1990 Horní Ves", "* 3. 5. 1910 Dolní Ves 7", "× 4. 6. 1935 Horní Ves Jan Novák", "švadlena – průkaz 5. 7. 1940"],
     ["* 3. 5. 1910 Dolní Ves 7", "× 4. 6. 1935 Horní Ves Jan Novák", "švadlena – průkaz 5. 7. 1940", "† 2. 4. 1990 Horní Ves"]),
    ("údaj bez data zůstane za předchozím",
     ["* 1. 2. 1850 Lhota 3", "rolník v Lhotě čp. 3", "× 3. 4. 1875 Lhota Marie", "† 5. 6. 1920"],
     ["* 1. 2. 1850 Lhota 3", "rolník v Lhotě čp. 3", "× 3. 4. 1875 Lhota Marie", "† 5. 6. 1920"]),
    ("datum s římským měsícem a samotný rok",
     ["× asi X 1720 Újezd", "grunt převzal 1760", "~ 6. 7. 1730 Újezd", "svědek 2. V. 1725"],
     ["~ 6. 7. 1730 Újezd", "× asi X 1720 Újezd", "svědek 2. V. 1725", "grunt převzal 1760"]),
    ("pohřeb a křest", ["pohřben 8. 9. 1750", "~ 7. 8. 1690"], ["~ 7. 8. 1690", "pohřben 8. 9. 1750"]),
    ("prázdný seznam", [], []),
]

chyby = 0
for nazev, vstup, cekam in PRIPADY:
    vysl = chrono(vstup)
    ok = vysl == cekam
    chyby += not ok
    print(("OK   " if ok else "CHYBA"), nazev, "" if ok else f"\n  čekám {cekam}\n  dostal {vysl}")
print(f"{len(PRIPADY) - chyby}/{len(PRIPADY)} prošlo")
sys.exit(1 if chyby else 0)
