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


def kontrola(P, SAME=None, zaznamy=(), prepisy=None, ukazka=(), mista=None):
    """Postaví projekt a vrátí výstup kontrola.py; zápisy s klíčem v `ukazka` jsou vymyšlené (jako v ukázce).
    Když kontrola neskončí kódem 0 (chyba v datech, pád), výstup začíná „NÁVRATOVÝ KÓD“ a případ neprojde."""
    tmp = tempfile.mkdtemp(prefix="kontrola_cisla_")
    try:
        zapis(os.path.join(tmp, "data", "osoby.py"), f"P = {P!r}\nSAME = {SAME or {}!r}\n")
        if mista:
            zapis(os.path.join(tmp, "data", "mista.json"), json.dumps(mista, ensure_ascii=False))
        zaz = [dict(klic=k, druh="křest", datum="1900", nazev=k, shrnuti=s, odkaz="https://example.org/snimek",
                    **({"ukazka": True} if k in ukazka else {})) for k, s in zaznamy]
        zapis(os.path.join(tmp, "data", "zaznamy.json"), json.dumps(zaz, ensure_ascii=False))
        zapis(os.path.join(tmp, "data", "prepisy.json"), json.dumps(prepisy or {}, ensure_ascii=False))
        os.makedirs(os.path.join(tmp, "tools"))
        shutil.copy(KONTROLA, os.path.join(tmp, "tools", "kontrola.py"))
        r = subprocess.run(PY + [os.path.join(tmp, "tools", "kontrola.py")], capture_output=True, text=True,
                           encoding="utf-8")
        return (f"NÁVRATOVÝ KÓD {r.returncode}\n" if r.returncode else "") + r.stdout + r.stderr
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def ma(nazev, vystup, text, cekam):
    ok = (text in vystup) == cekam and not vystup.startswith("NÁVRATOVÝ KÓD")
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

# Regrese z revize: datum, věk ani jiné číslo nedokládá číslo domu
PRE_DAT = {"krest_jan_1900": {"orig": "[Datum] 5. 1. 1767\n[Dům] No 34\n[Věk] 23 let", "cs": "Narozen 5. ledna 1767."}}
P = {1: osoba("Jan Novák", "* 5. 1. 1767 Holice čp. 5", "kovář v Holicích čp. 1", "rolník, Holice čp. 23", st="doc",
              r=["krest_jan_1900"])}
out = kontrola(P, zaznamy=ZAZ, prepisy=PRE_DAT)
ma("den v datu nedokládá čp. 5 – upozornění", out, "čp. 5 " + CP, True)
ma("měsíc v datu nedokládá čp. 1 – upozornění", out, "čp. 1 " + CP, True)
ma("věk nedokládá čp. 23 – upozornění", out, "čp. 23 " + CP, True)

# Zápisy čísel domů z reálných přepisů (vymyšlená místa a čísla)
TVARY = ["Rottenschachen No 34", "z Neplachova No 21", "Putim No. 81", "Neplachov čp. 35", "č. 18", "N. 6", "Nro 7",
         "N° 9", "Stožice čís. 10, okres Vodňany", "Erdweiss No. 5 |", "domu 44", "Haus 45", "v domě čp. 112"]
PRE_TV = {"krest_jan_1900": {"orig": "[Datum] 3. 5. 1900\n" + "\n".join(f"[Svědek] Josef Malý, {t}" for t in TVARY)
                             + "\n[Dům] Neplachov 46\n[Haus] 47\n[Číslo domu nevěsty] 48 | kath. | 24",
                             "cs": ""}}
CISLA = [34, 21, 81, 35, 18, 6, 7, 9, 10, 5, 44, 45, 112, 46, 47, 48]
P = {1: osoba("Jan Novák", *[f"Holice čp. {c}" for c in CISLA], st="doc", r=["krest_jan_1900"])}
out = kontrola(P, zaznamy=ZAZ, prepisy=PRE_TV)
for c in CISLA:
    ma(f"tvar čísla domu {c} z přepisu se uzná", out, f"čp. {c} " + CP, False)

