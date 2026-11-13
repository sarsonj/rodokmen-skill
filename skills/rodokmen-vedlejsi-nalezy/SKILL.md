---
name: rodokmen-vedlejsi-nalezy
description: Postup pro odkládání vedlejších nálezů při rodopisném výzkumu (příbuzná jména, sourozenci, povolání, úmrtí, další manželství, domy, svědci) a jejich pozdější zpětné spojování s rodokmenem. Použít při každém čtení matrik a při čištění odkladiště.
---

# Vedlejší nálezy: odkládat a spojovat zpětně

## Proč
Při hledání jednoho předka se na stejných stranách potká spousta jmen, která se hodí až ve vyšších generacích, u sourozenců, nebo při určování příbuzenství. Bez uložení se musí číst znovu.

## Kde se co ukládá
- `data/vedlejsi_nalezy.md` – odkladiště, po oddílech podle rodu a knihy: `- [kniha, snímek/strana, rok] osoba – údaj (jistota)`. Nic odtud není ověřeno jako příbuzenství.
- `SIDE` v `data/osoby.py` – sourozenci, děti a jiní příbuzní mimo přímou linii: kdy a kde se narodili, zemřeli (nebo „úmrtí nenalezeno“). Zobrazuje se na stránce osoby.
- `MANZELSTVI` v `data/osoby.py` – druhé a předchozí manželství předků (manžele i manželky, rozvody, ovdovění). Předky těch druhých osob nehledáme.
- `data/research_log.md` – deník včetně neúspěšných hledání (kniha, snímky, roky, čitelnost).
- Domy podle čísel popisných (souřadnice dnešních domů přes RÚIAN) se hodí zapsat zvlášť, např. do `data/domy.json`.

## Pravidla
1. Čtenář uvede vedlejší nálezy v každém hlášení. Hlavní chat je zapíše dřív, než zapíše hlavní nález.
2. Ke každému údaji patří zdroj (kniha, snímek) a jistota `(?)`.
3. Nikdy nepřepisovat vedlejší nález do `P` (osoby) bez ověření na snímku.

## Zpětné spojování (čistění)
- Po každém uzavřeném nálezu projít odkladiště podle příjmení a domu (čp.): co se shoduje s novým předkem, přesunout do `P`/`SIDE` a v odkladišti označit „→ zapsáno“.
- Pokud web má stránku souvislostí rodů, ta hledá automaticky stejné příjmení (i rodné) a stejný dům u předků z různých větví; každé takové shody věnovat otázku „sourozenci, nebo sestřenice?“ a hledat společné rodiče.
- U každé generace sledovat teploměr na stránce „Co hledáme“; nálezy pro vyšší generace nechat v odkladišti, dokud se nedokončí nižší.
- Opakovaná jména a svědci (kmotři, svědci sňatku) často označují příbuzné; mezi nimi hledat nové předky.
