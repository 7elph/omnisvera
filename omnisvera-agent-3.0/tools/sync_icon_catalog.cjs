// Copy data, not the React runtime. Re-run when the legacy icon mapping changes.
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm'), crypto = require('node:crypto');
const project = path.resolve(__dirname, '..');
const frontend = path.resolve(project, '../omnisvera-agent/frontend');
const ts = require(require.resolve('typescript', {paths: [frontend]}));
const source = fs.readFileSync(path.join(frontend, 'src/companionIconCatalog.ts'), 'utf8');
const code = ts.transpileModule(source + '\nexport const GODOT_DATA = {ids: ITEM_ICON_IDS, aliases: ITEM_ALIASES, extensions: ITEM_ICON_EXTENSIONS};', {
  compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020}
}).outputText;
const context = {exports: {}};
vm.runInNewContext(code, context, {timeout: 1000});
const data = {schema_version: 1, source: 'frontend/src/companionIconCatalog.ts', source_sha256: crypto.createHash('sha256').update(source).digest('hex'), ...context.exports.GODOT_DATA};
fs.writeFileSync(path.join(project, 'assets/ui/item-icons.json'), JSON.stringify(data, null, 2) + '\n');
console.log('Synced ' + data.ids.length + ' existing item icon mappings');
