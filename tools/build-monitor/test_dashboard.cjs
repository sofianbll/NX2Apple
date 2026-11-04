const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {join} = require('node:path');
const vm = require('node:vm');

const html = readFileSync(join(__dirname, 'index.html'), 'utf8');
const context = vm.createContext({document: {addEventListener() {}}});
vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);
const run = source => JSON.parse(JSON.stringify(vm.runInContext(source, context)));
const game = (values = {}) => ({name:'Test game', title_id:'0000000000000000', slug:'test', state:'unsupported', files:{base:1,updates:0,dlc:0}, app:false, ...values});
const call = (name, ...args) => run(`${name}(${args.map(arg => JSON.stringify(arg)).join(',')})`);

test('one family for all Pokémon editions, French app selected even when English is first', () => {
  const rows = [game({group:'Pokémon FireRed',edition:'en'}),game({group:'Pokémon FireRed',edition:'fr',app:true,state:'experimental'})];
  const families = call('groupGames',rows);
  assert.equal(families.length,1);
  assert.equal(families[0].editions.length,2);
  assert.equal(families[0].game.edition,'fr');
});

test('an experimental app is not described as gameplay-verified', () => {
  const view = call('gameView',game({app:true,state:'experimental'}));
  assert.equal(view.label,'À tester en jeu');
  assert.equal(view.tone,'warning');
});

test('Stardew confirmation applies only to the current successful build', () => {
  const stardew = game({title_id:'0100E65002BB8000',app:true,state:'done'});
  assert.equal(call('gameView',stardew).label,'Jouable · confirmé');
  assert.equal(call('gameView',{...stardew,state:'available'}).label,'Application disponible');
});

test('Mario requires an update, not a repeat build of its 32-bit base', () => {
  const mario = game({title_id:'0100152000022000',state:'untested'});
  assert.equal(call('gameView',mario).label,'Mise à jour requise');
  assert.equal(call('gameCommand',mario),null);
  const updated = {...mario,files:{...mario.files,updates:1},state:'ready'};
  assert.equal(call('gameView',updated).label,'À compiler');
  assert.equal(call('gameCommand',updated),'make build GAME=test');
});

test('known Nintendo 64 failure does not suggest an integrity bypass or a blind retry', () => {
  const n64 = game({title_id:'0100C9A00ECE6000'});
  assert.equal(call('gameView',n64).label,'Analyse nécessaire');
  assert.equal(call('gameCommand',n64),null);
});

test('commands select the right edition, existing apps never get experimental build flags', () => {
  const pokemon = game({group:'Pokémon FireRed',edition:'en'});
  assert.equal(call('gameCommand',pokemon),'make build GAME=pokemon EDITION=en EXPERIMENTAL=1');
  assert.equal(call('gameCommand',{...pokemon,edition:'fr',app:true,state:'experimental'}),'make run GAME=pokemon EDITION=fr');
});

test('search ignores accents; availability filters count families, not languages', () => {
  const families = call('groupGames',[game({group:'Pokémon FireRed',edition:'fr',app:true}),game({group:'Pokémon FireRed',edition:'en'}),game({title_id:'0100152000022000'})]);
  assert.equal(call('visibleFamilies',families,'all','pokemon').length,1);
  assert.equal(call('visibleFamilies',families,'available','').length,1);
  assert.equal(call('visibleFamilies',families,'prepare','').length,1);
  assert.equal(call('visibleFamilies',families,'all','absent').length,0);
});

test('unknown titles and empty libraries remain usable without catalog artwork', () => {
  assert.equal(call('groupGames',[]).length,0);
  assert.equal(call('groupGames',[game()])[0].meta.title,'Test game');
  assert.equal(call('gameCommand',game({state:'running'})),null);
});

test('catalog ownership is unknown before the library loads, then matches Title IDs regardless of case', () => {
  vm.runInContext('data = null', context);
  assert.equal(run('ownedTitleIds()'),null);
  vm.runInContext('data = {games:[{title_id:"0100ABCDEF000000"}]}',context);
  assert.equal(run('ownedTitleIds().has("0100abcdef000000")'),true);
});

test('the compact progress card shows only a valid current-stage fraction, never a fabricated total', () => {
  assert.equal(call('stageFraction',{state:'running',stage_frac:.25}),.25);
  assert.equal(call('stageFraction',{state:'running',stage_frac:0}),0);
  for (const active of [null,{state:'running',stage_frac:null},{state:'running',stage_frac:2},{state:'done',stage_frac:1}]) {
    assert.equal(call('stageFraction',active),null);
  }
});

test('a catalogue fetch failure stays retryable instead of becoming an empty catalogue', async () => {
  let requests=0;
  const isolated=vm.createContext({
    document:{addEventListener(){},getElementById(){return {}; }},
    AbortSignal:{timeout(){}},
    fetch:async()=>{requests++;throw new Error('Offline');}
  });
  vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],isolated);
  vm.runInContext('renderCatalog = () => {}',isolated);
  await vm.runInContext('loadCatalog()',isolated);
  await vm.runInContext('loadCatalog()',isolated);
  assert.equal(requests,2);
  assert.equal(vm.runInContext('catalogGames',isolated),null);
});

