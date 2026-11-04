# Žádosti archivům, matričním úřadům a obcím

Postup je v SKILL.md (Fáze 2, „Žádosti“). Tady jsou podrobnosti a tři vzory.

## Kam s čím
- **Matriční úřad** (obec s matrikou). Zákon č. 301/2000 Sb., o matrikách, rozlišuje dvě věci:
  - *Kde je kniha* (§ 23): úřad ji drží 100 let (narození), 75 let (manželství, partnerství i úmrtí) od posledního
    zápisu ve svazku, pak ji předá státnímu oblastnímu archivu. Kniha úmrtí tedy bývá na úřadě i s 50 let starými zápisy.
  - *Kdo smí dostat zápis* (§ 25b odst. 1): po 100 letech od zápisu narození, 75 letech od zápisu manželství
    a 30 letech od zápisu úmrtí dostane výpis nebo kopii kdokoli, bez doložení příbuzenství. Lhůta běží od daného
    zápisu, ne od posledního zápisu ve svazku.
  - Mladší zápis (§ 25 odst. 1): jen ten, koho se týká, a člen rodiny. Člen rodiny je podle § 8a odst. 6 manžel,
    partner, rodiče, děti, sourozenci, prarodiče, vnuci a pravnuci, tedy ne každý předek nebo potomek. Žadatel doloží
    příbuzenství řetězem dokladů od sebe k hledané osobě (vlastní rodný list, rodný list rodiče…). Úřad vydá úplný
    výpis, případně kopii zápisu (§ 25 odst. 7). Za doklad se platí správní poplatek, výši a platbu úřad sdělí.
  - Ověřeno na zakonyprolidi.cz/cs/2000-301 (znění od 1. 1. 2025), 4. 11. 2026.
- **Archiv** (SOA, SOkA, archiv města): rešerše v pozemkových knihách, kronikách, spisech, sčítání lidu. Krátce napsat,
  co hledáte a proč, a uvést, co už víte (jméno, čp., roky). Archiv odpoví na všechno najednou, proto nanejvýš jedna
  otevřená žádost na archiv. Rešerše bývá placená, o ceně se ptát předem.
- **Obec** (správce hřbitova): evidence hrobů, kdo je v hrobě uložen a kdy, kdo hrob platí. Často odpoví zdarma.

## Kanály
- E-mail z odkazu `tools/mailto.py` stačí na dotaz a na rešerši. Žádost o matriční doklad bez podpisu může úřad
  vzít jen jako dotaz a požádat o podání jinak.
- **Datová schránka** (zdarma pro každou osobu; podání z ní má stejné účinky jako podepsaná písemná žádost,
  zákon č. 300/2008 Sb., § 18 odst. 2): nejjistější cesta
  k matričnímu úřadu. Text žádosti je stejný, přílohy jako PDF. Odesílá uživatel sám.
- Pošta s úředně ověřeným podpisem nebo osobní návštěva, když úřad nic jiného nebere.
- Adresu instituce (e-mail podatelny nebo matriky, ID datové schránky) vždy ověř na jejím oficiálním webu.

## Koncept
Soubor `pracovni/zadosti/<instituce>_<co>.md`. Víc žádostí v jednom souboru odděl řádkem `---`. Kontakty uživatele
(adresa, telefon) patří jen sem, ne do `data/`.

    ## Matriční úřad <obec> – úmrtí <jméno>

    **Komu:** matrika@<obec>.cz
    **Předmět:** Žádost o kopii zápisu o úmrtí (<jméno>, † <rok>)

    Dobrý den,
    …

