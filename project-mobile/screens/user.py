from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.metrics import dp
from core import BLUE, BLUE_LIGHT, WHITE, GREEN, RED, GRAY, BG, colored, header_bar, bottom_tabs, GradBtn, menu_card, sess, _user


class HomeScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self.build_ui()

    def build_ui(self):
        h = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(170), padding=[dp(20), dp(20)])
        colored(h, BLUE)
        h.add_widget(Image(source='assets/logo.png', size_hint_y=None, height=dp(55), keep_ratio=True))
        h.add_widget(Label(text='ИАРА', font_size=dp(22), bold=True, color=WHITE, size_hint_y=None, height=dp(30)))
        h.add_widget(Label(text='Добре дошли!', font_size=dp(14), color=(0.7, 0.85, 1, 1), size_hint_y=None, height=dp(24)))
        body = BoxLayout(orientation='vertical', padding=[dp(30), dp(60)], spacing=dp(15))
        body.add_widget(Label(text='Успешен вход!', font_size=dp(22), bold=True, color=BLUE, size_hint_y=None, height=dp(60)))
        body.add_widget(menu_card('Моят профил', BLUE_LIGHT, lambda x: self.go_profile()))
        root = BoxLayout(orientation='vertical'); root.add_widget(h); root.add_widget(body); self.add_widget(root)

    def go_profile(self):
        self.manager.get_screen('profile')._user_data = dict(_user)
        self.manager.current = 'profile'