// Isolated page with stubbed DOM, timers and network; no real fetch ever leaves the test.
function page(fetchImpl) {
  const elements = {};
  const context = vm.createContext({
    document: {addEventListener() {}, createElement: () => ({append() {}}), getElementById: id => elements[id] ??= {dataset: {}, replaceChildren() {}, showModal() {}, close() {}}},
    AbortSignal: {timeout() {}}, setTimeout: (fn, ms) => setTimeout(fn, ms).unref(), clearTimeout,
    fetch: fetchImpl,
  });
  vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);
  return {context, elements, eval: source => vm.runInContext(source, context)};
}
const pokemon = (edition, extra = {}) => game({group: 'Pokémon FireRed', edition, slug: `pokemon-${edition}`, app: true, state: 'experimental', ...extra});

test('canPlay needs an Mac app that is not building, and no running build', () => {
  assert.equal(call('canPlay', game({app: true, state: 'done'}), null), true);
  assert.equal(call('canPlay', game({app: false}), null), false);
  assert.equal(call('canPlay', game({app: true, state: 'running'}), null), false);
  assert.equal(call('canPlay', game({app: true, state: 'done'}), {state: 'running'}), false);
  assert.equal(call('canPlay', game({app: true, state: 'done'}), {state: 'done'}), true);
  assert.equal(call('canPlay', null, null), false);
});

test('pills never promise more than the game view: only the confirmed Stardew is ready', () => {
  assert.deepEqual(call('pillOf', game({title_id: '0100E65002BB8000', app: true, state: 'done'})), {status: 'ready', label: 'Jouable'});
  assert.deepEqual(call('pillOf', game({app: true, state: 'experimental'})), {status: 'test', label: 'À tester'});
  assert.deepEqual(call('pillOf', game({app: true, state: 'running'})), {status: 'compiling', label: 'Construction'});
  assert.deepEqual(call('pillOf', game({files: {base: 0, updates: 0, dlc: 0}})), {status: 'test', label: 'Base manquante'});
});

test('the build card exists only for a running build and carries only the current stage fraction', () => {
  const stages = [{index: 1, name: 'Extraire', status: 'done'}, {index: 2, name: 'Compiler', status: 'current'}];
  const running = extra => ({state: 'running', current: 2, total: 5, stages, ...extra});
  assert.deepEqual(call('buildCardState', running({stage_frac: 0.25})), {name: 'Compiler', progress: 0.25});
  assert.deepEqual(call('buildCardState', running({stage_frac: 0})), {name: 'Compiler', progress: 0});
  assert.deepEqual(call('buildCardState', running({stage_frac: 1})), {name: 'Compiler', progress: 1});
  for (const stage_frac of [undefined, null, 2, -0.1]) assert.equal(call('buildCardState', running({stage_frac})).progress, null);
  assert.equal(call('buildCardState', running({current: 9, stage_frac: 0.5})).name, 'Préparation');
  for (const state of ['done', 'stopped', 'error']) assert.equal(call('buildCardState', {state, current: 5, total: 5, stages, stage_frac: 0.5}), null);
  assert.equal(call('buildCardState', null), null);
});

test('selection keeps a visible family, else prefers the confirmed Stardew, then any app, then the first', () => {
  const families = call('groupGames', [game({title_id: '0100E65002BB8000', app: true, state: 'done'}), game({title_id: '01006BB00C6F0000', app: true}), game({title_id: '0100152000022000'})]);
  assert.equal(call('pickFamily', families, '01006BB00C6F0000').id, '01006BB00C6F0000');
  assert.equal(call('pickFamily', families, 'missing').id, '0100E65002BB8000');
  assert.equal(call('pickFamily', families.slice(2), 'missing').id, '0100152000022000');
  assert.equal(call('pickFamily', [], 'x'), null);
});

test('Play posts the exact slug of the selected edition, not the family default', async () => {
  const requests = [];
  const p = page(async (url, options) => {requests.push({url, options}); return {ok: true, status: 200, json: async () => ({ok: true})};});
  p.context.rows = [pokemon('fr'), pokemon('en')];
  p.eval('families = groupGames(rows); selectedFamilyId = "Pokémon FireRed"; selectedEdition = {"Pokémon FireRed": "en"}');
  assert.equal(p.eval('selectedGame().slug'), 'pokemon-en');
  await p.eval('playGame(selectedGame())');
  assert.equal(requests.length, 1);
  assert.equal(requests[0].url, '/play');
  assert.equal(requests[0].options.method, 'POST');
  assert.deepEqual({...requests[0].options.headers}, {'Content-Type': 'application/json'});
  assert.equal(requests[0].options.body, JSON.stringify({slug: 'pokemon-en'}));
  assert.equal(p.elements.toast.textContent, 'Ouverture demandée à macOS');
});

test('a double click sends one request, then Play is available again', async () => {
  let requests = 0, release;
  const p = page(() => {requests++; return new Promise(resolve => {release = () => resolve({ok: true, status: 200, json: async () => ({ok: true})});});});
  const target = game({app: true, state: 'done', slug: 'stardew'});
  p.context.target = target;
  const first = p.eval('playGame(target)'), second = p.eval('playGame(target)');
  assert.equal(p.eval('playBusy'), true);
  release();
  await Promise.all([first, second]);
  assert.equal(requests, 1);
  assert.equal(p.eval('playBusy'), false);
});

