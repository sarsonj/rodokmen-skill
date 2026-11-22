// Test třídění povolání pro stránku Statistiky (vymyšlené osoby a povolání, žádná skutečná data).
// Z kořene repozitáře:  node tests/povolani/test_povolani.mjs
import { sestavSkupiny, trid, pocetSlov, SKUPINY } from '../../skills/rodokmen/template/web/src/lib/povolani.js';

let chyby = 0;
const ma = (nazev, ok, detail = '') => { if (!ok) chyby++; console.log((ok ? 'OK   ' : 'CHYBA ') + nazev + (ok ? '' : '\n    ' + detail)); };

// každé povolání = jedna osoba; vrací { skupina → [povolání] } a řádky navíc
function zkus(povolani, cfg) {
  const osoby = povolani.map((t, i) => ({ slug: 'o' + i, facts: ['* 1800', 'povolání: ' + t] }));
  const r = trid(osoby, sestavSkupiny(cfg));
  const kam = {};
  for (const row of r.rows) for (const s of row.people) (kam[osoby.find((o) => o.slug === s).facts[1].slice(10)] ??= []).push(row.name);
  return { r, kam };
}
const skup = (kam, t) => (kam[t] || []).join(' | ');

// 1. tři jazyky
const PRIKLADY = [
  // [povolání, začátek názvu skupiny]
  ['sedlák', 'Sedláci'], ['Bauer', 'Sedláci'], ['agricola', 'Sedláci'],
  ['chalupník', 'Chalupníci'], ['Häusler', 'Chalupníci'], ['Gärtner', 'Chalupníci'], ['hortulanus', 'Chalupníci'],
  ['nádeník', 'Podruzi'], ['Tagelöhner', 'Podruzi'], ['Inwohner', 'Podruzi'], ['inquilinus', 'Podruzi'], ['Dienstmagd', 'Podruzi'],
  ['kovář', 'Kováři'], ['Hufschmied', 'Kováři'], ['faber ferrarius', 'Kováři'], ['faber', 'Kováři'],
  ['tkadlec', 'Tkalci'], ['Leinweber', 'Tkalci'], ['textor', 'Tkalci'],
  ['krejčí', 'Krejčí'], ['Schneider', 'Krejčí'], ['sartor', 'Krejčí'],
  ['švec', 'Ševci'], ['Schuhmacher', 'Ševci'], ['sutor', 'Ševci'],
  ['mlynář', 'Mlynáři'], ['Müller', 'Mlynáři'], ['molitor', 'Mlynáři'],
  ['zedník', 'Kameníci'], ['Maurer', 'Kameníci'], ['murarius', 'Kameníci'],
  ['truhlář', 'Tesaři'], ['Zimmermann', 'Tesaři'], ['faber lignarius', 'Tesaři'],
  ['řezník', 'Řezníci'], ['Fleischhauer', 'Řezníci'], ['pistor', 'Řezníci'],
  ['hostinský', 'Hostinští'], ['Gastwirt', 'Hostinští'], ['caupo', 'Hostinští'], ['Kaufmann', 'Hostinští'],
  ['voják', 'Vojáci'], ['Soldat', 'Vojáci'], ['miles', 'Vojáci'],
  ['horník', 'Horníci'], ['Bergmann', 'Horníci'], ['Kohlenbrenner', 'Horníci'], ['carbonarius', 'Horníci'],
  ['hajný', 'Lesníci'], ['Förster', 'Lesníci'], ['Fischer', 'Lesníci'], ['venator', 'Lesníci'],
  ['pastýř', 'Šafáři'], ['Hirt', 'Šafáři'], ['Schafhirt', 'Šafáři'], ['opilio', 'Šafáři'],
  ['formán', 'Doprava'], ['Fuhrmann', 'Doprava'], ['auriga', 'Doprava'],
  ['rychtář', 'Úředníci'], ['Richter', 'Úředníci'], ['scriba', 'Úředníci'],
  ['učitel', 'Učitelé'], ['Kirchendiener', 'Učitelé'], ['Totengräber', 'Učitelé'], ['kostelník', 'Učitelé'], ['parochus', 'Učitelé'],
  ['porodní bába', 'Lékaři'], ['Hebamme', 'Lékaři'], ['obstetrix', 'Lékaři'],
  ['Ausgedinger', 'Výměnkáři'], ['výměnkář', 'Výměnkáři'],
];
const { r: r1, kam } = zkus(PRIKLADY.map((x) => x[0]));
for (const [t, g] of PRIKLADY) {
  const got = kam[t] || [];
  ma(`„${t}“ → ${g}`, got.some((n) => n.startsWith(g)), `skupiny: ${got.join(' | ') || '(žádná)'}`);
}
ma('všechna povolání z příkladu jsou v nějaké skupině (žádný řádek navíc)', r1.rows.every((x) => !x.own), r1.rows.filter((x) => x.own).map((x) => x.name).join(', '));

