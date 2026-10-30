// Private pipe, not the MCP/user input. The parent sends one byte only AFTER
// assigning this exact Node child to its owned Windows process group.
const fs=require('node:fs');
const gate=Buffer.alloc(1);
try{
 if(fs.readSync(0,gate,0,1,null)!==1||gate[0]!==49)process.exit(2);
 fs.closeSync(0);
}catch{process.exit(2);}
