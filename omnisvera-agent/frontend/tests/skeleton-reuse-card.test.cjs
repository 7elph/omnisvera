const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');

const source=ts.createSourceFile('SessionWorkspace.tsx',fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8'),ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
let expression;
function visit(node){
 if(ts.isIfStatement(node)&&node.expression.getText(source).includes("['levantar-esqueleto','levantar-um-esqueleto']")){
  function button(child){
   if(ts.isJsxOpeningElement(child)&&child.tagName.getText(source)==='button'){
    const disabled=child.attributes.properties.find(attr=>attr.name?.getText(source)==='disabled');
    if(disabled)expression=disabled.initializer.expression.getText(source);
   }
   ts.forEachChild(child,button);
  }
  button(node.thenStatement);
 }
 ts.forEachChild(node,visit);
}
visit(source);assert.ok(expression,'Read the actual skeleton card disabled expression');
const disabled=(extra={})=>vm.runInNewContext(expression,{canOperate:false,character:{access_level:'owner'},busy:'',ability:{blocked:false},...extra});

test('owner can reopen a living skeleton after casting and outside their action window',()=>assert.equal(disabled(),false));
test('public sheet never exposes controlled skeleton commands',()=>assert.equal(disabled({character:{access_level:'public'}}),true));
test('pending command and blocked ability keep the skeleton card disabled',()=>{
 assert.equal(disabled({busy:'ability:levantar-um-esqueleto'}),true);
 assert.equal(disabled({ability:{blocked:true}}),true);
});
