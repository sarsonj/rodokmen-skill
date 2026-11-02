#!/usr/bin/env python3
"""Sdílená cache stažených snímků matrik – každý celý snímek se z archivu stáhne jen jednou.

Příště ho nástroj vezme z disku bez dotazu na archiv (méně zátěže archivu, menší riziko zablokování, rychlejší
práce). Cache je společná pro všechny projekty na počítači: ~/.cache/rodokmen_snimky/ (Windows
%LOCALAPPDATA%\\rodokmen_snimky), jinou složku nastavíš proměnnou RODOKMEN_SNIMKY.
Používají ji aron_img.py, ebadatelna.py, trebon.py, portafontium.py, soal_zoomify.py a ahmp_scan.py.
Výřezy (x0,y0,x1,y1) se stahují vždy znovu, jsou malé. Vadný snímek v cache smaž a stáhni znovu (cesta se vypíše).
Celou cache lze kdykoli smazat, nástroje si snímky stáhnou znovu.
"""
import os, shutil

KOREN = os.environ.get("RODOKMEN_SNIMKY") or os.path.join(
    os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".cache"), "rodokmen_snimky")


def cesta(klic):
    """Soubor v cache; klíč je relativní cesta s „/“, např. „aron/<apu>/sn0012-u1.jpg“."""
    return os.path.join(KOREN, *klic.split("/"))


def uloz(klic, data):
    """Atomicky zapíše bajty do cache (souběžné stahování téhož snímku si nepřekáží)."""
    p = cesta(klic)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = f"{p}.{os.getpid()}.tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, p)
    return p


def soubor(klic, out, stahni):
    """Snímek z cache, nebo ho stáhne funkcí stahni(cil) a uloží. Pak ho zkopíruje do out. Vrátí True při zásahu cache."""
    p = cesta(klic)
    zasah = os.path.exists(p)
    if zasah:
        print("z cache, bez stahování:", p)
    else:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        root, ext = os.path.splitext(p)
        tmp = f"{root}.{os.getpid()}.tmp{ext}"   # přípona zůstává – podle ní ImageMagick volí formát
        try:
            stahni(tmp)
            os.replace(tmp, p)
        finally:
            if os.path.exists(tmp):   # nedokončené stažení do cache nepatří (i při sys.exit)
                os.remove(tmp)
    if out and os.path.abspath(out) != os.path.abspath(p):
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        shutil.copyfile(p, out)
    return zasah


if __name__ == "__main__":   # samokontrola bez sítě: python3 -I tools/cache.py
    import sys, tempfile
    with tempfile.TemporaryDirectory() as d:
        KOREN = os.path.join(d, "cache")
        volani = []

        def stahni(cil):
            volani.append(cil)
            open(cil, "wb").write(b"snimek")

        def spadne(cil):
            open(cil, "wb").write(b"pul")
            sys.exit("portál neodpovídá")
        out = os.path.join(d, "pracovni", "a.jpg")
        assert soubor("x/kniha/sn0001-u0.jpg", out, stahni) is False
        assert soubor("x/kniha/sn0001-u0.jpg", out, stahni) is True and len(volani) == 1
        assert open(out, "rb").read() == b"snimek"
        try:
            soubor("x/kniha/sn0002-u0.jpg", None, spadne)
        except SystemExit:
            pass
        assert os.listdir(os.path.dirname(cesta("x/kniha/sn0002-u0.jpg"))) == ["sn0001-u0.jpg"]
    print("cache.py: samokontrola OK")
