// Snímkovač – seznam webů a jejich stav. Sdílí ho popup i service worker.
// stav: 'povoleno' = pasivní ukládání zobrazeného snímku je v pořádku (zapíná se samo / jedním klikem),
//       'zakazano' = server nástroje výslovně zakazuje (podle poznámek projektu),
//       'neznamo'  = nemáme ověřeno, že to server dovoluje → bráno jako NEPOVOLENO, zapnutí chce potvrzení.
// Nový web přidej do 'povoleno' až poté, co jsi přečetl jeho robots.txt a podmínky užití.
const WEBY = [
  { host: 'ebadatelna.soapraha.cz', nazev: 'eBadatelna SOA Praha', stav: 'povoleno', vestaveno: true,
    pozn: 'robots.txt (od 2. 11. 2026) blokuje nástroj projektu „rodokmen“ a skripty archiv odmítá; prohlížení v prohlížeči je v pořádku a rozšíření ukládá jen to, co sám zobrazíš.' },
  // MZA (ověřeno 14. 11. 2026): robots.txt Acta Publica nezakazuje; podmínky užití o nástrojích mlčí, ale zakazují
  // snímky zveřejňovat bez písemného souhlasu. Projekt (tools/slusne.py) skripty na MZA nepouští → bráno jako neověřené.
  { host: 'mza.cz', nazev: 'MZA Brno (Acta Publica)', stav: 'neznamo',
    pozn: 'robots.txt Acta Publica nezakazuje. Podmínky užití o nástrojích ani ukládání nic neříkají; zakazují ale snímky zveřejňovat nebo dál šířit bez písemného souhlasu vlastníka archiválií. Starší poznámky uvádějí blok IP po asi 45 snímcích za den (při čtení Claudem); při ručním prohlížení 14. 11. 2026 prošlo 118 snímků za 39 minut bez bloku.' },
  // SOA Třeboň (ověřeno 14. 11. 2026): robots.txt stránky digitálního archivu nezakazuje; nástroj projektu („rodokmen“)
  // archiv od 2. 11. 2026 odmítá (403), prohlížení v prohlížeči funguje. Podmínky užití analýza na stránce nenašla.
  { host: 'digi.ceskearchivy.cz', nazev: 'SOA Třeboň (Digitální archiv)', stav: 'neznamo',
    pozn: 'robots.txt prohlížení snímků nezakazuje; skripty archiv odmítá, prohlížeč funguje. Každé otevření snímku stáhne dlaždice znovu – na snímku vyřiď vše najednou.' },
  // Matricula Online (ověřeno 14. 11. 2026): podmínky užití dávají snímky pod licencí CC BY-NC-ND 2.0 (nekomerční kopírování
  // dovoleno, při zveřejnění informovat archiv / uvést odkaz). robots.txt zakazuje robotům procházet stránky snímků (?pg=)
  // a AI crawlerům (i ClaudeBot) celý web – to se týká automatického procházení, ne ručního prohlížení.
  // AHMP (ověřeno 14. 11. 2026): robots.txt katalogů (katalog.ahmp.cz, digi.ahmp.cz) i obrazového serveru zakazuje všem
  // robotům celý web; podmínky online katalogu nástroje ani ukládání neupravují. Badatelna dovoluje kopie vlastním zařízením
  // „pro osobní studijní potřebu“ (po souhlasu). → neověřené. Plátno nejde přečíst, ukládá se snímek viditelné části záložky.
  { host: 'katalog.ahmp.cz', nazev: 'AHMP – Praha Publica (starý katalog)', stav: 'neznamo',
    pozn: 'robots.txt zakazuje všem robotům celý katalog; podmínky online katalogu o nástrojích mlčí. Badatelna AHMP dovoluje kopie vlastním zařízením pro osobní studijní potřebu. Rozšíření ukládá jen snímek toho, co vidíš na obrazovce.' },
  { host: 'digi.ahmp.cz', nazev: 'AHMP – Praha Publica (nový katalog)', stav: 'neznamo',
    pozn: 'robots.txt zakazuje všem robotům celý katalog; podmínky online katalogu o nástrojích mlčí. Rozšíření ukládá jen snímek toho, co vidíš na obrazovce.' },
  { host: 'data.matricula-online.eu', nazev: 'Matricula Online', stav: 'povoleno',
    pozn: 'Snímky jsou pod licencí CC BY-NC-ND 2.0: ukládat pro vlastní bádání lze; zveřejnit jen nekomerčně, s uvedením zdroje a s informováním archivu. robots.txt zakazuje automatické procházení stránek snímků – listuj jen ručně.' }
];

function najdiWeb(hostname) {
  return WEBY.find(w => hostname === w.host || hostname.endsWith('.' + w.host)) || null;
}

function stavWebu(hostname) {
  const w = najdiWeb(hostname);
  return w ? w.stav : 'neznamo';
}
