#!/usr/bin/env python3
"""Koncept žádosti (.md) -> odkazy, které otevřou nový e-mail s vyplněným adresátem, předmětem a textem.

Použití: python3 -I tools/mailto.py pracovni/zadosti/<koncept>.md [--gmail] [--outlook] [--seznam]
  bez voleb   odkaz mailto: (otevře výchozí poštovní program)
  --gmail     navíc odkaz do Gmailu na webu (když aplikace odkazy mailto: neotevře)
  --outlook   navíc odkaz do Outlooku na webu (outlook.office.com)
  --seznam    navíc odkaz do Seznam Emailu (email.seznam.cz); v Seznamu buďte předem přihlášeni,
              přihlašovací stránka rozepsaný e-mail zahodí

Formát konceptu: bloky oddělené řádkem ---, v bloku nadpis „## …“, řádky **Komu:** (víc adres odděl čárkou),
volitelně **Kopie:**, a **Předmět:**, pod nimi text e-mailu. Bloky bez Komu a Předmětu se přeskočí.
Odstavec piš na jeden řádek (zalomení se v e-mailu zachová); pokračovací řádek odrážky odsazený dvěma mezerami
se připojí k odrážce.
Na konec konceptu zapíše (při dalším spuštění nahradí) oddíl „## Odkazy k odeslání“ a odkazy vypíše i s délkou.
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


def adresy(blok, pole):
    m = re.search(r"^\*\*%s:\*\*[ \t]*(.*)$" % pole, blok, re.M)
    return (",".join(a.strip() for a in re.split(r"[,;]", m.group(1)) if a.strip()), m) if m else ("", None)


def main():
    volby = [a for a in sys.argv[1:] if a.startswith("--")]
    soubory = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(soubory) != 1 or any(v not in WEB for v in volby):
        sys.exit(__doc__)
    src = Path(soubory[0])
    text = src.read_text(encoding="utf-8").replace("\r\n", "\n")
    # starý oddíl s odkazy (i s čárou --- nad ním) zahodit
    text = re.split(r"(?:\n---[ \t]*\n\s*)?^" + re.escape(NADPIS), text, maxsplit=1, flags=re.M)[0].rstrip() + "\n"
    radky, varovani = [], []
    for blok in re.split(r"^---[ \t]*$", text, flags=re.M):
        komu, m_komu = adresy(blok, "Komu")
        kopie, m_kopie = adresy(blok, "Kopie")
        predmet = re.search(r"^\*\*Předmět:\*\*[ \t]*(.+)$", blok, re.M)
        if not (komu and predmet):
            continue
        nadpis = re.search(r"^## (.+)$", blok, re.M)
        nadpis = nadpis.group(1).strip() if nadpis else predmet.group(1).strip()
        konec = max(m.end() for m in (m_komu, m_kopie, predmet) if m)
        telo = re.sub(r"\n  (?=\S)", " ", blok[konec:].strip())
        predmet = predmet.group(1).strip()
        dotaz = {"subject": predmet, "body": telo.replace("\n", "\r\n")}
        if kopie:
            dotaz = {"cc": kopie, **dotaz}
        odkaz = "mailto:%s?%s" % (urllib.parse.quote(komu, safe="@,"),
                                  urllib.parse.urlencode(dotaz, quote_via=urllib.parse.quote))
        radky.append("- **%s** (%s): [otevřít e-mail](%s) (%d znaků)" % (nadpis, komu, odkaz, len(odkaz)))
        if len(odkaz) > LIMIT:
            varovani.append("POZOR: %s: odkaz mailto: má %d znaků, některé programy text uříznou. Použijte "
                            "--gmail nebo --outlook, nebo text zkopírujte z konceptu." % (nadpis, len(odkaz)))
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
    with open(src, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n---\n\n" + NADPIS + " (klikněte, otevře se e-mail s vyplněným textem)\n\n"
                + "\n".join(radky) + "\n")
    print("\n".join(radky + varovani))


if __name__ == "__main__":
    main()
