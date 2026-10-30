export function selectGridTarget(selected: string[], id:string, valid:boolean, maximum:number) {
  if (!valid) return {selected, decision:'invalid' as const};
  if (selected.includes(id)) return {selected, decision:'repeat' as const};
  if (selected.length>=maximum) return {selected,decision:'full' as const};
  const next=[...selected,id];
  return {selected:next,decision:next.length===maximum?'confirm' as const:'continue' as const};
}
