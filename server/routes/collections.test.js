const assert = require('node:assert/strict');
const express = require('express');
const db = require('../db');
const {createSearchRouter} = require('./search');
const {createUserStateRouter} = require('./user_state');
const {Bm25Index} = require('../search/bm25');
const {createCollections} = require('../collections');
const {SimilarIndex} = require('../search/similar');
const ps = [
  {id:'codeforces-1-a',platform:'codeforces',title:'Path one',statement:'Find graph paths',patterns:['bfs'],difficulty:1200},
  {id:'codeforces-1-b',platform:'codeforces',title:'Path two',statement:'Find graph paths',patterns:['bfs'],difficulty:1600},
  {id:'codeforces-1-c',platform:'codeforces',title:'Path three',statement:'Find graph paths',patterns:['bfs']},
  {id:'cses-1',platform:'cses',title:'Path four',statement:'Find graph paths',patterns:['bfs'],cses_difficulty:{band:2}},
];
const registry={version:1,collections:[{id:'contest-a',name:'Test A',problems:['codeforces-1-b','codeforces-1-a'],resources:[]},{id:'contest-b',name:'Test B',problems:['cses-1'],resources:[]}],aliases:{'codeforces-9-a':'codeforces-1-a'}};
const c=createCollections(ps,registry);
assert.equal(c.canonical('codeforces-9-a'),'codeforces-1-a');
assert.equal(c.passes(ps[0],c.parse('missing')),false);
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
