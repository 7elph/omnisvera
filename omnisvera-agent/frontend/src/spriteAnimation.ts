/** Independent atlas timing/math. No game state, movement budget or entity writes. */
export type SpriteFrame={x:number;y:number;w:number;h:number;offset_x:number;offset_y:number;scale:number};
export type SpriteAnimation={frames:number[];fps:number;loop:boolean;direction:string;durations_ms?:number[]};
export type SpriteMetadata={schema_version:1;canvas_width:number;canvas_height:number;pivot:[number,number];scale:number;frames:SpriteFrame[];animations:Record<string,SpriteAnimation>};
export type SpriteAsset={id:string;version:number;image_hash:string;width:number;height:number;metadata:SpriteMetadata;name?:string;updated_at?:string};

export function animationFor(meta:SpriteMetadata,state:string):SpriteAnimation {
  return meta.animations[state] || meta.animations.idle || Object.values(meta.animations)[0];
}
export function frameAt(meta:SpriteMetadata,state:string,elapsed:number,reduced=false):number {
  const animation=animationFor(meta,state);
  if(!animation?.frames.length)return 0;
  if(reduced)return animation.frames[0];
  const durations=animation.durations_ms || animation.frames.map(()=>1000/animation.fps);
  const total=durations.reduce((a,b)=>a+b,0);
  if(total<=0)return animation.frames[0];
  let time=animation.loop ? Math.max(0,elapsed)%total : Math.min(Math.max(0,elapsed),total-.001);
  for(let i=0;i<durations.length;i++){if(time<durations[i])return animation.frames[i];time-=durations[i];}
  return animation.frames[animation.frames.length-1];
}
export function walkDirection(dx:number,dy:number):string {
  return Math.abs(dx)>Math.abs(dy) ? (dx<0?'walk_left':'walk_right') : (dy<0?'walk_up':'walk_down');
}
export function sliceSheet(width:number,height:number,cellWidth:number,cellHeight:number):SpriteFrame[] {
  if(![width,height,cellWidth,cellHeight].every(n=>Number.isInteger(n)&&n>0))throw new Error('Dimensões inválidas');
  const cols=Math.floor(width/cellWidth),rows=Math.floor(height/cellHeight);
  if(!cols||!rows||cols*rows>256)throw new Error('Use entre 1 e 256 quadros');
  return Array.from({length:cols*rows},(_,n)=>({x:n%cols*cellWidth,y:Math.floor(n/cols)*cellHeight,w:cellWidth,h:cellHeight,offset_x:0,offset_y:0,scale:1}));
}

export type ImageResult=HTMLImageElement;
const images=new Map<string,Promise<ImageResult>>();
const decodedPixels=new Map<string,number>();
function trimImages(keep:string){
  while(images.size>24||Array.from(decodedPixels.values()).reduce((a,b)=>a+b,0)>8_000_000){
    const oldest=Array.from(images.keys()).find(key=>key!==keep);if(!oldest)break;
    images.delete(oldest);decodedPixels.delete(oldest);
  }
}
/** One decoded image shared by all pins/previews; bounded, no per-frame fetch. */
export function loadSpriteImage(url:string):Promise<ImageResult> {
  const existing=images.get(url);if(existing){images.delete(url);images.set(url,existing);return existing;}
  const promise=new Promise<ImageResult>((resolve,reject)=>{const image=new Image();image.onload=()=>{if(images.has(url)){decodedPixels.set(url,(image.naturalWidth||0)*(image.naturalHeight||0));trimImages(url);}resolve(image);};image.onerror=()=>reject(new Error('Falha ao carregar sprite'));image.src=url;});
  images.set(url,promise);
  trimImages(url);
  return promise;
}

type Tick=(now:number)=>void;
const listeners=new Set<Tick>();let raf=0;
function tick(now:number){raf=0;if(!document.hidden)listeners.forEach(fn=>fn(now));if(listeners.size)raf=requestAnimationFrame(tick);}
export function subscribeSpriteClock(listener:Tick){listeners.add(listener);if(!raf)raf=requestAnimationFrame(tick);return()=>{listeners.delete(listener);if(!listeners.size&&raf){cancelAnimationFrame(raf);raf=0;}};}
