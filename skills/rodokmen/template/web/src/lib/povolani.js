// Povolání pro stránku Statistiky: skupiny, klíčová slova a třídění. Čistý modul bez závislosti na datech webu
// (aby šel zkoušet samostatně: node tests/povolani/test_povolani.mjs).
//
// Tři vrstvy:
//  1. Široké skupiny inspirované hlavními skupinami klasifikace HISCO (zemědělství, řemesla, obchod, služby, doprava,
//     úřady a církev, armáda, těžba a hutě, zdravotnictví …) s klíčovými slovy česky, německy a latinsky – tak je
//     matriky píšou. Slova jsou jen názvy povolání, sestavená z veřejných slovníků a odborné literatury (viz ZDROJE).
//  2. Povolání, které žádná skupina nezná, se neztratí: dostane vlastní řádek podle textu („Kostelník“ …).
//  3. Projekt smí skupiny a slova doplnit nebo přepsat v data/web.json, položka „povolani“ (viz reference/web.md).
//
// ZDROJE slov (jen názvy povolání, nic se neopisuje):
//  - HISCO, Historical International Standard Classification of Occupations – hlavní skupiny: odborná a technická
//    povolání, správa a úřady, kancelářská práce, obchod, služby, zemědělci/rybáři/lovci/lesníci, výroba, doprava,
//    dělníci (iisg.amsterdam, History of Work; https://iisg.amsterdam/en/data/data-websites/history-of-work).
//  - WikiTree, Help:Glossary Czech (https://www.wikitree.com/wiki/Help:Glossary_Czech).
//  - FEEFHS, Czech word list (https://former.feefhs.org/guides/Czech-wordlist.pdf) – české, německé a anglické názvy
//    povolání z matrik.
//  - Běžná latinská a německá terminologie farních matrik 18.–19. století (příručky k čtení matrik, např. Archivní
//    správa, „Latinsko-německo-český slovníček pro čtení matrik“).
//
// Zápis slova (porovnává se bez ohledu na velikost písmen, vždy s kmenem, aby se chytily pády a rody):
//   „kovář“    slovo (kmen) začínající na začátku slova: kovář, kováře, kovářský …
//   „*schmied“ slovo se smí vyskytnout i uvnitř složeniny: Hufschmied, Kupferschmied
//   „magd$“    na konci slova musí slovo skončit (aby „magd“ nechytilo „Magdalena“)
//   „/regex/“  vlastní regulární výraz (bez ohraničení slova), když to jinak nejde
// Nejde-li o skupinu jednoznačně (např. latinské „pastor“ je pastýř i farář), slovo radši vynecháme –
// povolání se pak neztratí, objeví se jako vlastní řádek.

const w = (cs, de, la) => ({ cs, de, la });