// 2. nejednoznačnosti: faber lignarius není kovář, „Magdalena“ není služka, „Bürgermeister“ není měšťan
ma('„faber lignarius“ není mezi kováři', !skup(kam, 'faber lignarius').includes('Kováři'), skup(kam, 'faber lignarius'));
{
  const { kam: k } = zkus(['Magdalena', 'Bürgermeister', 'Wirtschafter', 'Hausknecht']);
  ma('„Magdalena“ není služebnictvo', !skup(k, 'Magdalena').includes('Podruzi'), skup(k, 'Magdalena'));
  ma('„Bürgermeister“ není měšťan', !skup(k, 'Bürgermeister').includes('Měšťané') && skup(k, 'Bürgermeister').includes('Úředníci'), skup(k, 'Bürgermeister'));
  ma('„Wirtschafter“ není hostinský', !skup(k, 'Wirtschafter').includes('Hostinští'), skup(k, 'Wirtschafter'));
  ma('„Hausknecht“ (složenina) je služebnictvo', skup(k, 'Hausknecht').includes('Podruzi'), skup(k, 'Hausknecht'));
}

// 3. neznámé povolání dostane vlastní řádek, nikdy se neztratí
{
  const osoby = [
    { slug: 'a', facts: ['* 1800', 'povolání: Kolovrátkář'] },
    { slug: 'b', facts: ['povolání: kolovrátkář (1850)'] },
    { slug: 'c', facts: ['povolání: Lampář, sedlák'] },     // jedna skupina sedí → neznámé „Lampář“ se nevytváří
    { slug: 'd', facts: ['povolání: Lampář'] },
    { slug: 'e', facts: ['povolání: Brusič skla; Kolovrátkář'] },
    { slug: 'f', facts: ['pomáhal rodičům', 'děti: Jan 1820', '† 1850', '× 1820', 'Matka: Marie'] },  // není povolání
  ];
  const r = trid(osoby, sestavSkupiny());
  const row = (n) => r.rows.find((x) => x.name === n);
  ma('neznámé „Kolovrátkář“ má vlastní řádek se 3 osobami (velikost písmen a závorka nevadí)', row('Kolovrátkář')?.people.length === 3, JSON.stringify(r.rows.map((x) => [x.name, x.people])));
  ma('neznámé „Lampář“ má vlastní řádek jen u osoby bez známé skupiny', row('Lampář')?.people.join() === 'd', JSON.stringify(row('Lampář')));
  ma('„Brusič skla“ (část za středníkem) má vlastní řádek', row('Brusič skla')?.people.join() === 'e');
  ma('osoba bez povolání se nepočítá (děti, ×, †, pomáhal …)', !r.rows.some((x) => x.people.includes('f')) && r.known === 5, `known=${r.known}`);
  ma('řádky navíc jsou označené own', row('Kolovrátkář')?.own === true && row('Sedláci, rolníci, statkáři')?.own === false);
}

// 4. konfigurace projektu
{
  const cfg = { skupiny: [
    { nazev: 'Kolovrátkáři', slova: ['kolovrátkář', 'Drehorgelspieler'] },           // nová skupina
    { nazev: 'mlynáři', slova: ['moučník'] },                                         // doplnění (název bez ohledu na velikost)
    { nazev: 'Vojáci a četníci', slova: ['legionář'], nahradit: true },                // přepsání
  ], odstranit: ['Žebráci a chudí'] };
  const { kam: k } = zkus(['Kolovrátkář', 'Drehorgelspieler', 'moučník', 'voják', 'legionář', 'žebrák'], cfg);
  ma('nová skupina z konfigurace', skup(k, 'Kolovrátkář') === 'Kolovrátkáři' && skup(k, 'Drehorgelspieler') === 'Kolovrátkáři', skup(k, 'Kolovrátkář'));
  ma('doplněná slova výchozí skupiny', skup(k, 'moučník') === 'Mlynáři', skup(k, 'moučník'));
  ma('nahrazená slova: nové platí, staré ne', skup(k, 'legionář') === 'Vojáci a četníci' && skup(k, 'voják') === 'Voják', `${skup(k, 'legionář')} / ${skup(k, 'voják')}`);
  ma('odstraněná skupina: povolání dostane vlastní řádek', skup(k, 'žebrák') === 'Žebrák');
  const g0 = sestavSkupiny();
  ma('bez konfigurace platí výchozí skupiny', g0.length === SKUPINY.length && sestavSkupiny({}).length === SKUPINY.length);
  ma('sestavSkupiny nemění výchozí seznam', SKUPINY.find((s) => s.nazev === 'Mlynáři').slova.cs.every((x) => x !== 'moučník'));
}

const n = pocetSlov();
console.log(`\nSkupin: ${SKUPINY.length}; slov česky ${n.cs}, německy ${n.de}, latinsky ${n.la}`);
console.log(chyby ? `\n${chyby} CHYB` : '\nVšechno prošlo.');
process.exit(chyby ? 1 : 0);
