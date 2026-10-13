// Preview server: node video/render/serve.mjs [--port 8130]
// then open http://127.0.0.1:8130/scenes/<scene>.html  (?play=1, ?t=12.3, ?static=1)
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readdirSync } from 'node:fs';
import { startServer } from './static_server.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const i = process.argv.indexOf('--port');
const port = i > 0 ? Number(process.argv[i + 1]) : 8130;
const { port: p } = await startServer(root, port);
console.log(`Serving ${root} at http://127.0.0.1:${p}/`);
for (const f of readdirSync(path.join(root, 'scenes')).filter((f) => f.endsWith('.html'))) {
  console.log(`  http://127.0.0.1:${p}/scenes/${f}?play=1`);
}
