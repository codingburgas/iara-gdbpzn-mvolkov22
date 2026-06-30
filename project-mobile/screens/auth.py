from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.metrics import dp
from core import API, api_get, BLUE, GREEN, RED, GRAY, sess, _user, GradBtn


class LoginScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation='vertical', padding=[dp(30), dp(50), dp(30), dp(20)], spacing=dp(10))
        root.add_widget(Widget(size_hint_y=None, height=dp(10)))
        root.add_widget(Image(source='assets/logo.png', size_hint_y=None, height=dp(100), keep_ratio=True))
        root.add_widget(Label(text='ИАРА', font_size=dp(28), bold=True, color=BLUE, size_hint_y=None, height=dp(34)))
        root.add_widget(Label(text='Вход', font_size=dp(14), color=GRAY, size_hint_y=None, height=dp(22)))
        root.add_widget(Widget(size_hint_y=None, height=dp(20)))
        self.em = TextInput(hint_text='Имейл', size_hint_y=None, height=dp(44), multiline=False, font_size=dp(14), padding=(dp(12), dp(10)))
        root.add_widget(self.em)
        self.pw = TextInput(hint_text='Парола', password=True, size_hint_y=None, height=dp(44), multiline=False, font_size=dp(14), padding=(dp(12), dp(10)))
        root.add_widget(self.pw)
        self.err = Label(text='', color=RED, size_hint_y=None, height=dp(18), font_size=dp(12))
        root.add_widget(self.err)
        root.add_widget(GradBtn('ВХОД', BLUE, (0.15, 0.3, 0.55, 1), on_press=self.do_login))
        root.add_widget(GradBtn('РЕГИСТРАЦИЯ', GREEN, (0.05, 0.6, 0.25, 1), on_press=lambda x: setattr(self.manager, 'current', 'register')))
        root.add_widget(Widget(size_hint_y=1))
        self.add_widget(root)

    def do_login(self, _):
        e, p = self.em.text.strip(), self.pw.text
        if not e or not p: self.err.text = 'Попълнете всички полета'; return
        try:
            r = sess.post(f'{API}/auth/login', data={'email': e, 'password': p}, allow_redirects=False, timeout=10)
            if r.status_code in (200, 302):
                me = api_get('/me')
                if me:
                    _user.update(me)
                    target = 'inspector_dashboard' if me.get('role') == 'inspector' else 'home'
                    self.manager.current = target
                else: self.err.text = 'Грешка при проверка на профила'
            else: self.err.text = 'Грешен имейл или парола'
        except: self.err.text = 'Няма връзка със сървъра'


class RegisterScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation='vertical', padding=[dp(30), dp(20), dp(30), dp(20)], spacing=dp(8))
        root.add_widget(Image(source='assets/logo.png', size_hint_y=None, height=dp(60), keep_ratio=True))
        root.add_widget(Label(text='Регистрация', font_size=dp(20), bold=True, color=BLUE, size_hint_y=None, height=dp(30)))
        for attr, hint, pw in [('fn', 'Пълно име', False), ('em', 'Имейл', False), ('pw', 'Парола', True), ('pw2', 'Повторете паролата', True), ('idf', 'ЕГН/ЕИК', False), ('ph', 'Телефон', False)]:
            inp = TextInput(hint_text=hint, password=pw, size_hint_y=None, height=dp(40), multiline=False, font_size=dp(13), padding=(dp(12), dp(10)))
            setattr(self, f'{attr}_i', inp); root.add_widget(inp)
        self.err = Label(text='', color=RED, size_hint_y=None, height=dp(16), font_size=dp(12))
        root.add_widget(self.err)
        root.add_widget(GradBtn('РЕГИСТРИРАЙ СЕ', GREEN, (0.05, 0.6, 0.25, 1), on_press=self.do_reg))
        root.add_widget(GradBtn('НАЗАД', GRAY, (0.7, 0.7, 0.75, 1), on_press=lambda x: setattr(self.manager, 'current', 'login')))
        root.add_widget(Widget(size_hint_y=1)); self.add_widget(root)

    def do_reg(self, _):
        e, pw, pw2, fn, idf = self.em_i.text.strip(), self.pw_i.text, self.pw2_i.text, self.fn_i.text.strip(), self.idf_i.text.strip()
        if not all([e, pw, pw2, fn, idf]): self.err.text = 'Попълнете всички задължителни полета'; return
        if pw != pw2: self.err.text = 'Паролите не съвпадат'; return
        if len(pw) < 6: self.err.text = 'Паролата трябва да е поне 6 символа'; return
        try:
            r = sess.post(f'{API}/auth/register', data={'email': e, 'password': pw, 'password2': pw2, 'full_name': fn, 'identifier': idf, 'phone': self.ph_i.text.strip()}, allow_redirects=False, timeout=10)
            if r.status_code in (200, 302):
                me = api_get('/me'); self.err.text = ''
                if me: _user.update(me)
                self.manager.current = 'inspector_dashboard' if me and me.get('role') == 'inspector' else 'home'
            else: self.err.text = f'Грешка: {r.status_code}'
        except: self.err.text = 'Няма връзка със сървъра'
