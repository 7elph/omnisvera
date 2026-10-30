import {useEffect,useRef,useState} from 'react';
import {bindSprite,exportSprite,listSprites,saveSprite,spriteImageUrl} from '../spriteApi';
import {frameAt,subscribeSpriteClock,loadSpriteImage,sliceSheet,type SpriteAsset,type SpriteMetadata} from '../spriteAnimation';
import './spriteStudio.css';

const states=['idle','walk_down','walk_up','walk_left','walk_right','attack','cast','hit','death'];
const initial:SpriteMetadata={schema_version:1,canvas_width:128,canvas_height:128,pivot:[.5,.5],scale:1,frames:[],animations:{}};
type Entity={entity_type:'character'|'token';id:string;name:string};
export default function SpriteStudio({entities,onChange}:{entities:Entity[];onChange:()=>Promise<void>}){
  const [assets,setAssets]=useState<SpriteAsset[]>([]),[selected,setSelected]=useState<SpriteAsset|null>(null);
  const [name,setName]=useState(''),[meta,setMeta]=useState<SpriteMetadata>(initial),[encoded,setEncoded]=useState<string>();
  const [source,setSource]=useState(''),[size,setSize]=useState({width:0,height:0}),[cells,setCells]=useState({w:128,h:128});
  const [zoom,setZoom]=useState(1),[active,setActive]=useState<number[]>([]),[state,setState]=useState('idle'),[playing,setPlaying]=useState(true);
  const [entity,setEntity]=useState(''),[busy,setBusy]=useState(false),[notice,setNotice]=useState(''),[error,setError]=useState('');
  const sheet=useRef<HTMLCanvasElement>(null),alive=useRef(true),request=useRef<{fingerprint:string;id:string}|undefined>(undefined);
  useEffect(()=>{alive.current=true;listSprites().then(items=>{if(alive.current)setAssets(items);}).catch(e=>{if(alive.current)setError(String(e.message));});return()=>{alive.current=false;};},[]);
  useEffect(()=>{
    let canceled=false;
    if(source)loadSpriteImage(source).then(image=>{
      if(canceled||!sheet.current)return;
      const canvas=sheet.current;canvas.width=image.width;canvas.height=image.height;
      const ctx=canvas.getContext('2d')!;ctx.clearRect(0,0,canvas.width,canvas.height);ctx.drawImage(image,0,0);
      meta.frames.forEach((frame,index)=>{ctx.strokeStyle=active.includes(index)?'#55dcff':'#778999';ctx.lineWidth=active.includes(index)?3:1;ctx.strokeRect(frame.x+.5,frame.y+.5,frame.w-1,frame.h-1);});
      if(zoom>=8){ctx.beginPath();ctx.strokeStyle='#9995';ctx.lineWidth=.12;for(let x=0;x<image.width;x++){ctx.moveTo(x,0);ctx.lineTo(x,image.height);}for(let y=0;y<image.height;y++){ctx.moveTo(0,y);ctx.lineTo(image.width,y);}ctx.stroke();}
    }).catch(()=>{if(!canceled)setError('Não foi possível abrir o PNG');});
    return()=>{canceled=true;};
  },[source,meta.frames,active,zoom]);
  function useAsset(asset:SpriteAsset){setSelected(asset);setName(asset.name||'Sprite');setMeta(structuredClone(asset.metadata));setSource(spriteImageUrl(asset));setSize({width:asset.width,height:asset.height});setEncoded(undefined);setActive([]);setError('');setNotice('');}
  async function importPng(file:File){
    setError('');setNotice('');
    if(file.size>8_000_000){setError('Use PNG de até 8 MB');return;}
    try{
      const bytes=new Uint8Array(await file.arrayBuffer());
      if([137,80,78,71,13,10,26,10].some((n,i)=>bytes[i]!==n))throw new Error('Importe um PNG válido');
      const url=await new Promise<string>((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result));reader.onerror=reject;reader.readAsDataURL(file);});
      const image=await loadSpriteImage(url);if(image.width>4096||image.height>4096||image.width*image.height>8_000_000)throw new Error('Imagem excede os limites');
      if(!alive.current)return;
      setSource(url);setSize({width:image.width,height:image.height});setEncoded(url.split(',')[1]);
      if(!selected){setName(file.name.replace(/\.png$/i,''));setCells({w:image.width,h:image.height});setMeta({...initial,canvas_width:Math.min(512,image.width),canvas_height:Math.min(512,image.height),frames:sliceSheet(image.width,image.height,image.width,image.height),animations:{idle:{frames:[0],fps:4,loop:true,direction:'down'}}});}
      setActive([]);
    }catch(reason){setError(reason instanceof Error?reason.message:'Falha ao importar PNG');}
  }
  function slice(){try{const frames=sliceSheet(size.width,size.height,cells.w,cells.h);setMeta({...meta,canvas_width:Math.min(1024,cells.w),canvas_height:Math.min(1024,cells.h),frames,animations:{idle:{frames:[0],fps:4,loop:true,direction:'down'}}});setActive([]);setError('');}catch(e){setError(String((e as Error).message));}}
  function assign(){if(!active.length)return;setMeta({...meta,animations:{...meta.animations,[state]:{frames:[...active],fps:meta.animations[state]?.fps||6,loop:state!=='death',direction:state.replace('walk_','')}}});}
  async function operation(fn:()=>Promise<void>){if(busy)return;setBusy(true);setError('');setNotice('');try{await fn();}catch(e){setError(e instanceof Error?e.message:'Falha na operação');}finally{if(alive.current)setBusy(false);}}
  async function save(){
    const payload={asset_id:selected?.id,expected_version:selected?.version||0,name,metadata:meta,png_base64:encoded};
    const fingerprint=JSON.stringify(payload);
    if(request.current?.fingerprint!==fingerprint)request.current={fingerprint,id:crypto.randomUUID()};
    const asset=await saveSprite({...payload,request_id:request.current.id});
    setAssets(items=>[asset,...items.filter(item=>item.id!==asset.id)]);useAsset(asset);setNotice('Sprite salvo');await onChange();
  }
  const preview:SpriteAsset={id:selected?.id||'draft',version:selected?.version||0,image_hash:selected?.image_hash||'',width:size.width,height:size.height,metadata:meta};
  const frame=active.length===1?meta.frames[active[0]]:null;
  const animation=meta.animations[state];
  return <section className="sprite-studio" aria-label="Sprite Studio">
    <fieldset disabled={busy} style={{border:0,padding:0,margin:0,minWidth:0}}>
    <header><h3>Sprite Studio</h3><button disabled={busy} onClick={()=>{setSelected(null);setName('');setMeta(initial);setSource('');setEncoded(undefined);setActive([]);setNotice('');}}>Novo</button><button disabled={busy} onClick={()=>void operation(async()=>{
      const root=(import.meta.env.VITE_API_BASE_URL||'')+'/companion-assets/sprites/';
      const [json,image]=await Promise.all([fetch(root+'dorn-demo-v1.json'),fetch(root+'dorn-demo-v1.png')]);
      if(!json.ok||!image.ok)throw new Error('Exemplo de Dorn indisponível');
      const draft:SpriteMetadata=await json.json();const blob=await image.blob();
      const url=await new Promise<string>((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result));reader.onerror=reject;reader.readAsDataURL(blob);});
      setSelected(null);setName('Dorn — animação de teste');setSource(url);setEncoded(url.split(',')[1]);setMeta(draft);setSize({width:512,height:336});setCells({w:128,h:168});setActive([]);setZoom(1);setNotice('Arte de teste derivada do original de Dorn. Salve e associe para usar.');
    })}>Exemplo de Dorn</button></header>
    <div className="sprite-asset-list">{assets.map(asset=><button key={asset.id} onClick={()=>useAsset(asset)} aria-pressed={selected?.id===asset.id}>{asset.name}</button>)}</div>
    <label>PNG / sprite sheet<input aria-label="Importar PNG" type="file" accept="image/png" disabled={busy} onChange={e=>{const file=e.target.files?.[0];if(file)void operation(()=>importPng(file));e.target.value='';}}/></label>
    {source&&<div className="sprite-editor">
      <label>Nome<input aria-label="Nome do sprite" value={name} maxLength={100} onChange={e=>setName(e.target.value)}/></label>
      <div className="sprite-tools"><label>Largura do recorte<input aria-label="Largura do quadro" type="number" min={1} max={4096} value={cells.w} onChange={e=>setCells({...cells,w:Number(e.target.value)})}/></label><label>Altura do recorte<input aria-label="Altura do quadro" type="number" min={1} max={4096} value={cells.h} onChange={e=>setCells({...cells,h:Number(e.target.value)})}/></label><button onClick={slice}>Separar quadros</button><label>Zoom<select value={zoom} onChange={e=>setZoom(Number(e.target.value))}>{[.25,.5,1,2,4,8,16].map(n=><option key={n} value={n}>{n}×</option>)}</select></label></div>
      <div className="sprite-sheet-viewport"><canvas ref={sheet} aria-label="Selecionar quadros na imagem" style={{width:size.width*zoom,height:size.height*zoom}} onClick={event=>{const rect=event.currentTarget.getBoundingClientRect();const x=(event.clientX-rect.left)/zoom,y=(event.clientY-rect.top)/zoom;const index=meta.frames.findIndex(f=>x>=f.x&&x<f.x+f.w&&y>=f.y&&y<f.y+f.h);if(index>=0)setActive(items=>items.includes(index)?items.filter(i=>i!==index):[...items,index]);}}/></div>
      <div className="sprite-timeline" aria-label="Quadros disponíveis">{meta.frames.map((_,i)=><button key={i} aria-label={`Quadro ${i+1}`} aria-pressed={active.includes(i)} onClick={()=>setActive(items=>items.includes(i)?items.filter(n=>n!==i):[...items,i])}>{i+1}</button>)}</div>
      <small>Selecione os quadros na ordem de reprodução.</small>
      {frame&&<details><summary>Recorte e alinhamento do quadro {active[0]+1}</summary><div className="sprite-tools">{(['x','y','w','h','offset_x','offset_y','scale'] as const).map(key=><label key={key}>{key}<input aria-label={`Quadro ${key}`} type="number" step={key==='scale'?'.1':'1'} value={frame[key]} onChange={e=>setMeta({...meta,frames:meta.frames.map((f,i)=>i===active[0]?{...f,[key]:Number(e.target.value)}:f)})}/></label>)}<button onClick={()=>setMeta({...meta,frames:[...meta.frames,{...frame}]})} disabled={meta.frames.length>=256}>Duplicar quadro</button></div></details>}
      <div className="sprite-tools"><label>Animação<select aria-label="Estado da animação" value={state} onChange={e=>setState(e.target.value)}>{Array.from(new Set([...states,...Object.keys(meta.animations)])).map(n=><option key={n}>{n}</option>)}</select></label><button disabled={!active.length} onClick={assign}>Usar seleção nesta animação</button><button onClick={()=>{const value=window.prompt('Nome do novo estado (ex.: interact)');if(value&&/^[a-z][a-z0-9_]{0,39}$/.test(value)){setState(value);setMeta({...meta,animations:{...meta.animations,[value]:{frames:[0],fps:6,loop:true,direction:'down'}}});}}}>+ Estado</button></div>
      {animation&&<><div className="sprite-tools"><label>FPS<input aria-label="FPS" type="number" min={1} max={30} value={animation.fps} onChange={e=>setMeta({...meta,animations:{...meta.animations,[state]:{...animation,fps:Number(e.target.value),durations_ms:undefined}}})}/></label><label><input type="checkbox" checked={animation.loop} onChange={e=>setMeta({...meta,animations:{...meta.animations,[state]:{...animation,loop:e.target.checked}}})}/>Repetir</label><button aria-label={playing?'Pausar prévia':'Reproduzir prévia'} onClick={()=>setPlaying(!playing)}>{playing?'Pausar':'Reproduzir'}</button></div><div className="sprite-timeline" aria-label="Timeline">{animation.frames.map((n,i)=><button key={i} title="Clique para remover da sequência" onClick={()=>{if(animation.frames.length>1)setMeta({...meta,animations:{...meta.animations,[state]:{...animation,frames:animation.frames.filter((_,j)=>i!==j),durations_ms:undefined}}});}}>{n+1} ×</button>)}</div></>}
      <div className="sprite-preview-box">{meta.frames.length>0&&<LocalPreview asset={preview} source={source} state={state} playing={playing}/>}</div>
      <div className="sprite-tools"><label>Escala no mapa<input aria-label="Escala do sprite" type="number" min={.25} max={4} step={.25} value={meta.scale} onChange={e=>setMeta({...meta,scale:Number(e.target.value)})}/></label><button disabled={busy||!name||!meta.frames.length} onClick={()=>void operation(save)}>Salvar sprite</button>{selected&&<button disabled={busy} onClick={()=>void operation(()=>exportSprite(selected))}>Exportar PNG + JSON</button>}</div>
      {selected&&<div className="sprite-binding"><label>Personagem, criatura ou objeto<select aria-label="Associar sprite" value={entity} onChange={e=>setEntity(e.target.value)}><option value="">Selecionar…</option>{entities.map(item=><option key={`${item.entity_type}:${item.id}`} value={`${item.entity_type}:${item.id}`}>{item.name}</option>)}</select></label><button disabled={!entity||busy} onClick={()=>void operation(async()=>{const split=entity.indexOf(':');await bindSprite(entity.slice(0,split) as 'character'|'token',entity.slice(split+1),selected.id,crypto.randomUUID());await onChange();setNotice('Sprite associado ao pin');})}>Associar</button><button disabled={!entity||busy} onClick={()=>void operation(async()=>{const split=entity.indexOf(':');await bindSprite(entity.slice(0,split) as 'character'|'token',entity.slice(split+1),null,crypto.randomUUID());await onChange();setNotice('Token estático restaurado');})}>Usar token estático</button></div>}
    </div>}
    </fieldset>
    {error&&<p role="alert">{error}</p>}{notice&&<p role="status">{notice}</p>}
  </section>;
}