test('Play never calls the network when it is not allowed', async () => {
  let requests = 0;
  const p = page(async () => {requests++;});
  p.context.apps = [game({app: false, slug: 'a'}), game({app: true, state: 'running', slug: 'b'})];
  for (const index of [0, 1]) await p.eval(`playGame(apps[${index}])`);
  p.eval('data = {active: {state: "running"}, games: []}');
  p.context.ok = game({app: true, state: 'done', slug: 'c'});
  await p.eval('playGame(ok)');
  assert.equal(requests, 0);
});

test('Play reports server errors and treats network failures as unconfirmed, never as success', async () => {
  const outcomes = [
    {ok: false, status: 500, json: async () => ({error: 'App introuvable'})},
    {ok: false, status: 502, json: async () => {throw new Error('not json');}},
    {ok: true, status: 200, json: async () => ({})},
    new Error('timeout'),
  ];
  const p = page(async () => {const next = outcomes.shift(); if (next instanceof Error) throw next; return next;});
  p.context.target = game({app: true, state: 'done', slug: 'stardew'});
  const messages = [];
  for (let i = 0; i < 4; i++) {await p.eval('playGame(target)'); messages.push(p.elements.toast.textContent);}
  assert.equal(messages[0], 'App introuvable');
  assert.equal(messages[1], 'Ouverture refusée (HTTP 502).');
  assert.match(messages[2], /^Ouverture non confirmée/);
  assert.match(messages[3], /^Ouverture non confirmée.*avant de réessayer/);
  assert.equal(p.eval('playBusy'), false);
});

const profile = (extra = {}) => ({name: 'Absolum', title_id: '0100ABCDEF000000', build: '1.1.2', sdk: '18.3.2', engine: 'FNA / .NET', graphics: 'NVN', art: '/art/catalog/0100ABCDEF000000.jpg', art_kind: 'cover', ...extra});

const catalog = (profiles, owned, filter, query) => {
  context.profilesUnderTest = profiles;
  return run(`visibleCatalog(profilesUnderTest,${owned ? `new Set(${JSON.stringify(owned)})` : 'null'},${JSON.stringify(filter)},${JSON.stringify(query)})`);
};

test('catalogue filters: ownership is unknown until the library loads, then splits owned and new', () => {
  const profiles = [profile(), profile({name: 'Baba Is You', title_id: '0100000000000001', engine: 'Multimedia Fusion'})];
  const owned = ['0100abcdef000000'];
  assert.equal(catalog(profiles, null, 'all', '').length, 2);
  assert.equal(catalog(profiles, null, 'owned', '').length, 0);
  assert.equal(catalog(profiles, null, 'new', '').length, 0);
  assert.deepEqual(catalog(profiles, owned, 'owned', '').map(g => g.name), ['Absolum']);
  assert.deepEqual(catalog(profiles, owned, 'new', '').map(g => g.name), ['Baba Is You']);
});

test('catalogue search ignores accents and matches title, Title ID and engine', () => {
  const profiles = [profile({name: 'Pokémon Écarlate'}), profile({name: 'Baba', title_id: '0100000000000001', engine: 'Multimédia Fusion'})];
  assert.equal(catalog(profiles, null, 'all', 'POKEMON ecarlate').length, 1);
  assert.equal(catalog(profiles, null, 'all', '0100000000000001').length, 1);
  assert.equal(catalog(profiles, null, 'all', 'multimedia').length, 1);
  assert.equal(catalog(profiles, null, 'all', 'absent').length, 0);
});

test('catalogue art: only the strict local route is used, and only art_kind cover is called a cover', () => {
  assert.deepEqual(call('catalogArt', profile()), {src: '/art/catalog/0100ABCDEF000000.jpg', kind: 'cover'});
  assert.equal(call('catalogArt', profile({art_kind: 'screenshot'})).kind, 'screenshot');
  assert.equal(call('catalogArt', profile({art_kind: null})).kind, 'screenshot');
  for (const art of [null, '', 'https://example.com/x.jpg', '//evil/x.jpg', '/art/stardew.jpg', '/art/catalog/../x.jpg', 'javascript:alert(1)']) assert.equal(call('catalogArt', profile({art})), null);
});

test('a profile finds its library family and edition by Title ID; an unknown profile has no library link', () => {
  const rows = [game({title_id: '01004B3023412000', group: 'Pokémon FireRed', edition: 'fr'}), game({title_id: '0100E65002BB8000'})];
  assert.deepEqual(call('libraryTarget', rows, '01004b3023412000'), {familyId: 'Pokémon FireRed', edition: 'fr'});
  assert.deepEqual(call('libraryTarget', rows, '0100e65002bb8000'), {familyId: '0100E65002BB8000', edition: null});
  assert.equal(call('libraryTarget', rows, '0100000000000001'), null);
  assert.equal(call('libraryTarget', null, '0100000000000001'), null);
  const unknown = call('profileView', profile(), rows);
  assert.equal(unknown.library, null);
  assert.equal(unknown.label, 'Profil référencé');
  assert.ok(unknown.facts.includes('SDK : 18.3.2'));
  assert.equal(call('profileView', profile({title_id: '0100E65002BB8000'}), rows).label, 'Dans la bibliothèque');
});