/** Výchozí skupiny: { nazev, slova: { cs, de, la } }. */
export const SKUPINY = [
  { nazev: 'Sedláci, rolníci, statkáři', slova: w(
    ['sedlák', 'sedlač', 'rolník', 'rolnick', 'hospodář', 'statkář', 'velkostatkář', 'gruntovník', 'usedlík', 'zemědělec', 'zemědělsk', 'držitel'],
    ['bauer', 'ackerbauer', 'landwirt', 'gutsbesitzer', 'gutsherr', 'grundbesitzer', 'hofbesitzer', 'wirtschaftsbesitzer', 'ökonom', 'oekonom', 'landmann'],
    ['agricola', 'agricultor', 'rusticus', 'colonus', 'possessor', 'oeconomus', 'fundi possessor']) },
  { nazev: 'Chalupníci, domkáři, zahradníci (drobní držitelé)', slova: w(
    ['chalupník', 'domkář', 'čtvrtláník', 'půlláník', 'zahradník', 'zahrádkář', 'zahradnick'],
    ['häusler', 'kleinhäusler', 'chalupner', 'gärtner', 'kleinbauer', 'halbbauer', 'viertelbauer', 'viertellehner', 'halblehner', 'gaertner'],
    ['hortulanus', 'casarius']) },
  { nazev: 'Podruzi, nádeníci, čeleď a služebnictvo', slova: w(
    ['podruh', 'podruž', 'nádeník', 'čeledín', 'čeleď', 'služebn', 'služka', 'sluha', 'děvečka', 'pacholek', 'hospodyně', 'kuchařka', 'chůva', 'pradlena', 'posluhovačk', 'chovanec'],
    ['tagelöhner', 'taglöhner', 'inwohner', 'inmann', 'inlieger', 'dienstbote', 'dienstknecht', '*knecht', 'magd$', 'dienstmagd', 'dienstmädchen', 'hausgenoss', 'einwohner', 'köchin', 'kinderfrau', 'wäscherin', 'haushälterin'],
    ['inquilinus', 'mercenarius', 'famulus', 'famula', 'servus', 'serva', 'ancilla', 'operarius', 'jornalis', 'nutrix', 'coqua']) },
  { nazev: 'Výměnkáři a penzisté', slova: w(
    ['výměnkář', 'výminkář', 'vejminkář', 'vejměnek', 'důchodce', 'penzista'],
    ['ausgedinger', 'auszügler', 'ausnehmer', 'austrägler', 'altsitzer', 'pensionist'],
    ['emeritus', 'pensionista']) },
  { nazev: 'Kováři a kovodělci', slova: w(
    ['kovář', 'podkovář', 'zámečník', 'klempíř', 'kotlář', 'hřebíkář', 'nožíř', 'cvokař', 'pasíř', 'puškař', 'kovářsk'],
    ['*schmied', 'schlosser', 'spengler', 'klempner', 'nagler', 'zinngießer', 'büchsenmacher'],
    ['/(?<!\\p{L})faber(?! +(?:lign|mur|lapid|textor|sutor|tign))/', 'ferrarius', 'ferrari', 'fabri ferr', 'serrarius', 'faber ferr']) },
  { nazev: 'Tkalci a soukeníci', slova: w(
    ['tkadlec', 'tkadlc', 'tkalec', 'tkalc', 'soukeník', 'soukenick', 'přadlen', 'přadlák', 'plátenník', 'barvíř', 'valchář', 'punčochář', 'kloboučník', 'pletař'],
    ['*weber', 'tuchmacher', 'tuchscherer', 'spinner', 'färber', 'strumpfwirker', 'hutmacher', 'leinweber', 'weberei'],
    ['textor', 'pannifex', 'lanifex', 'tinctor', 'fullo', 'linifex']) },
  { nazev: 'Krejčí a švadleny', slova: w(
    ['krejčí', 'krejčovsk', 'švadlen', 'šička', 'módní'],
    ['*schneider', 'näherin', 'schneiderin'],
    ['sartor', 'sartrix']) },
  { nazev: 'Ševci, koželuzi a kožedělníci', slova: w(
    ['švec', 'ševc', 'ševcovsk', 'koželuh', 'kožišník', 'sedlář', 'řemenář', 'rukavičkář', 'tobolář'],
    ['schuster', 'schuhmacher', 'schuhmach', 'gerber', 'lederer', 'sattler', 'kürschner', 'riemer', 'schuhflicker'],
    ['sutor', 'coriarius', 'cerdo', 'pellio', 'sellarius', 'corrigiarius']) },
  { nazev: 'Mlynáři', slova: w(
    ['mlynář', 'mlynářsk', 'mlýnsk', 'mlynářsk'],
    ['müller', '*müller', 'mühlknappe', 'mahlmüller', 'müllerknecht'],
    ['molitor', 'molendinarius', 'molinarius', 'molendin']) },
  { nazev: 'Kameníci, zedníci a cihláři', slova: w(
    ['kameník', 'zedník', 'zednick', 'cihlář', 'štukatér', 'pokrývač', 'lomař', 'vápeník'],
    ['maurer', 'steinmetz', 'steinbrecher', 'ziegelbrenner', 'ziegler', 'dachdecker', 'kalkbrenner'],
    ['murarius', 'lapicida', 'caementarius', 'latomus', 'laterarius', 'faber murarius', 'faber lapidarius']) },
  { nazev: 'Tesaři, truhláři, bednáři a kováři kol', slova: w(
    ['tesař', 'truhlář', 'stolař', 'kolář', 'bednář', 'sudař', 'dřevař', 'soustružník', 'řezbář'],
    ['zimmermann', 'zimmerer', 'tischler', 'schreiner', 'wagner', 'binder', 'fassbinder', 'faßbinder', 'böttcher', 'drechsler', 'rädermacher', 'schnitzer'],
    ['carpentarius', 'lignarius', 'faber lignarius', 'tignarius', 'doliarius', 'cuparius', 'rotarius', 'tornator']) },
  { nazev: 'Řezníci, pekaři a cukráři', slova: w(
    ['řezník', 'pekař', 'uzenář', 'cukrář', 'perníkář', 'řeznick', 'pekařsk'],
    ['fleischhauer', 'fleischer', 'fleischhacker', 'metzger', 'selcher', 'bäcker', '*bäcker', 'konditor', 'lebzelter'],
    ['lanio', 'carnifex', 'macellarius', 'pistor', 'pistrinarius', 'panifex']) },
  { nazev: 'Hostinští, šenkýři a obchod', slova: w(
    ['šenkýř', 'hostinsk', 'hostinec', 'hospodsk', 'krčmář', 'výčepní', 'pivovarník', 'sladovník', 'palírník', 'kupec', 'obchodník', 'obchodní', 'trhovec', 'hokynář', 'kramář', 'handlíř', 'překupník', 'podomní'],
    ['*wirt$', 'wirtin$', 'gastwirt', 'schankwirt', 'schenker', 'kretschmer', 'brauer', 'bierbrauer', 'bräuer', 'branntweinbrenner', 'kaufmann', 'kaufleute', '*händler', 'krämer', 'hausierer', 'handelsmann'],
    ['caupo', 'cauponarius', 'tabernarius', 'propinator', 'braxator', 'cerevisiarius', 'mercator', 'institor', 'negotiator', 'caupona']) },
  { nazev: 'Ostatní řemesla (hrnčíři, sklenáři, hodináři, holiči, kominíci …)', slova: w(
    ['hrnčíř', 'sklář', 'sklenář', 'hodinář', 'knihař', 'tiskař', 'malíř', 'holič', 'provazník', 'svíčkař', 'mydlář', 'kominík', 'kuchař', 'řemeslník', 'varhanář', 'zlatník', 'hudebník', 'muzikant'],
    ['töpfer', 'hafner', 'glaser', 'glasmacher', 'uhrmacher', 'buchbinder', 'buchdrucker', 'seifensieder', 'seiler', 'rauchfangkehrer', 'kaminfeger', 'barbier', 'friseur', 'maler', 'goldschmied', 'musikant', 'musiker', 'handwerker'],
    ['figulus', 'vitrarius', 'horologiarius', 'bibliopegus', 'typographus', 'pictor', 'funarius', 'tonsor', 'cocus', 'artifex', 'musicus']) },
  { nazev: 'Vojáci a četníci', slova: w(
    ['voják', 'vojín', 'vojensk', 'pluk', 'důstojník', 'setník', 'četník', 'granátník', 'dragoun', 'husar', 'kanonýr', 'invalida', 'poručík'],
    ['soldat', 'militär', 'infanterist', 'husar', 'dragoner', 'kanonier', 'gendarm', 'feldwebel', 'korporal', 'grenadier', 'invalide', 'offizier', 'regiment', 'wachtmeister', 'unteroffizier'],
    ['miles$', 'milit', 'gregarius', 'caporalis', 'veteranus', 'centurio', 'tribunus', 'tormentarius']) },
  { nazev: 'Horníci, hutníci, uhlíři a dělníci', slova: w(
    ['horník', 'havíř', 'dělník', 'dělnice', 'továrn', 'tovární', 'hutník', 'uhlíř', 'kamenolom'],
    ['bergmann', 'bergknappe', 'bergarbeiter', 'knappe', 'hüttenarbeiter', 'hüttenmann', 'arbeiter', 'fabriksarbeiter', 'fabrikarbeiter', 'kohlenbrenner', 'köhler'],
    ['minerarius', 'metallifodinarius', 'carbonarius', 'fodinarius', 'fabricator']) },
  { nazev: 'Lesníci, myslivci, rybáři', slova: w(
    ['lesník', 'lesní', 'hajný', 'hajn', 'myslivec', 'polesn', 'revírník', 'lovec', 'dřevorubec', 'drvoštěp', 'rybář', 'rybníkář', 'voraři'],
    ['förster', 'jäger', 'heger', 'waldheger', 'holzhauer', 'holzknecht', 'holzfäller', 'forstwart', 'fischer', '*fischer', 'teichwärter', 'flößer'],
    ['forestarius', 'venator', 'piscator', 'lignator', 'custos silvae', 'silvicola']) },
  { nazev: 'Šafáři, ovčáci a pastýři', slova: w(
    ['šafář', 'ovčák', 'pastýř', 'pastevec', 'pasák', 'pasáček', 'koňař', 'kolmistr', 'volař', 'kravař', 'honák', 'včelař'],
    ['hirt', '*hirt', 'schäfer', 'schafhirt', 'kuhhirt', 'gänsehirt', 'schweinehirt', 'meier', 'schafmeister', 'pferdeknecht'],
    ['villicus', 'opilio', 'bubulcus', 'subulcus', 'porcarius', 'caprarius', 'pastor ovium', 'pastor gregis']) },
  { nazev: 'Doprava a pošta (formani, železničáři)', slova: w(
    ['železničář', 'výpravčí', 'strojvedoucí', 'topič', 'formán', 'forman', 'povozník', 'vozka', 'kočí', 'lodník', 'plavec', 'poštmistr', 'listonoš', 'poštovní', 'průvodčí', 'traťový', 'brzdař', 'drážní'],
    ['fuhrmann', '*fuhrmann', 'fuhrwerker', 'kutscher', 'postillon', 'postmeister', 'briefträger', 'bahn', 'eisenbahner', 'heizer', 'lokomotivführer', 'schiffer', 'zugführer'],
    ['auriga', 'vector', 'nauta', 'portitor', 'cursor', 'tabellarius', 'vehiculator']) },
  { nazev: 'Úředníci, rychtáři, písaři', slova: w(
    ['rychtář', 'písař', 'úředník', 'úřední', 'purkmistr', 'perkmistr', 'starosta', 'radní', 'konšel', 'soudce', 'právník', 'notář', 'advokát', 'účetní', 'ředitel', 'správce', 'berní', 'celník', 'obecní'],
    ['richter', 'schultheiß', 'schultheiss', 'bürgermeister', 'gemeindevorsteher', 'gemeindediener', 'schreiber', 'beamter', 'beamte', 'rentmeister', 'verwalter', 'amtmann', 'notar', 'advokat', 'rechtsanwalt', 'rechnungs', 'zöllner', 'amtsdiener'],
    ['judex', 'scriba', 'notarius', 'consul', 'praefectus', 'iudex', 'praetor', 'syndicus', 'provisor']) },
  { nazev: 'Učitelé, duchovní, kostelníci a hrobníci', slova: w(
    ['učitel', 'podučitel', 'řídící', 'kněz', 'farář', 'kaplan', 'děkan', 'biskup', 'duchovní', 'kostelník', 'hrobník', 'zvoník', 'varhaník', 'kantor', 'ministrant', 'student'],
    ['lehrer', 'schullehrer', 'oberlehrer', 'schulmeister', 'unterlehrer', 'pfarrer', 'kaplan', 'dechant', 'priester', 'kooperator', 'kirchendiener', 'kirchenvater', 'mesner', 'messner', 'küster', 'glöckner', 'totengräber', 'organist', 'kantor', 'student'],
    ['ludimagister', 'rector scholae', 'magister scholae', 'parochus', 'capellanus', 'sacerdos', 'presbyter', 'decanus', 'episcopus', 'cantor', 'organista', 'aedituus', 'custos', 'campanarius', 'sepulturarius', 'fossor$', 'studiosus']) },
  { nazev: 'Lékaři, lékárníci a porodní báby', slova: w(
    ['porodní', 'porodnic', 'bába porodní', 'babice', 'lékař', 'felčar', 'ranhojič', 'ranhoj', 'chirurg', 'lékárník', 'ošetřovatel', 'zdravotní', 'zvěrolékař'],
    ['hebamme', 'wehmutter', 'arzt', 'wundarzt', 'chirurg', 'apotheker', 'bader', 'krankenpfleger', 'krankenschwester', 'tierarzt', 'heilgehilfe'],
    ['obstetrix', 'medicus', 'chirurgus', 'pharmacopola', 'apothecarius', 'balneator', 'medicinae']) },
  { nazev: 'Měšťané, šlechta a soukromníci', slova: w(
    ['měšťan', 'měšťansk', 'šlechtic', 'rytíř', 'hrabě', 'svobodný pán', 'soukromník', 'rentiér', 'majitel domu', 'majitel realit'],
    ['bürger$', 'edler', 'ritter', 'graf$', 'freiherr', 'baron', 'privatier', 'rentier', 'realitätenbesitzer', 'hausbesitzer'],
    ['civis', 'nobilis', 'generosus', 'baro$', 'privatus', 'eques']) },
  { nazev: 'Žebráci a chudí', slova: w(
    ['žebrák', 'žebrav', 'almužn', 'chuďas', 'vandrák', 'tulák', 'starobinec', 'chudobinec'],
    ['bettler', 'almosen', 'pfründner', 'pfründler', 'armenhaus', 'vagabund', 'landstreicher'],
    ['mendicus', 'mendic', 'pauper', 'eleemosyn']) },
];

