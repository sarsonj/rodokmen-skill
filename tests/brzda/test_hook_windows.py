"""Hook hlídače na Windows: do .claude/settings.json jde plná cesta k Pythonu, ne „python“ z PATH.

Hooky Claude Code běží s jiným PATH než příkaz, kterým se projekt aktualizoval – „python“ tam může vést na nefunkční
zástupce z Microsoft Store (WindowsApps) a hlídač by se tiše nespustil. Test napodobí Windows (os.name, shutil.which).
Z kořene repozitáře:
  python3 -I tests/brzda/test_hook_windows.py skills/rodokmen
"""
import os, shutil, sys

sys.path.insert(0, os.path.join(os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "skills/rodokmen"), "tools"))
import novy_projekt  # noqa: E402

vysledky = []


def check(nazev, ok, detail=""):
    vysledky.append(bool(ok))
    print(f"[{'OK ' if ok else 'CHYBA'}] {nazev}{'' if ok else '  ' + str(detail)}", flush=True)


puvodni_name, puvodni_which = os.name, shutil.which
try:
    novy_projekt.os.name = "nt"
    for v_path in ("C:/Users/x/AppData/Local/Programs/Python/Python312/python.exe",
                   "C:/Users/x/AppData/Local/Microsoft/WindowsApps/python.exe", None):
        novy_projekt.shutil.which = lambda _n, v=v_path: v
        h = novy_projekt.hook_hlidace()
        check(f"Windows, python v PATH = {v_path}: plná cesta k Pythonu aktualizace",
              h.get("command") == sys.executable and h.get("args", [None])[0] == "-I", h)
finally:
    novy_projekt.os.name, novy_projekt.shutil.which = puvodni_name, puvodni_which

print(f"\n{sum(vysledky)} z {len(vysledky)} správně")
sys.exit(0 if all(vysledky) else 1)