test('selecting a catalogue profile opens a read-only sheet and never touches the network', async () => {
  let requests = 0;
  const p = page(async () => {requests++;});
  p.context.profiles = [profile()];
  p.eval('catalogGames = profiles; data = {games: []}');
  p.eval('openProfile("0100ABCDEF000000")');
  assert.equal(p.elements['profile-library'].hidden, true);
  assert.equal(p.elements['profile-title'].textContent, 'Absolum');
  assert.equal(requests, 0);
  p.eval('openProfile("missing")');  // unknown id: nothing happens
  assert.equal(p.elements['profile-title'].textContent, 'Absolum');
});

test('the 2 s status poll does not rebuild the catalogue grid unless the visible inventory changes', () => {
  let rebuilds = 0;
  const element = () => ({dataset: {}, classList: {toggle() {}, contains: () => false, add() {}}, append() {}, setAttribute() {}, removeAttribute() {}, replaceChildren() {}});
  const elements = {};
  const context = vm.createContext({
    document: {addEventListener() {}, querySelectorAll: () => [], createElement: element, getElementById: id => elements[id] ??= element()},
    AbortSignal: {timeout() {}}, fetch: async () => {},
  });
  vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);
  elements['catalog-games'] = {...element(), replaceChildren() {rebuilds++;}};
  const p = {eval: source => vm.runInContext(source, context)};
  context.profiles = [profile({art: null, art_kind: null})];
  p.eval('catalogGames = profiles; data = null');
  p.eval('renderCatalog(); renderCatalog(); renderCatalog()');
  assert.equal(rebuilds, 1);                                   // unchanged: no DOM rebuild, no image reload
  p.eval('data = {games: [{title_id: "0100ABCDEF000000"}]}; renderCatalog(); renderCatalog()');
  assert.equal(rebuilds, 2);                                   // ownership went unknown -> loaded: one rebuild
  p.eval('catalogQuery = "abs"; renderCatalog(); renderCatalog()');
  assert.equal(rebuilds, 3);                                   // search change: one rebuild
  p.eval('catalogGames = [...profiles]; catalogKey = ""; renderCatalog()');
  assert.equal(rebuilds, 4);                                   // fresh /catalog response forces a rebuild
});

test('Jouer is greyed out with a reason when there is no app or a build is running, and never for a ready game', () => {
  const ready = game({app: true, state: 'done'});
  assert.equal(call('playBlock', ready, null), '');
  assert.equal(call('playBlock', ready, {state: 'done'}), '');
  assert.equal(call('playBlock', game({app: false}), null), 'Application Mac absente');
  assert.match(call('playBlock', ready, {state: 'running'}), /fin de la construction/);
  assert.match(call('playBlock', game({app: true, state: 'running'}), null), /fin de la construction/);
});

test('tiles use the dedicated square cover first; hero and fiche keep their wide art', () => {
  const families = ['0100E65002BB8000', '01006BB00C6F0000', 'Pokémon FireRed', '0100152000022000', '0100C9A00ECE6000'];
  const covers = families.map(id => run(`coverSource(CATALOG[${JSON.stringify(id)}])`));
  assert.equal(new Set(covers).size, 5);
  for (const [i, id] of families.entries()) {
    assert.match(covers[i], /^\/art\/(?:catalog|library)\/[0-9A-F]{16}\.jpg$/);
    assert.notEqual(covers[i], run(`artSource(CATALOG[${JSON.stringify(id)}])`));  // wide art stays a separate asset
  }
  assert.equal(run('CATALOG["0100E65002BB8000"].heroSrc'), '/art/stardew-hero.png');
  assert.equal(call('coverSource', {art: 'zelda'}), '/art/zelda.jpg');                // no dedicated cover: wide art
  assert.equal(call('coverSource', {title: 'Unknown'}), '');                          // unknown game: placeholder
});

test('a failed tile image is retried once on the tile itself, then replaced by a text placeholder', () => {
  const timers = [], listeners = {}, attributes = [], classes = new Set();
  const context = vm.createContext({
    document: {addEventListener() {}, createElement: () => ({append() {}})},
    setTimeout: fn => timers.push(fn),
  });
  vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);
  Object.assign(context, {
    cell: {isConnected: true, append() {}, classList: {contains: name => classes.has(name), add: name => classes.add(name)}},
    tile: {shadowRoot: {querySelector: () => ({addEventListener: (type, fn) => {listeners[type] = fn;}})}, setAttribute: (name, value) => attributes.push([name, value]), removeAttribute: name => attributes.push([name, null])},
  });
  vm.runInContext('setTileArt(cell, tile, "Zelda", "/art/catalog/X.jpg", "")', context);
  assert.deepEqual(attributes, [['src', '/art/catalog/X.jpg']]);   // a single load, no probe image
  listeners.error();                                                // first failure: retry later
  assert.equal(timers.length, 1);
  assert.equal(classes.has('no-art'), false);
  timers[0]();
  assert.deepEqual(attributes.at(-1), ['src', '/art/catalog/X.jpg']);
  listeners.error();                                                // second failure: placeholder
  assert.equal(classes.has('no-art'), true);
  assert.deepEqual(attributes.at(-1), ['src', null]);
});

test('detail art: wide art stays 16:9, a lone square cover stays square, captures are contained', () => {
  assert.deepEqual(call('detailArt', {art: 'zelda', coverSrc: '/art/catalog/01006BB00C6F0000.jpg'}), {src: '/art/zelda.jpg', kind: 'wide'});
  assert.deepEqual(call('detailArt', {coverSrc: '/art/catalog/0100ABCDEF000000.jpg'}), {src: '/art/catalog/0100ABCDEF000000.jpg', kind: 'square'});
  assert.equal(call('detailArt', {title: 'Unknown'}), null);
  assert.equal(call('profileFrame', {src: 'x', kind: 'cover'}), 'square');
  assert.equal(call('profileFrame', {src: 'x', kind: 'screenshot'}), 'contain');
});

