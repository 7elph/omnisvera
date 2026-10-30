// Compare a multiset: inherited GM warnings do not become errors of this action.
function unexpectedAlerts(before,after){
 const remaining=new Map();
 for(const text of before)remaining.set(text,(remaining.get(text)||0)+1);
 return after.filter(text=>{
  const count=remaining.get(text)||0;
  if(count){remaining.set(text,count-1);return false;}
  return true;
 });
}
module.exports={unexpectedAlerts};
