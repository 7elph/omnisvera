const {test}=require('node:test');
const assert=require('node:assert/strict');
const {unexpectedAlerts}=require('./rest-alerts.cjs');

test('existing unrelated GM warnings are not attributed to full rest',()=>{
 const warnings=['Referência ausente','Componente pendente','Prévia indisponível'];
 assert.deepEqual(unexpectedAlerts(warnings,warnings),[]);
});

test('a new failure after full rest is never suppressed',()=>{
 assert.deepEqual(unexpectedAlerts(['Aviso anterior'],['Aviso anterior','Falha ao concluir descanso']),['Falha ao concluir descanso']);
});

test('matching text still detects an additional occurrence and allows removed warnings',()=>{
 assert.deepEqual(unexpectedAlerts(['Falha'],['Falha','Falha']),['Falha']);
 assert.deepEqual(unexpectedAlerts(['Aviso'],[]),[]);
});
