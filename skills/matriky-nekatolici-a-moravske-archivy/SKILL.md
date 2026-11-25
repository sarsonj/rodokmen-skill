---
name: matriky-nekatolici-a-moravske-archivy
description: Kde hledat matriky evangelíků (helvetské a augsburské vyznání), jak se orientovat v knihách farnosti po obcích a jak číst zápisy v češtině, němčině a latině. Pokrývá ARON (východní Čechy), SOA Třeboň, Acta Publica (Morava) a Matriculu (Vídeň). Použít, když rodina není katolická, když se z ARON nedaří nic najít, nebo když předci pocházejí z Moravy či Vídně.
---

# Matriky nekatolíků a moravské archivy

## Nejdřív vyznání
Zeptat se na vyznání rodiny a hledat oddací listy, kroniky, náhrobky. Evangelíci (Českobratrská, helvetské vyznání) mají vlastní knihy: v ARON **L 3-x** (sbor Krucemburk: L 3-1 1782–96, L 3-2 narození 1797–1830, L 3-3 až 3-5, 3-9 narození, L 3-6 až 3-8038 oddaní, L 3-8 a 3-10 zemřelí). Do toleranční doby (1781) a u smíšených sňatků jsou stopy i v katolických knihách.

## Knihy po obcích
Farnost má často **samostatnou knihu pro každou obec** (Krucemburk, Hluboká 6029/6030, Ransko, Benátky, Kohoutov…). Rejstřík farnosti označuje obce písmeny (u Krucemburku U = Hluboká). Čísla zápisů v roce jsou společná pro celou farnost, proto v knize jedné obce chybí. Nevěsta se obvykle vdávala v **nevěstině farnosti/sboru** – sňatek často není tam, kde žil ženich.

## Archivy
- **ARON** (SOA Zámrsk): `aron_search.py`, `aron_img.py`; snímek = dvojstrana; kalibrace rok ↔ snímek čtením dat; zápis v knize `150-6` (Solnice narození 1837–1872) 8–10 snímků na rok.
- **SOA Třeboň** (`trebon.py`): jmenné rejstříky dobrovolníků jen u některých knih.
- **Acta Publica (MZA Brno)**: Morava, evangelické matriky Sněžné (16766 narození 1795–1808, 16773 oddaní 1820–1864), katolické Radostín/Vojnův Městec (16528). URL `…/detail/<ID>?image=<prefix>-<n×10 pětimístně>.jp2`. Jen prohlížeč, curl nefunguje; čtení pomalé (10–25 s/snímek).
- **Matricula** (Vídeň, Hernals): bez přihlášení; obrázky přes tokeny stránky (`matricula_dl.sh`).
- **RÚIAN (ČÚZK)**: z čísla popisného souřadnice dnešního domu: `AdresniMisto`, `adresa LIKE 'Obec 12, <PSČ>%'`; pozor na č.ev. a ulice ve městech.

## Čtení
- Do ~1800 latinská tištěná tabulka, pak německý kurent, od ~1850 česká tištěná forma. Úroveň 2 stačí na tištěné formuláře, na kurent úroveň 1 a zvětšit výřez.
- Povolání: výměnkář = starý hospodář na výměnku, chalupník/domkář malý majetek, podruh/nájemník bez půdy, havíř horník.
- Okrajové poznámky tužkou dávají data narození a sňatku rodičů (n = narozen, e = sňatek).
- Název obce a čp. se po generacích mění (přečíslování); čp. 28 ↔ 77 nebo 114 ↔ 14 může být chyba čtení.
