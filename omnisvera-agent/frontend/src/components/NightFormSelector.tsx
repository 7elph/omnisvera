import { mediaUrlFromVaultPath } from '../api';

export const NIGHT_FORMS = [
  {id:'coruja',label:'Coruja',image:'zz_media/ui/icons/uploads/raziel_coruja_969cca62e9.jpg'},
  {id:'morcego',label:'Morcego',image:'zz_media/ui/icons/uploads/raziel_morcego_82a3c8733e.jpg'},
  {id:'corvo',label:'Corvo',image:'zz_media/ui/icons/uploads/raziel_corvo_ae9c2df01e.jpg'},
];

export default function NightFormSelector({value,onChange}:{value:string;onChange:(value:string)=>void}) {
  const selected=NIGHT_FORMS.find(form=>form.id===value)||NIGHT_FORMS[2];
  return <details className="workspace-night-form-selector" style={{minWidth:0}}>
    <summary aria-label="Animal da Forma da Noite" style={{display:'flex',alignItems:'center',gap:8,cursor:'pointer'}}>
      {selected.label} ▾
    </summary>
    <div role="group" aria-label="Escolher animal da Forma da Noite" style={{display:'grid',gap:4}}>
      {NIGHT_FORMS.map(form=><button key={form.id} type="button" aria-pressed={value===form.id} style={{display:'flex',alignItems:'center',gap:8,textAlign:'left'}} onClick={event=>{onChange(form.id);event.currentTarget.closest('details')?.removeAttribute('open');}}>
        <img src={mediaUrlFromVaultPath(form.image)} alt="" style={{width:48,height:48,objectFit:'cover'}} />{form.label}
      </button>)}
    </div>
  </details>;
}
