const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
test('today encounter is fixed to TEMP, real prepared enemies and digital dice',()=>{
 const source=fs.readFileSync(path.join(__dirname,'today-encounter-probe.cjs'),'utf8');
 for(const check of ['health.database_path','health.vault_path',"assert.equal(base,'http://127.0.0.1:8871')",'PREP',"roll_mode:'digital'",'session_changed','expected_position_version','expected_combat_version:state.version','GM_REPOSITION'])assert.ok(source.includes(check),check);
 assert.doesNotMatch(source,/access_tokens\.json|8787|8788|d20:\s*\d|Math\.random/);
 assert.ok(source.includes('client.fetch(new URL(url,base).href'),'Browser request contexts need an absolute fixture URL');
});
test('encounter path is adjacent, bounded and ends within the movement budget',()=>{
 const {pathToward}=require('./today-encounter-probe.cjs');
 assert.deepEqual(pathToward([0,0],[8,5],4),[[0,0],[1,1],[2,2],[3,3],[4,4]]);
 assert.deepEqual(pathToward([4,4],[5,5],4),[[4,4]]);
 assert.deepEqual(pathToward([1,1],[1,1],4),[[1,1]]);
});
