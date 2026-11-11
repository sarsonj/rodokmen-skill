# Sdílení přečteného – Mapa matrik a index matrik

## Manifest

Každý, kdo dělá rodokmen se skillem, otevírá tytéž knihy: listuje desítky snímků, aby našel, kde začíná rok nebo ves,
a čte zápisy, které už někdo přečetl. Platí za to tokeny, čas – a archivy, které pak blokují přístup všem (#138).
Řešením není posílat si mezi sebou snímky (patří archivu a jejich šíření podléhá jeho podmínkám), ale **sdílet to,
co se ze snímků přečetlo**:

1. **Kde co v knize je** → [Mapa matrik](https://github.com/ondrnovy/mapa-matrik): rozcestník (které knihy pokrývají
   obec a rok) a orientační body „snímek → rok, ves, strana, začátek rejstříku“. Žádná jména, žádné osobní údaje.
2. **Co v zápisu stojí** → [index matrik](https://github.com/pe-pan/matriky-index): přepisy zápisů přečtených očima
   (a OCR celých knih). Jen zákonně veřejné zápisy, vždy s odkazem na snímek u archivu.

Zásady:
- **Nejdřív se zeptej, pak čti.** Před otevřením knihy se podívej do mapy a indexu – co už někdo přečetl, nečti znovu.
- **Co přečteš, vrať.** Nic navíc: body a zápisy vznikají z toho, co stejně zapisuješ do `data/`.
- **Uživatele neotravuj.** Na sdílení se zeptej **jednou** za projekt; pak buď odesílej sám na konci kola, nebo nikdy.
- **Jen ověřitelné.** Každý bod a zápis vede na konkrétní snímek; nejisté čtení je označené, nic se nedomýšlí.
- **Nic soukromého.** Žádné výřezy, fotky, údaje od rodiny, závěry „kdo je kdo“, nic o žijících lidech.
- **Šetrně k archivům i ke sdíleným serverům.** Čtení mapy a indexu jde přes brzdu a na den se ukládá.

## Čtení (vždy, bez ptaní)

Ve smyčce Fáze 2, krok 3 (Najdi svazek), **před otevřením knihy**:
- `python3 -I tools/sdileni.py najdi "Obec" [rok] [N|O|Z]` – knihy z mapy s odhadem snímku, poznámky ke knize
  (posuny stránkování, oddíly po vsích) a kolik zápisů z knihy už je v indexu.
- `python3 -I tools/sdileni.py kniha <klíč svazku | adresa knihy>` – všechny orientační body knihy a zápisy, které už
  někdo přečetl. Je-li hledaný zápis v indexu, **ověř ho na snímku** (odkaz ze snímku) – ušetříš hledání, ne čtení.

Mapa i index jsou jen nápověda: odhad snímku může být o pár snímků vedle a cizí čtení může být chybné.
Nemá-li mapa obec ani knihu, postupuj jako dřív (portály v `portaly.md`).

## Zápis (automaticky, bez ptaní)

- **Body ze zápisů** se vytvoří samy: každý zápis v `data/zaznamy.json` (svazek + snímek + druh + rok) je orientační
  bod. Nic dalšího nedělej.
- **Body z listování** zapiš jen tam, kde se v knize orientuješ a nic nezapisuješ – začátek roku nebo vsi, začátek
  rejstříku, skok ve stránkování: `python3 -I tools/sdileni.py bod <klíč svazku> <snímek> rok=1785 ves=Lhota strana=fol. 12`
  (`rejstrik=A–C` u rejstříku). Jeden příkaz na snímek, který jsi stejně otevřel; bez jmen osob.
- **Zápisy pro index** jsou zápisy se záznamem v `zaznamy.json` a přepisem v `prepisy.json`, starší lhůt indexu
  (narození 100 let, sňatky a úmrtí 75 let).

## Jak se zeptat (jednou za projekt)

`python3 -I tools/sdileni.py prehled` řekne, kolik je nového k nasdílení, a stav souhlasu v `data/sdileni.json`.
Je-li **NEROZHODNUTO** a je co sdílet, zeptej se na konci prvního kola, kde něco našel (ne na začátku, ne uprostřed
hledání), krátce a jednou:

> Při hledání jsem přečetl N zápisů a zjistil, kde v M knihách začínají roky a vsi. Můžu to přidat do dvou
> otevřených projektů, ze kterých jsem dnes sám čerpal: Mapa matrik (jen „snímek 40 = rok 1785“, bez jmen) a index
> matrik (přepisy zápisů starších 100 / 75 let s odkazem na snímek, licence CC BY 4.0)?
>
> **Proč to má smysl:** stejné knihy čtou desítky rodin. Kdo přijde po nás, otevře rovnou správný snímek místo
> listování desítkami stran – ušetří čas i kredity a archivy nezatěžuje tolik, že by blokovaly přístup všem (už se to
> stalo). A pomůže to i nám: čím víc lidí přispívá, tím víc knih z našich vsí bude zmapovaných, až půjdeme o generaci
> dál. Přepisy navíc najdou vzdálení příbuzní, kteří hledají stejné předky.
>
> Potřebuju k tomu účet GitHub (zdarma, jednou se přihlásíš). Mám to pak dělat sám na konci každého kola?
> A chceš být u přepisů uvedený, nebo anonymně? Můžu napsat tvoje jméno, přezdívku, nebo nic (jen že četl Claude).
> Pull request ale vždycky ponese název tvého účtu GitHub – kdo nechce být dohledatelný, zvolí si v něm přezdívku.

Jméno ani přezdívku nenavrhuj sám z dat rodokmenu.

Je-li v tom kole něco z mapy nebo indexu opravdu využité, řekni to konkrétně („dnes nám mapa ušetřila listování
v Liblínu 01“) – je to nejlepší důvod.

Odpověď zapiš: `python3 -I tools/sdileni.py souhlas ano "Jméno nebo přezdívka"`, anonymně `souhlas ano` (bez jména),
nebo `souhlas ne`. Při **NE** se už
neptej (uživatel může názor změnit sám). Účet GitHub: `gh auth login` (dej uživateli s `!`); bez něj sdílení vynech.

## Odeslání (na konci kola, jen při ANO)

Ve stejné chvíli jako uložení do gitu po větším kroku:
1. `python3 -I tools/sdileni.py navrh` – připraví `pracovni/sdileni/zapisy.jsonl`. U každého zápisu doplň
   `datum` (ISO, např. 1817-03-12), `obec` (ves a číslo domu), `osoby` (`dítě: Josef; otec: Matěj Mudra, podruh;
   matka: Magdalena`, u sňatku ženich, nevěsta a jejich rodiče, u úmrtí zemřelý), `ostatni` (kmotři, svědci, kněz,
   věk, příčina smrti, strana) a `jistota` (vysoká / střední / nízká) – **jen z `_orig` a `_shrnuti`**, nejisté místo
   `[?]`, bez ztotožnění osob a závěrů rodokmenu. Zápisy bez přepisu tam nejsou.
2. `SDILENI_MODEL=<id modelu>/<effort> python3 -I tools/sdileni.py odeslat` (např. `claude-opus-5-5/high`; index chce
   vědět, čím se četlo). Nástroj založí fork, přidá body do mapy a zápisy do indexu (jen nové řádky, kontrolu indexu
   spustí sám) a otevře dva pull requesty.
3. Uživateli řekni **jednou větou** výsledek s odkazy („Nasdílel jsem 12 bodů do Mapy matrik a 5 zápisů do indexu
   matrik: …“). Neptej se znovu.

Mapa slučuje datové PR automaticky, index ručně správcem. Co už odešlo, je v `data/sdileni.json` a znovu se neposílá.

## Podporované archivy

Mapa: SOA Plzeň (Porta fontium), SOA Praha (eBadatelna). Index: navíc AHMP. Ostatní knihy `prehled` vypíše a vynechá
– u nich zatím jen čtení (mapa a index je mohou mít od jiných přispěvatelů).
