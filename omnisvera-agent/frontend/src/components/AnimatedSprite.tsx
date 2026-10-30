import {useEffect,useRef,useState} from 'react';
import {animationFor,frameAt,loadSpriteImage,subscribeSpriteClock,walkDirection,type SpriteAsset} from '../spriteAnimation';
import {spriteImageUrl} from '../spriteApi';
import './spriteStudio.css';

type Point={longitude:number;latitude:number;map_id?:string};
export default function AnimatedSprite({asset,point,state='idle',playing=true,fallback,preview=false}:{asset:SpriteAsset;point?:Point;state?:string;playing?:boolean;fallback?:React.ReactNode;preview?:boolean}){
  const canvas=useRef<HTMLCanvasElement>(null),previous=useRef<Point|undefined>(point);
  const motion=useRef({state:'idle',until:0,dx:0,dy:0});
  const [failed,setFailed]=useState(false);
  useEffect(()=>{
    const old=previous.current;previous.current=point;
    if(point&&old&&point.map_id===old.map_id&&(point.longitude!==old.longitude||point.latitude!==old.latitude)){
      const dx=point.longitude-old.longitude,dy=point.latitude-old.latitude;
      motion.current={state:walkDirection(dx,dy),until:performance.now()+600,dx,dy};
    }else if(point?.map_id!==old?.map_id)motion.current={state:'idle',until:0,dx:0,dy:0};
  },[point?.longitude,point?.latitude,point?.map_id]);
  useEffect(()=>{
    let disposed=false,unsubscribe=()=>{},visible=true;setFailed(false);
    const node=canvas.current;if(!node)return;
    const observer=typeof IntersectionObserver!=='undefined'?new IntersectionObserver(entries=>{visible=entries[0]?.isIntersecting??true;}):null;
    observer?.observe(node);
    const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const started=performance.now();let lastFrame=-1,lastState='';
    loadSpriteImage(spriteImageUrl(asset)).then(image=>{
      if(disposed)return;
      const draw=(now:number)=>{
        if(!visible||disposed)return;
        const moving=motion.current.until>now&&!preview;
        const active=moving?motion.current.state:state;
        const frameIndex=frameAt(asset.metadata,active,playing?now-started:0,reduced);
        const frame=asset.metadata.frames[frameIndex];if(!frame)return;
        node.dataset.state=active;node.dataset.animation=Object.keys(asset.metadata.animations).find(key=>asset.metadata.animations[key]===animationFor(asset.metadata,active));
        if(frameIndex!==lastFrame||active!==lastState){
          const ctx=node.getContext('2d');if(!ctx)return;
          ctx.clearRect(0,0,node.width,node.height);ctx.imageSmoothingEnabled=false;
          const fit=Math.min(node.width/frame.w,node.height/frame.h)*frame.scale;
          const w=frame.w*fit,h=frame.h*fit;
          const [px,py]=asset.metadata.pivot;
          ctx.drawImage(image,frame.x,frame.y,frame.w,frame.h,node.width*px-w*px+frame.offset_x,node.height*py-h*py+frame.offset_y,w,h);
          lastFrame=frameIndex;lastState=active;node.dataset.frame=String(frameIndex);
        }
        // Cosmetic interpolation only AFTER a new confirmed coordinate arrives.
        const map=node.parentElement?.parentElement;
        const progress=moving&&!reduced?(motion.current.until-now)/600:0;
        const transform=progress&&map?`translate(${-motion.current.dx*map.clientWidth/100*progress}px,${-motion.current.dy*map.clientHeight/100*progress}px) scale(${asset.metadata.scale})`:`scale(${asset.metadata.scale})`;
        if(node.style.transform!==transform)node.style.transform=transform;
      };
      draw(started);unsubscribe=subscribeSpriteClock(draw);
    }).catch(()=>{if(!disposed)setFailed(true);});
    return()=>{disposed=true;unsubscribe();observer?.disconnect();};
  },[asset.id,asset.version,asset.image_hash,state,playing,preview]);
  return <><canvas ref={canvas} style={{display:failed?'none':undefined}} className={preview?'sprite-preview':'sprite-map-canvas'} width={asset.metadata.canvas_width} height={asset.metadata.canvas_height} role="img" aria-label="Sprite animado"/>{failed&&(fallback||<span title="Imagem do sprite indisponível">◇</span>)}</>;
}
