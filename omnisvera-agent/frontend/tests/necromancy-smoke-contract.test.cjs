const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');

test('native touch smoke accepts the atomic automatic receipt, not a second confirmation request',()=>{
 const source=fs.readFileSync('tests/morthak-necromancy-smoke.cjs','utf8');
 const touch=source.split("if(kind==='touch'){")[1].split("}else if(kind==='fear'){")[0];
 assert.doesNotMatch(touch,/const confirmed=response/);
 assert.match(touch,/const result=await cast\('toque-sombrio'/);
 assert.match(touch,/assert\.ok\(result\.confirmed\)/);
});

test('corpse placement is fixture setup before combat, not an administrative teleport during a turn',()=>{
 const source=fs.readFileSync('tests/morthak-necromancy-smoke.cjs','utf8');
 const corpse=source.indexOf("name:'Cadáver exclusivo do ensaio '");
 assert.ok(corpse>=0&&corpse<source.indexOf("await command('start'"));
});

test('card availability is re-resolved after React refresh instead of waiting on a captured DOM node',()=>{
 const source=fs.readFileSync('tests/morthak-necromancy-smoke.cjs','utf8');
 const click=source.split('const click=')[1].split('const response=')[0];
 assert.doesNotMatch(click,/elementHandle|waitForFunction/);
 assert.ok(click.includes('button[data-card-command]:enabled'));
});
