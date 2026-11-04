#!/usr/bin/env python3
"""Osobní odkazy na rodinný web (vstup bez rodinné otázky, každý člověk má svůj).

  python3 -I tools/pozvanky.py pridej "Teta Jana"        nový odkaz (vypíše se jen jednou)
  python3 -I tools/pozvanky.py seznam                    kdo má odkaz
  python3 -I tools/pozvanky.py prejmenuj p1 "Jana Nováková"
  python3 -I tools/pozvanky.py nova p1                   náhrada ztraceného odkazu, starý přestane platit
  python3 -I tools/pozvanky.py zrus p1                   zrušení odkazu
  (Windows: python -I -X utf8 …)

V data/pozvanky.json je u každého odkazu jen otisk klíče (SHA-256), klíč sám se nikam neukládá.
Adresa odkazu je prihlaseni.adresa z data/web.json. Změny platí na webu až po nasazení (`npm run nasadit`):
export vloží otisky do brány web/netlify/edge-functions/brana.js. Docker/CapRover osobní odkazy neumí.
"""
import datetime, hashlib, json, os, secrets, sys
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

SOUBOR = "pozvanky.json"
DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
NASADIT = "Na webu to začne platit po nasazení: cd web && npm run nasadit"


def otisk(klic):
    return hashlib.sha256(klic.encode()).hexdigest()


def load(data_dir):
    path = os.path.join(data_dir, SOUBOR)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(data_dir, odkazy):
    """Celý soubor naráz přes dočasný soubor: při chybě zápisu zůstane původní."""
    path = os.path.join(data_dir, SOUBOR)
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(odkazy, f, ensure_ascii=False, indent=1)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def adresa(data_dir):
    try:
        with open(os.path.join(data_dir, "web.json"), encoding="utf-8") as f:
            return ((json.load(f).get("prihlaseni") or {}).get("adresa") or "").rstrip("/")
    except (OSError, ValueError, AttributeError):
        return ""


def vypis_odkaz(data_dir, jmeno, klic):
    base = adresa(data_dir)
    print(f"Odkaz pro {jmeno} (uložte si ho, znovu se neukáže):")
    print(f"  {base}/?k={klic}")
    if not base:
        print("POZOR: v data/web.json chybí prihlaseni.adresa (třeba https://<název>.netlify.app), "
              "před /?k= doplňte adresu webu.")


def main(argv, data_dir, today):
    cmd, args = (argv[0], argv[1:]) if argv else ("", [])
    if cmd == "seznam" and not args:
        odkazy = load(data_dir)
        if not odkazy:
            print("Žádné odkazy. Nový: pozvanky.py pridej \"Jméno\"")
        for z in odkazy:
            print(f"{z['id']:>4}  {z['vytvoreno']}  {z['jmeno']}")
        return 0
    if cmd == "pridej" and len(args) == 1 and args[0].strip():
        odkazy = load(data_dir)
        klic = secrets.token_urlsafe(16)   # 128 bitů, 22 znaků
        cisla = [int(z["id"][1:]) for z in odkazy]
        odkazy.append({"id": f"p{max(cisla, default=0) + 1}", "jmeno": args[0].strip(),
                       "otisk": otisk(klic), "vytvoreno": today})
        save(data_dir, odkazy)
        vypis_odkaz(data_dir, args[0].strip(), klic)
        print(NASADIT)
        return 0
    if cmd in ("prejmenuj", "nova", "zrus") and len(args) == (2 if cmd == "prejmenuj" else 1):
        odkazy = load(data_dir)
        z = next((z for z in odkazy if z["id"] == args[0]), None)
        if z is None:
            print(f"CHYBA: odkaz {args[0]} neexistuje (seznam: pozvanky.py seznam)", file=sys.stderr)
            return 1
        if cmd == "prejmenuj":
            if not args[1].strip():
                print("CHYBA: prázdné jméno", file=sys.stderr)
                return 1
            z["jmeno"] = args[1].strip()
            save(data_dir, odkazy)
            print(f"{z['id']} se teď jmenuje {z['jmeno']}.")
        elif cmd == "nova":
            klic = secrets.token_urlsafe(16)
            z["otisk"], z["vytvoreno"] = otisk(klic), today
            save(data_dir, odkazy)
            vypis_odkaz(data_dir, z["jmeno"], klic)
            print("Starý odkaz přestane platit.")
        else:
            odkazy.remove(z)
            save(data_dir, odkazy)
            print(f"Odkaz {z['id']} ({z['jmeno']}) zrušen.")
        print(NASADIT)
        return 0
    print(__doc__, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], DATA, datetime.date.today().isoformat()))
