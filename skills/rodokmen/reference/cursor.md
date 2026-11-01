# Cursor

Skill funguje v Cursoru stejně jako v Claude Code. Tady je jen to, čím se liší instalace a cloud agenti.
Zbytek návodu (fáze, matriky, web) platí beze změny.

Osobní skill patří do `~/.cursor/skills/rodokmen/` (na Windows `C:\Users\<jméno>\.cursor\skills\rodokmen\`).
Ve složce musí ležet `SKILL.md`.

Tento repozitář nejde přidat přes **Customize → From GitHub Repository**. Ten postup čeká
`.cursor-plugin/marketplace.json` a tady je manifest pro Claude Code (`.claude-plugin`).
Cesta je ruční kopie složky `skills/rodokmen`.

V chatu Cursor skill načte podle jména. Stačí napsat „rodokmen“ nebo jinou spouštěcí větu z `SKILL.md`.

Nový projekt dostane `AGENTS.md` se stejným textem jako `CLAUDE.md`. Složku projektu pak otevřete
v Cursoru i v Claude Code a oba navážou stejně.

Cloud agent vezme skill z repozitáře, když leží v `.cursor/skills/` nebo `.agents/skills/`.
Osobní skill z domovské složky použije jen se zapnutým
**Settings → Agents → Context and Tools → Sync Skills for Cloud Agents**.
Automatické běhy (automation) takto synchronizované osobní skilly nenačítají – u nich musí být skill v repozitáři.
