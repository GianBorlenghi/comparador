"""
Comparador de precios de supermercados - Pergamino
Busca un producto en MasOnline, VEA y Carrefour usando sus APIs directas.

Requisitos:
    py -m pip install requests
"""

import re
import unicodedata
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

# ── Colores ANSI ──────────────────────────────
VERDE    = "\033[92m"
AMARILLO = "\033[93m"
RESET    = "\033[0m"
NEGRITA  = "\033[1m"

SUPERMERCADOS = {
    "MasOnline": "https://www.masonline.com.ar/api/catalog_system/pub/products/search?ft={query}&_from=0&_to=49",
    "VEA":       "https://www.vea.com.ar/api/catalog_system/pub/products/search?ft={query}&_from=0&_to=49",
    "Carrefour": "https://www.carrefour.com.ar/api/catalog_system/pub/products/search?ft={query}&_from=0&_to=49",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

MAX_POR_SUPER = 8
PRECIO_MINIMO = 1000   # mínimo razonable en pesos argentinos 2025
RATIO_MAX     = 3.0    # si precio_original > 3x precio_final → dato corrupto

PALABRAS_PACK = ["pack", "combo", "fardo", "bulto"]
# "x2","x3" etc los manejamos con regex para no bloquear "2.25x3" etc


# ── Normalización ─────────────────────────────

def normalizar(texto: str) -> str:
    """
    Minúsculas, sin tildes, coma decimal → punto, número pegado a unidad.
    Ej: "2,25 Lts" → "2.25lts"  |  "Niñas" → "ninas"
    """
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"(\d),(\d)", r"\1.\2", texto)           # 2,25 → 2.25
    texto = re.sub(r"(\d\.?\d*)\s*(l|lt|lts|ml|kg|g|gr)\b", r"\1\2", texto)
    return texto


def terminos_de(query: str) -> list[str]:
    return [t for t in normalizar(query).split() if len(t) >= 2]


# ── Validación de precio ──────────────────────

def precio_valido(precio_final, precio_original) -> bool:
    if precio_final is None or precio_final < PRECIO_MINIMO:
        return False
    if precio_original and precio_original > 0:
        if (precio_original / precio_final) > RATIO_MAX:
            return False
    return True


# ── Filtro de relevancia ──────────────────────

def es_pack(nombre: str, query: str) -> bool:
    nombre_n = normalizar(nombre)
    query_n  = normalizar(query)
    for palabra in PALABRAS_PACK:
        if palabra in nombre_n and palabra not in query_n:
            return True
    # Detectar "x4", "x6" etc en el nombre pero NO en la query
    packs_re = re.findall(r"\bx\d+\b", nombre_n)
    query_packs = re.findall(r"\bx\d+\b", query_n)
    for p in packs_re:
        if p not in query_packs:
            return True
    return False


def es_relevante(nombre_producto: str, terminos: list[str]) -> bool:
    """
    1. Todos los términos deben aparecer en el nombre normalizado.
    2. El primer término debe estar entre las primeras 3 palabras.
    3. Si el usuario NO escribió 'polvo', 'en polvo' no debe aparecer.
    4. Si el usuario NO escribió 'chocolatada', no mostrar chocolatadas.
    5. Si el usuario NO escribió 'crema', no mostrar cremas.
    """
    nombre_n = normalizar(nombre_producto)
    query_n  = " ".join(terminos)

    # Todos los términos presentes
    if not all(t in nombre_n for t in terminos):
        return False

    # Primer término en las primeras 3 palabras
    primeras = " ".join(nombre_n.split()[:3])
    if terminos[0] not in primeras:
        return False

    # Exclusiones: variantes que el usuario no pidió
    exclusiones = {
        "polvo":       "polvo",
        "chocolatada": "chocolatada",
        "crema":       "crema",
        "saborizad":   "saborizad",
        "condensad":   "condensad",
    }
    for palabra_prod, palabra_query in exclusiones.items():
        if palabra_prod in nombre_n and palabra_query not in query_n:
            return False

    return True


