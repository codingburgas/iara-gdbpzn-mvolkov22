from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from core import api_get, api_post, BLUE, BLUE_LIGHT, WHITE, GREEN, RED, GRAY, ORANGE, BG, colored, header_bar, back_btn, bottom_tabs, GradBtn


class LogbookListScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self._back_to = 'home'; self.build_ui()

    def build_ui(self):
        sv = ScrollView()
        self.list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4), padding=[dp(8), dp(4)])
        self.list.bind(minimum_height=self.list.setter('height'))
        sv.add_widget(self.list)
        top = BoxLayout(orientation='vertical')
        top.add_widget(header_bar('Моят улов', ORANGE))
        top.add_widget(GradBtn('+ НОВ УЛОВ', ORANGE, (0.8, 0.4, 0.05, 1), on_press=lambda x: setattr(self.manager, 'current', 'logbook_create')))
        top.add_widget(sv)
        main = BoxLayout(orientation='vertical'); main.add_widget(top); main.add_widget(back_btn(self)); main.add_widget(bottom_tabs('home', self))
        self.add_widget(main)

    def on_enter(self):
        self.list.clear_widgets()
        entries = api_get('/logbook')
        if not entries: self.list.add_widget(Label(text='Нямате регистриран улов', color=GRAY, size_hint_y=None, height=dp(50))); return
        status_labels = {'draft': 'Чернова', 'submitted': 'Изпратен', 'confirmed': 'Потвърден'}
        status_colors = {'draft': GRAY, 'submitted': ORANGE, 'confirmed': GREEN}
        for e in entries:
            clr = status_colors.get(e['status'], GRAY)
            box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(70), padding=[dp(10), dp(6)])
            colored(box, BG)
            info = BoxLayout(orientation='vertical')
            vessel = e.get('vessel') or {}
            total_kg = sum(c.get('quantity_kg', 0) for c in e.get('catches', []))
            info.add_widget(Label(text=f'{vessel.get("marking","Без кораб")}  [{status_labels.get(e["status"], e["status"])}]', bold=True, color=clr, size_hint_y=None, height=dp(26)))
            info.add_widget(Label(text=f'{e.get("start_datetime","")[:10]}  |  {total_kg} кг', color=GRAY, size_hint_y=None, height=dp(20)))
            box.add_widget(info)
            arrow = Button(text='>', size_hint=(0.12, 1), background_color=(0,0,0,0), color=clr, bold=True, font_size=dp(18))
            eid = e['id']; arrow.bind(on_press=lambda x, i=eid: self.open_entry(i))
            box.add_widget(arrow); self.list.add_widget(box)

    def open_entry(self, eid):
        self.manager.get_screen('logbook_detail').load(eid); self.manager.current = 'logbook_detail'


class LogbookCreateScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self.vessels = []; self._back_to = 'logbook_list'; self.build_ui()

    def build_ui(self):
        main = BoxLayout(orientation='vertical')
        main.add_widget(header_bar('Регистрирай улов', ORANGE))
        sv = ScrollView()
        root = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8), padding=[dp(15), dp(8)])
        root.bind(minimum_height=root.setter('height'))
        colored(root, WHITE)
        self.vs = Spinner(text='Избери кораб', values=['Зареждане...'], size_hint_y=None, height=dp(44))
        root.add_widget(self.vs)
        self.dt = TextInput(hint_text='Начало (YYYY-MM-DD HH:MM)', size_hint_y=None, height=dp(40), multiline=False, font_size=dp(13))
        root.add_widget(self.dt)
        self.loc = TextInput(hint_text='Локация на риболов', size_hint_y=None, height=dp(40), multiline=False, font_size=dp(13))
        root.add_widget(self.loc)
        self.gear = TextInput(hint_text='Използвани уреди', size_hint_y=None, height=dp(40), multiline=False, font_size=dp(13))
        root.add_widget(self.gear)
        root.add_widget(Label(text='Улов (вид, кг):', bold=True, color=BLUE, size_hint_y=None, height=dp(22)))
        self.catch_rows = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4))
        self.catch_rows.bind(minimum_height=self.catch_rows.setter('height'))
        root.add_widget(self.catch_rows)
        root.add_widget(GradBtn('+ ДОБАВИ ВИД', BLUE_LIGHT, (0.2, 0.5, 0.8, 1), on_press=self.add_catch_row))
        self.err = Label(text='', color=RED, size_hint_y=None, height=dp(18), font_size=dp(12))
        root.add_widget(self.err)
        root.add_widget(GradBtn('ЗАПИШИ УЛОВ', ORANGE, (0.8, 0.4, 0.05, 1), on_press=self.submit))
        root.add_widget(GradBtn('ОТМЕНИ', GRAY, (0.5, 0.5, 0.5, 1), on_press=lambda x: setattr(self.manager, 'current', 'logbook_list')))
        sv.add_widget(root)
        main.add_widget(sv)
        main.add_widget(back_btn(self))
        self.add_widget(main)

    def on_enter(self):
        vs = api_get('/vessels'); self.vessels = vs or []
        self.vs.values = ['Без кораб'] + [f'{v["marking"]} ({v["cfr_number"]})' for v in self.vessels]
        self.vs.text = 'Без кораб'
        self.catch_rows.clear_widgets()
        self.add_catch_row()

    def add_catch_row(self, _=None):
        entry = BoxLayout(orientation='vertical', size_hint_y=None)
        row1 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(34), spacing=dp(4))
        sp = TextInput(hint_text='Вид', size_hint_x=0.35, size_hint_y=None, height=dp(34), multiline=False, font_size=dp(12))
        kg = TextInput(hint_text='Кг', size_hint_x=0.2, size_hint_y=None, height=dp(34), multiline=False, font_size=dp(12))
        pcs = TextInput(hint_text='Бр', size_hint_x=0.18, size_hint_y=None, height=dp(34), multiline=False, font_size=dp(12))
        rm = Button(text='X', size_hint_x=0.27, size_hint_y=None, height=dp(34), background_color=RED, color=WHITE, bold=True, font_size=dp(12))
        rm.bind(on_press=lambda x: (self.catch_rows.remove_widget(entry), None))
        row1.add_widget(sp); row1.add_widget(kg); row1.add_widget(pcs); row1.add_widget(rm)
        entry.add_widget(row1)

        row2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(28), spacing=dp(4))
        nt = TextInput(hint_text='Бележка', size_hint_x=1, size_hint_y=None, height=dp(28), multiline=False, font_size=dp(11))
        row2.add_widget(nt)
        entry.add_widget(row2)

        entry._sp = sp
        entry._kg = kg
        entry._pcs = pcs
        entry._nt = nt
        self.catch_rows.add_widget(entry)

    def submit(self, _):
        vid = None
        if self.vs.text != 'Без кораб':
            idx = self.vs.values.index(self.vs.text) if self.vs.text in self.vs.values else -1
            vessel_idx = idx - 1
            if idx < 0 or vessel_idx < 0 or vessel_idx >= len(self.vessels):
                self.err.text = 'Изберете кораб'
                return
            vid = self.vessels[vessel_idx]['id']
        catches = []
        for entry in reversed(self.catch_rows.children):
            sp = entry._sp.text.strip()
            kg = entry._kg.text.strip()
            pcs = entry._pcs.text.strip()
            nt = entry._nt.text.strip()
            if sp and kg:
                try:
                    c = {'species': sp, 'quantity_kg': float(kg)}
                    if pcs:
                        c['quantity_pcs'] = int(pcs)
                    if nt:
                        c['notes'] = nt
                    catches.append(c)
                except ValueError:
                    self.err.text = f'Невалидно количество: {kg}'
                    return
        data = {
            'vessel_id': vid,
            'start_datetime': self.dt.text.strip() if self.dt.text.strip() else None,
            'start_location': self.loc.text.strip(),
            'gear_used': self.gear.text.strip(),
            'catches': catches,
        }
        r = api_post('/logbook', data)
        if r.status_code == 201:
            self.manager.current = 'logbook_list'
        else:
            self.err.text = 'Грешка при запис'


class LogbookDetailScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self._back_to = 'logbook_list'; self.build_ui()

    def build_ui(self):
        sv = ScrollView()
        self.root = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(6), padding=[dp(15), dp(10)])
        self.root.bind(minimum_height=self.root.setter('height'))
        colored(self.root, WHITE)
        sv.add_widget(self.root)
        main = BoxLayout(orientation='vertical'); main.add_widget(sv); main.add_widget(back_btn(self)); self.add_widget(main)

    def load(self, eid):
        self.root.clear_widgets()
        data = api_get(f'/logbook/{eid}')
        if not data: self.root.add_widget(Label(text='Грешка', color=RED, size_hint_y=None, height=dp(40))); return
        vessel = data.get('vessel') or {}
        self.root.add_widget(header_bar(f'Улов: {vessel.get("marking","Без кораб")}', ORANGE))
        status_labels = {'draft': 'Чернова', 'submitted': 'Изпратен', 'confirmed': 'Потвърден'}
        status_colors = {'draft': GRAY, 'submitted': ORANGE, 'confirmed': GREEN}
        clr = status_colors.get(data['status'], GRAY)
        self.root.add_widget(Label(text=f'Статус: {status_labels.get(data["status"], data["status"])}', bold=True, color=clr, size_hint_y=None, height=dp(24)))
        for l, v in [('Начало', data.get('start_datetime','—')[:16]), ('Край', data.get('end_datetime','—')[:16] if data.get('end_datetime') else '—'), ('Локация', data.get('start_location','—')), ('Уреди', data.get('gear_used','—'))]:
            self.root.add_widget(Label(text=f'{l}: {v}', size_hint_y=None, height=dp(22), color=(0.2, 0.2, 0.2, 1)))
        if data.get('notes'): self.root.add_widget(Label(text=f'Бележки: {data["notes"]}', size_hint_y=None, height=dp(22), color=GRAY))
        catches = data.get('catches', [])
        if catches:
            self.root.add_widget(Label(text='Улов:', bold=True, color=BLUE, size_hint_y=None, height=dp(26)))
            total = 0
            for c in catches:
                parts = [f'{c["species"]}: {c["quantity_kg"]} кг']
                if c.get('quantity_pcs'):
                    parts.append(f'{c["quantity_pcs"]} бр')
                if c.get('notes'):
                    parts.append(f'({c["notes"]})')
                self.root.add_widget(Label(text='  ' + '  '.join(parts), size_hint_y=None, height=dp(20), color=(0.2, 0.2, 0.2, 1)))
                total += c['quantity_kg']
            self.root.add_widget(Label(text=f'Общо: {total} кг', bold=True, color=BLUE, size_hint_y=None, height=dp(24)))
