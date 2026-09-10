let messages = [];
let mcpTools = [];

function getShowRawChecked(){
  const a=document.getElementById('showRaw');
  const b=document.getElementById('showRawMobile');
  return (a && a.checked) || (b && b.checked);
}
function syncRawCheckboxes(source){
  const a=document.getElementById('showRaw');
  const b=document.getElementById('showRawMobile');
  if(source==='a' && b) b.checked=a.checked;
  if(source==='b' && a) a.checked=b.checked;
}

async function refreshStatus(){
  try{
    const r = await fetch('/api/status');
    const j = await r.json();
    document.getElementById('s-ollama').textContent = 'Ollama: ' + j.ollama;
    document.getElementById('s-mcp').textContent = 'MCP: ' + j.mcp;
    document.getElementById('s-tools').textContent = 'Tools: ' + j.tools;
    document.getElementById('toolsCount').textContent = '(' + j.tools + ')';
    const listEl=document.getElementById('toolsList');
    listEl.innerHTML='';
    (j.toolsList||[]).forEach(t=>{
      const div=document.createElement('div');
      div.className='tool';
      div.textContent=t;
      listEl.appendChild(div);
    });
    mcpTools=j.toolsList||[];
  }catch(e){
    document.getElementById('s-mcp').textContent='MCP: error';
  }
}

function renderMarkdown(md){
  let raw = (md || '').replace(/\\n/g, '\n');
  try{
    if(window.marked && window.DOMPurify){
      const parsed = window.marked.parse(raw, {gfm:true, breaks:true});
      return window.DOMPurify.sanitize(parsed);
    }
  }catch(e){ /* fallthrough */ }
  let html = raw.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  // minimal table support for fallback
  if(html.includes('|')){
    html = html.replace(/^\|(.+)\|\n\|[-| ]+\|\n((?:\|.+\|\n?)*)/gm, (m, head, body)=>{
      const th = head.split('|').filter(s=>s.trim()).map(s=>`<th>${s.trim()}</th>`).join('');
      const rows = body.trim().split('\n').map(r=>`<tr>${r.split('|').filter(s=>s.trim()).map(s=>`<td>${s.trim()}</td>`).join('')}</tr>`).join('');
      return `<table><thead><tr>${th}</tr></thead><tbody>${rows}</tbody></table>`;
    });
  }
  html = html.replace(/\n/g,'<br/>');
  return html;
}

function createAssistantBubble(content){
  const chat=document.getElementById('chat');
  const div=document.createElement('div');
  div.className='bubble ai markdown';
  div.innerHTML = renderMarkdown(content);
  // ensure links open safely
  div.querySelectorAll('a').forEach(a=>{
    a.setAttribute('target','_blank');
    a.setAttribute('rel','noopener noreferrer');
  });
  chat.appendChild(div);
  chat.scrollTop=chat.scrollHeight;
}

function createUserBubble(text){
  const chat=document.getElementById('chat');
  const div=document.createElement('div');
  div.className='bubble user';
  div.textContent=text;
  chat.appendChild(div);
  chat.scrollTop=chat.scrollHeight;
}

function createErrorBubble(text){
  const chat=document.getElementById('chat');
  const div=document.createElement('div');
  div.className='bubble ai markdown';
  div.innerHTML = renderMarkdown('**Error:** ' + text);
  chat.appendChild(div);
  chat.scrollTop=chat.scrollHeight;
}

function formatDuration(ms){
  if(ms==null || isNaN(ms)) return '';
  const s=(ms/1000).toFixed(1);
  return s+'s';
}

