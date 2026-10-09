from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
errors = []
routes = []

class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.has_title = False
        self.has_main = False
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        self.has_title |= tag == 'title'
        self.has_main |= tag == 'main'
        for attr in ('href', 'src'):
            if attr in values: self.refs.append(values[attr])

for page in DIST.rglob('*.html'):
    parser = References()
    source = page.read_text()
    parser.feed(source)
    routes.append(str(page.relative_to(DIST)))
    if not parser.has_title or not parser.has_main: errors.append(f'{page}: missing page structure')
    if 'google_tags_first_party' in source or 'G-P8L2KTXDN0' in source: errors.append(f'{page}: analytics retained')
    for reference in parser.refs:
        if not reference.startswith('/') or reference.startswith('//'): continue
        target = DIST / unquote(urlsplit(reference).path).lstrip('/')
        if target.is_dir(): target = target / 'index.html'
        if not target.exists(): errors.append(f'{page.name}: broken {reference}')

for style in DIST.rglob('*.css'):
    for value in re.findall(r'url\([\x27"]?([^\x27")]+)', style.read_text()):
        if value.startswith('/') and not (DIST / value.lstrip('/')).exists(): errors.append(f'Missing CSS resource {value}')

for script in DIST.rglob('*.js'):
    checked = subprocess.run(['node', '--check', str(script)], capture_output=True, text=True)
    if checked.returncode: errors.append(f'{script.name}: {checked.stderr[:300]}')

for file in DIST.rglob('*.wasm'):
    if file.read_bytes()[:4] != b'\x00asm': errors.append(f'Invalid WASM {file}')
for file in DIST.rglob('*.glb'):
    if file.read_bytes()[:4] != b'glTF': errors.append(f'Invalid model {file}')

print(json.dumps({'pages':routes, 'resources':sum(1 for p in DIST.rglob('*') if p.is_file()), 'errors':errors},indent=2))
raise SystemExit(1 if errors else 0)
