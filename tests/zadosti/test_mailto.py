"""Testy nástroje skills/rodokmen/tools/mailto.py: koncept žádosti (.md) -> odkazy, které otevřou hotový e-mail.

Nástroj se spouští jako podproces na dočasném konceptu se dvěma bloky (odrážky s pokračovacími řádky, diakritika,
dva adresáti oddělení čárkou, kopie). Kontroluje, že se odkazy dekódují zpět na správného adresáta, předmět a text,
že tělo odkazu mailto: má konce řádků CRLF, že druhé spuštění oddíl s odkazy nahradí (nepřidá další), varování
u dlouhého odkazu mailto: a odkazy do Gmailu, Outlooku a Seznam Emailu s volbami --gmail, --outlook a --seznam. Nic nestahuje, jen standardní
knihovna.

Z kořene repozitáře:
  python3 -I tests/zadosti/test_mailto.py
Na Windows `python -I -X utf8 tests/zadosti/test_mailto.py`.
"""
import os, subprocess, sys, tempfile, urllib.parse

KOREN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NASTROJ = os.path.join(KOREN, "skills", "rodokmen", "tools", "mailto.py")
NADPIS = "## Odkazy k odeslání"

ODSTAVEC = "Prosím o vyhledání zápisu v pozemkové knize pro čp. 12 v obci Lhota a o sdělení ceny rešerše."
KONCEPT = (
    "# Koncepty žádostí\n\nPoznámka nad bloky se nezpracuje.\n\n---\n\n"
    "## Matriční úřad Horní Lhota – úmrtí Jana Nováka\n\n"
    "**Komu:** matrika@hornilhota.cz, podatelna@hornilhota.cz\n"
    "**Kopie:** ja@example.cz\n"
    "**Předmět:** Žádost o kopii zápisu o úmrtí (Jan Novák, †1962)\n\n"
    "Dobrý den,\n\n"
    "prosím o kopii zápisu o úmrtí:\n"
    "- Jan Novák, zemřel 3. 4. 1962 v Horní Lhotě,\n"
    "  bydliště čp. 5\n"
    "- otec Josef Novák\n\n"
    "Děkuji, Žofie Nováková\n"
    "\n---\n\n"
    "## Archiv – rešerše\n\n"
    "**Komu:** badatelna@archiv.example.cz\n"
    "**Předmět:** Rešerše – pozemková kniha čp. 12\n\n"
    "Dobrý den,\n\n" + (ODSTAVEC + "\n\n") * 20 + "S pozdravem\n"
)
TELO1 = ("Dobrý den,\n\nprosím o kopii zápisu o úmrtí:\n- Jan Novák, zemřel 3. 4. 1962 v Horní Lhotě, bydliště čp. 5\n"
         "- otec Josef Novák\n\nDěkuji, Žofie Nováková")
TELO2 = "Dobrý den,\n\n" + (ODSTAVEC + "\n\n") * 20 + "S pozdravem"

vysledky = []


def ok(nazev, podminka, detail=""):
    vysledky.append(bool(podminka))
    print(("OK    " if podminka else "CHYBA ") + nazev + ("" if podminka else f"  ({detail})"))


def spust(cesta, *volby):
    r = subprocess.run([sys.executable, "-I", NASTROJ, cesta, *volby], capture_output=True)
    return r.returncode, r.stdout.decode("utf-8"), r.stderr.decode("utf-8")


def odkazy(text, zacatek):
    """Všechny odkazy (http… nebo mailto:…) v oddílu s odkazy, které začínají daným prefixem, v pořadí."""
    oddil = text.split(NADPIS, 1)[1] if NADPIS in text else ""
    return [c.split(")", 1)[0] for c in oddil.split("](")[1:] if c.startswith(zacatek)]


def mailto(odkaz):
    adresa, dotaz = odkaz[len("mailto:"):].split("?", 1)
    return urllib.parse.unquote(adresa), urllib.parse.parse_qs(dotaz)


slozka = tempfile.mkdtemp(prefix="test_mailto_")
cesta = os.path.join(slozka, "koncept.md")
with open(cesta, "w", encoding="utf-8", newline="\n") as f:
    f.write(KONCEPT)