# Číslo hned za obcí z mista.json („z Holic 23“, „Holice 24;“), ale ne datum ani rok za obcí
MISTA = {"Holice": {"lat": 50.0, "lon": 16.0, "re": "Holic"}}
PRE_OB = {"krest_jan_1900": {"orig": "Holice 24; 26; ledig | Holice 5. 1. 1767 | Holice 1767",
                             "cs": "Jan Novák, sedlák z Holic 23, 55 let."}}
P = {1: osoba("Jan Novák", "* Holice čp. 23", "Holice čp. 24", "Holice čp. 5", "Holice čp. 176", st="doc",
              r=["krest_jan_1900"])}
out = kontrola(P, zaznamy=ZAZ, prepisy=PRE_OB, mista=MISTA)
ma("„z Holic 23“ dokládá čp. 23", out, "čp. 23 " + CP, False)
ma("„Holice 24;“ dokládá čp. 24", out, "čp. 24 " + CP, False)
ma("„Holice 5. 1. 1767“ nedokládá čp. 5 – upozornění", out, "čp. 5 " + CP, True)
ma("„Holice 1767“ nedokládá čp. 176 – upozornění", out, "čp. 176 " + CP, True)

# Neznámý rodič („otec neuveden“, „?“) není partner, kterého by sňatek měl jmenovat
for nezn in ("otec neuveden", "?"):
    P = {1: osoba("Petr Novák"), 2: osoba(nezn, st="unk"), 3: osoba("Anna Malá", "× 1900 Holice Josef Hrubý")}
    ma(f"partner „{nezn}“ – bez upozornění", kontrola(P), PARTNER, False)

# SAME: zápis citovaný u aliasu dokládá číslo domu hlavní osoby (a naopak)
P = {1: osoba("Petr Novák"), 2: osoba("Jan Novák"), 3: osoba("Marie Králová"),
     4: osoba("Josef Novák", "* 1880 Holice čp. 34", st="doc", r=["r1"]), 6: osoba("Karel Král"),
     7: osoba("Ludmila Malá"), 12: osoba("Josef Novák", "TÁŽ OSOBA jako 4", "rolník, Holice čp. 35", st="doc", r=["r2"])}
out = kontrola(P, SAME={12: 4}, zaznamy=[("r1", "Křest Josefa Nováka, Holice čp. 35"), ("r2", "Sňatek")],
               prepisy={"r2": {"orig": "[Dům] No 34", "cs": ""}})
ma("SAME – čp. doložené zápisem aliasu – bez upozornění", out, "čp. 34 " + CP, False)
ma("SAME – čp. aliasu doložené zápisem hlavní osoby – bez upozornění", out, "čp. 35 " + CP, False)

# Místo sňatku se jménem partnera nepočítá (Holice × Holický)
MISTA = {"Holice": {"lat": 50.0, "lon": 16.0, "re": "Holic"}}
P = {1: osoba("Petr Novák"), 2: osoba("Jan Holický", "× 1950 Holice Marie Králová"),
     3: osoba("Anna Malá", "× 1950 Holice Karel Hrubý")}
ma("místo sňatku (Holice) neznamená partnera Holického – upozornění", kontrola(P, mista=MISTA),
   "osoba 3 (Anna Malá): žádný sňatek (×) nejmenuje partnera 2", True)

# Regrese z 2. revize
# Výraz obce s vlastním příznakem nebo skupinou: kontrola nespadne a číslo za obcí najde
for vyraz, obec in (("(?i)Holic", "z holic 23"), ("(Holic|Holitz)", "z Holitz 23")):
    P = {1: osoba("Jan Novák", "* Holice čp. 23", "× 1920 Holice Marie Králová", st="doc", r=["krest_jan_1900"]),
         2: osoba("Karel Novák"), 3: osoba("Marie Králová", "× 1920 Holice Karel Novák")}
    out = kontrola(P, zaznamy=ZAZ, prepisy={"krest_jan_1900": {"orig": obec, "cs": ""}},
                   mista={"Holice": {"lat": 50.0, "lon": 16.0, "re": vyraz}})
    ma(f"výraz obce {vyraz} – kontrola doběhne a „{obec}“ dokládá čp. 23", out, "čp. 23 " + CP, False)