const DUMMY = 'https://drive.example.test/shared/item';
function links(initial, failWrites = false) {
  const store = new Map(initial ? [['nxnative-download-links', initial]] : []);
  let requests = 0;
  const context = vm.createContext({
    document: {addEventListener() {}}, URL, fetch: async () => {requests++;},
    localStorage: {getItem: key => store.get(key) ?? null, setItem: (key, value) => {if (failWrites) throw new Error('quota'); store.set(key, value);}},
  });
  vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);
  return {store, requests: () => requests, eval: source => JSON.parse(JSON.stringify(vm.runInContext(source, context) ?? null))};
}

test('download link validation: https only, no credentials, empty removes', () => {
  const l = links();
  assert.equal(l.eval(`cleanDownloadUrl(${JSON.stringify(DUMMY)})`), DUMMY);
  assert.equal(l.eval('cleanDownloadUrl("  ")'), '');
  for (const bad of ['http://drive.example.test/x', 'javascript:alert(1)', 'data:text/html,x', 'file:///etc/hosts', 'https://user:pw@drive.example.test/x', 'https://user@drive.example.test/x', 'drive.example.test/x', 'not a url', 'https://' + 'a'.repeat(2100)]) {
    assert.equal(l.eval(`cleanDownloadUrl(${JSON.stringify(bad)})`), null, bad.slice(0, 20));
  }
  assert.equal(l.eval('canonicalTitleId("0100e65002bb8000")'), '0100E65002BB8000');
  for (const bad of ['', null, '0100E65002BB800', '0100E65002BB80000', 'ZZZZE65002BB8000']) assert.equal(l.eval(`canonicalTitleId(${JSON.stringify(bad)})`), null);
});

test('download links are stored per Title ID, so each edition has its own, under a canonical key', () => {
  const l = links();
  assert.deepEqual(l.eval(`saveDownloadLink("01004b3023412000", ${JSON.stringify(DUMMY + '-fr')})`), {ok: true, url: DUMMY + '-fr'});
  assert.equal(l.eval(`saveDownloadLink("0100554023408000", ${JSON.stringify(DUMMY + '-en')}).ok`), true);
  assert.deepEqual(JSON.parse(l.store.get('nxnative-download-links')), {'01004B3023412000': DUMMY + '-fr', '0100554023408000': DUMMY + '-en'});
  assert.equal(l.eval('downloadLink("01004B3023412000")'), DUMMY + '-fr');
  assert.equal(l.eval('downloadLink("0100554023408000")'), DUMMY + '-en');
  assert.equal(l.eval('downloadLink("0100000000000001")'), '');
  assert.equal(l.eval('saveDownloadLink("not-an-id", "https://drive.example.test/x").ok'), false);
  assert.equal(l.requests(), 0);                                   // never fetched
});

test('an invalid link keeps the previous one; an empty value removes it; a failed write is reported', () => {
  const l = links();
  l.eval(`saveDownloadLink("0100E65002BB8000", ${JSON.stringify(DUMMY)})`);
  const refused = l.eval('saveDownloadLink("0100E65002BB8000", "javascript:alert(1)")');
  assert.equal(refused.ok, false);
  assert.match(refused.error, /https/);
  assert.equal(l.eval('downloadLink("0100E65002BB8000")'), DUMMY);
  assert.deepEqual(l.eval('saveDownloadLink("0100E65002BB8000", "")'), {ok: true, url: ''});
  assert.equal(l.eval('downloadLink("0100E65002BB8000")'), '');
  const broken = links(JSON.stringify({'0100E65002BB8000': DUMMY}), true);
  const failed = broken.eval(`saveDownloadLink("0100E65002BB8000", ${JSON.stringify(DUMMY + '-new')})`);
  assert.equal(failed.ok, false);
  assert.match(failed.error, /n’a pas été conservé/);
  assert.equal(broken.eval('downloadLink("0100E65002BB8000")'), DUMMY);   // no false confirmation: old value still read
});

test('stored links are re-validated on read: corrupt data and unsafe entries are ignored', () => {
  assert.deepEqual(links('{broken').eval('readLinks()'), {});
  const l = links(JSON.stringify({'0100E65002BB8000': DUMMY, 'bad-key': DUMMY, '0100000000000001': 'javascript:alert(1)', '0100000000000002': 42}));
  assert.deepEqual(l.eval('readLinks()'), {'0100E65002BB8000': DUMMY});
});

test('runtime labels are separate from build state and never create a gameplay confirmation', () => {
  const ready = game({title_id:'0100E65002BB8000',app:true,state:'done',runtime:{state:'running'}});
  assert.equal(call('gameView',ready).label,'Jouable · confirmé');
  assert.deepEqual(call('runtimeView',ready),{label:'Jeu ouvert',tone:'info'});
  assert.equal(call('runtimeView',{runtime:{state:'launcher'}}).label,'Menu ouvert');
  assert.equal(call('runtimeView',{runtime:{state:'unknown'}}).label,'État du jeu inconnu');
  assert.equal(call('runtimeView',{runtime:{state:'stopped'}}),null);
  assert.equal(call('runtimeView',{}),null);
});