/** Text slova z klíčových slov → regulární výraz (viz zápis nahoře). */
function slovoRx(s) {
  const t = String(s).trim();
  if (t.length > 2 && t.startsWith('/') && t.endsWith('/')) return t.slice(1, -1);
  let begin = true, end = false, x = t;
  if (x.startsWith('*')) { begin = false; x = x.slice(1); }
  if (x.endsWith('$')) { end = true; x = x.slice(0, -1); }
  const esc = x.toLowerCase().replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/ +/g, '\\s+');
  return (begin ? '(?<![\\p{L}])' : '') + esc + (end ? '(?![\\p{L}])' : '');
}
export function slovaRx(slova) {
  const parts = slova.filter((s) => String(s).trim()).map(slovoRx);
  return parts.length ? new RegExp('(?:' + parts.join('|') + ')', 'iu') : /(?!)/;
}

const klic = (s) => String(s).trim().toLocaleLowerCase('cs');
const ploche = (s) => (Array.isArray(s) ? s : Object.values(s || {}).flat());

/**
 * Výchozí skupiny + úpravy projektu (data/web.json → „povolani“):
 *   { "skupiny": [ { "nazev": "Uhlíři", "slova": ["uhlíř", "Köhler"] },                 // nová skupina
 *                  { "nazev": "Mlynáři", "slova": ["moučník"] },                          // doplní slova do výchozí skupiny
 *                  { "nazev": "Vojáci a četníci", "slova": ["voják"], "nahradit": true } ],// slova výchozí skupiny nahradí
 *     "odstranit": ["Žebráci a chudí"] }                                                  // výchozí skupinu vypustí
 * Vrací [{ name, rx }].
 */
