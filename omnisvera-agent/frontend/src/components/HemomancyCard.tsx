import type { ReactNode } from 'react';
import SpellCard from './SpellCard';
import SheetSection from './SheetSection';
import HemomancyWeaponIcon from './HemomancyWeaponIcon';

export default function HemomancyCard({options,value,onChange,blood,children,animal,activeWeapon}:{
  options:{id:string;label:string}[];value:string;onChange:(id:string)=>void;
  blood:number;children:ReactNode;animal?:string|null;activeWeapon?:{weapon:string;name:string};
}){
  return <SheetSection title="Hemomancia"><section className="workspace-action-catalog workspace-hemomancy" aria-label="Hemomancia">
    <header><span>HEMOMANCIA</span></header>
    <div className="workspace-hemomancy-halves">
    <SpellCard className="workspace-hemomancy-card" heading={<span>Armas</span>} summary={null}>
      <label>Arma<select aria-label="Arma da Hemomancia" value={value} onChange={event=>onChange(event.target.value)} disabled={Boolean(animal)}>
        {options.map(option=><option key={option.id} value={option.id}>{option.label}</option>)}
      </select></label>
      {animal?<p role="status">Forma animal ativa: sem ataques, fala ou poderes humanoides. Desative para usar Hemomancia.</p>:children}
    </SpellCard>
    <aside className="workspace-active-blood-weapon" aria-label="Arma ativa" title={activeWeapon?.name||'Nenhuma arma ativa'}>
      <HemomancyWeaponIcon weapon={activeWeapon?.weapon}/>
      <span className="workspace-visually-hidden">{activeWeapon?.name||'Nenhuma arma ativa'}</span>
    </aside></div>
  </section></SheetSection>;
}
