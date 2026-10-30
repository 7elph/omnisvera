const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const source=ts.createSourceFile('SessionWorkspace.tsx',fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8'),ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
let disclosure;
function visit(node){
 if(ts.isJsxElement(node)&&node.openingElement.tagName.getText(source)==='details'&&node.getText(source).includes('<MasterAssetPanel '))disclosure=node.getText(source);
 ts.forEachChild(node,visit);
}
visit(source);assert.ok(disclosure,'Use the actual GM Assets disclosure');
function harness(){
 let open=false;
 const context={React:{createElement:(type,props,...children)=>({type,props:props||{},children})},MasterToolHeading:'heading',MasterAssetPanel:'asset-panel',get assetPanelOpen(){return open;},setAssetPanelOpen:value=>{open=value;}};
 const code=ts.transpileModule('function render(){return ('+disclosure+');}',{compilerOptions:{jsx:ts.JsxEmit.React}}).outputText;
 vm.createContext(context);vm.runInContext(code,context);
 return {render:()=>context.render(),get open(){return open;}};
}
const mounted=node=>Boolean(node&&typeof node==='object'&&(node.type==='asset-panel'||node.children?.some(mounted)));

test('closed GM Assets tool does not mount its polling/reference subtree',()=>{
 const h=harness();assert.equal(mounted(h.render()),false);
});
test('opening mounts Assets and closing unmounts its background polling',()=>{
 const h=harness(),target={open:true};
 h.render().props.onToggle({target,currentTarget:target});assert.equal(h.open,true);assert.equal(mounted(h.render()),true);
 target.open=false;h.render().props.onToggle({target,currentTarget:target});assert.equal(mounted(h.render()),false);
});
test('nested reference disclosures cannot toggle the outer Assets mounting state',()=>{
 const h=harness();h.render().props.onToggle({target:{open:true},currentTarget:{open:true}});assert.equal(h.open,false);
});
