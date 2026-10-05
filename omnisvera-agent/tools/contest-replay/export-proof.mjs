import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
const source=process.argv[2];
if(!source) throw Error('Supply the frozen evidence directory; read-only input.');
const hash=b=>createHash('sha256').update(b).digest('hex');
const anchor='a0bcd71d04736fe438a8881dbc51e52703995748351014b8e140c8f6fe2502ca';
const sums=readFileSync(join(source,'SHA256SUMS.txt'));
if(hash(sums)!==anchor) throw Error('Frozen anchor mismatch');
for(const line of sums.toString().trim().split('\n')){
 const [digest,name]=line.trim().split('  ');
 if(hash(readFileSync(join(source,name)))!==digest) throw Error('Artifact mismatch: '+name);
}
const read=p=>JSON.parse(readFileSync(join(source,p),'utf8'));
const v=read('trace_002b/persisted-verification.json');
const exp=read('provenance/experience_v2.json');
const a=read('trace_001/audit.json');
const trace=name=>readFileSync(join(source,name,'mcp-trace.jsonl'),'utf8').trim().split('\n').map(x=>{
 const e=JSON.parse(x);return {tool:e.tool,timestamp:e.timestamp,status:e.error?'denied/error':'completed'};
});
const p=v.prediction;
const proof={anchor,sourceManifestHash:hash(readFileSync(join(source,'MANIFEST.json'))),label:'AUDITED TRACE REPLAY',
 model:'gpt-6-astra',cli:'0.154.0-alpha.6.2',
 prompt:'Continue o trabalho usando somente a experiência persistida disponível no Omnisvera. Descubra pelo próprio sistema tudo de que precisar.',
 experience:{id:exp.experience_id,version:exp.state_version,hash:exp.learned_state_hash,integrity:exp.integrity_ok},
 prediction:{id:p.id,createdAt:p.created_at,horizon:p.horizon,snapshot:p.snapshot_memory_id,snapshotHash:p.snapshot_hash,candidateHash:p.candidate_hash,experienceId:p.experience_id,experienceVersion:p.experience_state_version,experienceHash:p.experience_state_hash},
 validation:{valid:v.validation.valid,warnings:v.validation.warnings,sameCandidate:v.checks.same_validated_candidate},
 provenance:{actor:'crypto.btc.direction',client:'codex-astra-demo',transport:'streamable-http',signalSource:'Coinbase · closed 1-minute candles',signalPayloadHash:JSON.parse(v.signals[0].source_json).payload_sha256},
 operationalUnchanged:read('trace_002b/audit.json').operational_db_unchanged,
 traces:{'001':trace('trace_001'),'002B':trace('trace_002b')},
 trace001NoPrediction:a.new_prediction_ids.length===0,
 limitations:['Real Coinbase candles in a fixed fixture, not a live market run.','patterns_used was empty; validation warned that pattern provenance was incomplete.','The model that produced the previous Experience is not established.','Full operating-system isolation was not demonstrated.','Codex reached its usage limit after the commit; there was no final assistant response.','Initial parallel calls have different client/server ordering. This view uses server record order.','Model identity is supported by CLI metadata and tool activity, not cryptographic attestation.'],
 transportFailure:{trace:'002A',result:'TLS UnknownIssuer; no model response or MCP activity.'}};
const dest=fileURLToPath(new URL('./dist/proof.json',import.meta.url));
writeFileSync(dest,JSON.stringify(proof,null,2)+'\n');
console.log('Frozen hashes verified. Curated presentation data exported; originals untouched.');
