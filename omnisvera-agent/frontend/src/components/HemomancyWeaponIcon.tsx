export default function HemomancyWeaponIcon({weapon}:{weapon?:string}){
 const paths:Record<string,string>={arco:'M7 3 Q22 12 7 21 L7 3 M3 12 H22 M18 8 L22 12 L18 16',foice:'M8 22 L13 3 Q23 0 23 11 Q18 5 13 6',marreta:'M12 22 V9 M5 3 H19 V9 H5 Z',escudo:'M4 3 H20 V12 Q20 19 12 23 Q4 19 4 12 Z',lanca:'M4 22 L18 8 M14 7 L22 2 L19 11 Z'};
 return <svg className="workspace-blood-weapon-icon" viewBox="0 0 26 26" role="img" aria-label={weapon||'Arma inativa'} fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d={paths[weapon||'']||'M6 6 L20 20 M20 6 L6 20'}/></svg>;
}
