const {test}=require('node:test');
const assert=require('node:assert/strict');
const {shieldNearMiss}=require('./shield-near-miss.cjs');

test('controlled roll would hit without the shield but misses the effective AC',()=>{
 const result=shieldNearMiss(12,14,0);
 assert.equal(result.d20,13);
 assert.ok(result.attack_total>=12&&result.attack_total<14);
 assert.equal(result.margin,1);
});
test('fixture accounts for the actual attack bonus',()=>{
 const result=shieldNearMiss(12,14,3);
 assert.equal(result.d20,10);assert.equal(result.attack_total,13);
});
test('natural twenty cannot fake a shield avoidance; try the other valid margin',()=>{
 const result=shieldNearMiss(19,21,0);
 assert.equal(result.d20,19);assert.equal(result.margin,2);
});
test('impossible or invalid fixture is not reported as a valid controlled miss',()=>{
 for(const values of [[25,27,0],[12,12,0],[12,15,0],[NaN,14,0],[12,14,1.5]])
  assert.equal(shieldNearMiss(...values),null);
});
