const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const source = fs.readFileSync(path.join(__dirname, '../src/components/diceTiming.ts'), 'utf8');
const compiled = ts.transpileModule(source, {compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText;
const timingModule = {exports:{}};
vm.runInNewContext(compiled, {module:timingModule, exports:timingModule.exports});
const timing = timingModule.exports;

test('visual settling uses wall clock at 60, 30, 15 and 10 FPS', () => {
  const end = timing.DICE_SETTLE_START + timing.DICE_SETTLE_DURATION;
  for (const fps of [60,30,15,10]) {
    let frame = 0;
    while (timing.diceElapsedSeconds(1000, 1000 + frame * 1000 / fps) < end) frame++;
    assert.ok(frame / fps <= end + 1 / fps);
    assert.ok(frame / fps < 1.7);
  }
  assert.ok(timing.DICE_OVERLAY_MS > end * 1000);
  assert.ok(timing.DICE_OVERLAY_MS <= 2500);
});

test('overlay renders the server result before any physics-ready callback', () => {
  let cursor = 0;
  const roll = {id:1,label:'Teste',dice:'1d20',individual_results:[15],modifier:4,total:19};
  const module = {exports:{}};
  const jsx = (type,props) => ({type,props:props || {}});
  const react = {useState:initial => [cursor++ === 0 ? roll : initial,()=>{}],
    useRef:value => ({current:value}),useEffect:()=>{}};
  const overlaySource = fs.readFileSync(path.join(__dirname, '../src/components/DiceRollOverlay.tsx'), 'utf8');
  const code = ts.transpileModule(overlaySource, {compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText;
  vm.runInNewContext(code,{module,exports:module.exports,
    require:name => name === 'react' ? react : name === 'react/jsx-runtime' ? {jsx,jsxs:jsx}
      : name === './diceTiming' ? timing : {default:()=>null,preloadDicePhysics:()=>new Promise(()=>{})}});
  const tree = module.exports.default({});
  const math = tree.props.children.find(n => n?.props?.className === 'dice-roll-math');
  assert.ok(math);
  assert.equal(math.props.children.find(n=>n.type === 'strong').props.children,19);
});
