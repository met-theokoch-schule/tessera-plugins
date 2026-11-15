// Execute Tessera's actual editor functions with empty-page store fixtures.
// Usage: node kidsplayer/tests/test_resize.mjs CORE_CHECKOUT < sizes.json
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { stripTypeScriptTypes } from 'node:module';
const core = process.argv[2];
const sizes = JSON.parse(fs.readFileSync(0, 'utf8'));
function extract(file, name) {
  const text = fs.readFileSync(path.join(core, file), 'utf8');
  const start = text.indexOf(`export function ${name}(`);
  assert(start >= 0, `Missing editor function ${name}`);
  // These functions have a line containing only } at their end.
  const end = text.indexOf('\n}', start);
  assert(end >= 0);
  return text.slice(start, end + 2).replace('export ', '');
}
const grid = {columns: 2, rows: 3};
const doc = {editorLayout: {grid, occupied: () => [], fits: (_, slot, size) => {
  const d = context.dimensions(size, grid);
  return slot % grid.columns + d.columns <= grid.columns && Math.floor(slot / grid.columns) + d.rows <= grid.rows;
}}, layout: {}, document: {pages: [{tiles: [{id: 'kids'}]}]}};
let bounds = sizes;
const context = vm.createContext({
  asSize: x => x,
  useDocumentStore: () => doc,
  useInventoryStore: () => ({tallerTilesEnabled: true}),
  usePluginsStore: () => ({pluginTileOf: () => ({tile: bounds})}),
  screenSizes: () => ['single', 'wide', 'tall', 'square', 'full'],
  pageTarget: () => false,
  currentView: x => x,
  sizeOf: x => x.options.size,
  entriesOf: () => [], validateCardOptions: () => {},
  spanOffered: () => false,
  DEFAULT_GRID: grid,
});
const source = [
  extract('web/src/model/sizes.ts', 'spanOf'),
  extract('web/src/model/layout.ts', 'dimensions'),
  extract('web/src/editor/tiles.ts', 'tileSizeChoices'),
  extract('web/src/editor/tiles.ts', 'resizeChoices'),
].join('\n');
vm.runInContext(stripTypeScriptTypes(source), context);
const choices = (size, axis) => Array.from(context.resizeChoices({id:'kids', entity:'plugin:kidsplayer.library', slot:0, options:{size}}, axis));
// Reproduce the reported failure with the old manifest.
bounds = {min:'2x2', max:'4x4'};
assert.deepEqual(choices('single', 'columns'), []);
assert.deepEqual(choices('single', 'rows'), []);
// Both resize paths must work with the shipped manifest.
bounds = sizes;
assert(choices('single', 'columns').includes('wide'));
assert(choices('single', 'rows').includes('tall'));
assert(choices('wide', 'rows').includes('square'));
assert(choices('tall', 'columns').includes('square'));
assert(choices('square', 'rows').includes('wide'));
console.log('Actual Tessera editor: old missing handles reproduced; 1x1 → 2x1/1x2 → 2x2 and shrinking passed');
