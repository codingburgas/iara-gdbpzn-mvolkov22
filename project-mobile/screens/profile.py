from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from core import API, WHITE, BLUE, GRAY, RED, BG, colored, header_bar, bottom_tabs, GradBtn, _user, sess


class ProfileScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self._user_data = {}; self.build_ui()

    def build_ui(self):
        sv = ScrollView()
        self.content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10))
        self.content.bind(minimum_height=self.content.setter('height'))
        colored(self.content, WHITE)
        self.content.add_widget(header_bar('Моят профил', BLUE))

        self.avatar = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(120), padding=[dp(30), dp(15)])
        colored(self.avatar, BG)
        self.name_lbl = Label(text='', font_size=dp(20), bold=True, color=BLUE, size_hint_y=None, height=dp(30))
        self.role_lbl = Label(text='', font_size=dp(13), color=GRAY, size_hint_y=None, height=dp(20))
        self.avatar.add_widget(self.name_lbl); self.avatar.add_widget(self.role_lbl)
        self.content.add_widget(self.avatar)

        info = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4), padding=[dp(20), dp(10)])
        info.bind(minimum_height=info.setter('height'))
        self.email_lbl = Label(text='', font_size=dp(14), size_hint_y=None, height=dp(28), color=(0.2, 0.2, 0.2, 1))
        self.id_lbl = Label(text='', font_size=dp(14), size_hint_y=None, height=dp(28), color=(0.2, 0.2, 0.2, 1))
        self.phone_lbl = Label(text='', font_size=dp(14), size_hint_y=None, height=dp(28), color=(0.2, 0.2, 0.2, 1))
        info.add_widget(self.email_lbl); info.add_widget(self.id_lbl); info.add_widget(self.phone_lbl)
        self.content.add_widget(info)

        self.content.add_widget(Widget(size_hint_y=1))
        sv.add_widget(self.content)

        logout_bar = BoxLayout(size_hint_y=None, height=dp(44), padding=[dp(15), dp(5)])
        colored(logout_bar, (0,0,0,0))
        logout_bar.add_widget(Widget(size_hint_x=1))
        logout_btn = Button(text='Изход', size_hint=(None, 1), width=dp(80),
                            background_color=(0.7, 0.1, 0.1, 1), color=WHITE, bold=True, font_size=dp(12))
        logout_btn.bind(on_press=self.do_logout)
        logout_bar.add_widget(logout_btn)

        main = BoxLayout(orientation='vertical')
        main.add_widget(sv); main.add_widget(logout_bar); main.add_widget(bottom_tabs('profile', self))
        self.add_widget(main)

    def on_enter(self):
        u = self._user_data or _user
        self.name_lbl.text = u.get('full_name', '—')
        rm = {'inspector': 'Инспектор', 'admin': 'Администратор', 'user': 'Потребител'}
        self.role_lbl.text = rm.get(u.get('role', ''), u.get('role', '—'))
        self.email_lbl.text = f'Имейл: {u.get("email", "—")}'
        self.id_lbl.text = f'ЕГН/ЕИК: {u.get("identifier", "—")}'
        self.phone_lbl.text = f'Телефон: {u.get("phone", "—")}'

    def do_logout(self, _):
        sess.get(f'{API}/auth/logout', timeout=5)
        _user.clear(); self.manager.current = 'login'