test('Play remains legacy-compatible without runtime, but is blocked by a menu, a game or an unknown runtime', () => {
  const ready = game({app:true,state:'done'});
  assert.equal(call('canPlay',ready,null),true);
  for (const state of ['launcher','running','unknown']) {
    assert.equal(call('canPlay',{...ready,runtime:{state}},null),false,state);
    assert.ok(call('playBlock',{...ready,runtime:{state}},null));
  }
  assert.equal(call('canPlay',{...ready,runtime:{state:'stopped'}},null),true);
  assert.equal(call('playBlock',{...ready,runtime:{state:'stopped'}},null),'');
});

function fakeElement(tag = 'div') {
  const listeners = {};
  return {
    tagName:tag.toUpperCase(),children:[],dataset:{},classList:{add(){},remove(){},toggle(){},contains(){return false;}},
    hidden:false,disabled:false,value:'',checked:false,textContent:'',title:'',
    append(...nodes){this.children.push(...nodes);},
    replaceChildren(...nodes){this.children=[...nodes];},
    addEventListener(type,fn){(listeners[type] ??= []).push(fn);},
    dispatch(type,event={}){for(const fn of listeners[type] || [])fn({preventDefault(){},...event});},
    setAttribute(name,value){this[name]=String(value);},removeAttribute(name){delete this[name];},
  };
}
function settingsPage(fetchImpl, store = new Map(), failWrites = false) {
  const elements = {};
  const context = vm.createContext({
    document:{addEventListener(){},createElement:tag=>fakeElement(tag),getElementById:id=>elements[id] ??= fakeElement(id)},
    localStorage:{getItem:key=>store.get(key) ?? null,setItem:(key,value)=>{if(failWrites)throw new Error('quota');store.set(key,value);}},
    AbortSignal:{timeout(){}},fetch:fetchImpl,URL,URLSearchParams,setTimeout,clearTimeout,
  });
  vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],context);
  vm.runInContext('settingsPanel = settingsBox()',context);
  return {context,elements,store,eval:source=>vm.runInContext(source,context)};
}
const response = (body,status=200) => ({ok:status>=200&&status<300,status,json:async()=>body});
const nativeSettings = (values={}) => ([
  {env:'DM_FULLSCREEN',kind:'choice',section:'Game',label:'Display mode',note:'',default:'0',options:[['0','Window'],['1','Fullscreen']],value:values.DM_FULLSCREEN || '0',locked:false},
  {env:'DM_RUMBLE',kind:'toggle',section:'Controls',label:'Game rumble',note:'',default:'1',on:'1',off:'0',value:'1',locked:false},
  {env:'DM_RUMBLE_GAIN',kind:'range',section:'Controls',label:'Rumble strength',note:'',default:'1.0',min:0,max:3,step:.1,needs:'DM_RUMBLE=1',value:'1.0',locked:false},
  {env:'DM_METAL_HUD',kind:'toggle',section:'Performance',label:'Performance HUD',note:'',default:'0',on:'1',off:'0',value:'1',locked:true},
]);
const settingsBody = (slug='test',values={}) => ({slug,settings:nativeSettings(values),runtime:{state:'stopped'}});

test('menu choice is validated, persists per Title ID across reloads, and only an explicit choice changes Play payload', () => {
  const store = new Map();
  const first = settingsPage(async()=>{throw new Error('unexpected fetch');},store);
  assert.equal(first.eval('launchMenuChoice("0100E65002BB8000")'),null);
  assert.deepEqual(JSON.parse(first.eval('JSON.stringify(playPayload({slug:"Pokémon FR",title_id:"0100E65002BB8000"}))')),{slug:'Pokémon FR'});
  assert.equal(store.has('nxnative-launch-menu'),false);  // displaying the default writes nothing
  assert.equal(first.eval('saveLaunchMenuChoice("0100e65002bb8000",false).ok'),true);
  const reloaded = settingsPage(async()=>{throw new Error('unexpected fetch');},store);
  assert.equal(reloaded.eval('launchMenuChoice("0100E65002BB8000")'),false);
  assert.deepEqual(JSON.parse(reloaded.eval('JSON.stringify(playPayload({slug:"Pokémon FR",title_id:"0100E65002BB8000"}))')),{slug:'Pokémon FR',show_launcher:false});
  assert.equal(reloaded.eval('saveLaunchMenuChoice("bad",true).ok'),false);
  const broken = settingsPage(async()=>{throw new Error('unexpected fetch');},store,true);
  const failed = broken.eval('saveLaunchMenuChoice("0100E65002BB8000",true)');
  assert.equal(failed.ok,false);assert.match(failed.error,/n’a pas été conservé/);
  assert.equal(broken.eval('launchMenuChoice("0100E65002BB8000")'),false);
});

