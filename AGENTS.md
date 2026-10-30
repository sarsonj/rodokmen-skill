# Správa repozitáře rodokmen-skill

Vydání nové verze: zvedni číslo ve třech místech najednou – `.claude-plugin/plugin.json` (`version`),
`skills/rodokmen/VERZE` (podle něj agent u uživatele pozná, že má aktualizovat projekt) a README („Stav k … (verze …)“).
Mění-li se formát mezi `tools/` a `template/web/`, otestuj i aktualizaci projektu založeného předchozí verzí
(`novy_projekt.py` na stejnou složku, `npm install`, `npm run data`, `npm run build`).

Skill se vyvíjí a zkouší v Claude Code. Jde použít i v Codexu a OMP (Oh My Pi), které ho instalují ze stejného
`.claude-plugin/marketplace.json` – ten proto nepřesouvej. Když měníš pokyny vázané na aplikaci (nástroje, příkazy,
restart), uprav i stávající zmínky o Codexu a OMP, ať si neodporují. V Codexu ani OMP je ověřovat nemusíš.
