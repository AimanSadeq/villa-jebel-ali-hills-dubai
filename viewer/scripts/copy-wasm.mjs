// Copy the web-ifc WASM files that match the installed version into public/wasm,
// so the model viewer loads them locally instead of from a CDN. Runs before dev
// and build.
import { cpSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const out = join(root, 'public', 'wasm');
mkdirSync(out, { recursive: true });
for (const f of ['web-ifc.wasm', 'web-ifc-mt.wasm']) {
  cpSync(join(root, 'node_modules', 'web-ifc', f), join(out, f));
}
console.log('web-ifc wasm copied to public/wasm');
