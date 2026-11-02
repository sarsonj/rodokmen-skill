# Testy brzdy proti zablokování archivem

Regresní testy pro `skills/rodokmen/tools/slusne.py` (brzda) a `skills/rodokmen/tools/hlidac_site.py` (volitelný hlídač).
Ve složce skillu nejsou, aby se nekopírovaly uživatelům. Nic nestahují z internetu: brzdu zkoušejí na lokálních serverech
(127.0.0.2 a 127.0.0.3 – localhost brzda záměrně nebrzdí), hlídači jen posílají JSON jako Claude Code.

Z kořene repozitáře, přes obal (testy samy obsahují příkazy s curl):

    python3 -I skills/rodokmen/tools/slusne.py tests/brzda/test_brzda.py skills/rodokmen/tools/slusne.py
    python3 -I skills/rodokmen/tools/slusne.py tests/brzda/test_hlidac.py skills/rodokmen

Na Windows `python -I -X utf8` a obojí pustit z Git Bashe i z PowerShellu. `ROZSIRENI=0` spustí u brzdy jen základní testy
(bez heredocu, prodlužování stopky, podprocesů a opakovaného souběhu vláken).

Výsledky na Windows 11 (Python 3.13, Git Bash, PowerShell 7), 2. 11. 2026:

| | Git Bash | PowerShell |
|---|---|---|
| `test_brzda.py`, 0.6.0 (základní testy) | 16 z 19 | 16 z 19 (bash s curl nebrzdí) |
| `test_brzda.py`, tato větev | 24 z 24 | 24 z 24 |
| `test_hlidac.py`, 0.6.0 | 39 z 59 | 0 z 59 (příkaz hooku se nespustí) |

Na macOS a Linuxu jsem testy nespouštěl. Na macOS je pro 127.0.0.2 potřeba alias na lo0
(`sudo ifconfig lo0 alias 127.0.0.2 up`, stejně pro .3 a .4).
