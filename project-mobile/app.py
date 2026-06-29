import os
from kivy.config import Config
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
import requests

API = 'http://127.0.0.1:5000'

Config.set('graphics', 'resizable', True)
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '750')

BLUE = (0.094, 0.208, 0.451, 1)
WHITE = (1, 1, 1, 1)
GREEN = (0, 0.5, 0.2, 1)
RED = (0.8, 0.15, 0.15, 1)
GRAY = (0.6, 0.6, 0.65, 1)

Config.set('graphics', 'resizable', True)
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '750')

class GradientButton(BoxLayout):
    def __init__(self, text, color_top, color_bottom, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(46)
        self.color_top = color_top
        self.color_bottom = color_bottom
        self.bind(size=self._draw)

        button = Button(
            text=text,
            background_color=(0, 0, 0, 0),
            background_normal='',
            color=WHITE,
            bold=True,
            font_size=dp(15),
            **kwargs,
        )
        self.add_widget(button)

    def _draw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.color_top)
            Rectangle(size=(self.width, self.height * 0.5), pos=self.pos)
            Color(*self.color_bottom)
            Rectangle(size=(self.width, self.height * 0.5), pos=(self.x, self.y + self.height * 0.5))


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation='vertical', padding=[dp(30), dp(50), dp(30), dp(20)], spacing=dp(10))

        root.add_widget(Widget(size_hint_y=None, height=dp(10)))
        root.add_widget(Image(source='assets/logo.png', size_hint_y=None, height=dp(100), keep_ratio=True))
        root.add_widget(Label(text='ИАРА', font_size=dp(28), bold=True, color=BLUE, size_hint_y=None, height=dp(34)))
        root.add_widget(Label(text='Вход', font_size=dp(14), color=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=dp(22)))

        root.add_widget(Widget(size_hint_y=None, height=dp(20)))

        self.email_input = TextInput(hint_text='Имейл', size_hint_y=None, height=dp(42), multiline=False, font_size=dp(14), padding=(dp(12), dp(10)))
        root.add_widget(self.email_input)

        self.password_input = TextInput(hint_text='Парола', password=True, size_hint_y=None, height=dp(42), multiline=False, font_size=dp(14), padding=(dp(12), dp(10)))
        root.add_widget(self.password_input)

        self.error_label = Label(text='', color=RED, size_hint_y=None, height=dp(18), font_size=dp(12))
        root.add_widget(self.error_label)

        root.add_widget(Widget(size_hint_y=None, height=dp(6)))

        root.add_widget(GradientButton('ВХОД', BLUE, (0.15, 0.3, 0.55, 1), on_press=self.do_login))
        root.add_widget(GradientButton('РЕГИСТРАЦИЯ', GREEN, (0.05, 0.6, 0.25, 1), on_press=self.go_register))

        root.add_widget(Widget(size_hint_y=1))
        self.add_widget(root)

    def do_login(self, instance):
        email = self.email_input.text.strip()
        password = self.password_input.text

        if not email or not password:
            self.error_label.text = 'Попълнете всички полета'
            return

        try:
            response = requests.post(
                f'{API}/auth/login',
                data={'email': email, 'password': password},
                allow_redirects=False,
                timeout=10,
            )
            if response.status_code in (200, 302):
                self.error_label.text = ''
                self.manager.current = 'home'
            else:
                self.error_label.text = 'Грешен имейл или парола'
        except requests.ConnectionError:
            self.error_label.text = 'Няма връзка със сървъра'
        except Exception:
            self.error_label.text = 'Грешка при връзка със сървъра'

    def go_register(self, instance):
        self.manager.current = 'register'


class RegisterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation='vertical', padding=[dp(30), dp(20), dp(30), dp(20)], spacing=dp(8))

        root.add_widget(Image(source='assets/logo.png', size_hint_y=None, height=dp(60), keep_ratio=True))
        root.add_widget(Label(text='Регистрация', font_size=dp(20), bold=True, color=BLUE, size_hint_y=None, height=dp(30)))

        fields = [
            ('full_name_input', 'Пълно име', False),
            ('email_input', 'Имейл', False),
            ('password_input', 'Парола', True),
            ('password2_input', 'Повторете паролата', True),
            ('identifier_input', 'ЕГН/ЕИК', False),
            ('phone_input', 'Телефон', False),
        ]

        for attr_name, hint_text, is_password in fields:
            text_input = TextInput(
                hint_text=hint_text,
                password=is_password,
                size_hint_y=None,
                height=dp(40),
                multiline=False,
                font_size=dp(13),
                padding=(dp(12), dp(10)),
            )
            setattr(self, attr_name, text_input)
            root.add_widget(text_input)

        self.error_label = Label(text='', color=RED, size_hint_y=None, height=dp(16), font_size=dp(12))
        root.add_widget(self.error_label)

        root.add_widget(GradientButton('РЕГИСТРИРАЙ СЕ', GREEN, (0.05, 0.6, 0.25, 1), on_press=self.do_register))
        root.add_widget(GradientButton('НАЗАД', GRAY, (0.7, 0.7, 0.75, 1), on_press=lambda x: setattr(self.manager, 'current', 'login')))

        root.add_widget(Widget(size_hint_y=1))
        self.add_widget(root)

    def do_register(self, instance):
        email = self.email_input.text.strip()
        password = self.password_input.text
        password2 = self.password2_input.text
        full_name = self.full_name_input.text.strip()
        identifier = self.identifier_input.text.strip()

        if not all([email, password, password2, full_name, identifier]):
            self.error_label.text = 'Попълнете всички задължителни полета'
            return

        if password != password2:
            self.error_label.text = 'Паролите не съвпадат'
            return

        if len(password) < 6:
            self.error_label.text = 'Паролата трябва да е поне 6 символа'
            return

        try:
            data = {
                'email': email,
                'password': password,
                'password2': password2,
                'full_name': full_name,
                'identifier': identifier,
                'phone': self.phone_input.text.strip(),
            }
            response = requests.post(f'{API}/auth/register', data=data, allow_redirects=False, timeout=10)
            if response.status_code in (200, 302):
                self.error_label.text = ''
                self.manager.current = 'home'
            else:
                self.error_label.text = f'Грешка: {response.status_code}'
        except requests.ConnectionError:
            self.error_label.text = 'Няма връзка със сървъра'
        except Exception:
            self.error_label.text = 'Грешка при връзка със сървъра'


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        def refresh_header(widget, _):
            widget.canvas.before.clear()
            with widget.canvas.before:
                Color(*BLUE)
                Rectangle(size=widget.size, pos=widget.pos)

        header = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(170), padding=[dp(20), dp(20)])
        header.bind(size=refresh_header, pos=refresh_header)
        refresh_header(header, None)
        header.add_widget(Image(source='assets/logo.png', size_hint_y=None, height=dp(55), keep_ratio=True))
        header.add_widget(Label(text='ИАРА', font_size=dp(22), bold=True, color=WHITE, size_hint_y=None, height=dp(30)))
        header.add_widget(Label(text='Добре дошли!', font_size=dp(14), color=(0.7, 0.85, 1, 1), size_hint_y=None, height=dp(24)))

        body = BoxLayout(orientation='vertical', padding=[dp(30), dp(80)], spacing=dp(10))
        body.add_widget(Label(text='Успешен вход!', font_size=dp(22), bold=True, color=BLUE, size_hint_y=None, height=dp(100)))

        root = BoxLayout(orientation='vertical')
        root.add_widget(header)
        root.add_widget(body)
        self.add_widget(root)


class IARAApp(App):
    def build(self):
        Window.size = (400, 750)
        Window.title = 'ИАРА'
        Window.clearcolor = (1, 1, 1, 1)

        screen_manager = ScreenManager()
        screen_manager.add_widget(LoginScreen(name='login'))
        screen_manager.add_widget(RegisterScreen(name='register'))
        screen_manager.add_widget(HomeScreen(name='home'))
        return screen_manager


if __name__ == '__main__':
    IARAApp().run()
