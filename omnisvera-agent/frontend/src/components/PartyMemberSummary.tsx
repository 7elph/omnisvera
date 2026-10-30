export default function PartyMemberSummary({name,className,level,color,hp,maximumHp}:{
  name:string;className:string;level:number|null|undefined;color?:string;hp?:number|null;maximumHp?:number|null;
}){
  const percent=maximumHp?Math.max(0,Math.min(100,Number(hp||0)/maximumHp*100)):0;
  return <span className="party-card-copy"><strong style={{color}}>{name}</strong><small>{className}</small>
    <span className="party-card-vitals"><i role="progressbar" aria-label={`Vida de ${name}`} aria-valuenow={hp??0} aria-valuemin={0} aria-valuemax={maximumHp||1}><b style={{width:`${percent}%`}} /></i>
      <em className="party-card-level" aria-label={`Nível ${level??'não informado'}`} title="Nível">{level??'—'}</em>
    </span>
  </span>;
}