# ── Promociones ───────────────────────────────

def interpretar_promociones(oferta: dict) -> list[str]:
    promos = []
    teasers = oferta.get("PromotionTeasers") or oferta.get("teasers") or []
    precio_final    = oferta.get("Price")
    precio_original = oferta.get("ListPrice")

    for t in teasers:
        nombre = (
            t.get("Name") or t.get("name") or
            t.get("<Name>k__BackingField", "")
        ).strip()

        condiciones = (
            t.get("Conditions") or t.get("conditions") or
            t.get("<Conditions>k__BackingField") or {}
        )
        min_qty = (
            condiciones.get("MinimumQuantity") or
            condiciones.get("minimumQuantity") or
            condiciones.get("<MinimumQuantity>k__BackingField") or 0
        )

        efectos = (
            t.get("Effects") or t.get("effects") or
            t.get("<Effects>k__BackingField") or {}
        )
        parametros = (
            efectos.get("Parameters") or efectos.get("parameters") or
            efectos.get("<Parameters>k__BackingField") or []
        )

        pct = None
        for p in parametros:
            pnom = p.get("Name") or p.get("name") or p.get("<Name>k__BackingField", "")
            pval = p.get("Value") or p.get("value") or p.get("<Value>k__BackingField", "")
            if pnom == "PercentualDiscount":
                try:
                    pct = int(round(abs(float(pval))))
                except (ValueError, TypeError):
                    pass

        if pct is not None:
            if   min_qty == 2 and pct == 100: promos.append("🎁 2x1 (llevás 2, pagás 1)")
            elif min_qty == 3 and pct == 100: promos.append("🎁 3x2 (llevás 3, pagás 2)")
            elif min_qty == 2 and pct == 50:  promos.append("🎁 2da unidad al 50%")
            elif min_qty == 3 and pct == 67:  promos.append("🎁 3ra unidad al 33%")
            elif min_qty >= 2 and 0 < pct <= 70:
                promos.append(f"🎁 {pct}% OFF llevando {min_qty} unidades")
            elif min_qty <= 1 and 0 < pct <= 70:
                label = f" — {nombre}" if nombre else ""
                promos.append(f"🏷️  {pct}% OFF{label}")
        elif nombre and 2 < len(nombre) < 60:
            promos.append(f"🏷️  {nombre}")

    # Fallback por diferencia de precios
    if not promos and precio_final and precio_original and precio_original > precio_final:
        if (precio_original / precio_final) <= RATIO_MAX:
            pct = round((1 - precio_final / precio_original) * 100)
            if 0 < pct <= 70:
                promos.append(f"🏷️  {pct}% OFF")

    return promos


# ── Scraping ──────────────────────────────────

def formatear_precio(valor: float) -> str:
    return f"${valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def buscar_en_super(nombre_super: str, url_template: str, query: str, terminos: list[str]) -> list[dict]:
    resultados = []
    url = url_template.format(query=quote(query))

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        productos = resp.json()

        for prod in productos:
            nombre_prod = prod.get("productName", "").strip()
            if not nombre_prod:
                continue
            if not es_relevante(nombre_prod, terminos):
                continue
            if es_pack(nombre_prod, query):
                continue

            link            = prod.get("link", "")
            precio_final    = None
            precio_original = None
            promociones     = []

            items = prod.get("items", [])
            if items:
                sellers = items[0].get("sellers", [])
                if sellers:
                    oferta          = sellers[0].get("commertialOffer", {})
                    precio_final    = oferta.get("Price")
                    precio_original = oferta.get("ListPrice")

                    if not precio_valido(precio_final, precio_original):
                        continue

                    promociones = interpretar_promociones(oferta)

            if precio_final is None:
                continue

            resultados.append({
                "supermercado":    nombre_super,
                "nombre":          nombre_prod,
                "precio_final":    precio_final,
                "precio_original": precio_original,
                "precio_str":      formatear_precio(precio_final),
                "promociones":     promociones,
                "url":             link,
            })

            if len(resultados) >= MAX_POR_SUPER:
                break

    except requests.exceptions.Timeout:
        print(f"  ❌ [{nombre_super}] Tiempo de espera agotado.")
    except requests.exceptions.HTTPError as e:
        print(f"  ❌ [{nombre_super}] Error HTTP: {e.response.status_code}")
    except Exception as e:
        print(f"  ❌ [{nombre_super}] Error: {e}")

    return resultados


