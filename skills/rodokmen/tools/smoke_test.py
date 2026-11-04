#!/usr/bin/env python3
"""Rychlá kontrola, že síťové nástroje a portály pořád fungují (spouští se ručně, třeba jednou za čas nebo když nástroj selže).

Použití (z kořene projektu):
  smoke_test.py                  -> vyzkouší všechny nástroje jedním bezpečným dotazem (hledání, žádné stahování snímků)
  smoke_test.py aron kramerius   -> jen vybrané (názvy viz `--seznam`)
  smoke_test.py --seznam         -> vypíše názvy a dotazy bez spuštění
Výstup: OK | CHYBA | NEDOSTUPNÉ | ZASTAVENO | PŘESKOČENO.
  CHYBA      portál odpověděl, ale nástroj nenašel očekávaný obsah – portál se nejspíš změnil, nástroj i návod v `portaly.md` je třeba opravit
  NEDOSTUPNÉ portál neodpovídá (síť, výpadek, blokace) – nepovažuje se za chybu nástroje
  ZASTAVENO  brzda `slusne.py` web zastavila (archiv dal najevo, že ho zatěžujeme); nic se neopakuje, řeš `slusne.py stav`
  PŘESKOČENO nástroj v této verzi skillu není, chybí bash, nebo nástroj čeká na souhlas uživatele s podmínkami portálu
Návratový kód je 1 jen při CHYBĚ. Test jde stejnými cestami jako nástroje (brzda: 1 dotaz za 2 s, ARON a ZA Opava pomaleji),
mezi nástroji jsou pauzy. Souhlas s podmínkami portálů nepotvrzuje a nic za uživatele nezapisuje.
"""
import os, shutil, subprocess, sys, time
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
PY = [sys.executable, "-I", "-X", "utf8"]

# (název, [nástroj, argumenty…], očekávaný text ve výstupu, volitelné: jakákoli chyba nástroje se bere jako NEDOSTUPNÉ)
TESTY = [
    ("aron", ["aron_search.py", "Holice"], "count", False),
    ("portafontium", ["portafontium.py", "fara", "Dolní Bělá"], "dolni-bela", False),
    ("ahmp", ["@bash", "ahmp_search.sh", "Smíchov"], "Smíchov", False),
    ("prihlasky", ["policie_prihlasky.py", "Novak", "Jan"], "záznamů", False),
    ("kramerius", ["kramerius.py", 'text_ocr:"Jan Novák" AND datum_begin:[1900 TO 1905]', "3"], "found", False),
    ("anno", ["anno.py", '"Johann Nowak"', "1880", "1890", "1"], "", True),
    ("brno", ["brno_encyklopedie.py", "hledat", "Bakala dirigent"], "Bakala", False),
    ("mauthausen", ["mauthausen.py", "hledat", "Novak", "--stran", "1"], "Novak", False),
    ("obeti", ["obeti.py", "hledat", "--prijmeni", "Neumannová", "--jmeno", "Anna", "--stran", "1"], "Neumann", False),
    ("arolsen", ["arolsen.py", "hledat", "Novák Josef 1905", "--max", "3"], "|", False),
]
SIT = ("urlopen error", "timed out", "Connection", "connection", "Name or service", "Temporary failure", "CERTIFICATE", "HTTP Error 403",
       "HTTP Error 5", "HTTP Error 429", "Max retries", "remote end closed", "RemoteDisconnected", "Errno 104", "Errno 111", "gaierror",
       "Server Exception", "blokac")


def vyhodnot(kod, vystup, chyby, ocek, volitelne, dt="0 s"):
    """(stav, popis) podle návratového kódu a výstupu nástroje. Kód 3 = brzda zastavila web, kód 4 = chybí souhlas uživatele."""
    posledni = ((vystup or "") + "\n" + (chyby or "")).strip().splitlines()
    posledni = (posledni or ["bez výstupu"])[-1][:140]
    if kod == 3:
        return "ZASTAVENO", posledni
    if kod == 4:
        return "PŘESKOČENO", "čeká na souhlas uživatele s podmínkami portálu (viz `souhlas` u nástroje)"
    if kod == 0 and ocek in (vystup or ""):
        return "OK", dt
    if any(s in (vystup or "") + (chyby or "") for s in SIT) or volitelne:
        return "NEDOSTUPNÉ", posledni
    return "CHYBA", f"{dt}; očekáváno „{ocek}“; poslední řádek: {posledni}"


def spust(prikaz, ocek, volitelne):
    if prikaz[0] == "@bash":
        if not shutil.which("bash"):
            return "PŘESKOČENO", "bash není k dispozici"
        skript, cmd = prikaz[1], ["bash", os.path.join(HERE, prikaz[1]), *prikaz[2:]]
    else:
        skript, cmd = prikaz[0], [*PY, os.path.join(HERE, prikaz[0]), *prikaz[1:]]
    if not os.path.exists(os.path.join(HERE, skript)):
        return "PŘESKOČENO", f"nástroj {skript} v této verzi skillu není"
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=150, cwd=os.path.dirname(HERE))
    except subprocess.TimeoutExpired:
        return "NEDOSTUPNÉ", "časový limit 150 s"
    return vyhodnot(r.returncode, r.stdout, r.stderr, ocek, volitelne, f"{time.time() - t0:.0f} s")


def main():
    a = sys.argv[1:]
    if "--seznam" in a:
        for n, p, o, v in TESTY:
            print(f"{n:14} {' '.join(p)[:100]}")
        return 0
    nezname = [x for x in a if x not in {t[0] for t in TESTY}]
    if nezname:
        sys.exit("Neznámé nástroje: " + ", ".join(nezname) + " (viz --seznam)")
    vyber = [t for t in TESTY if not a or t[0] in a]
    chyby = 0
    for i, (n, p, o, v) in enumerate(vyber):
        stav, popis = spust(p, o, v)
        chyby += stav == "CHYBA"
        print(f"{stav:11} {n:14} {popis}", flush=True)
        if i < len(vyber) - 1 and stav not in ("PŘESKOČENO", "ZASTAVENO"):
            time.sleep(1.5)   # pauza mezi portály
    print(f"\nHotovo: {len(vyber)} nástrojů, chyb {chyby}.")
    return 1 if chyby else 0


if __name__ == "__main__":
    sys.exit(main())
