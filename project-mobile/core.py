import requests as req
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle

API = 'http://127.0.0.1:5000'
BLUE = (0.094, 0.208, 0.451, 1)
BLUE_LIGHT = (0.15, 0.35, 0.6, 1)
WHITE = (1, 1, 1, 1)
GREEN = (0, 0.5, 0.2, 1)
RED = (0.8, 0.15, 0.15, 1)
GRAY = (0.6, 0.6, 0.65, 1)
ORANGE = (0.9, 0.55, 0.1, 1)
BG = (0.96, 0.97, 0.98, 1)

sess = req.Session()
_user = {}


def api_get(path):
    try:
        r = sess.get(f'{API}/api{path}', timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None


def api_post(path, data):
    try: return sess.post(f'{API}/api{path}', json=data, timeout=10)
    except: return type('R', (), {'status_code': 0})()


def colored(w, c):
    w.canvas.before.clear()
    with w.canvas.before: Color(*c); Rectangle(size=w.size, pos=w.pos)
    w.bind(size=lambda x, _: colored(x, c))


def header_bar(text, color=BLUE):
    h = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(72), padding=[dp(20), dp(8)])
    colored(h, color)
    h.add_widget(Label(text=text, font_size=dp(18), bold=True, color=WHITE, size_hint_y=None, height=dp(28)))
    return h


def back_btn(screen):
    b = BoxLayout(size_hint_y=None, height=dp(48), padding=[dp(5), 0])
    colored(b, BLUE)
    btn = Button(text='<  НАЗАД', size_hint=(1, 1), background_color=(0,0,0,0), color=WHITE, bold=True, font_size=dp(14))
    btn.bind(on_press=lambda x: setattr(screen.manager, 'current', screen._back_to))
    b.add_widget(btn)
    return b


def bottom_tabs(active, screen):
    from core import _user
    role = _user.get('role', 'user')
    if role == 'inspector':
        tabs = [('Главная', 'inspector_dashboard'), ('Профил', 'profile')]
    else:
        tabs = [('Главная', 'home'), ('Профил', 'profile')]
    b = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(0))
    colored(b, (0.05, 0.1, 0.2, 1))
    for label, key in tabs:
        on = key == active
        btn = Button(text=label, font_size=dp(12), bold=on,
                     background_color=(0.2, 0.3, 0.55, 1) if on else (0,0,0,0),
                     color=WHITE if on else (0.6, 0.7, 0.9, 1))
        btn.bind(on_press=lambda x, k=key: setattr(screen.manager, 'current', k))
        b.add_widget(btn)
    return b


def menu_card(text, color, on_press):
    btn = Button(text=f'  {text}  >', font_size=dp(16), bold=True, color=WHITE,
                 background_color=(0,0,0,0), halign='left', valign='middle', padding=(dp(20), 0))
    btn.bind(on_press=on_press)
    box = BoxLayout(size_hint_y=None, height=dp(60))
    colored(box, color); box.add_widget(btn)
    return box


class GradBtn(BoxLayout):
    def __init__(self, text, c1, c2, **kw):
        super().__init__(**kw)
        self.orientation = 'vertical'; self.size_hint_y = None; self.height = dp(48)
        self.c1, self.c2 = c1, c2; self.bind(size=self._draw)
        self.add_widget(Button(text=text, background_color=(0,0,0,0), background_normal='',
                               color=WHITE, bold=True, font_size=dp(15), **kw))
    def _draw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.c1); Rectangle(size=(self.width, self.height*.5), pos=self.pos)
            Color(*self.c2); Rectangle(size=(self.width, self.height*.5), pos=(self.x, self.y+self.height*.5))
