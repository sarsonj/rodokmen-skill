---
name: rodokmen-orchestrace
description: Jak vést rodopisný výzkum s mnoha čtenáři najednou (ARON, SOA, Acta Publica): rozdělení práce, limity stahování, ověřování zápisů, ukládání vedlejších nálezů a postup po generacích. Použít, kdykoli se hledá víc předků paralelně nebo se zadává práce pomocným agentům.
---

# Rodopis: orchestrace čtenářů

## Role
- **Hlavní chat** plánuje, zapisuje do `data/`, ověřuje klíčové údaje na snímku a mluví s uživatelem. Čtenář (Sonnet) čte rukopis a hlásí; Haiku se na rukopis nepoužívá.
- **Čtenář nikdy nepíše do `data/`**, ukládá jen do `pracovni/pom_<kód>/`. Každý nález (datum, čp., rodiče, kmotři) musí hlavní chat ověřit na vlastním výřezu, než ho zapíše jako `doc`.

## Zadání čtenáři (vždy)
1. Jeden úkol, přesné jméno, rok, čp., apu knihy a kalibrace snímků z dřívějška.
2. „Jedno stahování najednou, nespouštěj duplicity, nejdřív využij hotové cache `pracovni/cache_*`.“
3. „Vypiš i vedlejší nálezy: sourozence, děti, povolání, úmrtí, další manželství, kmotry, svědky, příbuzná jména, kde a kdy.“
4. „U negativního výsledku přesně uveď knihu, snímky, roky a čitelnost.“

## Limity serverů
- ARON vydrží asi 6–8 souběžných stahování celkem. Víc (20–40 procesů) ho zahltí a snímek pak trvá desítky minut. Kontrolovat `curl -m 20 https://aron.vychodoceskearchivy.cz/` a procesy `aron_img`.
- Acta Publica (MZA Brno) nelze stahovat přes curl (HTTP 426). Čte se jen v prohlížeči; hromadné stahování dlaždic skriptem je považováno za obcházení ochrany – nedělat.

## Zápis nálezu (pořadí)
výřez `vyrez.py` → rámeček `ramecek.py` → JSON záznamu a přepisu → `zapis.py` → osoby v `osoby.py` (i prarodiče jako nové Kekulé čísla) → `kontrola.py` → `npm run data` → deník (`research_log.md`) a vedlejší nálezy (`vedlejsi_nalezy.md`).
Nová kniha = nový záznam `svazky.json` (jinak kontrola selže).

## Postup po generacích
- Teploměr generací na stránce „Co hledáme“. Nejdřív dokončit generaci, pak další; co se najde navíc, uložit do odkladiště.
- Větve, které uživatel označí jako prioritní, jdou nejhlouběji; ostatní se dotahují do stejné generace.
- Jiné manželství, sourozenec nebo dítě předka se zapíše do `MANZELSTVI` / `SIDE`, jeho předky nehledáme.

## Kvalita čtení (měřeno na vlastních ověřených zápisech)
- **Plné rozlišení (úroveň 0, výřez jednoho zápisu)** čte český rukopis téměř bez chyb. **Poloviční rozlišení u kurentu je téměř nečitelné** (jména nahrazená „?“), hodí se jen na orientaci v knize.
- Německé formuláře (např. Vídeň) mají víc chyb: **roky, stav (ledig × vdovec), povolání, adresy a jména svědků.** Právě tyhle údaje vždy ověř na výřezu, než je zapíšeš jako `doc`. Příznak jistoty od čtenáře na to nestačí – čtenář u chybného roku napsal „střední“.
- Do databáze ani do dat neukládej „?“ jako hodnotu; nejisté pole vynech a popiš v poznámce.
- Přepis celé strany místo jedné vybrané řádky stál při měření jen asi o desetinu tokenů víc (obrázek se platí tak jako tak); užitečné je ukládat i zápisy cizích rodin, které čtenář stejně přečetl pořádně.

## Chyby, které se opakovaly
- Haiku četl špatně čísla a roky.
- Duplicitní stahování zahltila server.
- Negativní výsledek bez rozsahu zavádí.
- Kniha s „chybějícími čísly“ nemusí mít chybějící strany: čísla zápisů jsou společná pro celou farnost, obce mají vlastní knihy.