Řádky `**Komu:**`, `**Kopie:**` (volitelně) a `**Předmět:**` patří hned pod nadpis; od prvního jiného řádku je
všechno text e-mailu. Odstavec piš na jeden řádek. Pokračování odrážky odsaď dvěma mezerami. Nástroj zapíše odkazy
mezi značky `<!-- odkazy:zacatek -->` a `<!-- odkazy:konec -->` a při dalším spuštění nahradí jen je, další žádost
se tedy dá připsat kamkoli.
Pak `python3 -I tools/mailto.py pracovni/zadosti/<soubor>.md`. Odkaz `mailto:` otevře výchozí poštovní program.
Kdo píše z pošty v prohlížeči, dostane odkaz navíc: `--gmail`, `--outlook` (outlook.office.com), `--seznam`
(Seznam Email; uživatel musí být v Seznamu přihlášený předem, jinak přihlašovací stránka text zahodí). Odkaz
`mailto:` delší než 1800 znaků některé programy uříznou, nástroj na to upozorní. Pak raději pošta v prohlížeči,
nebo ať uživatel text zkopíruje z konceptu.

## Vzor 1: matriční úřad, výpis nebo kopie zápisu

    **Předmět:** Žádost o výpis ze zápisu o úmrtí (<jméno a příjmení>, † <datum>)

    Dobrý den,

    prosím o výpis nebo kopii zápisu o úmrtí pro rodinný rodokmen:
    - <jméno a příjmení>, narozen(a) <datum> v <obec>, zemřel(a) <datum nebo rok> v <obec>, bydliště <obec čp.>
    - manžel(ka): <jméno>, rodiče: <jména, pokud je znám>

    Jsem <vnuk / pravnučka …> zemřelého. Příbuzenství dokládám přiloženými kopiemi: <můj rodný list>, <rodný list
    otce / matky>, <…>.

    Prosím o sdělení výše správního poplatku a způsobu platby. Pokud je potřeba žádost podat jinak (datovou schránkou,
    s ověřeným podpisem), dejte mi prosím vědět.

    Děkuji a přeji hezký den,
    <jméno a příjmení>
    <adresa, telefon>

Odstavec o příbuzenství jen u zápisu mladšího než lhůty z § 25b (úmrtí 30 let, sňatek 75, narození 100); u staršího
ho vynech. Pro sňatek stejně: „zápisu o uzavření manželství“, oba snoubenci, datum a místo sňatku.

## Vzor 2: archiv, rešerše

    **Předmět:** Žádost o rešerši – pozemková kniha, <obec> čp. <N>

    Dobrý den,

    pro rodinný rodokmen hledám majitele domu čp. <N> v <obec> v letech <od>–<do>. Podle matrik tam žil <jméno>
    (<povolání>, † <rok>).

    Prosím o sdělení, zda je pozemková kniha pro <katastrální území> ve vašem archivu a zda je možné udělat rešerši
    zápisů k čp. <N>, případně jakou cenu a lhůtu mám čekat. Rád(a) také přijedu do badatelny.

    Děkuji,
    <jméno a příjmení>
    <adresa, telefon>

## Vzor 3: obec, evidence hrobů

    **Předmět:** Dotaz do evidence hrobů – rodina <příjmení>

    Dobrý den,

    pro rodinný rodokmen hledám hrob rodiny <příjmení> na hřbitově v <obec>. Pochováni tam mohou být:
    - <jméno a příjmení>, † <rok>
    - <jméno a příjmení>, † <rok>

    Prosím o sdělení, zda je v evidenci hrobů najdete, číslo hrobu a kdo je v něm uložen (jména a data uložení).

    Děkuji,
    <jméno a příjmení>
    <telefon>

## Po odpovědi
Shrň uživateli, co přišlo. Ne každá odpověď žádost uzavírá:
- Je potřeba ještě něco udělat (zaplatit rešerši nebo poplatek, doplnit doklady, podat žádost jinak, odpovědět na
  dotaz)? Žádost zůstává v Otevřených, do Stavu napiš další krok: „čeká na úhradu“, „doplnit doklady“,
  „odpověď – zpracovat“.
- Uzavři ji, až je vyřízená (údaje přišly), zamítnutá, nebo když ji uživatel vzdá (opuštěno, třeba po marné
  připomínce bez odpovědi). Nové údaje zapiš do dat (`osoby.py`, matriční doklad jako dokument do `dokumenty.json`)
  a do `research_log.md`, řádek v `data/zadosti.md` přesuň do Uzavřených. U zamítnuté napiš do Stavu i důvod,
  ať se žádost neopakuje.
