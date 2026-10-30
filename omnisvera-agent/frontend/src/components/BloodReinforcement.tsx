export default function BloodReinforcement({multiplier,turns,blood,disabled,onActivate}:{multiplier:number;turns:number;blood:number;disabled:boolean;onActivate:(factor:number)=>void}){
 return <div className="workspace-blood-multipliers" aria-label="Reforço de ataque e dano"><span>Reforço</span><div role="group" aria-label="Multiplicador">
  {[1,2,3].map(factor=><button type="button" key={factor} aria-pressed={multiplier===factor} disabled={disabled||(factor>1&&(blood<factor||multiplier>1))} title={factor===1?'Normal; cancelar não devolve sangue':`${factor} sangue · BA e dano por 2 turnos`} onClick={()=>onActivate(factor)}>x{factor}</button>)}
 </div>{multiplier>1&&<small>{turns} turnos</small>}</div>;
}
