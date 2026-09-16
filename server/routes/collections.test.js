const assert = require('node:assert/strict');
const express = require('express');
const db = require('../db');
const {createSearchRouter} = require('./search');
const {createUserStateRouter} = require('./user_state');
const {Bm25Index} = require('../search/bm25');
const {createCollections, validateRegistry} = require('../collections');
const {SimilarIndex} = require('../search/similar');
const ps = [
  {id:'codeforces-1-a',platform:'codeforces',title:'Path one',statement:'Find graph paths',patterns:['bfs'],difficulty:1200},
  {id:'codeforces-1-b',platform:'codeforces',title:'Path two',statement:'Find graph paths',patterns:['bfs'],difficulty:1600},
  {id:'codeforces-1-c',platform:'codeforces',title:'Path three',statement:'Find graph paths',patterns:['bfs']},
  {id:'cses-1',platform:'cses',title:'Path four',statement:'Find graph paths',patterns:['bfs'],cses_difficulty:{band:2}},
];
const registry={version:1,collections:[{id:'contest-a',name:'Test A',short:'A 24',problems:['codeforces-1-b','codeforces-1-a'],resources:[]},{id:'contest-b',name:'Test B',problems:['cses-1'],resources:[]},{id:'contest-c',name:'Test C',short:'C 26',problems:['codeforces-1-b'],resources:[]}],aliases:{'codeforces-9-a':'codeforces-1-a'}};
const c=createCollections(ps,registry);
assert.equal(c.canonical('codeforces-9-a'),'codeforces-1-a');
assert.equal(c.passes(ps[0],c.parse('missing')),false);
// A problem in two contests names them in registry order, always — the card
// shows the first one and lists the rest in its tooltip.
assert.deepEqual(c.memberships.get('codeforces-1-b').map(m=>m.id),['contest-a','contest-c']);
assert.deepEqual(c.memberships.get('codeforces-1-b').map(m=>m.short),['A 24','C 26']);
assert.equal(c.payload().collections.find(x=>x.id==='contest-a').short,'A 24');
// `short` is optional, and short: the chip it labels sits in the judge row.
const base={id:'x',name:'X',family:'f',organizer:'o',stage:'prelims',problems:[],evidence:['https://example.com/x'],held_date:null,resources:[]};
const check=extra=>validateRegistry({version:1,collections:[{...base,...extra}]},ps);
assert.deepEqual(check({}),[]);
assert.deepEqual(check({short:'WF 2024'}),[]);
assert.deepEqual(check({short:'India Prelims 25'}),[],'16 characters is the limit, not one under it');
assert.ok(check({short:'x'.repeat(17)}).some(e=>/short/.test(e)),'17 is too long');
assert.ok(check({short:'  '}).some(e=>/short/.test(e)),'blank is not a label');
assert.ok(check({short:2024}).some(e=>/short/.test(e)),'not a string');
// A membership may be a bare id or an object carrying what the corpus never
// learned about that problem. Both shapes flatten to the same `problems`, so
// every existing consumer is untouched; `members` is where the extra lives.
{
  const objectReg={version:1,collections:[{...registry.collections[0],id:'contest-o',problems:[
    {id:'codeforces-1-b',letter:'B',order:2,title:'Path two'},
    {id:'codeforces-9-a',letter:'A',order:1,title:'Path one',url:'https://example.com/a',kattis_difficulty:{score:7.4,label:'hard'},solves:{full:12,source:'icpc-standings',observed_at:'2026-09-16'},code:'PATHONE'},
  ]}],aliases:registry.aliases};
  const oc=createCollections(ps,objectReg);
  assert.deepEqual(oc.payload().collections[0].problems,['codeforces-1-b','codeforces-1-a'],
    'object members flatten to the same canonical id list a string member would');
  const members=oc.payload().collections[0].members;
  assert.deepEqual(members.map(m=>m.id),['codeforces-1-b','codeforces-1-a'],'aliases resolve on members too');
  assert.equal(members[1].letter,'A');
  assert.equal(members[1].order,1);
  assert.equal(members[1].kattis_difficulty.score,7.4);
  assert.equal(members[1].solves.full,12);
  assert.equal(members[1].code,'PATHONE');
  // A string member still ships as a member, so the page can walk one list.
  const plain=createCollections(ps,registry).payload().collections[0].members;
  assert.deepEqual(plain.map(m=>m.id),['codeforces-1-b','codeforces-1-a']);
  assert.deepEqual(Object.keys(plain[0]),['id'],'a bare id carries nothing it was not given');
}
// Field validators. The dup check is first because it used to compare object
// identity, so two objects naming one problem passed silently.
{
  const base={id:'x',name:'X',family:'f',organizer:'o',stage:'prelims',evidence:['https://example.com/x'],held_date:null,resources:[]};
  const members=extra=>validateRegistry({version:1,collections:[{...base,problems:extra}]},ps);
  assert.deepEqual(members([{id:'a'},{id:'b'}]),[]);
  assert.ok(members([{id:'a'},{id:'a'}]).some(e=>/ordered memberships/.test(e)),'two objects naming one problem is a duplicate');
  assert.ok(members(['a',{id:'a'}]).some(e=>/ordered memberships/.test(e)),'so is a string and an object naming one problem');
  assert.deepEqual(members([{id:'a',letter:'A'},{id:'b',letter:'B2'}]),[]);
  assert.ok(members([{id:'a',letter:'a'}]).some(e=>/letter/.test(e)));
  assert.ok(members([{id:'a',order:0}]).some(e=>/order/.test(e)));
  assert.ok(members([{id:'a',order:1},{id:'b',order:1}]).some(e=>/duplicate order/.test(e)));
  assert.deepEqual(members([{id:'a',order:1},{id:'b',order:2}]),[]);
  assert.ok(members([{id:'a',title:'  '}]).some(e=>/title/.test(e)));
  assert.ok(members([{id:'a',url:'javascript:alert(1)'}]).some(e=>/url/.test(e)));
  assert.ok(members([{id:'a',kattis_difficulty:{score:11}}]).some(e=>/kattis score/.test(e)));
  assert.ok(members([{id:'a',kattis_difficulty:{score:7.4,host:'open.kattis.com'}}]).some(e=>/kattis difficulty/.test(e)),'the staging blob carries fields the registry does not');
  assert.deepEqual(members([{id:'a',kattis_difficulty:{score:0}}]),[]);
  assert.ok(members([{id:'a',solves:{full:-1,source:'icpc-standings'}}]).some(e=>/solve count/.test(e)));
  assert.ok(members([{id:'a',solves:{full:3,source:'guessed'}}]).some(e=>/solves source/.test(e)),'a solve count needs a source that can be re-read');
  assert.ok(members([{id:'a',solves:{full:3,source:'icpc-standings',observed_at:'yesterday'}}]).some(e=>/solves date/.test(e)));
  assert.deepEqual(members([{id:'a',solves:{full:3,source:'kattis-source-page'}}]),[]);
  assert.ok(members([{id:'a',code:''}]).some(e=>/code/.test(e)));
  assert.ok(members([{id:'a',position:3}]).some(e=>/unknown member field position/.test(e)),'a typo must not sit in the registry rendering nothing');
  assert.ok(members([{letter:'A'}]).some(e=>/needs an id/.test(e)));
}
const structural=new SimilarIndex(ps,null).similar(ps[0].id);
assert.equal(structural.ranker,'technique');
assert.ok(structural.hits.every(h=>h.problem.id!==ps[0].id));
const original=db.query;
db.query=async()=>({rows:[{problem_id:'codeforces-1-b',done:true,bookmarked:true,recall:'again',done_at:new Date('2020-01-01'),bookmarked_at:new Date('2021-01-01'),updated_at:new Date('2021-01-01')}]});
const app=express();app.use((req,res,next)=>{if(req.headers['x-test-user'])req.user={id:'u'};next();});
app.use('/api',createSearchRouter({problems:ps,indexes:{bm25:new Bm25Index(ps)},defaultRanker:'bm25',collectionRegistry:registry}));
app.use('/api',createUserStateRouter({problems:ps,collectionRegistry:registry}));
const server=app.listen(0,async()=>{
 const base=`http://127.0.0.1:${server.address().port}/api`;
 const get=async(path,user=false)=>(await fetch(base+path,{headers:user?{'x-test-user':'1'}:{}})).json();
 const ids=r=>r.hits.map(h=>h.problem.id);
 try{
  assert.deepEqual(ids(await get('/search?contest=contest-a')),['codeforces-1-b','codeforces-1-a']);
  // Provenance rides along on every hit so a card can say where it came from.
  const memberOf=(await get('/search?contest=contest-a')).hits.find(h=>h.problem.id==='codeforces-1-b');
  assert.deepEqual(memberOf.competitions.map(m=>m.id),['contest-a','contest-c']);
  assert.equal(memberOf.competitions[0].short,'A 24');
  const unaffiliated=(await get('/search?q=graph')).hits.find(h=>h.problem.id==='codeforces-1-c');
  assert.deepEqual(unaffiliated.competitions,[]);
  assert.equal((await get('/search?contest=missing')).total,0);
  assert.deepEqual(ids(await get('/search?contest=contest-a,contest-b&platform=cses')),['cses-1']);
  assert.deepEqual(ids(await get('/search?q=graph&contest=contest-a&difficulty=cf:1500-1700')),['codeforces-1-b']);
  const a=await get('/similar/codeforces-9-a?k=1');const b=await get('/similar/codeforces-9-a?k=1&offset=1');
  assert.equal(a.total,3);assert.notEqual(ids(a)[0],ids(b)[0]);
  assert.deepEqual(ids(await get('/similar/codeforces-1-a?contest=contest-a&library=bookmarked&recall=again&aged=30',true)),['codeforces-1-b']);
  assert.deepEqual(ids(await get('/similar/codeforces-1-a?filter=notdone',true)),['codeforces-1-c','cses-1']);
  assert.equal((await get('/similar/codeforces-1-a?contest=missing')).total,0);
  assert.equal((await get('/similar/codeforces-1-a?k=-5')).k,1);
  assert.deepEqual(ids(await get('/similar/codeforces-1-a?practice=1',true)),['cses-1']);
  assert.equal((await get('/similar/codeforces-1-a?practice=1&contest=contest-a',true)).total,0);
  const lib=await get('/library?type=all&contest=contest-b',true);assert.equal(lib.total,0);
  console.log('collection union/intersection, order, alias, similar paging/state/fallback passed');
 }finally{db.query=original;server.close();}
});
