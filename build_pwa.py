# goryu-ski.html（アーティファクト版）から PWA 版 docs/ を組み立てる（GitHub Pages の公開元）
import json, pathlib, shutil, hashlib

root = pathlib.Path(__file__).parent
src = (root / 'goryu-ski.html').read_text()
out = root / 'docs'
(out / 'assets').mkdir(parents=True, exist_ok=True)
for f in (root / 'assets').iterdir():
    shutil.copy(f, out / 'assets' / f.name)

version = hashlib.sha1(src.encode()).hexdigest()[:8]

head = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">
<meta name="theme-color" content="#0F2536">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="五竜ダウンヒル">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icons/icon-180.png">
<link rel="icon" href="icons/icon-192.png">
<style>html,body{margin:0;height:100%}</style>
</head>
<body>
"""
tail = """
<script>
if ('serviceWorker' in navigator) addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {}));
</script>
</body>
</html>
"""
(out / 'icons').mkdir(exist_ok=True)
for f in (root / 'icons').iterdir():
    shutil.copy(f, out / 'icons' / f.name)
(out / 'index.html').write_text(head + src + tail)

manifest = {
    "name": "五竜ダウンヒル",
    "short_name": "五竜ダウンヒル",
    "description": "白馬五竜の実地形を滑るスキー。右足荷重で左ターン。",
    "start_url": "./",
    "scope": "./",
    "display": "fullscreen",
    "orientation": "portrait",
    "background_color": "#0F2536",
    "theme_color": "#0F2536",
    "lang": "ja",
    "icons": [
        {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}
(out / 'manifest.webmanifest').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))

sw = """// 五竜ダウンヒル service worker（版: %s）
const CACHE = 'goryu-%s';
const CORE = ['./', 'index.html', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png',
  'assets/goryu-course.json', 'assets/goryu-terrain.json', 'assets/chairlift.json',
  'assets/liftpole.json', 'assets/snow-diffuse.jpg', 'assets/snow-normal.jpg'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
// ページ本体は最新優先（オフライン時はキャッシュ）、それ以外（データ・CDNのライブラリ）はキャッシュ優先
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).then(r => { const c = r.clone(); caches.open(CACHE).then(k => k.put('index.html', c)); return r; }).catch(() => caches.match('index.html')));
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(r => {
    if (r.ok || r.type === 'opaque') { const c = r.clone(); caches.open(CACHE).then(k => k.put(req, c)); }
    return r;
  })));
});
""" % (version, version)
(out / 'sw.js').write_text(sw)
(out / '.nojekyll').write_text('')
print('built pwa/ version', version)
