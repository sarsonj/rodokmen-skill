# Přímí předci podle Kekulého čísel: 1 = výchozí osoba (ten, pro koho rodokmen děláme),
# otec osoby n má číslo 2n, matka 2n+1. Tedy 2 = otec, 3 = matka, 4–7 prarodiče, 8–15 pradědečci a prababičky…
#
# Každá osoba:  číslo: dict(n="Jméno Příjmení", y="1850–1910", st="doc", f=[...], r=[...], note="...")
#   n    jméno; ženy rodným příjmením („Anna Dvořáková“), u nejistého čtení otazník („Marie Špalková (?)“)
#   y    roky života pro přehledy: "* 1931" (žije / úmrtí neznámé), "1850–1910", "asi 1720–1785", "1680 – před 1740"
#   st   stav doložení:  doc  = doloženo matrikou (čteno přímo ze snímku)
#                        prob = pravděpodobné (shoda údajů, ale ne přímý doklad)
#                        fam  = údaj od rodiny / z rodinného dokumentu
#                        mh   = jen z cizího rodokmenu na internetu (MyHeritage, Geni…) – neověřeno
#                        unk  = neznámé (jen místo v rodokmenu)
#   f    fakta jako krátké věty: "* 12. 3. 1873 Hořice čp. 477", "kovář", "× 28. 1. 1897 Anna Stejskalová", "† 14. 5. 1902"
#        (* narození, × sňatek, † úmrtí – podle těchto značek web pozná sňatky a místa pro mapu)
#   r    klíče zápisů z data/zaznamy.json, které osobu dokládají
#   note poznámka: proč je údaj nejistý, rozpory, odkud se vzal
#   sex  jen u osoby 1: "M" nebo "F" (u ostatních plyne z čísla)
#   sour stav hledání sourozenců (stromový graf): "hotovo" = všichni dohledáni, "částečně"; chybí = zatím nehledáno
# Žijící lidé: jen jméno a rok narození (soukromí), note="Žijící – údaje jen základní."
# Neznámý otec nemanželského dítěte: dict(n="otec neuveden", st="unk", f=[], note="…")

P = {
}

# Rody = osm větví podle pradědečků a prababiček (čísla 8–15). Doplňte, jakmile je znáte:
# 8: ("Novákové", "Jedna věta, kdo to byli a odkud – ukáže se na webu u rodu."),
LINES = {
}

# Osoby mimo přímou linii pro stromový graf: sourozenci předků, jejich partneři a děti, předci partnerů…
# "zkratka": dict(n="Marie Nováková", y="1892–1970", sex="F", otec=16, matka=17, st="doc", f=[...], r=[...], note="…")
#   otec, matka  číslo přímého předka (16) nebo zkratka jiné osoby z RODINA ("karel-hruby"); chybí = neznámý.
#                Sourozenec předka 8 má otec=16, matka=17 – i když 16/17 ještě neznáme (poznají se jako sourozenci).
#   partner      seznam partnerů bez společného dítěte v rodokmenu, např. partner=[44] (první manželka předka 44)
#   sex          "M" nebo "F" (povinné); n, y, st, f, r, note jako u předků. Žijící: jen jméno a rok narození.
RODINA = {
}

# Poznámky o příbuzných, které nejdou zapsat do RODINA (nejistý vztah, celá větev jednou větou): k = číslo předka.
# dict(k=16, n="Josef Novák", v="bratr", y="1865–1920", t="Bratr Jana. Kovář v …", r=["klic_zapisu"])
#   v  vztah k předkovi: "bratr", "sestra", "manžel", "manželka", "syn", "dcera", jinak volně ("příbuzný")
#   y  roky jako u předků ("* 1949", "1893–1960"); obojí volitelné
SIDE = [
]

# Rozpory a otevřené otázky (na web do „Co hledáme“) jako dvojice (otázka, odpověď). Odpověď začněte
# „Vyřešeno: …“ (na webu se skryje), „Hypotéza: …“ nebo „Otevřené: …“. Jde na web – nic citlivého.
# ("Kdy se narodil Jan Novák?", "Otevřené: rodina říká 1850, v Holicích 1848–1852 nenalezen.")
ISSUES = [
]

# Hypotézy o původu rodu nad rámec doložené linie (zobrazí se na stránce rodu):
# dict(rod=8, nadpis="Hypotéza: Novákové z Lhoty", text="…", polozky=[("Jan Novák", "kmotr 1681…")], zaznamy=["klic"])
HYPOTEZY = [
]

# Předek v rodokmenu vícekrát (příbuzní rodiče): {alias: hlavní číslo}, např. {350: 140}
SAME = {}
