// Fixture calibration only; never changes the game's attack or shield rules.
function shieldNearMiss(baseAc,shieldedAc,attackBonus=0){
 if(![baseAc,shieldedAc,attackBonus].every(Number.isInteger)||baseAc<=0||shieldedAc-baseAc!==2)return null;
 for(const margin of [1,2]){
  const attack_total=shieldedAc-margin,d20=attack_total-attackBonus;
  if(d20>=2&&d20<=19&&attack_total>=baseAc)
   return {d20,attack_total,target_ac:shieldedAc,margin};
 }
 return null;
}
module.exports={shieldNearMiss};
