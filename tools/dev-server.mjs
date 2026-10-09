import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(fileURLToPath(new URL('../dist/', import.meta.url)));
const mime = {
  '.html':'text/html; charset=utf-8', '.css':'text/css; charset=utf-8',
  '.js':'text/javascript; charset=utf-8', '.json':'application/json',
  '.webp':'image/webp', '.avif':'image/avif', '.svg':'image/svg+xml',
  '.png':'image/png', '.jpeg':'image/jpeg', '.jpg':'image/jpeg',
  '.woff2':'font/woff2', '.wasm':'application/wasm',
  '.glb':'model/gltf-binary', '.riv':'application/octet-stream',
  '.hdr':'application/octet-stream', '.ktx2':'image/ktx2'
};

createServer(async (request, response) => {
  try {
    let pathname = decodeURIComponent(new URL(request.url, 'http://local').pathname);
    let file = path.resolve(root, '.' + pathname);
    if (file !== root && !file.startsWith(root + path.sep)) { response.writeHead(403).end(); return; }
    let info;
    try { info = await stat(file); } catch {
      if (!path.extname(file)) { file = path.join(file, 'index.html'); info = await stat(file); }
      else throw new Error('Not found');
    }
    if (info.isDirectory()) file = path.join(file, 'index.html');
    const body = await readFile(file);
    response.writeHead(200, {'Content-Type':mime[path.extname(file)] || 'application/octet-stream', 'Cache-Control':'no-cache'});
    response.end(body);
  } catch { response.writeHead(404, {'Content-Type':'text/plain'}).end('Not found'); }
}).listen(Number(process.env.PORT || 4173), '0.0.0.0', () => console.log('Reference replica preview ready'));
