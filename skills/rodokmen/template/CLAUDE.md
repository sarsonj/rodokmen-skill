# Projekt rodokmenu

Tohle je projekt rodokmenu vedený skillem **rodokmen**. Na začátku každé konverzace:
1. Načti skill `rodokmen` (pokud ještě není načtený).
2. Přečti `data/STAV.md` – stav, pravidla a co je rozpracované – a posledních pár řádků deníku
   (`tail -n 5 data/research_log.md | cut -c1-600`). Deník ani `data/historie_kol.md` nečti celé, hledej v nich.
3. Pokračuj tam, kde se skončilo. Komunikuj česky, stručně a srozumitelně pro člověka bez zkušeností s genealogií a programováním.
4. Síť na weby archivů jen přes brzdu `tools/slusne.py` (vlastní skripty, curl), i v zadání pomocníků – viz skill, „Šetrně k archivům“.
5. Co by šlo ve skillu zlepšit (chyby nástrojů, nové archivy, nápady), zapisuj do `poznamky_pro_skill.md` – viz skill, sekce „Poznámky pro správce skillu“.
