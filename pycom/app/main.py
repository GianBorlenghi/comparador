"""
Pergamino Precios - APK KivyMD
App sencilla y amigable para comparar precios y ver promos bancarias.
"""
import threading
import webbrowser
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout

from core import buscar_en_todos, formatear_precio, obtener_promos_bancarias

KV = '''
MDScreen:
    MDNavigationLayout:
        MDScreenManager:
            id: sm
            MDScreen:
                name: "comparar"
                MDBoxLayout:
                    orientation: "vertical"
                    md_bg_color: 0.97, 0.97, 0.97, 1
                    MDTopAppBar:
                        title: "Pergamino Precios"
                        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
                        elevation: 2
                    MDBoxLayout:
                        orientation: "vertical"
                        padding: dp(14)
                        spacing: dp(10)
                        adaptive_height: True
                        MDLabel:
                            text: "¿Qué querés comparar?"
                            font_style: "H6"
                            size_hint_y: None
                            height: self.texture_size[1]
                            theme_text_color: "Primary"
                        MDBoxLayout:
                            size_hint_y: None
                            height: dp(52)
                            spacing: dp(8)
                            MDTextField:
                                id: search_field
                                hint_text: "Ej: coca cola 2.25, leche serenisima, yerba 1kg"
                                mode: "round"
                                on_text_validate: app.buscar()
                            MDRaisedButton:
                                text: "Buscar"
                                size_hint_x: None
                                width: dp(90)
                                on_release: app.buscar()
                        MDLabel:
                            id: status_label
                            text: "Tip: probá con menos palabras si no hay resultados"
                            font_style: "Caption"
                            theme_text_color: "Hint"
                            size_hint_y: None
                            height: self.texture_size[1]
                    MDScrollView:
                        MDBoxLayout:
                            id: results_box
                            orientation: "vertical"
                            spacing: dp(10)
                            padding: dp(12), dp(10), dp(12), dp(20)
                            adaptive_height: True
            MDScreen:
                name: "promos"
                MDBoxLayout:
                    orientation: "vertical"
                    md_bg_color: 0.97, 0.97, 0.97, 1
                    MDTopAppBar:
                        title: "Promos Bancarias"
                        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
                    MDBoxLayout:
                        padding: dp(12)
                        spacing: dp(8)
                        size_hint_y: None
                        height: dp(50)
                        MDRaisedButton:
                            text: "Actualizar promos"
                            on_release: app.cargar_promos_bancarias()
                        MDLabel:
                            id: promos_status
                            text: "Tocá actualizar para ver promos vigentes"
                            font_style: "Caption"
                            theme_text_color: "Hint"
                    MDScrollView:
                        MDBoxLayout:
                            id: promos_box
                            orientation: "vertical"
                            spacing: dp(12)
                            padding: dp(12)
                            adaptive_height: True
        MDNavigationDrawer:
            id: nav_drawer
            MDNavigationDrawerMenu:
                MDNavigationDrawerHeader:
                    title: "Pergamino Precios"
                    text: "MasOnline • VEA • Carrefour"
                    spacing: "4dp"
                    padding: "12dp", 0, 0, "56dp"
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
                    text: "Zona: Pergamino"
<DrawerClickableItem@MDNavigationDrawerItem>
'''

class PergaminoApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.accent_palette = "Orange"
        self.theme_cls.theme_style = "Light"
        self.title = "Pergamino Precios"
        return Builder.load_string(KV)

    def on_start(self):
        threading.Thread(target=self._load_promos_bg, daemon=True).start()
        self.root.ids.status_label.text = "Escribí un producto y tocá Buscar — Ej: coca cola 2.25"

    def _load_promos_bg(self):
        try:
            obtener_promos_bancarias()
        except Exception:
            pass

    def buscar(self):
        query = self.root.ids.search_field.text.strip()
        if not query:
            self.root.ids.status_label.text = "Escribí algo para buscar"
            return
        self.root.ids.status_label.text = f'Buscando "{query}" en 3 supers...'
        self.root.ids.results_box.clear_widgets()
        loading = MDLabel(text="  🔍 Buscando en MasOnline, VEA y Carrefour...", theme_text_color="Hint", size_hint_y=None, height=dp(30))
        self.root.ids.results_box.add_widget(loading)
        threading.Thread(target=self._buscar_thread, args=(query,), daemon=True).start()

    def _buscar_thread(self, query):
        try:
            resultados = buscar_en_todos(query)
        except Exception as e:
            err = str(e)
            Clock.schedule_once(lambda dt: self._mostrar_error(err))
            return
        Clock.schedule_once(lambda dt: self._mostrar_resultados(resultados, query))

    def _mostrar_error(self, err):
        self.root.ids.results_box.clear_widgets()
        self.root.ids.status_label.text = f"Error: {err}"

    def _mostrar_resultados(self, resultados, query):
        box = self.root.ids.results_box
        box.clear_widgets()
        if not resultados:
            self.root.ids.status_label.text = f'Sin resultados para "{query}"'
            card = MDCard(orientation="vertical", padding=dp(14), size_hint_y=None, height=dp(90), radius=[12,], elevation=1)
            card.add_widget(MDLabel(text="Sin resultados.\\nProbá: 'coca cola 2.25' / 'leche serenisima'", halign="center", theme_text_color="Hint"))
            box.add_widget(card)
            return
        precio_min = min(r["precio_final"] for r in resultados)
        try:
            precio_min_iguales = min(r.get("precio_efectivo_iguales", r["precio_final"]) for r in resultados)
        except:
            precio_min_iguales = precio_min
        self.root.ids.status_label.text = f'{len(resultados)} productos • Más barato x1: {formatear_precio(precio_min)} • Con promo: {formatear_precio(precio_min_iguales)} c/u'
        por_super = {}
        for r in resultados:
            por_super.setdefault(r["supermercado"], []).append(r)
        orden = ["MasOnline", "VEA", "Carrefour"]
        supers = sorted(por_super.keys(), key=lambda k: orden.index(k) if k in orden else 99)
        try:
            mejor = next(r for r in resultados if abs(r["precio_final"]-precio_min)<0.01)
            mejor_ig = next(r for r in resultados if abs(r.get("precio_efectivo_iguales", r["precio_final"])-precio_min_iguales)<0.01)
            resumen = MDCard(orientation="vertical", padding=dp(12), spacing=dp(4), size_hint_y=None, height=dp(90), radius=[12,], elevation=2, md_bg_color=(0.88, 1, 0.88, 1))
            resumen.add_widget(MDLabel(text=f"⭐ Más barato (1 unidad): {mejor['precio_str']} en {mejor['supermercado']}", font_style="Subtitle2", theme_text_color="Primary", size_hint_y=None, height=dp(20)))
            resumen.add_widget(MDLabel(text=mejor["nombre"][:50], font_style="Caption", theme_text_color="Hint", size_hint_y=None, height=dp(16)))
            if mejor_ig.get("precio_efectivo_iguales_str") and (abs(precio_min_iguales-precio_min)>0.01 or mejor["supermercado"]!=mejor_ig["supermercado"]):
                promo_txt = mejor_ig.get("promo_iguales","").split("→")[0].strip()[:40]
                resumen.add_widget(MDLabel(text=f"⭐ Con promo: {mejor_ig['precio_efectivo_iguales_str']} c/u en {mejor_ig['supermercado']} ({promo_txt})", font_style="Caption", theme_text_color="Primary", size_hint_y=None, height=dp(16)))
                resumen.height = dp(110)
            box.add_widget(resumen)
        except Exception:
            pass
        for super_nombre in supers:
            items = por_super[super_nombre]
            header = MDLabel(text=f"🛒  {super_nombre}  ({len(items)} productos)", font_style="H6", size_hint_y=None, height=dp(28), theme_text_color="Primary")
            box.add_widget(header)
            for r in items:
                card = MDCard(orientation="vertical", padding=dp(12), spacing=dp(6), size_hint_y=None, height=dp(140), radius=[12,], elevation=1)
                card.height = dp(110 + len(r.get("promociones",[]))*22)
                pf = r["precio_final"]
                pe_ig = r.get("precio_efectivo_iguales", pf)
                es_min = abs(pf - precio_min) < 0.01
                es_min_ig = abs(pe_ig - precio_min_iguales) < 0.01 and pe_ig < pf - 0.01
                nombre_lbl = MDLabel(text=r["nombre"][:52], font_style="Subtitle2", theme_text_color="Primary", size_hint_y=None, height=dp(20))
                card.add_widget(nombre_lbl)
                precio_txt = r["precio_str"]
                if es_min and es_min_ig:
                    precio_txt += "  ◄ MÁS BARATO (1u y promo)"
                elif es_min:
                    precio_txt += "  ◄ MÁS BARATO x1"
                precio_lbl = MDLabel(text=f"💲 {precio_txt}", font_style="H6", size_hint_y=None, height=dp(22))
                if es_min:
                    precio_lbl.theme_text_color = "Custom"
                    precio_lbl.text_color = (0, 0.6, 0.25, 1)
                card.add_widget(precio_lbl)
                po = r.get("precio_original")
                if po and po > pf:
                    try:
                        if po/pf <= 3.0:
                            card.add_widget(MDLabel(text=f"antes {formatear_precio(po)}", font_style="Caption", theme_text_color="Hint", size_hint_y=None, height=dp(14)))
                    except:
                        pass
                for promo in r.get("promociones", [])[:2]:
                    is_best = es_min_ig and promo == r.get("promo_iguales")
                    txt = f"• {promo}"
                    if is_best:
                        txt += "  ◄ MÁS BARATO c/u"
                    lbl = MDLabel(text=txt, font_style="Caption", theme_text_color="Primary" if is_best else "Hint", size_hint_y=None, height=dp(18))
                    if is_best:
                        lbl.theme_text_color = "Custom"
                        lbl.text_color = (0, 0.6, 0.25, 1)
                    card.add_widget(lbl)
                if not es_min and es_min_ig:
                    card.add_widget(MDLabel(text=f"   → Efectivo {r['precio_efectivo_iguales_str']} c/u (¡más barato llevando promo!)", theme_text_color="Custom", text_color=(0,0.6,0.25,1), font_style="Caption", size_hint_y=None, height=dp(16)))
                if r.get("url"):
                    btn = MDFlatButton(text="Ver en tienda", size_hint_y=None, height=dp(30), pos_hint={"center_x": 0.5})
                    btn.bind(on_release=lambda x, url=r["url"]: webbrowser.open(url))
                    card.add_widget(btn)
                box.add_widget(card)

    def cargar_promos_bancarias(self):
        self.root.ids.promos_status.text = "Cargando promos bancarias..."
        self.root.ids.promos_box.clear_widgets()
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
        self.root.ids.promos_status.text = f"Actualizado • {len(data)} supers"
        for super_nombre in ["MasOnline","VEA","Carrefour"]:
            promos = data.get(super_nombre, [])
            card = MDCard(orientation="vertical", padding=dp(14), spacing=dp(8), size_hint_y=None, height=dp(80 + len(promos)*30), radius=[12,], elevation=1)
            header_box = MDBoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
            header_box.add_widget(MDLabel(text=f"🏦 {super_nombre}", font_style="H6", theme_text_color="Primary", size_hint_x=0.7))
            header_box.add_widget(MDLabel(text=f"{len(promos)} promos", font_style="Caption", theme_text_color="Hint", halign="right", size_hint_x=0.3))
            card.add_widget(header_box)
            card.add_widget(MDLabel(text="─"*40, theme_text_color="Hint", font_style="Caption", size_hint_y=None, height=dp(10)))
            if not promos:
                card.add_widget(MDLabel(text="Sin promos detectadas", theme_text_color="Hint", font_style="Caption"))
            else:
                for p in promos[:6]:
                    banco = p.get("banco","Banco")
                    promo = p.get("promo","")
                    detalle = p.get("detalle","")
                    txt = f"• {banco}: {promo}"
                    if detalle:
                        txt += f" — {detalle}"
                    lbl = MDLabel(text=txt[:90], font_style="Caption", theme_text_color="Primary", size_hint_y=None, height=dp(28))
                    card.add_widget(lbl)
            box.add_widget(card)
        box.add_widget(MDLabel(text="Tip: Las promos bancarias se actualizan dinámicamente desde la API. Los descuentos de pago como Cencopay/CSI aparecen también en cada producto.", theme_text_color="Hint", font_style="Caption", size_hint_y=None, height=dp(40), halign="center"))
