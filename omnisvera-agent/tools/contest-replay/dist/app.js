export const stepCount=8;
export function advance(step){return Math.min(stepCount,step+1)}
export function visualState(index,step,playing){return index<step?(index===2?'not-issued':'completed'):(playing&&index===step?'active':'pending')}
export function technicalField(key){return !['Prompt','Between traces','Meaning of cold start','Replay timing','signalSource','result'].includes(key)}
export function assertProof(p){if(p.label!=='AUDITED TRACE REPLAY'||p.prediction.id!==17||!p.validation.valid||!p.validation.sameCandidate||!p.operationalUnchanged||!p.trace001NoPrediction||p.experience.id!==p.prediction.experienceId||p.experience.hash!==p.prediction.experienceHash)throw Error('Evidence contract mismatch');return p}
if(typeof document!=='undefined')init();
async function init(){
 const $=id=>document.getElementById(id);let step=0,playing=false,timer=null;
 const messages=['Ready · play the observed sequence','TRACE 001 · Experience recovered','TRACE 001 · Evidence insufficient','TRACE 001 · No Prediction issued','TRACE 002B · New evidence became available','TRACE 002B · Same Experience recovered','TRACE 002B · Persisted signals discovered','TRACE 002B · Candidate validated','TRACE 002B · Work continued — Prediction #17 committed'];
 function paint(){$('progress').value=step;$('status').textContent=messages[step];document.querySelectorAll('[data-step]').forEach(e=>{const index=Number(e.dataset.step);e.classList.toggle('revealed',index<step);e.dataset.state=visualState(index,step,playing);if(playing&&index===step)e.setAttribute('aria-current','step');else e.removeAttribute('aria-current')});$('play').textContent=playing?'Pause':step===stepCount?'Replay':'Play replay'}
 function stop(){playing=false;clearTimeout(timer);paint()}
 function schedule(){timer=setTimeout(()=>{step=advance(step);if(step===stepCount)stop();else{paint();schedule()}},1800/Number($('speed').value))}
 $('play').onclick=()=>{if(playing)return stop();if(step===stepCount)step=0;playing=true;paint();schedule()};$('reset').onclick=()=>{step=0;stop()};$('speed').onchange=()=>{if(playing){clearTimeout(timer);schedule()}};
 document.addEventListener('visibilitychange',()=>{if(document.hidden&&playing)stop()});
 $('proof-open').onclick=$('proof-inspect').onclick=()=>{if(playing)stop();$('proof').showModal()};$('proof-close').onclick=()=>$('proof').close();
 $('hero-play').onclick=()=>{step=0;clearTimeout(timer);playing=true;paint();schedule();$('replay').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'})};
 function node(tag,text,parent){const e=document.createElement(tag);e.textContent=text;parent.append(e);return e}
 function fields(title,values){const root=$('proof-content');node('h3',title,root);const dl=node('dl','',root);for(const [k,v]of Object.entries(values)){node('dt',k,dl);const value=node('dd',String(v),dl);if(technicalField(k))value.classList.add('technical-value')}}
 try{const response=await fetch('./proof.json');if(!response.ok)throw Error('Proof unavailable');const p=assertProof(await response.json());
 fields('One prompt. No injected state.',{Prompt:p.prompt,Model:p.model,'Codex version':p.cli});
 fields('Experimental setup',{'Between traces':'Test fixture + read scopes updated. The inherited Experience was preserved.','Meaning of cold start':'No IDs or previous state were supplied in the prompt; Astra recovered them through MCP. Full OS isolation was not demonstrated.','Replay timing':'Editorial playback speed, not measured tool latency.'});
 fields('Experience → governed continuation',{'Experience ID':p.experience.id,Version:p.experience.version,'State hash':p.experience.hash,'Integrity verified':p.experience.integrity,'Prediction ID':p.prediction.id,'Committed (UTC)':p.prediction.createdAt,'Horizon (UTC)':p.prediction.horizon,'Snapshot ID':p.prediction.snapshot,'Snapshot hash':p.prediction.snapshotHash,'Candidate hash':p.prediction.candidateHash,'Same validated candidate':p.validation.sameCandidate,'Operational DB unchanged':p.operationalUnchanged});
 fields('Provenance',p.provenance);fields('Frozen archive anchors',{'SHA256SUMS.txt SHA-256':p.anchor,'MANIFEST.json SHA-256':p.sourceManifestHash});
 for(const [name,events]of Object.entries(p.traces)){const d=node('details','',$('proof-content'));node('summary','TRACE '+name+' · full server tool sequence ('+events.length+')',d);const table=node('table','',d);const row=node('tr','',node('thead','',table));for(const heading of ['Tool','Recorded timestamp','Result'])node('th',heading,row);const body=node('tbody','',table);for(const event of events){const tr=node('tr','',body);for(const value of [event.tool,event.timestamp,event.status])node('td',value,tr)}}
 fields('Preserved transport failure',p.transportFailure);node('h3','Limitations — part of the evidence',$('proof-content'));const ul=node('ul','',$('proof-content'));p.limitations.forEach(x=>node('li',x,ul));
 $('play').disabled=false;$('reset').disabled=false;$('hero-play').disabled=false;paint();
 }catch(error){$('status').textContent='Replay unavailable: presentation evidence could not be loaded or validated.';node('p','Proof unavailable. No result should be inferred from this view.',$('proof-content'));console.error(error)}
}
