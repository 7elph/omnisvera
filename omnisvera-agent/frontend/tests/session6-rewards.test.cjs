const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const esbuild = require('esbuild');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');

function component(file) {
  const bundle = esbuild.buildSync({ entryPoints: [`src/components/${file}.tsx`], bundle: true, write: false,
    platform: 'node', format: 'cjs', jsx: 'automatic', external: ['react', 'react-dom'], define: { 'import.meta.env': '{}' } });
  const module = { exports: {} };
  vm.runInNewContext(bundle.outputFiles[0].text, { module, exports: module.exports, require, console, URL, URLSearchParams, localStorage: { getItem: () => null } });
  return module.exports.default;
}

test('bracelet stays beside item resources and never consumes inventory quantity', () => {
  const source = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
  assert.ok(source.includes("item.item_title === 'Pulseira de Vinhas'"));
  assert.ok(source.includes('<VineBraceletControl'));
  assert.ok(source.includes('<SkeletonReward token={openToken} />'));
  assert.ok(!fs.readFileSync('src/components/VineBraceletControl.tsx', 'utf8').includes('change_quantity'));
});

test('bracelet shows compact target selector and refuses use while unequipped', () => {
  const html = renderToStaticMarkup(React.createElement(component('VineBraceletControl'), {
    equipped: false, disabled: false, tokens: [{ id: 'enemy', name: 'Lobo', current_hp: 10 }], onChange: async () => {},
  }));
  assert.match(html, /Alvo da Pulseira de Vinhas/);
  assert.match(html, /Equipe para usar/);
  assert.match(html, /<button[^>]*disabled=""/);
});

test('skeleton reward card uses the essence icon and equipped state', () => {
  const html = renderToStaticMarkup(React.createElement(component('SkeletonReward'), {
    token: { sheet: { reward_items: [{ name: 'Essência de Mana', description: 'Recompensa', image_path: 'essence.jpg', equipped: true }] } },
  }));
  assert.match(html, /Essência de Mana/);
  assert.match(html, /essence.jpg/);
  assert.match(html, /Equipada por Morthak/);
});

test('bracelet exposes remaining daily charges beside its icon', () => {
  const html = renderToStaticMarkup(React.createElement(component('VineBraceletControl'), {
    equipped: true, disabled: false, remaining: 0, maximum: 2, tokens: [],
    onChange: async () => {}, onToggleEquipment: async () => {},
  }));
  assert.match(html, /<b>0\/2<\/b>/);
  assert.match(html, /<button[^>]*disabled="">Usar<\/button>/);
});

test('bracelet resource card never edits equipment; inventory remains the sole equipment control', () => {
  const Control = component('VineBraceletControl');
  for (const equipped of [false, true]) {
    const html = renderToStaticMarkup(React.createElement(Control, {
      equipped, disabled: true, equipmentDisabled: false, tokens: [],
      onChange: async () => {}, onToggleEquipment: async () => {},
    }));
    assert.ok(!html.includes('>Guardar</button>'));
    assert.ok(!html.includes('>Equipar</button>'));
  }
  const locked = renderToStaticMarkup(React.createElement(Control, {
    equipped: false, disabled: false, equipmentDisabled: true, tokens: [],
    onChange: async () => {}, onToggleEquipment: async () => {},
  }));
  assert.ok(!locked.includes('>Equipar</button>'));
  const source = fs.readFileSync('src/pages/SessionWorkspace.tsx', 'utf8');
  assert.ok(!source.includes('onToggleEquipment='));
  assert.ok(source.includes('"unequip_item", {item_path:openItem.item_path}'));
  assert.ok(source.includes('item.item_title === \'Pulseira de Vinhas\' || !resourceItem(item)'));
});
