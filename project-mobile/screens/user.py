from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from core import BLUE, BLUE_LIGHT, WHITE, GREEN, RED, GRAY, ORANGE, BG, colored, header_bar, bottom_tabs, GradBtn, menu_card, _user


class HomeScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self.build_ui()

    def build_ui(self):
        sv = ScrollView()
        root = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8), padding=[dp(0), dp(0)])
        root.bind(minimum_height=root.setter('height'))
        root.add_widget(header_bar('ИАРА — Рибарство', BLUE))
        root.add_widget(Label(text=_user.get('full_name', 'Потребител'), font_size=dp(16), bold=True, color=BLUE, size_hint_y=None, height=dp(36)))
        for txt, clr, sc in [
            ('Моите билети', GREEN, 'ticket_list'),
            ('Регистрирай улов', ORANGE, 'logbook_list'),
        ]:
            root.add_widget(menu_card(txt, clr, lambda x, s=sc: setattr(self.manager, 'current', s)))
        root.add_widget(Widget(size_hint_y=None, height=dp(20)))
        sv.add_widget(root)
        main = BoxLayout(orientation='vertical')
        main.add_widget(sv)
        main.add_widget(bottom_tabs('home', self))
        self.add_widget(main)
