# Zajímavosti a příběh rodu

Kvůli tomuhle rodina web čte. Tabulka jmen a dat nikoho nechytí, ale „prapradědeček se narodil 267 dní po svatbě“
nebo „rod žil sto let v jednom domě“ ano. Nečekej s tím až na konec výzkumu.

## Zajímavosti („fun facts“) – sbírej průběžně
Kdykoli při čtení zápisu narazíš na něco neobvyklého, **hned** to napiš do `data/zajimavosti.md` jako krátký odstavec
a řekni to uživateli jako příběh. Po každém větším kole spusť `python3 -I tools/napady.py`. Nástroj projde data
a vypíše náměty (svatby krátce před porodem, rod v jednom domě, sňatky příbuzných, dlouhověkost, epidemie…).
Každý námět si ověř v zápisu, než ho napíšeš.

Co bývá zajímavé (všechno z jednoho skutečného rodokmenu):
| Typ | Příklad, jak to napsat |
|---|---|
| Svatby na poslední chvíli | tabulka: svatba – dítě – za kolik dní (spočítej přesně); „přesná trefa“: narozen 267 dní po svatbě – počat nejspíš o svatební noci |
| Nemanželské děti, legitimace | „Jméno přežilo díky svobodné matce“ – příjmení se dědilo po matce; poznámka o legitimaci na okraji zápisu |
| Sto let v jednom domě | stejné číslo popisné přes 3–5 generací, kdo se v něm narodil a zemřel |
| Předek v rodokmenu vícekrát | děda a babička byli vzdálení příbuzní (`SAME`) – kde se větve potkaly |
| Neobvyklá jména | křestní jméno po světici (a jak se jméno v matrikách zkomolilo) |
| Významní svědci a kmotři | radní, rychtář, farář, vrchnostenský úředník na svatbě obyčejného řemeslníka |
| Dispense | svatba s povolením od biskupa (příbuzenství, zákaz ohlášek, adventní doba) |
| Řemesla v rodě | krejčí, puškaři, ranhojič, sládek… jako jeden odstavec přes všechny rody |
| Osudy žen | dvakrát vdova během deseti let; služka, která si vzala o 25 let staršího vdovce |
| Děti, které brzy přišly o rodiče | matka zemřela po porodu, otec v epidemii – kdo děti vychoval |
| Epidemie a války | cholera 1831/1855/1866, prusko-rakouská válka 1866, španělská chřipka 1918 (příčina úmrtí v zápisu!) |
| Moderní doba | civilní sňatek na úřadě a povolení soudu pro nezletilou nevěstu; přestěhování do pohraničí po 1945 |
| Rodinné vyprávění vs. matrika | „rodina říkala Marie, ve skutečnosti Anna“; potvrzená rodinná pověst („babička byla ze statku“) |
| Ztracený začátek | kde linie končí a proč (shořelé knihy, nemanželské dítě bez otce) |
| Noviny | výstřižek o jmenování, vyznamenání, penzi, parte – přidej obrázek do `dokumenty.json` |

Styl: nadpis `## Krátký a zvědavý`, 2–5 vět, konkrétní data a místa, odkazy na osoby `[Jméno](/osoba/<slug>/)`.
Nejlepší 2–4 dej i na úvod webu (`web.json` → `zajimavosti_na_uvodu`).
Citlivé věci z 20. století (sebevraždy, nemoci, rozvody, nemanželské děti u nedávno žijících) piš jen se souhlasem
uživatele (`reference/soukromi.md`). `kontrola.py` je hlídá.

## Příběh hlavního rodu
**Hlavní rod** je rod výchozí osoby (rodné příjmení, většinou rod č. 8 v `LINES`). Když uživatel chce jiný, nastav
`web.json` → `pribeh.rod`. Příběh se jmenuje **„Příběh <rodu ve 2. pádě>“** (Příběh Novákových, Příběh Dvořáků).
Má vlastní položku v menu a je hlavní věcí na úvodní stránce.

**Kdy psát:** jakmile má hlavní rod zhruba 5 generací doložených matrikou. Nečekej, až bude „hotovo“, protože příběh
jde později doplnit. `kontrola.py` na to upozorní. Uživateli to nabídni, i když dřív řekl „až bude víc dat“.

