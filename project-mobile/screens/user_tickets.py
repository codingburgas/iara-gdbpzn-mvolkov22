from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from core import api_get, api_post, BLUE, BLUE_LIGHT, WHITE, GREEN, RED, GRAY, ORANGE, BG, colored, header_bar, back_btn, bottom_tabs, menu_card, GradBtn


class TicketListScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self._back_to = 'home'; self.build_ui()

    def build_ui(self):
        sv = ScrollView()
        self.list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4), padding=[dp(8), dp(4)])
        self.list.bind(minimum_height=self.list.setter('height'))
        sv.add_widget(self.list)
        top = BoxLayout(orientation='vertical')
        top.add_widget(header_bar('Моите билети', GREEN))
        top.add_widget(GradBtn('+ НОВ БИЛЕТ', GREEN, (0.05, 0.6, 0.25, 1), on_press=lambda x: setattr(self.manager, 'current', 'ticket_buy')))
        top.add_widget(sv)
        main = BoxLayout(orientation='vertical'); main.add_widget(top); main.add_widget(back_btn(self)); main.add_widget(bottom_tabs('home', self))
        self.add_widget(main)

    def on_enter(self):
        self.list.clear_widgets()
        ticks = api_get('/tickets')
        if not ticks: self.list.add_widget(Label(text='Нямате билети', color=GRAY, size_hint_y=None, height=dp(50))); return
        type_labels = {'standard': 'Стандартен', 'reduced': 'Намален', 'disabled': 'Инвалиден'}
        status_colors = {'active': GREEN, 'expired': GRAY, 'cancelled': RED, 'pending': ORANGE}
        status_labels = {'active': 'Активен', 'expired': 'Изтекъл', 'cancelled': 'Анулиран', 'pending': 'Чака одобрение'}
        for t in ticks:
            clr = status_colors.get(t['status'], GRAY)
            box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(70), padding=[dp(10), dp(6)])
            colored(box, BG)
            info = BoxLayout(orientation='vertical')
            info.add_widget(Label(text=f'{t["receipt_number"]}  [{status_labels.get(t["status"], t["status"])}]', bold=True, color=clr, size_hint_y=None, height=dp(26)))
            info.add_widget(Label(text=f'{type_labels.get(t["ticket_type"], t["ticket_type"])} — {t["period"]}  |  {t.get("price",0)} EUR', color=GRAY, size_hint_y=None, height=dp(20)))
            if t.get('valid_until'): info.add_widget(Label(text=f'Важи до: {t["valid_until"][:10]}', color=GRAY, size_hint_y=None, height=dp(18)))
            box.add_widget(info)
            arrow = Button(text='>', size_hint=(0.12, 1), background_color=(0,0,0,0), color=clr, bold=True, font_size=dp(18))
            tid = t['id']; arrow.bind(on_press=lambda x, i=tid: self.open_ticket(i))
            box.add_widget(arrow); self.list.add_widget(box)

    def open_ticket(self, tid):
        self.manager.get_screen('ticket_detail').load(tid); self.manager.current = 'ticket_detail'


class TicketBuyScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self._back_to = 'ticket_list'; self.build_ui()

    def build_ui(self):
        sv = ScrollView()
        root = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8), padding=[dp(15), dp(10)])
        root.bind(minimum_height=root.setter('height'))
        colored(root, WHITE)
        root.add_widget(header_bar('Нов билет', GREEN))
        root.add_widget(Label(text='Тип билет:', bold=True, color=BLUE, size_hint_y=None, height=dp(24)))
        self.ts = Spinner(text='Стандартен', values=('Стандартен', 'Намален', 'Инвалиден'), size_hint_y=None, height=dp(44))
        self.ts.bind(text=lambda s, _: self.update_price())
        root.add_widget(self.ts)
        root.add_widget(Label(text='Период:', bold=True, color=BLUE, size_hint_y=None, height=dp(24)))
        self.ps = Spinner(text='1 седмица', values=('1 седмица', '1 месец', '6 месеца', '1 година'), size_hint_y=None, height=dp(44))
        self.ps.bind(text=lambda s, _: self.update_price())
        root.add_widget(self.ps)
        self.telk = TextInput(hint_text='ТЕЛК номер (само за инвалиден)', size_hint_y=None, height=dp(42), multiline=False, font_size=dp(13))
        root.add_widget(self.telk)
        self.price_lbl = Label(text='Цена: 6.14 EUR', bold=True, color=GREEN, size_hint_y=None, height=dp(30))
        root.add_widget(self.price_lbl)
        self.err = Label(text='', color=RED, size_hint_y=None, height=dp(20), font_size=dp(12))
        root.add_widget(self.err)
        root.add_widget(GradBtn('КУПИ БИЛЕТ', GREEN, (0.05, 0.6, 0.25, 1), on_press=self.submit))
        root.add_widget(GradBtn('ОТМЕНИ', GRAY, (0.5, 0.5, 0.5, 1), on_press=lambda x: setattr(self.manager, 'current', 'ticket_list')))
        root.add_widget(Widget(size_hint_y=None, height=dp(20)))
        sv.add_widget(root)
        main = BoxLayout(orientation='vertical'); main.add_widget(sv); main.add_widget(back_btn(self)); self.add_widget(main)

    def on_enter(self):
        self.telk.text = ''
        self.err.text = ''
        self.update_price()

    def on_spinner_change(self, *a):
        self.update_price()

    def update_price(self):
        type_map = {'Стандартен': 'standard', 'Намален': 'reduced', 'Инвалиден': 'disabled'}
        prices = {
            'standard': {'1 седмица': 6.14, '1 месец': 8.18, '6 месеца': 15.34, '1 година': 25.56},
            'reduced': {'1 седмица': 3.07, '1 месец': 4.09, '6 месеца': 7.67, '1 година': 12.78},
            'disabled': {'1 седмица': 0, '1 месец': 0, '6 месеца': 0, '1 година': 0},
        }
        t = type_map.get(self.ts.text, 'standard')
        p = self.ps.text
        price = prices.get(t, {}).get(p, 0)
        self.price_lbl.text = f'Цена: {price} EUR'

    def submit(self, _):
        type_map = {'Стандартен': 'standard', 'Намален': 'reduced', 'Инвалиден': 'disabled'}
        ttype = type_map.get(self.ts.text)
        period = self.ps.text
        telk = self.telk.text.strip()
        if ttype == 'disabled' and not telk:
            self.err.text = 'ТЕЛК номер е задължителен за инвалиден билет'
            return
        r = api_post('/tickets/buy', {'ticket_type': ttype, 'period': period, 'telk_number': telk})
        if r.status_code == 201:
            self.manager.current = 'ticket_list'
        else:
            self.err.text = 'Грешка при покупка'


class TicketDetailScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self._back_to = 'ticket_list'; self.build_ui()

    def build_ui(self):
        sv = ScrollView()
        self.root = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(6), padding=[dp(15), dp(10)])
        self.root.bind(minimum_height=self.root.setter('height'))
        colored(self.root, WHITE)
        sv.add_widget(self.root)
        main = BoxLayout(orientation='vertical'); main.add_widget(sv); main.add_widget(back_btn(self)); self.add_widget(main)

    def load(self, tid):
        self.root.clear_widgets()
        data = api_get(f'/tickets/{tid}')
        if not data: self.root.add_widget(Label(text='Грешка', color=RED, size_hint_y=None, height=dp(40))); return
        self.root.add_widget(header_bar(f'Билет {data["receipt_number"]}', GREEN))
        status_colors = {'active': GREEN, 'expired': GRAY, 'cancelled': RED, 'pending': ORANGE}
        clr = status_colors.get(data['status'], GRAY)
        self.root.add_widget(Label(text=f'Статус: {data["status_label"]}', bold=True, color=clr, size_hint_y=None, height=dp(26)))
        for l, v in [('Тип', data.get('ticket_type_label','—')), ('Период', data.get('period','—')), ('Цена', f'{data.get("price",0)} EUR')]:
            self.root.add_widget(Label(text=f'{l}: {v}', size_hint_y=None, height=dp(22), color=(0.2, 0.2, 0.2, 1)))
        if data.get('valid_from'): self.root.add_widget(Label(text=f'Валиден от: {data["valid_from"][:10]}', size_hint_y=None, height=dp(22), color=(0.2, 0.2, 0.2, 1)))
        if data.get('valid_until'): self.root.add_widget(Label(text=f'Валиден до: {data["valid_until"][:10]}', size_hint_y=None, height=dp(22), color=(0.2, 0.2, 0.2, 1)))
        if data.get('telk_number'): self.root.add_widget(Label(text=f'ТЕЛК: {data["telk_number"]}', size_hint_y=None, height=dp(22), color=(0.2, 0.2, 0.2, 1)))
        if data['status'] in ('active', 'pending'):
            self.root.add_widget(Widget(size_hint_y=None, height=dp(8)))
            self.root.add_widget(GradBtn('АНУЛИРАЙ БИЛЕТА', RED, (0.6, 0.1, 0.1, 1), on_press=lambda x: self.cancel(tid)))

    def cancel(self, tid):
        r = api_post(f'/tickets/{tid}/cancel', {})
        if r.status_code == 200: self.load(tid)
