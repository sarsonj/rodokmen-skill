// Test přihlašovací brány pro Netlify (Edge Function) ze šablony skills/rodokmen/template/web/netlify/brana.sablona.js.
// Z kořene repozitáře: node --test tests/pozvanky/brana.test.mjs   (Node 18+, nic nestahuje)
// Šablonu vyplní stejně jako tools/export_web.py (otisk odpovědi, otisky klíčů) a pošle do ní vymyšlené požadavky
// s napodobeným kontextem Netlify (context.cookies.get, context.next).
import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

const sha = (t) => createHash("sha256").update(t).digest("hex");
const sablona = readFileSync(new URL("../../skills/rodokmen/template/web/netlify/brana.sablona.js", import.meta.url), "utf8");
const OTAZKA = sha("rodokmen:kovar");   // otisk, který po správné odpovědi uloží do cookie přihlašovací stránka

async function nacti(hash, klice) {
  const zdroj = sablona.replace("{{HASH}}", hash).replace("{{OTISKY}}", JSON.stringify(klice.map(sha)));
  assert.ok(!zdroj.includes("{{"), "šablona má nevyplněnou značku");
  return import("data:text/javascript," + encodeURIComponent(zdroj));
}

const OBOJI = await nacti(OTAZKA, ["abc", "def"]);
const JEN_OTAZKA = await nacti(OTAZKA, []);
const JEN_ODKAZY = await nacti("", ["abc"]);

const LOGIN = "<html>prihlaseni</html>";
globalThis.fetch = async (url) => {
  assert.equal(new URL(url).pathname, "/prihlaseni.html");
  return new Response(LOGIN);
};

async function pozadavek(brana, cesta, cookie) {
  let dal = false;
  const context = {
    cookies: { get: (n) => (n === "rodokmen" ? cookie : undefined) },
    next: async () => { dal = true; return new Response("web"); },
  };
  const res = await brana.default(new Request("https://rod.netlify.app" + cesta), context);
  return { res, dal, telo: await res.text() };
}

function pusti(r) {
  assert.equal(r.dal, true);
  assert.equal(r.telo, "web");
  assert.equal(r.res.headers.get("x-robots-tag"), "noindex, nofollow");
}

const SMAZAT = "rodokmen=; Max-Age=0; Path=/; HttpOnly; Secure; SameSite=Lax";

function odmitne(r, cookie) {
  assert.equal(r.res.status, 401);
  assert.equal(r.dal, false);
  assert.equal(r.telo, LOGIN);
  // neplatnou cookie (třeba zrušený klíč, HttpOnly) brána smaže, jinak by ji odpověď na otázku nepřepsala
  assert.equal(r.res.headers.get("set-cookie"), cookie ? SMAZAT : null);
  assert.equal(r.res.headers.get("cache-control"), "no-store");
  assert.equal(r.res.headers.get("x-robots-tag"), "noindex, nofollow");
}

test("cookie s otiskem odpovědi projde", async () => {
  pusti(await pozadavek(OBOJI, "/osoba/jan/", OTAZKA));
  pusti(await pozadavek(JEN_OTAZKA, "/osoba/jan/", OTAZKA));
});

test("cookie s klíčem z osobního odkazu projde", async () => {
  pusti(await pozadavek(OBOJI, "/osoba/jan/", "def"));
  pusti(await pozadavek(JEN_ODKAZY, "/", "abc"));
});

test("bez otázky nepustí prázdnou ani žádnou cookie", async () => {
  odmitne(await pozadavek(JEN_ODKAZY, "/", ""));
  odmitne(await pozadavek(JEN_ODKAZY, "/", undefined));
  odmitne(await pozadavek(JEN_ODKAZY, "/", sha("")), sha(""));
});

test("otisk klíče místo klíče v cookie nestačí", async () => {
  odmitne(await pozadavek(OBOJI, "/", sha("abc")), sha("abc"));
});

