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

test('ambiance resolution prefers the URL parameter, then localStorage, then Cinéma', () => {
  assert.equal(call('resolveAmbiance','console','cinema'),'console');
  assert.equal(call('resolveAmbiance','cinema','console'),'cinema');
  assert.equal(call('resolveAmbiance',null,'console'),'console');
  assert.equal(call('resolveAmbiance','nuit','console'),'console');
  assert.equal(call('resolveAmbiance',null,null),'cinema');
  assert.equal(run('initialAmbiance()'),'cinema');  // no location/localStorage in this context
});

test('switching ambiance updates an explicit URL so reload keeps the selected view', () => {
  const storage=new Map();
  const isolated=vm.createContext({URL,URLSearchParams,
    location:{href:'http://127.0.0.1:8767/?ambiance=cinema&keep=yes',search:'?ambiance=cinema&keep=yes'},
    history:{replaceState(_state,_title,url){this.url=String(url);}},
    localStorage:{getItem:key=>storage.get(key),setItem:(key,value)=>storage.set(key,value)},
    document:{documentElement:{dataset:{}},addEventListener(){},querySelectorAll(){return [];}}
  });
  vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],isolated);
  vm.runInContext('renderCards=()=>{};placeBuildPanel=()=>{};applyAmbiance("console",true)',isolated);
  assert.equal(new URL(isolated.history.url).searchParams.get('ambiance'),'console');
  assert.equal(new URL(isolated.history.url).searchParams.get('keep'),'yes');
  assert.equal(storage.get('nxnative-ambiance'),'console');
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
