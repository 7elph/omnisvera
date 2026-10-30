const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
function render(open,extra={}){let next;const module={exports:{}};const jsx=(type,props)=>({type,props});
  vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/components/SheetDetail.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module,exports:module.exports,document:{body:'body'},require:id=>id==='react'?{useState:()=>[open,v=>next=v],useEffect:()=>{},useRef:()=>({current:null})}:id==='react-dom'?{createPortal:(tree,destination)=>({type:'portal',props:{children:tree,destination}})}:id==='../api'?{imagePreviewUrl:url=>url.startsWith('/media/')?url+'?preview_size=128':url}:{jsx,jsxs:jsx}});
  return {tree:module.exports.default({title:'Força Arcana',description:'Descrição aprovada',icon:'forca.jpg',...extra}),getNext:()=>next};
}
const walk=v=>Array.isArray(v)?v.flatMap(walk):v&&typeof v==='object'?[v,...walk(v.props?.children)]:[];

test('custom visual content may keep an explicit accessible trigger label',()=>{
 const {tree}=render(false,{children:'0 25 105 0',triggerLabel:'Editar moedas'});
 assert.equal(walk(tree).find(n=>n.type==='button').props['aria-label'],'Editar moedas');
 assert.equal(walk(render(false).tree).find(n=>n.type==='button').props['aria-label'],undefined,'Other existing trigger names remain unchanged');
});
test('read-only compact name opens detail without invoking any game action',()=>{
 const {tree,getNext}=render(false);const button=walk(tree).find(n=>n.type==='button');assert.equal(button.props.className,'workspace-ability-name');button.props.onClick();assert.equal(getNext(),true);assert.equal(walk(tree).filter(n=>n.type==='portal').length,0);
});
test('floating detail includes original image, text, accessible close and body portal',()=>{
 const {tree,getNext}=render(true),nodes=walk(tree);assert.equal(nodes.find(n=>n.type==='portal').props.destination,'body');assert.ok(nodes.some(n=>n.props?.role==='dialog'));assert.equal(nodes.find(n=>n.props?.className==='workspace-detail-image').props.src,'forca.jpg');assert.ok(nodes.some(n=>n.type==='p'&&n.props.children==='Descrição aprovada'));nodes.find(n=>n.props?.['aria-label']==='Fechar descrição').props.onClick();assert.equal(getNext(),false);
});

test('compact icon uses a preview while its detail preserves the original URL',()=>{
 const nodes=walk(render(true,{icon:'/media/zz_media/item.png'}).tree);
 assert.equal(nodes.find(n=>n.type==='img'&&!n.props.className).props.src,'/media/zz_media/item.png?preview_size=128');
 assert.equal(nodes.find(n=>n.props?.className==='workspace-detail-image').props.src,'/media/zz_media/item.png');
});
test('night form title spans the row above selector, without global font changes',()=>{
 const css=fs.readFileSync('src/styles.css','utf8');assert.match(css,/workspace-night-form-card > span \{ grid-column: 1; grid-row: 1;/);assert.match(css,/article.workspace-night-form-card \{ grid-template-columns: minmax\(0, 1fr\)/);
 const source=fs.readFileSync('src/pages/SessionWorkspace.tsx','utf8');assert.ok(source.includes("ability.id === 'forma-da-noite' ? 'workspace-night-form-card'"));assert.ok(source.includes('Imagem de ${ability.name}'));assert.ok(source.includes('ability.image_path || nightArt'));
});
