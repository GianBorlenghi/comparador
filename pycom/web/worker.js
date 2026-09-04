// Cloudflare Worker - CORS Proxy para Pergamino Precios
// Deploy en https://workers.cloudflare.com -> Nuevo Worker -> Pegar esto -> Deploy
// Luego en app.js cambia la primera URL del array proxies a: `https://TU-WORKER.workers.dev/?url=${encodeURIComponent(url)}`

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const target = url.searchParams.get('url');
    if (!target) {
      return new Response('Falta ?url=', {status: 400, headers: {"Access-Control-Allow-Origin":"*"}});
    }
    // Solo permitir VTEX de los 3 supers
    if (!target.includes("masonline.com.ar") && !target.includes("vea.com.ar") && !target.includes("carrefour.com.ar")) {
      return new Response('Dominio no permitido', {status: 403, headers: {"Access-Control-Allow-Origin":"*"}});
    }
    const res = await fetch(target, {
      headers: {"User-Agent":"Mozilla/5.0","Accept":"application/json"},
      cf: {cacheTtl: 60}
    });
    const body = await res.text();
    return new Response(body, {
      status: res.status,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": res.headers.get("Content-Type") || "application/json",
        "Cache-Control": "public, max-age=60"
      }
    });
  }
}