test('settings client validates kinds, clamps ranges, keeps unknown needs visible and sends default spelling', () => {
  const result=call('readSettingsResponse',settingsBody(),'test');
  assert.equal(result.values.DM_RUMBLE_GAIN,'1');
  const draft={...result.values,DM_FULLSCREEN:'1',DM_RUMBLE_GAIN:'99',DM_METAL_HUD:'0'};
  assert.deepEqual(call('changedSettings',result.settings,draft,result.values),{DM_FULLSCREEN:'1',DM_RUMBLE_GAIN:'3'});
  assert.equal(call('settingVisible',result.settings[2],result.settings,{DM_RUMBLE:'0'}),false);
  assert.equal(call('settingVisible',{needs:'DM_UNKNOWN=1'},result.settings,{DM_RUMBLE:'0'}),true);
  assert.equal(call('changedSettings',result.settings,{...result.values,DM_RUMBLE_GAIN:'1'},{...result.values,DM_RUMBLE_GAIN:'2'}).DM_RUMBLE_GAIN,'1.0');
});

test('settings save needs an explicit stopped runtime, an app, no build and a dirty unlocked draft', () => {
  const app=game({app:true,state:'done'});
  assert.equal(call('canSaveSettings',app,null,{state:'stopped'},true,false),true);
  for (const state of ['launcher','running','unknown']) assert.equal(call('canSaveSettings',app,null,{state},true,false),false);
  assert.equal(call('canSaveSettings',app,null,null,true,false),false);
  assert.equal(call('canSaveSettings',app,{state:'running'},{state:'stopped'},true,false),false);
  assert.equal(call('canSaveSettings',app,null,{state:'stopped'},false,false),false);
  assert.equal(call('canSaveSettings',app,null,{state:'stopped'},true,true),false);
  assert.equal(call('canSaveSettings',{...app,app:false},null,{state:'stopped'},true,false),false);
});

test('settings GET runs only for an open app sheet, escapes the slug and same-slug refreshes preserve the draft', async () => {
  const requests=[];
  const p=settingsPage(async(url,options)=>{requests.push({url,options});return response(settingsBody('Pokémon FR'));});
  p.context.target=game({slug:'Pokémon FR',app:true,state:'done'});
  await p.eval('settingsPanel.bind(target)');
  assert.equal(requests.length,1);assert.equal(requests[0].url,'/settings?slug=Pok%C3%A9mon%20FR');
  assert.equal(p.elements.settings.hidden,false);assert.equal(p.elements['settings-save'].disabled,true);
  p.eval('settingsPanel.session.draft.DM_FULLSCREEN="1";settingsPanel.refresh()');
  await p.eval('settingsPanel.bind(target)');await p.eval('settingsPanel.bind(target)');
  assert.equal(requests.length,1);
  assert.equal(p.eval('settingsPanel.session.draft.DM_FULLSCREEN'),'1');
  p.eval('settingsPanel.release();settingsPanel.bind({...target,app:false})');
  assert.equal(p.elements.settings.hidden,true);assert.equal(requests.length,1);
});

test('settings POST sends only changed unlocked values then refetches server values', async () => {
  const requests=[];
  const p=settingsPage(async(url,options={})=>{
    requests.push({url,options});
    if(options.method==='POST')return response({ok:true});
    const body=settingsBody('test',requests.some(r=>r.options.method==='POST')?{DM_FULLSCREEN:'1'}:{});return response(body);
  });
  p.context.target=game({slug:'test',app:true,state:'done'});await p.eval('settingsPanel.bind(target)');
  p.eval('settingsPanel.session.draft.DM_FULLSCREEN="1";settingsPanel.session.draft.DM_METAL_HUD="0";settingsPanel.refresh()');
  assert.equal(p.elements['settings-save'].disabled,false);
  await p.eval('settingsPanel.save()');
  assert.equal(requests.length,3);assert.equal(requests[1].options.method,'POST');
  assert.equal(requests[1].options.body,JSON.stringify({slug:'test',values:{DM_FULLSCREEN:'1'}}));
  assert.equal(p.eval('settingsPanel.session.draft.DM_FULLSCREEN'),'1');
  assert.equal(p.eval('settingsPanel.session.dirty'),false);
  assert.match(p.elements['settings-status'].textContent,/enregistrées et valeurs relues/);
});

test('settings failure is inline, keeps the dirty draft and a 502 asks for a reload without fake success', async () => {
  const requests=[];
  const p=settingsPage(async(url,options={})=>{requests.push({url,options});return options.method==='POST'?response({error:'Écriture interrompue'},502):response(settingsBody());});
  p.context.target=game({slug:'test',app:true,state:'done'});await p.eval('settingsPanel.bind(target)');
  p.eval('settingsPanel.session.draft.DM_FULLSCREEN="1";settingsPanel.refresh()');await p.eval('settingsPanel.save()');
  assert.equal(requests.length,2);assert.equal(p.eval('settingsPanel.session.draft.DM_FULLSCREEN'),'1');
  assert.equal(p.eval('settingsPanel.session.dirty'),true);assert.equal(p.elements['settings-save'].disabled,false);
  assert.match(p.elements['settings-status'].textContent,/partielle est possible.*recharge/);assert.equal(p.elements['settings-reload'].hidden,false);
});

test('an old settings response cannot overwrite a newer slug', async () => {
  const releases={};
  const p=settingsPage(url=>new Promise(resolve=>{const slug=new URLSearchParams(url.split('?')[1]).get('slug');releases[slug]=()=>resolve(response(settingsBody(slug,{DM_FULLSCREEN:slug==='new'?'1':'0'})));}));
  p.context.first=game({slug:'old',app:true,state:'done'});p.context.second=game({slug:'new',app:true,state:'done'});
  const old=p.eval('settingsPanel.bind(first)'),fresh=p.eval('settingsPanel.bind(second)');
  releases.new();await fresh;assert.equal(p.eval('settingsPanel.session.draft.DM_FULLSCREEN'),'1');
  p.eval('settingsPanel.session.draft.DM_FULLSCREEN="0";settingsPanel.refresh()');releases.old();await old;
  assert.equal(p.eval('settingsPanel.session.slug'),'new');assert.equal(p.eval('settingsPanel.session.draft.DM_FULLSCREEN'),'0');
});