**Postup:**
1. Sesbírej materiál: fakta a poznámky osob hlavního rodu, `SIDE`, zajímavosti, `udaje_od_rodiny.md`,
   rodinné paměti a dokumenty, novinové výstřižky.
2. Napiš **koncept do chatu** a nech si ho schválit (délka, tón, co ano/ne). Pod koncept připiš, co je z matrik
   a co od rodiny, a co jsi vynechal jako citlivé. Teprve po schválení ho ulož.
3. Ulož do `data/pribeh.md`:
   ```markdown
   ---
   title: Příběh Novákových
   lead: Jedna věta, která chytí – od koho k komu příběh vede.
   ---

   ## Prolog v mlze (1700–1750)
   …
   ## Kováři z čísla 112 (1777–1874)
   …
   ```
4. Nastav `web.json` → `"pribeh": {"menu": "Příběh Novákových", "rod": 8, "tlacitko": "Přečíst příběh Novákových"}`
   a úvod (`uvod.nadpis`, 2–3 odstavce lákadla, fotka). Bez úvodu se na úvodní stránce ukáže aspoň název a `lead` příběhu.

## Více příběhů
Když chce rodina samostatné příběhy pro několik větví nebo témat, ulož každý do `data/pribehy/<slug>.md`:

```markdown
---
title: "Příběh prvního rodu"
lead: Stručná věta, která uvede příběh.
rod: 8
---

## První kapitola
Text příběhu…
```

`slug` je název souboru z malých písmen bez diakritiky, číslic a pomlček (např. `prvni-rod`). Pole `rod` je číslo
rodu 8–15; slouží k odkazu na příslušnou větev. Web vytvoří přehled na `/pribehy/`, samostatnou stránku
`/pribehy/<slug>/`, odkaz v menu i tlačítko z úvodu. V `web.json` lze seznam a pořadí nastavit například
`"pribehy": ["prvni-rod", "druhy-rod"]`; pokud je seznam prázdný, použijí se všechny soubory v abecedním pořadí.
Je-li seznam vyplněný, musí obsahovat každý soubor právě jednou. Popisek položky menu a tlačítka lze dál nastavit
v `pribeh.menu` a `pribeh.tlacitko`.

Přítomnost Markdown souborů ve složce `data/pribehy/` má přednost před starým `data/pribeh.md`. Bez této složky
funguje původní jediný příběh beze změny. Po úpravě spusť `npm run data` a oprav případná upozornění
`POZOR: nefunkční odkaz`; odkazy na další příběhy piš jako `/pribehy/<slug>/`.

Před zveřejněním zkontroluj soukromí **každého** souboru `data/pribehy/*.md`, nejen příběhu zobrazeného jako první.
`tools/kontrola.py` hledá citlivý obsah ve všech těchto souborech; uživatel musí schválit každý zveřejňovaný údaj.

**Jak má vypadat** (osvědčený tvar, asi 800–1500 slov):
- Kapitoly po generacích, od nejstaršího předka k dnešku. Nadpis = člověk nebo jeho role + roky
  („Krejčí z Holic (asi 1756–1812)“, „Služka, která zachránila jméno“).
- Každá kapitola 1–3 krátké odstavce: kde žil, čím se živil, svatba, děti, něco lidského (zápis, svědek, nehoda, stěhování).
- Konkrétně: data, místa, čísla domů, citace ze zápisu v uvozovkách. Odkazy na osoby `[Jméno](/osoba/<slug>/)`
  (slugy ve `web/src/data/site.json`).
- Názvy obcí: archiv a OpenStreetMap píší třeba „Veliš“, rodina a dnešní úřední podoba „Velíš“. Zeptej se, jakou podobu
  rodina používá, a drž ji v celém textu.
- Poctivě: co nevíme, napiš jako otázku nebo domněnku („nejspíš“, „podle rodiny“). Nic nevymýšlej kvůli plynulosti.
- Na konci kapitola o dnešku: jen jména a vztahy žijících, bez podrobností.
- Ostatní rody dostanou svůj prostor na stránkách rodů (popis v `LINES`, `HYPOTEZY`) a v zajímavostech.