def buscar_en_todos(query: str) -> list[dict]:
    terminos = terminos_de(query)
    todos = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futuros = {
            executor.submit(buscar_en_super, nombre, url, query, terminos): nombre
            for nombre, url in SUPERMERCADOS.items()
        }
        for futuro in as_completed(futuros):
            todos.extend(futuro.result())
    return todos


# ── Presentación ──────────────────────────────

def mostrar_resultados(resultados: list[dict], query: str):
    print()
    print("═" * 65)
    print(f"  Resultados para: \"{query}\"  |  Zona: Pergamino")
    print("═" * 65)

    if not resultados:
        print()
        print("  Sin resultados. Probá con menos palabras.")
        print("  Ej: 'coca cola 2.25'  /  'leche serenisima'  /  'arroz largo'")
        print()
        print("═" * 65)
        return

    precio_min = min(r["precio_final"] for r in resultados)

    por_super: dict[str, list] = {}
    for r in resultados:
        por_super.setdefault(r["supermercado"], []).append(r)

    for nombre_super, items in por_super.items():
        print(f"\n  🛒  {NEGRITA}{nombre_super}{RESET}")
        print("  " + "─" * 55)

        for i, item in enumerate(items, 1):
            nombre = item["nombre"]
            if len(nombre) > 52:
                nombre = nombre[:52] + "…"

            es_min = abs(item["precio_final"] - precio_min) < 0.01

            if es_min:
                precio_txt = f"{VERDE}{NEGRITA}{item['precio_str']}  ◄ MÁS BARATO{RESET}"
            else:
                precio_txt = item["precio_str"]

            precio_antes = ""
            if item["precio_original"] and item["precio_original"] > item["precio_final"]:
                if (item["precio_original"] / item["precio_final"]) <= RATIO_MAX:
                    precio_antes = f"  {AMARILLO}antes {formatear_precio(item['precio_original'])}{RESET}"

            print(f"  {i}. {nombre}")
            print(f"     💲 {precio_txt}{precio_antes}")

            for promo in item["promociones"]:
                print(f"     {AMARILLO}{promo}{RESET}")

            if item["url"]:
                url = item["url"][:64] + "…" if len(item["url"]) > 64 else item["url"]
                print(f"     🔗 {url}")

    mejor = next(r for r in resultados if abs(r["precio_final"] - precio_min) < 0.01)
    nombre_corto = mejor["nombre"][:44] + "…" if len(mejor["nombre"]) > 44 else mejor["nombre"]

    print()
    print("═" * 65)
    print(f"  {VERDE}{NEGRITA}⭐ Más barato: {mejor['precio_str']} en {mejor['supermercado']}{RESET}")
    print(f"     {nombre_corto}")
    print("═" * 65)
    print()


# ── Main ──────────────────────────────────────

def main():
    print()
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  Comparador de Precios - Supermercados de Pergamino       ║")
    print("║  MasOnline  •  VEA  •  Carrefour                          ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()
    print("  Ejemplos: 'coca cola 2.25'  /  'leche serenisima descremada'")
    print("            'arroz largo fino'  /  'aceite girasol 1.5'")
    print("  (Escribí 'salir' para terminar)\n")

    while True:
        try:
            query = input("  Producto: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  ¡Hasta luego!")
            break

        if not query:
                continue
        if query.lower() in ("salir", "exit", "q"):
            print("\n  ¡Hasta luego!")
            break

        print(f"\n  Buscando \"{query}\"...\n")
        resultados = buscar_en_todos(query)
        mostrar_resultados(resultados, query)


if __name__ == "__main__":
    main()