function renderToolCalls(toolCalls){
  const chat=document.getElementById('chat');
  const showRaw=getShowRawChecked();
  toolCalls.forEach(tc=>{
    const name=tc.name || 'unknown';
    const duration = tc.duration_ms != null ? formatDuration(tc.duration_ms) : '';
    const isErr = tc.status==='error' || tc.isError || !!tc.error;
    const icon = isErr ? '✗' : '✓';

    if(!showRaw){
      // compact timeline: discrete, collapsible but no args/result JSON
      const wrap=document.createElement('div');
      wrap.className='toolcall compact';
      // make slightly collapsible via details if we want, but spec says discrete collapsible - we keep simple line, no details
      const iconSpan=document.createElement('span');
      iconSpan.className='status-icon';
      iconSpan.textContent=icon;
      iconSpan.style.color=isErr ? '#ff7b72' : '#56d364';

      const nameSpan=document.createElement('span');
      nameSpan.className='tool-name';
      nameSpan.textContent=name;

      const durSpan=document.createElement('span');
      durSpan.className='tool-duration';
      durSpan.textContent=duration;

      wrap.appendChild(iconSpan);
      wrap.appendChild(nameSpan);
      wrap.appendChild(durSpan);
      // optional: add title with status for accessibility
      wrap.title = isErr ? (tc.error||'error') : 'success';
      chat.appendChild(wrap);
    } else {
      // expanded with escaping, collapsible details
      const wrap=document.createElement('div');
      wrap.className='toolcall';

      const header=document.createElement('div');
      header.style.display='flex';
      header.style.alignItems='center';
      header.style.gap='8px';
      header.style.fontWeight='700';

      const iconSpan=document.createElement('span');
      iconSpan.textContent=icon;
      iconSpan.style.color=isErr ? '#ff7b72' : '#56d364';
      header.appendChild(iconSpan);

      const nameSpan=document.createElement('span');
      nameSpan.textContent=name;
      header.appendChild(nameSpan);

      const durSpan=document.createElement('span');
      durSpan.textContent=duration ? '· '+duration : '';
      durSpan.style.opacity='0.6';
      durSpan.style.fontWeight='400';
      durSpan.style.marginLeft='6px';
      header.appendChild(durSpan);

      const statusSpan=document.createElement('span');
      statusSpan.textContent= isErr ? 'error' : 'success';
      statusSpan.style.fontSize='10px';
      statusSpan.style.padding='2px 6px';
      statusSpan.style.borderRadius='999px';
      statusSpan.style.background=isErr ? '#ff7b7230' : '#56d36430';
      statusSpan.style.color=isErr ? '#ff7b72' : '#56d364';
      statusSpan.style.marginLeft='auto';
      header.appendChild(statusSpan);

      wrap.appendChild(header);

      const details=document.createElement('details');
      details.open=false;
      const summary=document.createElement('summary');
      summary.textContent='Detalhes';
      details.appendChild(summary);

      // Arguments
      const argSec=document.createElement('div');
      argSec.className='detail-section';
      const argLabel=document.createElement('div');
      argLabel.className='label';
      argLabel.textContent='Arguments';
      argSec.appendChild(argLabel);
      const argPre=document.createElement('pre');
      try{
        argPre.textContent=JSON.stringify(tc.arguments ?? {}, null, 2);
      }catch{ argPre.textContent=String(tc.arguments); }
      argSec.appendChild(argPre);
      details.appendChild(argSec);

      // Result
      const resSec=document.createElement('div');
      resSec.className='detail-section';
      const resLabel=document.createElement('div');
      resLabel.className='label';
      resLabel.textContent='Result';
      resSec.appendChild(resLabel);
      const resPre=document.createElement('pre');
      resPre.textContent=(tc.result||'').slice(0,8000);
      resSec.appendChild(resPre);
      details.appendChild(resSec);

      if(tc.error){
        const errSec=document.createElement('div');
        errSec.className='detail-section';
        const errLabel=document.createElement('div');
        errLabel.className='label';
        errLabel.textContent='Error';
        errSec.appendChild(errLabel);
        const errPre=document.createElement('pre');
        errPre.textContent=String(tc.error);
        errPre.style.color='#ff7b72';
        errSec.appendChild(errPre);
        details.appendChild(errSec);
      }

      // Duration
      const durSec=document.createElement('div');
      durSec.className='detail-section';
      const durLabel=document.createElement('div');
      durLabel.className='label';
      durLabel.textContent='Duration';
      durSec.appendChild(durLabel);
      const durPre=document.createElement('pre');
      durPre.textContent=duration || '0.0s';
      durSec.appendChild(durPre);
      details.appendChild(durSec);

      // started_at if present
      if(tc.started_at){
        const stSec=document.createElement('div');
        stSec.className='detail-section';
        const stLabel=document.createElement('div');
        stLabel.className='label';
        stLabel.textContent='Started At';
        stSec.appendChild(stLabel);
        const stPre=document.createElement('pre');
        stPre.textContent=String(tc.started_at);
        stSec.appendChild(stPre);
        details.appendChild(stSec);
      }

      wrap.appendChild(details);
      chat.appendChild(wrap);
    }
  });
  chat.scrollTop=chat.scrollHeight;
}

