#!/usr/bin/env python3
"""Assemble the public reference pages into a self-contained private replica."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlsplit, unquote
from urllib.request import Request, urlopen
import hashlib
import html
import json
import re
import subprocess

PROJECT = Path(__file__).resolve().parents[1]
REFERENCE = PROJECT / 'reference'
OUT = PROJECT / 'dist'
ORIGIN = 'https://landonorris.com/'
SOURCES = {
    'index.html': 'reference.html',
    'on-track/index.html': 'on-track.html',
    'off-track/index.html': 'off-track.html',
    'calendar/index.html': 'calendar.html',
    'legal/privacy-policy/index.html': 'legal-privacy-policy.html',
    'legal/terms-conditions/index.html': 'legal-terms-conditions.html',
}
MAPPINGS = {}
ASSETS = {}


def add(url, local=None):
    url = html.unescape(url)
    if url in MAPPINGS:
        return MAPPINGS[url]
    if local is None:
        parts = urlsplit(url)
        name = unquote(parts.path.rsplit('/', 1)[-1])
        name = re.sub(r'[^a-zA-Z0-9._+-]', '-', name)
        local = 'assets/site/' + name
        if parts.query:
            local = 'assets/site/' + hashlib.sha256(url.encode()).hexdigest()[:8] + '-' + name
    MAPPINGS[url] = '/' + local
    ASSETS[url] = local
    return MAPPINGS[url]


def strip_tracking(raw):
    raw = re.sub(r'<!--.*?-->', '', raw, flags=re.S)
    raw = re.sub(r'\s+(?:srcset|sizes)="[^"]*"', '', raw)
    raw = re.sub(r'<img\b[^>]*src="https://cdn\.prod\.website-files\.com/plugins/Basic/assets/placeholder\.[^"]*"[^>]*>', '', raw)
    def clean_script(match):
        block = match.group(0)
        if any(s in block for s in ('google_tags_first_party', 'dataLayer', '/avljl2rk', 'klaviyo.js', 'iubenda')):
            return ''
        return block
    raw = re.sub(r'<script\b[^>]*>.*?</script>', clean_script, raw, flags=re.S)
    raw = re.sub(r'<link\b[^>]*rel="(?:preconnect|dns-prefetch)"[^>]*>', '', raw)
    raw = re.sub(r'\s+(?:integrity|crossorigin)="[^"]*"', '', raw)
    raw = re.sub(r'<html\b[^>]*>', lambda m: re.sub(r'\sdata-wf-domain="[^"]*"', '', m.group(0)), raw, count=1)
    raw = raw.replace('href="/partnerships"', 'href="/off-track"')
    return raw


pages = {}
for destination, source in SOURCES.items():
    pages[destination] = strip_tracking((REFERENCE / source).read_text())

style = (REFERENCE / 'site.css').read_text()
runtime = (REFERENCE / 'main.js').read_text()
for document in [*pages.values(), style]:
    for url in re.findall(r'https?://[^\s"\x27<>`\\]+', document):
        if urlsplit(html.unescape(url)).hostname in ('cdn.prod.website-files.com', 'd3e54v103j8qbb.cloudfront.net'):
            add(url)

add('https://lando.itsoffbrand.io/dev-js/lando-by-OFF+BRAND.05.js', 'assets/runtime/site-runtime.js')
for name in ('signature', 'btn-ui', 'circuits', 'reef', 'phrases', 'ln4', 'mob-landscape'):
    add('https://assets.itsoffbrand.io/lando/rive/' + name + '.riv', 'assets/rive/' + name + '.riv')
add('https://lando.itsoffbrand.io/rive/page-transition.riv', 'assets/transition/page-transition.riv')
for _, path in re.findall(r'vQ\+(["`])([^"`]+)\1', runtime):
    if path.endswith('/'):
        continue
    for texture_type in ('webp', 'ktx2') if '${iQ}' in path else ('webp',):
        expanded = path.replace('${iQ}', texture_type)
        add('https://lando.itsoffbrand.io/gl' + expanded, 'assets/gl' + expanded)
for path in ('draco/draco_decoder.js', 'draco/draco_wasm_wrapper.js', 'draco/draco_decoder.wasm', 'basis/basis_transcoder.js', 'basis/basis_transcoder.wasm'):
    add('https://lando.itsoffbrand.io/gl/' + path, 'assets/gl/' + path)
add('https://unpkg.com/@rive-app/canvas-lite@2.26.4/rive.wasm', 'assets/runtime/rive.wasm')
add('https://cdn.jsdelivr.net/npm/@rive-app/canvas-lite@2.26.4/rive_fallback.wasm', 'assets/runtime/rive_fallback.wasm')


def download(item):
    url, local = item
    path = OUT / local
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size:
        return {'url': url, 'path': local, 'bytes': path.stat().st_size}
    if local == 'assets/runtime/site-runtime.js':
        data = runtime.encode()
    elif url.endswith('lando-offbrand.shared.6e09a725a.css'):
        data = style.encode()
    else:
        try:
            request = Request(url, headers={'Referer': ORIGIN, 'User-Agent': 'Mozilla/5.0'})
            with urlopen(request, timeout=65) as response:
                data = response.read()
        except Exception as error:
            # One recovery for ordinary network or resource-request failures.
            result = subprocess.run(['curl', '-L', '--fail', '--max-time', '60', '-sS', '-e', ORIGIN, url], capture_output=True)
            if result.returncode:
                return {'url': url, 'path': local, 'error': str(error)}
            data = result.stdout
    if not data:
        return {'url': url, 'path': local, 'error': 'Empty resource'}
    path.write_bytes(data)
    return {'url': url, 'path': local, 'bytes': len(data)}


results = []
print(f'Collecting {len(ASSETS)} unique local resources', flush=True)
with ThreadPoolExecutor(max_workers=14) as executor:
    futures = [executor.submit(download, item) for item in ASSETS.items()]
    for future in as_completed(futures):
        result = future.result()
        results.append(result)
        if 'error' in result:
            print('RESOURCE ERROR', json.dumps(result), flush=True)
        elif len(results) % 25 == 0:
            print(f'{len(results)}/{len(ASSETS)} resources collected', flush=True)

manifest = {r['url']: r for r in results}
(PROJECT / 'asset-manifest.json').write_text(json.dumps(manifest, indent=2))
errors = [r for r in results if 'error' in r]
if errors:
    print(f'{len(errors)} resources need repair', flush=True)


def localize(text):
    for url in sorted(MAPPINGS, key=len, reverse=True):
        if 'error' not in manifest[url]:
            text = text.replace(url, MAPPINGS[url]).replace(html.escape(url, quote=True), MAPPINGS[url])
    return text


for destination, page in pages.items():
    page = localize(page)
    page = page.replace('<title>', '<title>Replica · ', 1)
    page = page.replace('</head>', '<meta name="robots" content="noindex,nofollow"><script defer src="/assets/runtime/replica-guard.js"></script></head>')
    target = OUT / destination
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page)

for asset in results:
    if 'error' in asset:
        continue
    file = OUT / asset['path']
    if file.suffix == '.css':
        file.write_text(localize(file.read_text()))
    elif asset['path'] == 'assets/runtime/site-runtime.js':
        js = file.read_text()
        js = js.replace('https://assets.itsoffbrand.io/lando/rive/', '/assets/rive/')
        js = js.replace('https://lando.itsoffbrand.io/rive/', '/assets/transition/')
        js = js.replace('https://lando.itsoffbrand.io/gl', '/assets/gl')
        js = js.replace('f.wasmURL="https://unpkg.com/".concat(C.name,"@").concat(C.version,"/rive.wasm")', 'f.wasmURL="/assets/runtime/rive.wasm"')
        js = js.replace('"https://cdn.jsdelivr.net/npm/".concat(C.name,"@").concat(C.version,"/rive_fallback.wasm")', '"/assets/runtime/rive_fallback.wasm"')
        js = js.replace('var A=window.location.pathname,Q=document.querySelectorAll("a");', 'var A=window.location.pathname.replace(/\\/+$/,"")||"/",Q=document.querySelectorAll("a");')
        js = js.replace('CD()}c_();', 'CD()}c_().then(()=>{document.documentElement.dataset.replicaRuntime="ready"}).catch(error=>{console.error("Replica animation startup failed",error);window.dispatchEvent(new Event("replica-runtime-error"))});')
        file.write_text(js)

total = sum(r.get('bytes', 0) for r in results)
print(json.dumps({'pages': len(pages), 'resources': len(results), 'bytes': total, 'failed': len(errors)}), flush=True)