kod, out, err = spust(cesta)
ok("nástroj doběhl", kod == 0, err)
text = open(cesta, encoding="utf-8", newline="").read()
ok("koncept zůstal nad oddílem s odkazy", text.startswith(KONCEPT.rstrip() + "\n"))
ok("oddíl s odkazy je jednou", text.count(NADPIS) == 1, text.count(NADPIS))
ok("soubor má konce řádků LF", "\r\n" not in text)
m = odkazy(text, "mailto:")
ok("dva odkazy mailto:", len(m) == 2, m)
ok("bez --gmail žádný Gmail", "mail.google.com" not in text)
if len(m) == 2:
    komu, q = mailto(m[0])
    ok("dva adresáti", komu == "matrika@hornilhota.cz,podatelna@hornilhota.cz", komu)
    ok("kopie", q.get("cc") == ["ja@example.cz"], q.get("cc"))
    ok("předmět s diakritikou", q.get("subject") == ["Žádost o kopii zápisu o úmrtí (Jan Novák, †1962)"], q.get("subject"))
    telo = q.get("body", [""])[0]
    ok("tělo mailto: s CRLF", "%0D%0A" in m[0] and "\n" not in telo.replace("\r\n", ""), m[0][:200])
    ok("tělo: pokračovací řádek připojen k odrážce", telo == TELO1.replace("\n", "\r\n"), repr(telo))
    komu2, q2 = mailto(m[1])
    ok("druhý blok: adresát a předmět", komu2 == "badatelna@archiv.example.cz"
       and q2.get("subject") == ["Rešerše – pozemková kniha čp. 12"], (komu2, q2.get("subject")))
    ok("druhý blok: tělo", q2.get("body", [""])[0] == TELO2.replace("\n", "\r\n"))
    ok("výpis obsahuje odkazy", m[0] in out and m[1] in out)
    ok("výpis uvádí délku odkazů", f"{len(m[0])} znaků" in out and f"{len(m[1])} znaků" in out, out[-500:])
    ok("druhý odkaz je dlouhý (předpoklad testu)", len(m[1]) > 1800 > len(m[0]), (len(m[0]), len(m[1])))
    varovani = [r for r in (out + err).splitlines() if r.startswith("POZOR")]
    ok("varování jen u dlouhého odkazu", len(varovani) == 1 and "Archiv – rešerše" in varovani[0], varovani)

kod, out, err = spust(cesta, "--gmail", "--outlook")
ok("druhé spuštění doběhlo", kod == 0, err)
text = open(cesta, encoding="utf-8", newline="").read()
ok("po druhém spuštění oddíl s odkazy jednou", text.count(NADPIS) == 1, text.count(NADPIS))
ok("koncept nad oddílem beze změny", text.startswith(KONCEPT.rstrip() + "\n"))
ok("po druhém spuštění zase dva odkazy mailto:", len(odkazy(text, "mailto:")) == 2)
g = odkazy(text, "https://mail.google.com/")
ok("dva odkazy do Gmailu", len(g) == 2, g)
if g:
    zaklad, dotaz = g[0].split("?", 1)
    q = urllib.parse.parse_qs(dotaz)
    ok("Gmail: tvar odkazu", zaklad == "https://mail.google.com/mail/" and q.get("view") == ["cm"]
       and q.get("fs") == ["1"], g[0][:120])
    ok("Gmail: adresát, kopie, předmět", q.get("to") == ["matrika@hornilhota.cz,podatelna@hornilhota.cz"]
       and q.get("cc") == ["ja@example.cz"]
       and q.get("su") == ["Žádost o kopii zápisu o úmrtí (Jan Novák, †1962)"], q)
    ok("Gmail: tělo", q.get("body") == [TELO1], q.get("body"))
o = odkazy(text, "https://outlook.office.com/")
ok("dva odkazy do Outlooku", len(o) == 2, o)
if o:
    zaklad, dotaz = o[1].split("?", 1)
    q = urllib.parse.parse_qs(dotaz)
    ok("Outlook: tvar a obsah", zaklad == "https://outlook.office.com/mail/deeplink/compose"
       and q.get("to") == ["badatelna@archiv.example.cz"] and q.get("subject") == ["Rešerše – pozemková kniha čp. 12"]
       and q.get("body") == [TELO2], o[1][:160])

kod, out, err = spust(cesta, "--seznam")
text = open(cesta, encoding="utf-8", newline="").read()
s = odkazy(text, "https://email.seznam.cz/")
ok("--seznam: dva odkazy do Seznam Emailu", kod == 0 and len(s) == 2, (err, s))
if s:
    zaklad, dotaz = s[0].split("?", 1)
    q = urllib.parse.parse_qs(dotaz)
    vnitrni = q.get("mailto", [""])[0]
    ok("Seznam: tvar odkazu (newMessageScreen?mailto=<celý odkaz mailto:>)",
       zaklad == "https://email.seznam.cz/newMessageScreen" and vnitrni == odkazy(text, "mailto:")[0], s[0][:160])
    komu, q2 = mailto(vnitrni) if vnitrni.startswith("mailto:") else ("", {})
    ok("Seznam: adresát, předmět, tělo", komu == "matrika@hornilhota.cz,podatelna@hornilhota.cz"
       and q2.get("subject") == ["Žádost o kopii zápisu o úmrtí (Jan Novák, †1962)"]
       and q2.get("body") == [TELO1.replace("\n", "\r\n")], vnitrni[:160])