test("bez odkazů projde jen otázka", async () => {
  odmitne(await pozadavek(JEN_OTAZKA, "/", "abc"), "abc");
  odmitne(await pozadavek(JEN_OTAZKA, "/?k=abc"));
});

test("zrušený klíč ve staré cookie neplatí", async () => {
  odmitne(await pozadavek(JEN_ODKAZY, "/", "def"), "def");
});

test("cizí cookie a obrázek bez cookie: 401", async () => {
  odmitne(await pozadavek(OBOJI, "/", "jiny"), "jiny");
  odmitne(await pozadavek(OBOJI, "/img/a.jpg"));
});

test("platný klíč v adrese: cookie a přesměrování bez klíče", async () => {
  const { res, dal } = await pozadavek(OBOJI, "/?k=abc");
  assert.equal(res.status, 302);
  assert.equal(dal, false);
  assert.equal(res.headers.get("location"), "/");
  assert.equal(res.headers.get("set-cookie"), "rodokmen=abc; Max-Age=31536000; Path=/; HttpOnly; Secure; SameSite=Lax");
  assert.equal(res.headers.get("referrer-policy"), "no-referrer");
  assert.equal(res.headers.get("cache-control"), "no-store");
});

test("přesměrování zachová cestu a ostatní parametry", async () => {
  const { res } = await pozadavek(JEN_ODKAZY, "/osoba/jan/?k=abc&x=1");
  assert.equal(res.headers.get("location"), "/osoba/jan/?x=1");
});

for (const cesta of ["/?k=spatne", "/?k=", "/?k=a%20b", "/?k=" + OTAZKA]) {
  test(`neplatný klíč ${cesta.slice(0, 20)}: přihlašovací stránka 401`, async () => {
    odmitne(await pozadavek(OBOJI, cesta));
  });
}

test("neplatný klíč a platná cookie (otázka i odkaz): pustí, klíč z adresy zmizí", async () => {
  for (const cookie of [OTAZKA, "abc"]) {
    const { res, dal } = await pozadavek(OBOJI, "/osoba/jan/?k=stary", cookie);
    assert.equal(res.status, 302);
    assert.equal(dal, false);
    assert.equal(res.headers.get("location"), "/osoba/jan/");
    assert.equal(res.headers.get("set-cookie"), null);
  }
});

for (const cesta of ["//cizi.web/?k=abc", "/\\cizi.web/?k=abc", "///cizi.web/?k=abc", "/\\/cizi.web/?k=stary",
                     "//cizi.web/?k=stary"]) {
  test(`přesměrování zůstane na webu: ${cesta}`, async () => {
    const { res } = await pozadavek(OBOJI, cesta, OTAZKA);
    assert.equal(res.status, 302);
    const loc = res.headers.get("location");
    assert.ok(loc.startsWith("/") && !/^\/[\/\\]/.test(loc), loc);
    assert.equal(new URL(loc, "https://rod.netlify.app/").origin, "https://rod.netlify.app");
  });
}

test("přihlašovací stránka projde vždy", async () => {
  for (const b of [OBOJI, JEN_OTAZKA, JEN_ODKAZY]) {
    const { dal } = await pozadavek(b, "/prihlaseni.html");
    assert.equal(dal, true);
  }
});

test("brána běží na všech cestách", () => {
  assert.equal(OBOJI.config.path, "/*");
});

test("neplatný klíč v adrese i v cookie: 401 a stará cookie se smaže", async () => {
  odmitne(await pozadavek(OBOJI, "/?k=spatne", "zruseny"), "zruseny");
});

test("přihlašovací stránka smaže neplatnou cookie, platnou nechá", async () => {
  let r = await pozadavek(OBOJI, "/prihlaseni.html", "zruseny");
  assert.equal(r.dal, true);
  assert.equal(r.res.headers.get("set-cookie"), SMAZAT);
  for (const cookie of [OTAZKA, "abc", undefined]) {
    r = await pozadavek(OBOJI, "/prihlaseni.html", cookie);
    assert.equal(r.res.headers.get("set-cookie"), null);
  }
});
