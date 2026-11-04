# Žádosti archivům, matričním úřadům a obcím

Přehled žádostí, které jsme poslali nebo chystáme, a co na ně přišlo. Nejde na web.
Co by šlo zjistit, ale zatím o to nežádáme, patří do `archivni_dotazy.md`.
(Ukázka: řádky níže jsou vymyšlené, adresy a úřady neověřené.)

Stav: koncept → odesláno → odpověď s dalším krokem (čeká na úhradu, doplnit doklady, odpověď – zpracovat)
→ vyřízeno / zamítnuto / opuštěno. Otevřená zůstává, dokud je co udělat.
- Koncept je v `pracovni/zadosti/`, odkaz k odeslání z něj udělá `python3 -I tools/mailto.py <koncept.md>`.
- Odesláno: datum, kdy uživatel žádost poslal. Bez odpovědi déle než 30 dní → připomenout.
- Odpověď, po které je ještě co udělat, zůstává v Otevřených a do Stavu přijde další krok. Vyřízeno, zamítnuto
  nebo opuštěno: výsledek do dat a do `research_log.md`, řádek přesunout do Uzavřených.
- Na jeden archiv nanejvýš jedna otevřená žádost.
- Vaše adresa, telefon a e-mail sem nepatří, jen do konceptů v `pracovni/` (nejdou do gitu ani na web).

## Otevřené
| # | Komu | Co | Pro koho | Odesláno | Stav | Koncept / podklady |
|---|---|---|---|---|---|---|
| 2 | Matriční úřad Pardubice | kopie zápisu o úmrtí Františka Nováka († 1990); po 30 letech bez doložení příbuzenství, kniha je ještě na úřadě | 4 | | koncept | `pracovni/zadosti/pardubice_umrti_1990.md` |

## Odloženo
| # | Komu | Co | Pro koho | Odesláno | Stav | Koncept / podklady |
|---|---|---|---|---|---|---|
| 3 | Městský úřad Holice | evidence hrobů: kdo leží v hrobě rodiny Novákových | 8, 16 | | odloženo: nejdřív výsledek žádosti 2 | |

## Uzavřené
| # | Komu | Co | Pro koho | Odesláno | Stav | Koncept / podklady |
|---|---|---|---|---|---|---|
| 1 | Matriční úřad Holice | výpis ze zápisu o sňatku Františka Nováka a Marie Králové (1948) | 4, 5 | 3. 8. 2026 | vyřízeno 20. 8. 2026: datum sňatku potvrzeno, zapsáno do `osoby.py` a `research_log.md` | `pracovni/zadosti/holice_snatek_1948.md` |