/** Draft URL stays local; map renderer always uses the authorized saved atlas. */
function LocalPreview({asset,source,state,playing}:{asset:SpriteAsset;source:string;state:string;playing:boolean}){
  const ref=useRef<HTMLCanvasElement>(null);
  useEffect(()=>{let canceled=false,stop=()=>{};loadSpriteImage(source).then(image=>{if(canceled)return;const started=performance.now();let previous=-1;stop=subscribeSpriteClock(now=>{if(!ref.current)return;const index=frameAt(asset.metadata,state,playing?now-started:0);if(index===previous)return;const f=asset.metadata.frames[index],ctx=ref.current.getContext('2d');if(!f||!ctx)return;ctx.clearRect(0,0,128,128);ctx.imageSmoothingEnabled=false;const fit=Math.min(128/f.w,128/f.h)*f.scale;ctx.drawImage(image,f.x,f.y,f.w,f.h,(128-f.w*fit)/2+f.offset_x,(128-f.h*fit)/2+f.offset_y,f.w*fit,f.h*fit);previous=index;});}).catch(()=>{});return()=>{canceled=true;stop();};},[source,asset.metadata,state,playing]);
  return <canvas ref={ref} className="sprite-preview" width={128} height={128} aria-label="Prévia da animação"/>;
}
