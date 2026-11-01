const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const {webcrypto}=require('node:crypto');
const {execFileSync}=require('node:child_process');

function harness(){
 const storage=new Map([['omnisvera-access-token','synthetic-master']]);
 const session=new Map();let counter=0,fail=true,committed=0;const calls=[],receipts=new Map();
 const memory=map=>({getItem:key=>map.get(key)??null,setItem:(key,value)=>map.set(key,value),removeItem:key=>map.delete(key)});
 const fetch=async(url,options)=>{
  const payload=JSON.parse(options.body);calls.push({url,payload});
  const id=payload.request_id;
  if(!id||!receipts.has(id)){committed++;receipts.set(id,{item:'Fixture',receipt_id:id,quantity:1});}
  if(fail){fail=false;throw new Error('response lost after commit');}
  return {ok:true,json:async()=>receipts.get(id)};
 };
 function load(){
  const cache=new Map();
  const context=vm.createContext({fetch,setTimeout,clearTimeout,AbortController,TextEncoder,
   localStorage:memory(storage),sessionStorage:memory(session),crypto:{subtle:webcrypto.subtle,randomUUID:()=>`synthetic-request-${++counter}`}});
  function module(name){
   if(cache.has(name))return cache.get(name).exports;
   const result={exports:{}};cache.set(name,result);
   let source=name==='api'&&process.env.FOUNDATION_RETRY_BASELINE
    ?execFileSync('git',['show','HEAD:omnisvera-agent/frontend/src/api.ts'],{encoding:'utf8'})
    :fs.readFileSync(`src/${name}.ts`,'utf8');
   source=source.replaceAll('import.meta.env.VITE_API_BASE_URL',"''");
   const output=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText;
   const fn=vm.runInContext(`(function(require,module,exports){${output}\n})`,context);
   fn(id=>module(id.replace('./','')),result,result.exports);return result.exports;
  }
  const api=module('api');api.setAccessToken('synthetic-master');api.setAccessMode('gm');return api;
 }
 return {load,calls,session,get committed(){return committed;}};
}

test('legacy GM purchase recovers its command after reload and a lost committed response',async()=>{
 const h=harness(),payload={character_id:'fixture',stock_id:'stock',quantity:1,final_price_po:1,expected_purse:{coins:20}};
 await assert.rejects(h.load().buyFromMerchant('shop',payload),/response lost/);
 const result=await h.load().buyFromMerchant('shop',{...payload,expected_purse:{coins:19}});
 assert.ok(h.calls[0].payload.request_id,'A retry requires a command identity');
 assert.equal(h.calls[0].payload.request_id,h.calls[1].payload.request_id);
 assert.equal(h.committed,1);assert.equal(result.receipt_id,h.calls[0].payload.request_id);
 assert.equal(h.session.size,0);
});

test('legacy GM sale uses the same journal, and confirmed new sales get new identities',async()=>{
 const h=harness(),api=h.load(),payload={character_id:'fixture',item_path:'fixture-item',quantity:1,unit_price_po:1};
 await assert.rejects(api.sellToMerchant('shop',payload),/response lost/);
 await api.sellToMerchant('shop',payload);
 assert.ok(h.calls[0].payload.request_id);
 assert.equal(h.calls[0].payload.request_id,h.calls[1].payload.request_id);
 await api.sellToMerchant('shop',payload);
 assert.notEqual(h.calls[1].payload.request_id,h.calls[2].payload.request_id);
 assert.equal(h.committed,2);
});

test('pending trade journal stores neither access tokens nor item/wallet payloads',async()=>{
 const h=harness();
 await assert.rejects(h.load().buyFromMerchant('private-shop',{character_id:'private-character',stock_id:'private-item',final_price_po:1}));
 assert.equal(h.session.size,1);
 const journal=JSON.stringify([...h.session]);
 for(const value of ['synthetic-master','private-shop','private-character','private-item']) assert.ok(!journal.includes(value));
});

test('group chest recovers the same command after reload without sending recipients or rewards',async()=>{
 const h=harness();
 await assert.rejects(h.load().collectWorkspaceLoot('synthetic-corpse'),/response lost/);
 await h.load().collectWorkspaceLoot('synthetic-corpse');
 assert.equal(h.committed,1);
 assert.equal(h.calls[0].payload.request_id,h.calls[1].payload.request_id);
 assert.deepEqual(Object.keys(h.calls[0].payload).sort(),['request_id','token_id']);
 assert.match(h.calls[0].url,/\/workspace\/loot\/collect$/);
});
