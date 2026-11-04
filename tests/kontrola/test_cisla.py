"""Test kontroly partnerů na sousedním Kekulého čísle a čísel domů proti přepisům v tools/kontrola.py.

Z kořene repozitáře, testovaná kontrola je argument:
  python3 -I tests/kontrola/test_cisla.py skills/rodokmen/tools/kontrola.py
  (Windows: python -I -X utf8 …)
Každý případ si postaví vlastní dočasný projekt (data/osoby.py, zaznamy.json, prepisy.json) s vymyšlenou rodinou,
zkopíruje do něj kontrola.py a pustí ji. Nic nestahuje, jen standardní knihovna.
"""
import json, os, shutil, subprocess, sys, tempfile

KONTROLA = os.path.abspath(sys.argv[1])
PY = [sys.executable, "-I", "-X", "utf8"]
VYSLEDKY = []


def zapis(cesta, text):
    os.makedirs(os.path.dirname(cesta), exist_ok=True)
    with open(cesta, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def kontrola(P, SAME=None, zaznamy=(), prepisy=None, ukazka=()):
    """Postaví projekt a vrátí výstup kontrola.py; zápisy s klíčem v `ukazka` jsou vymyšlené (jako v ukázce)."""
    tmp = tempfile.mkdtemp(prefix="kontrola_cisla_")
    try:
        zapis(os.path.join(tmp, "data", "osoby.py"), f"P = {P!r}\nSAME = {SAME or {}!r}\n")
        zaz = [dict(klic=k, druh="křest", datum="1900", nazev=k, shrnuti=s, odkaz="https://example.org/snimek",
                    **({"ukazka": True} if k in ukazka else {})) for k, s in zaznamy]
        zapis(os.path.join(tmp, "data", "zaznamy.json"), json.dumps(zaz, ensure_ascii=False))
        zapis(os.path.join(tmp, "data", "prepisy.json"), json.dumps(prepisy or {}, ensure_ascii=False))
        os.makedirs(os.path.join(tmp, "tools"))
        shutil.copy(KONTROLA, os.path.join(tmp, "tools", "kontrola.py"))
        r = subprocess.run(PY + [os.path.join(tmp, "tools", "kontrola.py")], capture_output=True, text=True,
                           encoding="utf-8")
        return r.stdout + r.stderr
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def ma(nazev, vystup, text, cekam):
    ok = (text in vystup) == cekam
    VYSLEDKY.append(ok)
    print(("OK  " if ok else "CHYBA ") + nazev)
    if not ok:
        print(f"    {'čekal jsem' if cekam else 'nečekal jsem'} „{text}“ ve výstupu:\n    "
              + vystup.replace("\n", "\n    "))


def osoba(n, *f, **kw):
    return dict(n=n, y="", st=kw.pop("st", "fam"), f=list(f), **kw)


PARTNER = "nejmenuje partnera"
ZAKLAD = {1: osoba("Petr Novák"), 2: osoba("Jan Novák", "× 1950 Holice Marie Králová"),
          3: osoba("Marie Králová", "× 1950 Holice Jan Novák")}

# 1. Partner je ve faktu ×
ma("partner jmenovaný ve sňatku – bez upozornění", kontrola(ZAKLAD), PARTNER, False)

# 2. Sňatek patří někomu jinému (druhý sňatek vdovce přilepený k manželce)
P = dict(ZAKLAD)
P[3] = osoba("Marie Králová", "× 1955 Holice Anna Hrubá")
out = kontrola(P)
ma("sňatek nejmenuje partnera – upozornění", out, "osoba 3 (Marie Králová): žádný sňatek (×) nejmenuje partnera 2",
   True)
ma("u partnera se správným sňatkem bez upozornění", out, "osoba 2 (Jan Novák): žádný sňatek", False)

# 3. Vdovec: druhý sňatek s jinou ženou a sňatek s partnerkou
P = dict(ZAKLAD)
P[2] = osoba("Jan Novák", "× 1950 Holice Marie Králová", "× 1960 Holice Anna Hrubá")
ma("druhý sňatek vedle správného – bez upozornění", kontrola(P), PARTNER, False)

# 4. Diakritika a velikost písmen, datum a místo před jménem
P = dict(ZAKLAD)
P[2] = osoba("Jan Novák", "× 2. 2. 1950 Unserfrau MARIE KRALOVA")
ma("jméno bez diakritiky velkými písmeny – bez upozornění", kontrola(P), PARTNER, False)

# 5. Partner chybí – neznámý partner je běžný
P = {1: osoba("Petr Novák"), 2: osoba("Jan Novák", "× 1950 Holice Anna Hrubá")}
ma("partner v datech není – bez upozornění", kontrola(P), PARTNER, False)

# 6. SAME: předek je ve stromu dvakrát, partner je u druhého čísla
P = {1: osoba("Petr Novák"), 2: osoba("Jan Novák"), 3: osoba("Marie Králová"),
     4: osoba("Josef Novák", "× 1920 Holice Anna Malá"), 6: osoba("Karel Král"), 7: osoba("Ludmila Malá"),
     12: osoba("Josef Novák", "TÁŽ OSOBA jako 4"), 13: osoba("Anna Malá", "× 1920 Holice Josef Novák")}
ma("SAME – partner pod druhým číslem jmenovaný – bez upozornění", kontrola(P, SAME={12: 4}), PARTNER, False)
P[4] = osoba("Josef Novák", "× 1920 Holice Rozálie Hrubá")
out = kontrola(P, SAME={12: 4})
ma("SAME – partner pod druhým číslem nejmenovaný – upozornění", out,
   "osoba 4 (Josef Novák): žádný sňatek (×) nejmenuje partnera 13", True)
P[4] = osoba("Josef Novák", "× 1920 Holice Anna Malá")
P[13] = osoba("Anna Malá", "× 1920 Holice Karel Hrubý")
ma("SAME – alias se převede na hlavní osobu – upozornění u 13", kontrola(P, SAME={12: 4}),
   "osoba 13 (Anna Malá): žádný sňatek (×) nejmenuje partnera 4", True)

# Čísla domů
CP = "není v žádném citovaném zápisu"
ZAZ = [("krest_jan_1900", "Křest Jana Nováka v Holicích")]
PRE = {"krest_jan_1900": {"orig": "[Datum] 3. 5. 1900\n[Dům] No 34\n[Jméno] Jan", "cs": "Jan se narodil v Holicích."}}
P = {1: osoba("Jan Novák", "* 3. 5. 1900 Holice čp. 34", st="doc", r=["krest_jan_1900"])}
ma("čp. v přepisu jako „No 34“ – bez upozornění", kontrola(P, zaznamy=ZAZ, prepisy=PRE), CP, False)

P = {1: osoba("Jan Novák", "* 3. 5. 1900 Holice čp. 36", "rolník v Holicích čp. 134", st="doc", r=["krest_jan_1900"])}
out = kontrola(P, zaznamy=ZAZ, prepisy=PRE)
ma("čp. chybí v zápisech – upozornění", out, "osoba 1 (Jan Novák): čp. 36 není v žádném citovaném zápisu", True)
ma("čp. 134 neodpovídá „34“ (hranice čísla) – upozornění", out, "čp. 134 " + CP, True)

ZAZ2 = [("krest_jan_1900", "Křest Jana Nováka, Holice čp. 36")]
P = {1: osoba("Jan Novák", "* 3. 5. 1900 Holice čp. 36", st="doc", r=["krest_jan_1900"])}
ma("čp. v shrnutí zápisu – bez upozornění", kontrola(P, zaznamy=ZAZ2, prepisy=PRE), CP, False)

P = {1: osoba("Jan Novák", "* 3. 5. 1900 Holice čp. 36", st="doc")}
ma("osoba bez 'r' – bez upozornění", kontrola(P, zaznamy=ZAZ, prepisy=PRE), CP, False)

P = {1: osoba("Jan Novák", "* 3. 5. 1900 Holice čp. 36", st="doc", r=["krest_jan_1900"])}
ma("cituje jen vymyšlený zápis ukázky – bez upozornění", kontrola(P, zaznamy=ZAZ, ukazka={"krest_jan_1900"}), CP,
   False)
P = {1: osoba("Jan Novák", "* 3. 5. 1900 Holice čp. 36", "rolník, Holice čp. 41", st="doc",
              r=["krest_jan_1900", "snatek_jan_1925"])}
out = kontrola(P, zaznamy=ZAZ + [("snatek_jan_1925", "Ženich Jan Novák (Holice čp. 41)")], ukazka={"snatek_jan_1925"})
ma("skutečný i vymyšlený zápis – čp. ze shrnutí ukázky platí", out, "čp. 41 " + CP, False)
ma("skutečný i vymyšlený zápis – chybějící čp. hlásí", out, "čp. 36 " + CP, True)

P = {1: osoba("Jan Novák", "* 3. 5. 1900 Holice čp. 34", st="doc", r=["krest_jan_1900"],
              note="Sousedé Hrubí z čp. 99.")}
ma("čp. jen v poznámce – bez upozornění", kontrola(P, zaznamy=ZAZ, prepisy=PRE), CP, False)

P = {1: osoba("Jan Novák", "* 3. 5. 1900 Holice čp. 36 (podle stromu)", "rolník, Holice čp. 41 (z vyprávění)",
              "† Holice čp. 52 (mlýn)", st="doc", r=["krest_jan_1900"])}
out = kontrola(P, zaznamy=ZAZ, prepisy=PRE)
ma("čp. se zdrojem „(podle stromu)“ – bez upozornění", out, "čp. 36 " + CP, False)
ma("čp. se zdrojem „(z vyprávění)“ – bez upozornění", out, "čp. 41 " + CP, False)
ma("jiná závorka („(mlýn)“) zdroj neoznačuje – upozornění", out, "čp. 52 " + CP, True)

P = {1: osoba("Jan Novák", "* 3. 5. 1900 Holice čp. 36", r=["krest_jan_1900"])}
ma("osoba není 'doc' – bez upozornění", kontrola(P, zaznamy=ZAZ, prepisy=PRE), CP, False)

print(f"\n{sum(VYSLEDKY)} z {len(VYSLEDKY)} v pořádku")
sys.exit(0 if all(VYSLEDKY) else 1)