let progressTimer=null, progressStart=0;
const progressSteps=["Consultando Omnisvera…","Executando world.context…","Gerando resposta…"];
function startProgress(){
  const wrap=document.getElementById('progressWrap'), bar=document.getElementById('progressBar'), meta=document.getElementById('progressMeta');
  wrap.style.display='block';
  meta.style.display='flex';
  meta.classList.remove('error');
  bar.className='progress-bar indeterminate';
  bar.style.width='';
  progressStart=Date.now();
  let stepIdx=0;
  meta.textContent=`Pensando… 0.0s — ${progressSteps[0]}`;
  progressTimer=setInterval(()=>{
    const elapsed=(Date.now()-progressStart)/1000;
    stepIdx=Math.floor(elapsed/1.2) % progressSteps.length;
    const step=progressSteps[stepIdx];
    meta.textContent=`Pensando… ${elapsed.toFixed(1)}s — ${step}`;
  },120);
}
function stopProgress(success, durationMs){
  clearInterval(progressTimer);
  const bar=document.getElementById('progressBar'), meta=document.getElementById('progressMeta'), wrap=document.getElementById('progressWrap');
  const totalMs = durationMs != null ? durationMs : (Date.now()-progressStart);
  const totalSec=(totalMs/1000).toFixed(1);
  if(success){
    bar.className='progress-bar';
    bar.style.width='100%';
    meta.textContent=`Concluído em ${totalSec}s`;
    meta.classList.remove('error');
    setTimeout(()=>{ wrap.style.display='none'; meta.style.display='none'; bar.style.width='0%'; bar.className='progress-bar'; },900);
  }else{
    bar.className='progress-bar error';
    // keep not 100% - do not set width 100% on error per spec
    bar.style.width='70%';
    meta.textContent=`Erro após ${totalSec}s`;
    meta.classList.add('error');
    setTimeout(()=>{ wrap.style.display='none'; meta.style.display='none'; bar.style.width='0%'; bar.className='progress-bar'; meta.classList.remove('error'); },1300);
  }
}

async function send(){
  const input=document.getElementById('input');
  const text=input.value.trim();
  if(!text) return;
  const model=document.getElementById('modelSelect').value;
  input.value='';
  createUserBubble(text);
  messages.push({role:'user', content:text});
  document.getElementById('sendBtn').disabled=true;
  const overallStart=Date.now();
  startProgress();
  try{
    const r=await fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({messages, model})});
    const j=await r.json();
    const isHttpError=!r.ok;
    if(j.error && !j.content){
      createErrorBubble(j.error);
      if(Array.isArray(j.toolCalls) && j.toolCalls.length){
        renderToolCalls(j.toolCalls);
      }
      stopProgress(false, Date.now()-overallStart);
      return;
    }
    if(Array.isArray(j.toolCalls) && j.toolCalls.length){
      renderToolCalls(j.toolCalls);
    }
    if(j.content){
      // Never mix raw tool result into final AI text - content is separate sanitized markdown
      createAssistantBubble(j.content);
      messages.push({role:'assistant', content:j.content});
    } else if(!j.toolCalls || j.toolCalls.length===0){
      createAssistantBubble('(sem resposta)');
    }
    // decide success vs error based on http error or tool errors? spec says after error mark as error not 100%
    // if server returned error field, consider error
    const hasError = isHttpError || !!j.error;
    stopProgress(!hasError, Date.now()-overallStart);
  }catch(e){
    createErrorBubble(e.message);
    stopProgress(false, Date.now()-overallStart);
  }finally{
    document.getElementById('sendBtn').disabled=false;
    const chat=document.getElementById('chat');
    chat.scrollTop=chat.scrollHeight;
  }
}

document.getElementById('sendBtn').onclick=send;
document.getElementById('input').addEventListener('keydown', e=>{ if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); send(); }});
document.getElementById('clearBtn').onclick=()=>{ messages=[]; document.getElementById('chat').innerHTML=''; };
const showRaw=document.getElementById('showRaw');
const showRawMobile=document.getElementById('showRawMobile');
if(showRaw) showRaw.addEventListener('change', ()=> syncRawCheckboxes('a'));
if(showRawMobile) showRawMobile.addEventListener('change', ()=> syncRawCheckboxes('b'));
refreshStatus();
setInterval(refreshStatus, 5000);