test('closing and reopening the sheet refetches and drops its old draft, while menu localStorage survives', async () => {
  let requests=0;const store=new Map();const p=settingsPage(async()=>{requests++;return response(settingsBody());},store);
  p.context.target=game({slug:'test',app:true,state:'done'});await p.eval('settingsPanel.bind(target)');
  p.eval('settingsPanel.session.draft.DM_FULLSCREEN="1";settingsPanel.refresh();saveLaunchMenuChoice(target.title_id,false)');
  p.eval('settingsPanel.release()');await p.eval('settingsPanel.bind(target)');
  assert.equal(requests,2);assert.equal(p.eval('settingsPanel.session.draft.DM_FULLSCREEN'),'0');
  assert.equal(p.elements['launch-menu'].checked,false);
});

test('settings GET failure is retryable and its later response keeps a dirty draft', async () => {
  let unavailable=false,requests=0;
  const p=settingsPage(async()=>{requests++;return unavailable?response({error:'down'},502):response(settingsBody());});
  p.context.target=game({slug:'test',app:true,state:'done'});await p.eval('settingsPanel.bind(target)');
  p.eval('settingsPanel.session.draft.DM_FULLSCREEN="1";settingsPanel.refresh()');
  unavailable=true;await p.eval('settingsPanel.reload()');
  assert.equal(p.elements['settings-reload'].hidden,false);assert.match(p.elements['settings-status'].textContent,/HTTP 502/);
  unavailable=false;await p.eval('settingsPanel.reload()');
  assert.equal(requests,3);assert.equal(p.eval('settingsPanel.session.draft.DM_FULLSCREEN'),'1');assert.equal(p.eval('settingsPanel.session.dirty'),true);
  assert.match(p.elements['settings-status'].textContent,/brouillon non enregistré est conservé/);
});

test('a localStorage failure is shown by the menu control and restores its last saved value', async () => {
  const store=new Map([['nxnative-launch-menu',JSON.stringify({'0000000000000000':true})]]);
  const p=settingsPage(async()=>response(settingsBody()),store,true);p.context.target=game({slug:'test',app:true,state:'done'});
  await p.eval('settingsPanel.bind(target)');p.elements['launch-menu'].checked=false;p.elements['launch-menu'].dispatch('change');
  assert.match(p.elements['launch-menu-status'].textContent,/n’a pas été conservé/);assert.equal(p.elements['launch-menu'].checked,true);
  assert.deepEqual(JSON.parse(store.get('nxnative-launch-menu')),{'0000000000000000':true});
});

test('new Pokémon use their own square covers and no invented wide artwork', () => {
  const za=run('CATALOG["0100F43008C44000"]'),pearl=run('CATALOG["010018E011D92000"]');
  assert.equal(za.coverSrc,'/art/catalog/0100F43008C44000.jpg');assert.equal(pearl.coverSrc,'/art/library/010018E011D92000.jpg');
  assert.equal(call('detailArt',za).kind,'square');assert.equal(call('detailArt',pearl).kind,'square');
  assert.notEqual(za.coverSrc,pearl.coverSrc);assert.equal(za.art,undefined);assert.equal(pearl.art,undefined);
});

test('gamepad: A clicks the Jouer button itself, moves change the selection only, B closes an open sheet', () => {
  const clicks = [], focused = [], closed = [];
  const tile = id => ({dataset: {familyId: id}, closest() { return this; }, focus() { focused.push(id); }});
  const tiles = [tile('a'), tile('b')];
  const games = {contains: el => tiles.includes(el), querySelector: s => s === 'nx-tile[selected]' ? tiles[0] : tiles[0], querySelectorAll: () => tiles};
  const dialog = {open: false, close() { closed.push('detail'); this.open = false; }};
  const elements = {games, play: {click() { clicks.push('play'); }}, 'catalog-games': {}};
  const document = {activeElement: null, addEventListener() {}, getElementById: id => elements[id], querySelectorAll: s => s === 'dialog' ? [dialog] : []};
  const context = vm.createContext({document, getComputedStyle: () => ({gridTemplateColumns: '1fr 1fr 1fr 1fr'})});
  vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);
  vm.runInContext('playGame = () => { throw new Error("A must go through the button") }; selectFamily = (id, focus) => { selectedFamilyId = id; if (focus) document.lastFocus = id; }; filter = "all"', context);
  context.onPad('right');                       // nothing focused yet: focuses the selected tile, no move
  assert.equal(document.lastFocus, 'a');
  document.activeElement = tiles[0];
  context.onPad('right');
  assert.equal(document.lastFocus, 'b');
  assert.deepEqual(clicks, [], 'moving never plays');
  context.onPad('confirm');
  assert.deepEqual(clicks, ['play']);
  dialog.open = true;
  context.onPad('confirm');
  assert.deepEqual(clicks, ['play'], 'A does nothing behind an open sheet');
  context.onPad('back');
  assert.deepEqual(closed, ['detail']);
});