kod, out, err = spust(cesta)
text = open(cesta, encoding="utf-8", newline="").read()
ok("třetí spuštění bez voleb: Gmail zmizel", kod == 0 and text.count(NADPIS) == 1 and "mail.google.com" not in text)

# Žádost a poznámka připsané až za oddíl s odkazy: další spuštění je nesmí smazat a nová žádost dostane odkaz.
NOVA = ("\n---\n\n## Obec Horní Lhota – hroby\n\n**Komu:** obec@hornilhota.cz\n**Předmět:** Evidence hrobů\n\n"
        "Dobrý den, prosím o údaje z evidence hrobů.\n\nPoznámka pod čarou: poslat až po odpovědi matriky.\n")
with open(cesta, "a", encoding="utf-8", newline="\n") as f:
    f.write(NOVA)
kod, out, err = spust(cesta)
text = open(cesta, encoding="utf-8", newline="").read()
ok("žádost za oddílem s odkazy zůstala", kod == 0 and NOVA.strip() in text, (err, text[-400:]))
ok("oddíl s odkazy pořád jednou", text.count(NADPIS) == 1, text.count(NADPIS))
m = odkazy(text, "mailto:")
ok("žádost za oddílem dostala odkaz", len(m) == 3 and mailto(m[2])[0] == "obec@hornilhota.cz", m[2:])
kod, out, err = spust(cesta)
ok("další spuštění soubor nemění", open(cesta, encoding="utf-8", newline="").read() == text)

# Řádky s **Komu:**, **Kopie:** a **Předmět:** v textu e-mailu jsou text, ne hlavička; odsazený řádek mimo odrážku
# se nepřipojí k předchozímu.
TELO3 = ("Dobrý den,\n\nprosím o vyhledání zápisu o sňatku.\n\n**Kopie:** rodný list otce\n**Komu:** matrice na vědomí\n"
         "**Předmět:** sňatek 1948\nPřílohu přikládám.\n\nS pozdravem\nJan Novák\n  Horní Lhota 5")
cesta3 = os.path.join(slozka, "hlavicka.md")
with open(cesta3, "w", encoding="utf-8", newline="\n") as f:
    f.write("## Matrika – sňatek\n\n**Komu:** matrika@example.cz\n\n**Předmět:** Sňatek 1948\n\n" + TELO3 + "\n")
kod, out, err = spust(cesta3)
m = odkazy(open(cesta3, encoding="utf-8").read(), "mailto:")
komu, q = mailto(m[0]) if m else ("", {})
ok("hlavička: prázdný řádek mezi poli nevadí", komu == "matrika@example.cz" and q.get("subject") == ["Sňatek 1948"],
   (err, komu, q.get("subject")))
ok("pole v textu e-mailu nejsou kopie", "cc" not in q, q.get("cc"))
ok("text e-mailu celý, odsazený podpis na vlastním řádku", q.get("body") == [TELO3.replace("\n", "\r\n")],
   q.get("body"))

# Koncept s oddílem ve starém tvaru (bez značek, verze z projektu): oddíl se nahradí, nezdvojí.
cesta4 = os.path.join(slozka, "stary.md")
with open(cesta4, "w", encoding="utf-8", newline="\n") as f:
    f.write("## A\n\n**Komu:** a@example.cz\n**Předmět:** A\n\nText\n\n---\n\n" + NADPIS
            + " (klikněte)\n\n- [A – otevřít v Gmailu](https://mail.google.com/x)\n")
kod, out, err = spust(cesta4)
text = open(cesta4, encoding="utf-8").read()
ok("starý tvar oddílu nahrazen", kod == 0 and text.count(NADPIS) == 1 and "mail.google.com/x" not in text
   and len(odkazy(text, "mailto:")) == 1, text)

