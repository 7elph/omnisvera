export default function AttackDirectionChoice({required,value,onChange}:{
  required:boolean; value?:boolean; onChange:(value:boolean|undefined)=>void;
}) {
  if(!required)return null;
  return <label>Lado do escudo torre<select aria-label="Lado do escudo torre"
    value={value===undefined?'':value?'protected':'open'}
    onChange={event=>onChange(event.target.value==='protected'?true:event.target.value==='open'?false:undefined)}>
    <option value="">Confirmar direção…</option>
    <option value="protected">Pelo lado protegido</option>
    <option value="open">Pelo lado desprotegido</option>
  </select></label>;
}
