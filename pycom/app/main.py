"""
Pergamino Precios - App PRO
Diseño intuitivo, moderno y amigable.
"""
import threading
import webbrowser
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.storage.jsonstore import JsonStore
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.chip import MDChip
from kivy.uix.image import AsyncImage
from kivy.uix.behaviors import ButtonBehavior

from core import buscar_en_todos, formatear_precio, obtener_promos_bancarias

# Colores por super (branding)
COLORES = {
    "MasOnline": {"primary": (0.09, 0.45, 0.84, 1), "light": (0.88, 0.94, 1, 1), "icon": "store"},
    "VEA": {"primary": (0.83, 0.18, 0.18, 1), "light": (1, 0.92, 0.92, 1), "icon": "cart"},
    "Carrefour": {"primary": (0, 0.32, 0.67, 1), "light": (0.88, 0.92, 1, 1), "icon": "cart-variant"},
}

SUGERENCIAS = ["coca cola 2.25", "leche serenisima", "yerba amanda 1kg", "fideos lucchetti", "aceite 1.5", "paty"]

KV = '''
MDScreen:
    MDNavigationLayout:
        MDScreenManager:
            id: sm
            MDScreen:
                name: "comparar"
                MDBoxLayout:
                    orientation: "vertical"
                    md_bg_color: 0.965, 0.965, 0.97, 1

                    # ── TopBar PRO ──
                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(64)
                        md_bg_color: 0, 0.48, 0.48, 1
                        padding: dp(12)
                        spacing: dp(10)
                        MDIconButton:
                            icon: "menu"
                            theme_text_color: "Custom"
                            text_color: 1,1,1,1
                            on_release: nav_drawer.set_state("open")
                        MDBoxLayout:
                            orientation: "vertical"
                            spacing: dp(-4)
                            MDLabel:
                                text: "Pergamino Precios"
                                font_style: "H6"
                                theme_text_color: "Custom"
                                text_color: 1,1,1,1
                                size_hint_y: None
                                height: dp(22)
                            MDLabel:
                                text: "MasOnline  •  VEA  •  Carrefour"
                                font_style: "Caption"
                                theme_text_color: "Custom"
                                text_color: 1,1,1,0.85
                                size_hint_y: None
                                height: dp(14)
                        MDIconButton:
                            icon: "credit-card-outline"
                            theme_text_color: "Custom"
                            text_color: 1,1,1,1
                            on_release:
                                sm.current = "promos"
                                app.cargar_promos_bancarias()

                    # ── Buscador ──
                    MDCard:
                        size_hint_y: None
                        height: dp(96)
                        radius: [16,]
                        elevation: 2
                        padding: dp(12)
                        spacing: dp(8)
                        md_bg_color: 1,1,1,1
                        pos_hint: {"center_x": 0.5}
                        orientation: "vertical"

                        MDBoxLayout:
                            size_hint_y: None
                            height: dp(48)
                            spacing: dp(8)
                            MDTextField:
                                id: search_field
                                hint_text: "Buscá un producto..."
                                helper_text: "Ej: coca cola 2.25"
                                helper_text_mode: "on_focus"
                                mode: "round"
                                icon_left: "magnify"
                                on_text_validate: app.buscar()
                            MDRaisedButton:
                                id: btn_buscar
                                text: "Buscar"
                                md_bg_color: 0, 0.48, 0.48, 1
                                size_hint_x: None
                                width: dp(88)
                                on_release: app.buscar()

                        ScrollView:
                            size_hint_y: None
                            height: dp(28)
                            do_scroll_x: True
                            do_scroll_y: False
                            bar_width: 0
                            MDBoxLayout:
                                id: chips_box
                                spacing: dp(6)
                                adaptive_width: True
                                padding: dp(2)

                    MDLabel:
                        id: status_label
                        text: "Tocá una sugerencia o escribí para comparar"
                        font_style: "Caption"
                        theme_text_color: "Hint"
                        halign: "center"
                        size_hint_y: None
                        height: dp(18)
                        padding: dp(12), 0

                    # ── Resultados ──
                    MDScrollView:
                        id: scroll_results
                        MDBoxLayout:
                            id: results_box
                            orientation: "vertical"
                            spacing: dp(12)
                            padding: dp(12), dp(8), dp(12), dp(80)
                            adaptive_height: True

            MDScreen:
                name: "promos"
                MDBoxLayout:
                    orientation: "vertical"
                    md_bg_color: 0.965, 0.965, 0.97, 1

                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(64)
                        md_bg_color: 0, 0.48, 0.48, 1
                        padding: dp(12)
                        MDIconButton:
                            icon: "arrow-left"
                            theme_text_color: "Custom"
                            text_color: 1,1,1,1
                            on_release: sm.current = "comparar"
                        MDLabel:
                            text: "Promos Bancarias"
                            font_style: "H6"
                            theme_text_color: "Custom"
                            text_color: 1,1,1,1
                        MDIconButton:
                            icon: "refresh"
                            theme_text_color: "Custom"
                            text_color: 1,1,1,1
                            on_release: app.cargar_promos_bancarias()

                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(36)
                        padding: dp(12), dp(6)
                        MDLabel:
                            id: promos_status
                            text: "Promos vigentes por banco y medio de pago"
                            font_style: "Caption"
                            theme_text_color: "Hint"

                    MDScrollView:
                        MDBoxLayout:
                            id: promos_box
                            orientation: "vertical"
                            spacing: dp(14)
                            padding: dp(12), dp(6), dp(12), dp(80)
                            adaptive_height: True

        MDNavigationDrawer:
            id: nav_drawer
            MDNavigationDrawerMenu:
                MDNavigationDrawerHeader:
                    title: "Pergamino Precios"
                    text: "Compará y ahorrá en tu zona"
                    spacing: "4dp"
                    padding: "12dp", 0, 0, "40dp"
                MDNavigationDrawerLabel:
                    text: "Navegación"
                DrawerClickableItem:
                    text: "Comparar precios"
                    icon: "cart-search"
                    on_press:
                        sm.current = "comparar"
                        nav_drawer.set_state("close")
                DrawerClickableItem:
                    text: "Promos bancarias"
                    icon: "credit-card-outline"
                    on_press:
                        sm.current = "promos"
                        nav_drawer.set_state("close")
                        app.cargar_promos_bancarias()
                MDNavigationDrawerDivider:
                MDNavigationDrawerLabel:
                    text: "Zona: Pergamino • v1.0 PRO"

<DrawerClickableItem@MDNavigationDrawerItem>
'''

class PergaminoApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.primary_hue = "600"
        self.theme_cls.accent_palette = "Orange"
        self.theme_cls.theme_style = "Light"
        self.title = "Pergamino Precios"
        self.store = JsonStore("historial.json")
        root = Builder.load_string(KV)
        Clock.schedule_once(lambda dt: self._cargar_chips())
        return root

    def _cargar_chips(self):
        box = self.root.ids.chips_box
        box.clear_widgets()
        for txt in SUGERENCIAS:
            chip = MDChip(
                text=txt,
                icon="",
                size_hint_x=None,
                width=dp(len(txt)*7 + 32),
                md_bg_color=(0.92, 0.96, 0.96, 1),
                text_color=(0, 0.4, 0.4, 1),
            )
            chip.bind(on_release=lambda c, t=txt: self._usar_sugerencia(t))
            box.add_widget(chip)
        # Historial
        try:
            hist = self.store.get("hist")["q"] if self.store.exists("hist") else []
            for h in hist[:3]:
                if h not in SUGERENCIAS:
                    chip = MDChip(text=f"🕘 {h}", size_hint_x=None, width=dp(len(h)*7+40), md_bg_color=(1,0.94,0.88,1), text_color=(0.6,0.32,0,1))
                    chip.bind(on_release=lambda c, t=h: self._usar_sugerencia(t))
                    box.add_widget(chip)
        except:
            pass

    def _usar_sugerencia(self, txt):
        self.root.ids.search_field.text = txt
        self.buscar()

    def _guardar_historial(self, q):
        try:
            hist = self.store.get("hist")["q"] if self.store.exists("hist") else []
            if q not in hist:
                hist.insert(0, q)
                self.store.put("hist", q=hist[:5])
                self._cargar_chips()
        except:
            pass

    def on_start(self):
        threading.Thread(target=self._precarga_promos, daemon=True).start()

    def _precarga_promos(self):
        try:
            obtener_promos_bancarias()
        except:
            pass

    def buscar(self):
        query = self.root.ids.search_field.text.strip()
        if not query:
            self.root.ids.status_label.text = "Escribí un producto para comparar"
            return
        self._guardar_historial(query)
        self.root.ids.status_label.text = f'Buscando "{query}" en 3 supers…'
        self.root.ids.results_box.clear_widgets()
        # Loading card
        loading = MDCard(size_hint_y=None, height=dp(80), radius=[16,], elevation=1, padding=dp(16), md_bg_color=(1,1,1,1))
        loading.add_widget(MDLabel(text="🔍  Buscando en MasOnline, VEA y Carrefour…", halign="center", theme_text_color="Hint"))
        self.root.ids.results_box.add_widget(loading)
        # Deshabilitar botón
        self.root.ids.btn_buscar.disabled = True
        threading.Thread(target=self._buscar_thread, args=(query,), daemon=True).start()

    def _buscar_thread(self, query):
        try:
            resultados = buscar_en_todos(query)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._mostrar_error(str(e)))
            return
        Clock.schedule_once(lambda dt: self._mostrar_resultados(resultados, query))

    def _mostrar_error(self, err):
        self.root.ids.btn_buscar.disabled = False
        self.root.ids.results_box.clear_widgets()
        self.root.ids.status_label.text = f"Error: {err}"

    def _mostrar_resultados(self, resultados, query):
        self.root.ids.btn_buscar.disabled = False
        box = self.root.ids.results_box
        box.clear_widgets()
        if not resultados:
            self.root.ids.status_label.text = f'Sin resultados para "{query}"'
            card = MDCard(size_hint_y=None, height=dp(100), radius=[16,], elevation=1, padding=dp(16), md_bg_color=(1,1,1,1))
            card.add_widget(MDLabel(text="😕 Sin resultados\nProbá con menos palabras\nEj: 'coca cola' / 'leche' / 'yerba'", halign="center", theme_text_color="Hint"))
            box.add_widget(card)
            return

        precio_min = min(r["precio_final"] for r in resultados)
        try:
            precio_min_ig = min(r.get("precio_efectivo_iguales", r["precio_final"]) for r in resultados)
        except:
            precio_min_ig = precio_min
        self.root.ids.status_label.text = f'{len(resultados)} productos • Más barato: {formatear_precio(precio_min)} • Con promo: {formatear_precio(precio_min_ig)} c/u'

        # ── Resumen PRO ──
        try:
            mejor = next(r for r in resultados if abs(r["precio_final"]-precio_min)<0.01)
            mejor_ig = next(r for r in resultados if abs(r.get("precio_efectivo_iguales", r["precio_final"])-precio_min_ig)<0.01)
            resumen = MDCard(size_hint_y=None, height=dp(88), radius=[16,], elevation=2, padding=dp(14), spacing=dp(4), md_bg_color=(0.90, 1, 0.93, 1), orientation="vertical")
            resumen.add_widget(MDLabel(text=f"⭐ Más barato (1 unid.): {mejor['precio_str']} en {mejor['supermercado']}", font_style="Subtitle2", theme_text_color="Custom", text_color=(0,0.5,0.25,1), size_hint_y=None, height=dp(20)))
            resumen.add_widget(MDLabel(text=mejor["nombre"][:52], font_style="Caption", theme_text_color="Hint", size_hint_y=None, height=dp(16)))
            if mejor_ig.get("precio_efectivo_iguales_str") and (abs(precio_min_ig-precio_min)>0.01 or mejor["supermercado"]!=mejor_ig["supermercado"] or mejor["nombre"]!=mejor_ig["nombre"]):
                promo_txt = mejor_ig.get("promo_iguales","").split("→")[0].strip()[:38]
                ahorro = ""
                try:
                    ahorro_val = float(mejor["precio_final"]) - float(mejor_ig["precio_efectivo_iguales"])
                    if ahorro_val>0:
                        ahorro = f" • Ahorrás {formatear_precio(ahorro_val)}"
                except:
                    pass
                resumen.add_widget(MDLabel(text=f"🎁 Con promo: {mejor_ig['precio_efectivo_iguales_str']} c/u en {mejor_ig['supermercado']} • {promo_txt}{ahorro}", font_style="Caption", theme_text_color="Custom", text_color=(0,0.45,0.6,1), size_hint_y=None, height=dp(18)))
                resumen.height = dp(108)
            box.add_widget(resumen)
        except Exception:
            pass

        por_super = {}
        for r in resultados:
            por_super.setdefault(r["supermercado"], []).append(r)
        orden = ["MasOnline","VEA","Carrefour"]
        supers = sorted(por_super.keys(), key=lambda k: orden.index(k) if k in orden else 99)

        for super_nombre in supers:
            items = por_super[super_nombre]
            col = COLORES.get(super_nombre, COLORES["Carrefour"])
            # Header super con color
            header = MDCard(size_hint_y=None, height=dp(36), radius=[12,], elevation=0, md_bg_color=col["light"], padding=dp(10))
            header.add_widget(MDLabel(text=f"🛒  {super_nombre}  •  {len(items)} productos", font_style="Subtitle2", theme_text_color="Custom", text_color=col["primary"]))
            box.add_widget(header)

            for r in items:
                pf = r["precio_final"]
                pe_ig = r.get("precio_efectivo_iguales", pf)
                es_min = abs(pf - precio_min) < 0.01
                es_min_ig = abs(pe_ig - precio_min_ig) < 0.01 and pe_ig < pf -0.01

                card = MDCard(orientation="horizontal", size_hint_y=None, height=dp(116), radius=[16,], elevation=1, padding=dp(8), spacing=dp(10), md_bg_color=(1,1,1,1))
                # Imagen
                img_box = MDBoxLayout(size_hint_x=None, width=dp(84), md_bg_color=(0.97,0.97,0.97,1), radius=[12,])
                try:
                    if r.get("imagen"):
                        img = AsyncImage(source=r["imagen"], size_hint=(1,1), allow_stretch=True, keep_ratio=True)
                        img_box.add_widget(img)
                    else:
                        img_box.add_widget(MDLabel(text="🛍️", halign="center", font_style="H5"))
                except:
                    img_box.add_widget(MDLabel(text="🛍️", halign="center"))
                card.add_widget(img_box)

                # Info
                info = MDBoxLayout(orientation="vertical", spacing=dp(2))
                nombre = r["nombre"][:46] + ("…" if len(r["nombre"])>46 else "")
                info.add_widget(MDLabel(text=nombre, font_style="Subtitle2", theme_text_color="Primary", size_hint_y=None, height=dp(18)))

                # Precio
                if es_min and es_min_ig:
                    precio_txt = f"{r['precio_str']}  • MÁS BARATO"
                elif es_min:
                    precio_txt = f"{r['precio_str']}  • MÁS BARATO x1"
                else:
                    precio_txt = r["precio_str"]
                precio_lbl = MDLabel(text=f"💲 {precio_txt}", font_style="H6", size_hint_y=None, height=dp(22), theme_text_color="Custom", text_color=col["primary"] if es_min else (0.15,0.15,0.15,1))
                info.add_widget(precio_lbl)

                # Precio original tachado
                po = r.get("precio_original")
                if po and po > pf:
                    try:
                        if po/pf <= 3.0:
                            info.add_widget(MDLabel(text=f"antes {formatear_precio(po)}", font_style="Caption", theme_text_color="Hint", size_hint_y=None, height=dp(14)))
                    except:
                        pass

                # Promos (solo 1-2)
                for promo in r.get("promociones", [])[:2]:
                    is_best = es_min_ig and promo == r.get("promo_iguales")
                    chip_text = f"{'⭐' if is_best else '🏷️'} {promo}"
                    if len(chip_text) > 48:
                        chip_text = chip_text[:48] + "…"
                    lbl = MDLabel(text=chip_text, font_style="Caption", theme_text_color="Custom", text_color=(0,0.5,0.25,1) if is_best else (0.5,0.35,0,1), size_hint_y=None, height=dp(16))
                    info.add_widget(lbl)

                if not es_min and es_min_ig:
                    info.add_widget(MDLabel(text=f"→ {r['precio_efectivo_iguales_str']} c/u ¡más barato con promo!", font_style="Caption", theme_text_color="Custom", text_color=(0,0.6,0.25,1), size_hint_y=None, height=dp(14)))

                card.add_widget(info)

                # Botón abrir
                btn = MDIconButton(icon="open-in-new", theme_text_color="Custom", text_color=col["primary"], size_hint_x=None, width=dp(40))
                btn.bind(on_release=lambda x, url=r["url"]: webbrowser.open(url) if url else None)
                card.add_widget(btn)

                box.add_widget(card)

    def cargar_promos_bancarias(self):
        self.root.ids.promos_status.text = "Cargando promos bancarias…"
        self.root.ids.promos_box.clear_widgets()
        # Skeleton
        for i in range(3):
            sk = MDCard(size_hint_y=None, height=dp(60), radius=[12,], md_bg_color=(1,1,1,1), padding=dp(14))
            sk.add_widget(MDLabel(text="⏳ Cargando…", theme_text_color="Hint"))
            self.root.ids.promos_box.add_widget(sk)
        threading.Thread(target=self._cargar_promos_thread, daemon=True).start()

    def _cargar_promos_thread(self):
        try:
            data = obtener_promos_bancarias()
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.root.ids.promos_status, 'text', f"Error: {e}"))
            return
        Clock.schedule_once(lambda dt: self._mostrar_promos_bancarias(data))

    def _mostrar_promos_bancarias(self, data):
        box = self.root.ids.promos_box
        box.clear_widgets()
        self.root.ids.promos_status.text = "Promos vigentes • Tocá para actualizar"
        for super_nombre in ["MasOnline","VEA","Carrefour"]:
            promos = data.get(super_nombre, [])
            col = COLORES.get(super_nombre, COLORES["Carrefour"])
            card = MDCard(orientation="vertical", size_hint_y=None, height=dp(72 + len(promos)*32), radius=[16,], elevation=1, padding=dp(14), spacing=dp(8), md_bg_color=(1,1,1,1))
            # Header con color lateral
            header = MDBoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
            # Barra lateral color
            barra = MDBoxLayout(size_hint_x=None, width=dp(4), md_bg_color=col["primary"], radius=[4,])
            header.add_widget(barra)
            header.add_widget(MDLabel(text=f"🏦  {super_nombre}", font_style="H6", theme_text_color="Custom", text_color=col["primary"], size_hint_x=0.6))
            header.add_widget(MDLabel(text=f"{len(promos)} promos", font_style="Caption", theme_text_color="Hint", halign="right", size_hint_x=0.4))
            card.add_widget(header)
            card.add_widget(MDLabel(text="─"*36, theme_text_color="Hint", font_style="Caption", size_hint_y=None, height=dp(8)))
            if not promos:
                card.add_widget(MDLabel(text="Sin promos detectadas", theme_text_color="Hint", font_style="Caption"))
            else:
                for p in promos[:6]:
                    banco = p.get("banco","Banco")
                    promo = p.get("promo","")
                    detalle = p.get("detalle","")
                    # Fila promo
                    row = MDBoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
                    row.add_widget(MDLabel(text="💳", size_hint_x=None, width=dp(24), halign="center"))
                    txt = f"{banco}: {promo}"
                    if detalle:
                        txt += f" — {detalle}"
                    lbl = MDLabel(text=txt[:88], font_style="Caption", theme_text_color="Primary", halign="left")
                    row.add_widget(lbl)
                    card.add_widget(row)
            box.add_widget(card)
        box.add_widget(MDCard(size_hint_y=None, height=dp(56), radius=[12,], padding=dp(12), md_bg_color=(0.94,0.96,1,1), elevation=0))
        # Nota final se agrega como label dentro del último card ya, pero agregamos uno extra
        box.add_widget(MDLabel(text="💡 Tip: Las promos bancarias se actualizan dinámicamente. Los descuentos de pago aparecen también en cada producto.", theme_text_color="Hint", font_style="Caption", halign="center", size_hint_y=None, height=dp(36)))