# Datum se jménem měsíce není číslo domu
for datum in ("v Holicích 23. února 1890", "Holic No 23. Februar 1890", "Holice 23. Januarii 1767", "Holice 23. 9bris"):
    P = {1: osoba("Jan Novák", "* Holice čp. 23", st="doc", r=["krest_jan_1900"])}
    out = kontrola(P, zaznamy=ZAZ, prepisy={"krest_jan_1900": {"orig": "", "cs": f"Jan se narodil {datum}."}},
                   mista=MISTA)
    ma(f"„{datum}“ nedokládá čp. 23 – upozornění", out, "čp. 23 " + CP, True)

# Přepis a překlad se čtou zvlášť: pole [Dům] na konci přepisu nepokračuje do překladu
P = {1: osoba("Jan Novák", "* Holice čp. 23", "Holice čp. 34", st="doc", r=["krest_jan_1900"])}
out = kontrola(P, zaznamy=ZAZ, prepisy={"krest_jan_1900": {"orig": "[Datum] 1900\n[Dům] 34",
                                                           "cs": "Jan zemřel ve věku 23 let."}})
ma("věk v překladu za polem [Dům] nedokládá čp. 23 – upozornění", out, "čp. 23 " + CP, True)
ma("pole [Dům] na konci přepisu dokládá čp. 34", out, "čp. 34 " + CP, False)

# Obec se z faktu sňatku odstraní jen na začátku (za datem), ne ze jména partnera
P = {1: osoba("Petr Novák"), 2: osoba("Jan Holický", "× 1900 Holice Anna Malá"),
     3: osoba("Anna Malá", "× 1900 Holice Johann Holický")}
ma("„× 1900 Holice Johann Holický“ jmenuje Jana Holického – bez upozornění", kontrola(P, mista=MISTA), PARTNER, False)

# Obec bez souřadnic se v textu pozná taky
BEZ_LAT = {"Holice": {"re": "Holic"}}
P = {1: osoba("Jan Novák", "* Holice čp. 23", st="doc", r=["krest_jan_1900"])}
out = kontrola(P, zaznamy=ZAZ, prepisy={"krest_jan_1900": {"orig": "", "cs": "rolník z Holic 23"}}, mista=BEZ_LAT)
ma("obec bez souřadnic – „z Holic 23“ dokládá čp. 23", out, "čp. 23 " + CP, False)
P = {1: osoba("Petr Novák"), 2: osoba("Jan Holický", "× 1950 Holice Marie Králová"),
     3: osoba("Anna Malá", "× 1950 Holice Karel Hrubý")}
ma("obec bez souřadnic – Holice neznamená partnera Holického – upozornění", kontrola(P, mista=BEZ_LAT),
   "osoba 3 (Anna Malá): žádný sňatek (×) nejmenuje partnera 2", True)

# Číslo zápisu, strany nebo snímku není číslo domu
for cislo in ("zápis č. 23", "str. č. 23", "snímek č. 23", "fol. No 23"):
    P = {1: osoba("Jan Novák", "* Holice čp. 23", st="doc", r=["krest_jan_1900"])}
    out = kontrola(P, zaznamy=[("krest_jan_1900", f"Křest Jana Nováka, {cislo}")])
    ma(f"„{cislo}“ nedokládá čp. 23 – upozornění", out, "čp. 23 " + CP, True)

print(f"\n{sum(VYSLEDKY)} z {len(VYSLEDKY)} v pořádku")
sys.exit(0 if all(VYSLEDKY) else 1)
