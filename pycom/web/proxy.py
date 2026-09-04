"""
Proxy local para Pergamino Precios PWA
Evita CORS bloqueado en localhost / GitHub Pages
Uso: py proxy.py  -> corre en http://localhost:8001
La PWA lo usa automáticamente cuando está en localhost
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse, urllib.request, json

PORT = 8001
ALLOWED = ["masonline.com.ar", "vea.com.ar", "carrefour.com.ar"]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        target = qs.get("url", [None])[0]
        if not target:
            self.send_response(400)
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(b"Falta ?url=")
            return
        # Validar dominio permitido
        if not any(d in target for d in ALLOWED):
            self.send_response(403)
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(b"Dominio no permitido")
            return
        try:
            req = urllib.request.Request(target, headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
            with urllib.request.urlopen(req, timeout=12) as r:
                body = r.read()
                ctype = r.headers.get("Content-Type","application/json")
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin","*")
                self.send_header("Content-Type", ctype)
                self.send_header("Cache-Control","public, max-age=60")
                self.end_headers()
                self.wfile.write(body)
        except Exception as e:
            self.send_response(502)
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(f"Proxy error: {e}".encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[proxy] {self.path[:80]} -> {format%args}")

if __name__ == "__main__":
    print(f"Proxy CORS corriendo en http://localhost:{PORT}")
    print(f"Ejemplo: http://localhost:{PORT}/proxy?url=https://www.masonline.com.ar/api/catalog_system/pub/products/search?ft=coca%20cola&_from=0&_to=1")
    print("Dejalo corriendo y recargá la PWA en http://localhost:8000")
    HTTPServer(("localhost", PORT), Handler).serve_forever()