# Starý oddíl bez značek, za ním další žádost a poznámka: smaže se jen nadpis a odkazy, zbytek zůstane.
cesta5 = os.path.join(slozka, "stary_pokracovani.md")
DALSI = "## B\n\n**Komu:** b@example.cz\n**Předmět:** B\n\nText B\n\nPoznámka na konec.\n"
with open(cesta5, "w", encoding="utf-8", newline="\n") as f:
    f.write("## A\n\n**Komu:** a@example.cz\n**Předmět:** A\n\nText A\n\n---\n\n" + NADPIS + " (klikněte)\n\n"
            "- [A – otevřít v Gmailu](https://mail.google.com/x)  \n  ([mailto](mailto:a@example.cz?subject=A))\n\n"
            "---\n\n" + DALSI)
kod, out, err = spust(cesta5)
text = open(cesta5, encoding="utf-8").read()
m = odkazy(text, "mailto:")
ok("starý oddíl: žádost a poznámka za ním zůstaly", kod == 0 and DALSI.strip() in text and "Text A" in text, (err, text))
ok("starý oddíl: staré odkazy pryč, nový oddíl jednou", "mail.google.com/x" not in text and text.count(NADPIS) == 1)
ok("starý oddíl: žádost za ním dostala odkaz", len(m) == 2 and mailto(m[1])[0] == "b@example.cz", m)

# Poškozené značky (jen jedna z dvojice): nástroj soubor nezmění a skončí chybou.
for znacka in ("<!-- odkazy:zacatek -->", "<!-- odkazy:konec -->"):
    cesta6 = os.path.join(slozka, "poskozeny.md")
    obsah = "## A\n\n**Komu:** a@example.cz\n**Předmět:** A\n\nText A\n\n" + znacka + "\n---\n\n" + NADPIS + "\n\n- x\n"
    with open(cesta6, "w", encoding="utf-8", newline="\n") as f:
        f.write(obsah)
    kod, out, err = spust(cesta6)
    ok(f"poškozená značka {znacka}: chyba a soubor beze změny",
       kod != 0 and open(cesta6, encoding="utf-8", newline="").read() == obsah, (kod, out, err))

# Zápis přes dočasný soubor: když zápis selže (místo dočasného souboru je složka), původní koncept zůstane.
cesta7 = os.path.join(slozka, "zapis.md")
obsah = "## A\n\n**Komu:** a@example.cz\n**Předmět:** A\n\nText A\n"
with open(cesta7, "w", encoding="utf-8", newline="\n") as f:
    f.write(obsah)
os.mkdir(cesta7 + ".tmp")
kod, out, err = spust(cesta7)
ok("selhaný zápis: chyba a koncept beze změny", kod != 0 and open(cesta7, encoding="utf-8", newline="").read() == obsah,
   (kod, err[-300:]))
os.rmdir(cesta7 + ".tmp")

# UTF-8 s BOM (Poznámkový blok): první blok se nesmí ztratit.
for n in (1, 2):
    cesta8 = os.path.join(slozka, f"bom{n}.md")
    with open(cesta8, "w", encoding="utf-8-sig", newline="\n") as f:
        f.write("\n---\n\n".join("## %s\n\n**Komu:** %s@example.cz\n**Předmět:** %s\n\nText\n" % (x, x, x)
                                 for x in "ab"[:n]))
    kod, out, err = spust(cesta8)
    m = odkazy(open(cesta8, encoding="utf-8-sig").read(), "mailto:")
    ok(f"BOM, {n} blok(y): odkaz u každého", kod == 0 and len(m) == n and mailto(m[0])[0] == "a@example.cz",
       (err, m))

# Vnořená odrážka není pokračování; pokračovací řádek se připojí i po vnořené odrážce.
cesta9 = os.path.join(slozka, "vnorene.md")
TELO9 = "Údaje:\n- Rodiče:\n  - otec Josef\n  - matka Marie\n- bydliště čp. 5,\n  Horní Lhota\n\nDěkuji"
with open(cesta9, "w", encoding="utf-8", newline="\n") as f:
    f.write("## V\n\n**Komu:** v@example.cz\n**Předmět:** V\n\n" + TELO9 + "\n")
kod, out, err = spust(cesta9)
m = odkazy(open(cesta9, encoding="utf-8").read(), "mailto:")
ocek = "Údaje:\n- Rodiče:\n  - otec Josef\n  - matka Marie\n- bydliště čp. 5, Horní Lhota\n\nDěkuji"
telo = mailto(m[0])[1].get("body", [""])[0].replace("\r\n", "\n") if m else ""
ok("vnořené odrážky zůstanou na svých řádcích", telo == ocek, repr(telo))

print(f"== mailto.py: {sum(vysledky)} z {len(vysledky)} správně")
sys.exit(0 if all(vysledky) else 1)
