const CACHE = 'pergamino-v3';
const ASSETS = ['./index.html','./style.css','./app.js','./manifest.json'];
self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))));
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // NO interceptar APIs ni proxies CORS - dejar pasar directo
  if (url.hostname.includes('masonline.com.ar') || url.hostname.includes('vea.com.ar') || url.hostname.includes('carrefour.com.ar') || url.hostname.includes('allorigins.win') || url.hostname.includes('corsproxy.io') || url.hostname.includes('yacdn.org') || url.hostname.includes('cors.sh')) {
    return;
  }
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).catch(()=>caches.match('./index.html'))));
});