export function sestavSkupiny(cfg) {
  let g = SKUPINY.map((s) => ({ nazev: s.nazev, slova: ploche(s.slova) }));
  const out = (cfg && cfg.odstranit) || [];
  if (out.length) { const ox = new Set(out.map(klic)); g = g.filter((s) => !ox.has(klic(s.nazev))); }
  for (const u of (cfg && cfg.skupiny) || []) {
    if (!u || !u.nazev) continue;
    const slova = ploche(u.slova);
    const ex = g.find((s) => klic(s.nazev) === klic(u.nazev));
    if (ex) ex.slova = u.nahradit ? slova : [...ex.slova, ...slova];
    else g.push({ nazev: String(u.nazev).trim(), slova });
  }
  return g.map((s) => ({ name: s.nazev, rx: slovaRx(s.slova) }));
}

/** Počty slov výchozích skupin podle jazyků: { cs, de, la } (do statistiky a testů). */
export const pocetSlov = () => ({
  cs: SKUPINY.reduce((n, s) => n + s.slova.cs.length, 0),
  de: SKUPINY.reduce((n, s) => n + s.slova.de.length, 0),
  la: SKUPINY.reduce((n, s) => n + s.slova.la.length, 0),
});

/** Fakty, které nejsou povolání vlastní osoby (pomáhal, děti, rodina, svědek …). */
export const notOwn = /^(pomáhal|v domácnosti|sloužil|manželka|syn|dcera|děti|vdova|vdovec|z |ze |otec|matka|bratr|sestra|nemanželsk|kmotr|svědek)/iu;

