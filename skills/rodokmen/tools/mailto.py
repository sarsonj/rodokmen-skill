#!/usr/bin/env python3
"""Koncept žádosti (.md) -> odkazy, které otevřou nový e-mail s vyplněným adresátem, předmětem a textem.

Použití: python3 -I tools/mailto.py pracovni/zadosti/<koncept>.md [--gmail] [--outlook] [--seznam]
  bez voleb   odkaz mailto: (otevře výchozí poštovní program)
  --gmail     navíc odkaz do Gmailu na webu (když aplikace odkazy mailto: neotevře)
  --outlook   navíc odkaz do Outlooku na webu (outlook.office.com)
  --seznam    navíc odkaz do Seznam Emailu (email.seznam.cz); v Seznamu buďte předem přihlášeni,
              přihlašovací stránka rozepsaný e-mail zahodí

Formát konceptu: bloky oddělené řádkem ---, v bloku nadpis „## …“, hned pod ním řádky **Komu:** (víc adres odděl
čárkou), volitelně **Kopie:**, a **Předmět:**, pod nimi text e-mailu. Od prvního řádku, který není pole, je všechno
text e-mailu. Bloky bez Komu a Předmětu se přeskočí.
Odstavec piš na jeden řádek (zalomení se v e-mailu zachová); pokračovací řádek odrážky odsazený dvěma mezerami
se připojí k odrážce, jiné odsazené řádky zůstanou samostatně.
Na konec konceptu zapíše oddíl „## Odkazy k odeslání“ mezi značky <!-- odkazy:zacatek --> a <!-- odkazy:konec -->
a odkazy vypíše i s délkou. Při dalším spuštění nahradí jen tento oddíl; žádosti připsané za něj taky dostanou odkaz.
Odkaz mailto: delší než 1800 znaků některé programy uříznou – nástroj na to upozorní. Nic neodesílá.
"""
import re, sys, urllib.parse
from pathlib import Path
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

NADPIS = "## Odkazy k odeslání"
LIMIT = 1800
WEB = {"--gmail": ("Gmail", "https://mail.google.com/mail/?", {"view": "cm", "fs": "1"}, "su"),
       "--outlook": ("Outlook", "https://outlook.office.com/mail/deeplink/compose?", {}, "subject"),
       # Seznam bere celý odkaz mailto: v parametru mailto; tvar je z obsluhy mailto: v české verzi Firefoxu
       # (https://bugzilla.mozilla.org/show_bug.cgi?id=428475). Bez přihlášení přesměruje na login.seznam.cz
       # a rozepsaný e-mail zahodí (ověřeno 4. 11. 2026).
       "--seznam": ("Seznam Email", "https://email.seznam.cz/newMessageScreen?", None, "mailto")}


ZACATEK, KONEC = "<!-- odkazy:zacatek -->", "<!-- odkazy:konec -->"   # vygenerovaný oddíl; mimo něj se nic nemaže
POLE = re.compile(r"\*\*(Komu|Kopie|Předmět):\*\*[ \t]*(.*)$")
ODRAZKA = re.compile(r"\s*(?:[-*+]|\d+[.)])\s")


def adresy(hodnota):
    return ",".join(a.strip() for a in re.split(r"[,;]", hodnota) if a.strip())


def rozeber(blok):
    """Nadpis, pole hlavičky a text e-mailu. Hlavička jsou jen řádky **Komu:** / **Kopie:** / **Předmět:** hned pod
    nadpisem (prázdné řádky mezi nimi nevadí); od prvního jiného řádku je všechno text, i řádky, které vypadají jako pole."""
    radky = blok.strip("\n").split("\n")
    i = next((n + 1 for n, r in enumerate(radky) if r.startswith("## ")), 0)
    nadpis = radky[i - 1][3:].strip() if i else ""
    pole = {}
    while i < len(radky):
        m = POLE.match(radky[i])
        if not (m or not radky[i].strip()):
            break
        if m:
            pole[m.group(1)] = m.group(2).strip()
        i += 1
    telo, v_odrazce = [], False
    for r in radky[i:]:
        if v_odrazce and re.match(r"  \S", r):   # pokračování odrážky
            telo[-1] += " " + r.strip()
            continue
        v_odrazce = bool(ODRAZKA.match(r))
        telo.append(r)
    return nadpis, pole, "\n".join(telo).strip()


def main():
    volby = [a for a in sys.argv[1:] if a.startswith("--")]
    soubory = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(soubory) != 1 or any(v not in WEB for v in volby):
        sys.exit(__doc__)
    src = Path(soubory[0])
    text = src.read_text(encoding="utf-8").replace("\r\n", "\n")
    oddil = re.search(r"\n*" + re.escape(ZACATEK) + r".*?" + re.escape(KONEC) + r"[ \t]*\n?", text, re.S)
    if oddil:
        pred, po = text[:oddil.start()], text[oddil.end():]
    else:   # starší tvar bez značek: oddíl s odkazy (i s čárou --- nad ním) až do konce souboru
        pred = re.split(r"(?:\n---[ \t]*\n\s*)?^" + re.escape(NADPIS), text, maxsplit=1, flags=re.M)[0]
        po = ""
    radky, varovani = [], []
    for blok in re.split(r"^---[ \t]*$", pred + "\n" + po, flags=re.M):
        nadpis, pole, telo = rozeber(blok)
        komu, kopie, predmet = adresy(pole.get("Komu", "")), adresy(pole.get("Kopie", "")), pole.get("Předmět")
        if not (komu and predmet):
            continue
        nadpis = nadpis or predmet
        dotaz = {"subject": predmet, "body": telo.replace("\n", "\r\n")}
        if kopie:
            dotaz = {"cc": kopie, **dotaz}
        odkaz = "mailto:%s?%s" % (urllib.parse.quote(komu, safe="@,"),
                                  urllib.parse.urlencode(dotaz, quote_via=urllib.parse.quote))
        radky.append("- **%s** (%s): [otevřít e-mail](%s) (%d znaků)" % (nadpis, komu, odkaz, len(odkaz)))
        if len(odkaz) > LIMIT:
            varovani.append("POZOR: %s: odkaz mailto: má %d znaků, některé programy text uříznou. Použijte "
                            "--gmail, --outlook nebo --seznam, nebo text zkopírujte z konceptu." % (nadpis, len(odkaz)))
        for v in WEB:
            if v in volby:
                jmeno, zaklad, pevne, pole = WEB[v]
                if pevne is None:   # Seznam: celý odkaz mailto:
                    q = {pole: odkaz}
                else:
                    q = {**pevne, "to": komu, **({"cc": kopie} if kopie else {}), pole: predmet, "body": telo}
                url = zaklad + urllib.parse.urlencode(q, quote_via=urllib.parse.quote)
                radky.append("  [%s](%s) (%d znaků)" % (jmeno, url, len(url)))
    if not radky:
        sys.exit("V konceptu není žádný blok s řádky **Komu:** a **Předmět:**.")
    novy = (ZACATEK + "\n---\n\n" + NADPIS + " (klikněte, otevře se e-mail s vyplněným textem)\n\n"
            + "\n".join(radky) + "\n" + KONEC + "\n")
    with open(src, "w", encoding="utf-8", newline="\n") as f:
        f.write(pred.rstrip() + "\n\n" + novy + ("\n" + po.lstrip("\n") if po.strip() else ""))
    print("\n".join(radky + varovani))


if __name__ == "__main__":
    main()