/**
 * Rozdělení osob do skupin.
 * osoby: [{ slug, facts }] (jen zemřelé – žijící filtruje volající); skupiny: výstup sestavSkupiny().
 * Osoba se počítá ve všech skupinách, které sedí na některý její fakt. Když nesedí žádná, a osoba má fakt
 * „povolání: …“, dostane povolání vlastní řádek podle textu (nikdy se neztratí).
 * Vrací { known, rows: [{ name, rx, people: [slug], own }] } seřazené podle počtu osob.
 */
export function trid(osoby, skupiny) {
  const rows = skupiny.map((s) => ({ name: s.name, rx: s.rx, people: [], own: false }));
  const base = rows.length;
  let known = 0;
  for (const p of osoby) {
    const texts = (p.facts || []).filter((f) => !/^[*†×⚭]/.test(f) && !notOwn.test(f));
    if (!texts.length) continue;
    let hit = false;
    for (let i = 0; i < base; i++) {
      if (texts.some((f) => rows[i].rx.test(f))) { rows[i].people.push(p.slug); hit = true; }
    }
    if (!hit) {
      // povolání, které žádná skupina nezná: neztratí se, dostane vlastní řádek podle textu („Kostelník“ …)
      for (const f of (p.facts || []).filter((x) => /^povolání:/iu.test(x))) {
        for (const part of f.replace(/^povolání:\s*/iu, '').replace(/\s*\([^)]*\)/g, '').split(/[,;]/)) {
          const t = part.trim().replace(/\s+/g, ' ');
          if (!t) continue;
          const name = t.charAt(0).toLocaleUpperCase('cs') + t.slice(1);
          let r = rows.find((x, i) => i >= base && klic(x.name) === klic(name));
          if (!r) { r = { name, rx: /(?!)/, people: [], own: true }; rows.push(r); }
          if (!r.people.includes(p.slug)) r.people.push(p.slug);
          hit = true;
        }
      }
    }
    if (hit) known++;
  }
  return { known, rows: rows.filter((r) => r.people.length).sort((a, b) => b.people.length - a.people.length) };
}
