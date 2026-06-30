from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.metrics import dp
from core import (api_get, api_post, BLUE, BLUE_LIGHT, WHITE, GREEN, RED, GRAY, ORANGE, BG,
                  colored, header_bar, back_btn, bottom_tabs, menu_card, GradBtn, _user, sess)

class InspectorDashboard(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation='vertical', spacing=dp(0))
        root.add_widget(header_bar('Инспекторски панел', BLUE))

        user_bar = BoxLayout(size_hint_y=None, height=dp(44), padding=[dp(15), dp(5)])
        colored(user_bar, BG)
        user_bar.add_widget(Label(text=_user.get('full_name', 'Инспектор'), font_size=dp(13), color=GRAY, size_hint_y=None, height=dp(30)))
        root.add_widget(user_bar)

        sv = ScrollView()
        grid = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(12), padding=[dp(15), dp(15)])
        grid.bind(minimum_height=grid.setter('height'))
        for txt, clr, sc in [('Кораби', BLUE, 'vessel_list'), ('Актове', ORANGE, 'act_list'),
                              ('Глоби', RED, 'fine_list'), ('Проследимост', GREEN, 'trace_search')]:
            grid.add_widget(menu_card(txt, clr, lambda x, s=sc: setattr(self.manager, 'current', s)))
        sv.add_widget(grid)
        root.add_widget(sv)
        root.add_widget(bottom_tabs('inspector_dashboard', self))
        self.add_widget(root)

class VesselListScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self._back_to = 'inspector_dashboard'; self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation='vertical')
        root.add_widget(header_bar('Кораби', BLUE))
        top = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8), padding=[dp(10), dp(5)])
        self.srch = TextInput(hint_text='Търси по номер или маркировка...', size_hint_x=0.7, size_hint_y=None, height=dp(40), multiline=False, font_size=dp(13))
        btn = Button(text='Търси', size_hint_x=0.3, size_hint_y=None, height=dp(40), background_color=BLUE, color=WHITE, font_size=dp(13), bold=True)
        btn.bind(on_press=self.search); top.add_widget(self.srch); top.add_widget(btn); root.add_widget(top)
        sv = ScrollView()
        self.list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4), padding=[dp(8), dp(4)])
        self.list.bind(minimum_height=self.list.setter('height'))
        sv.add_widget(self.list); root.add_widget(sv)
        root.add_widget(back_btn(self)); self.add_widget(root)

    def on_enter(self): self.search(None)

    def search(self, _):
        self.list.clear_widgets()
        vessels = api_get(f'/vessels?search={self.srch.text}')
        if not vessels: self.list.add_widget(Label(text='Няма резултати', color=GRAY, size_hint_y=None, height=dp(50))); return
        for v in vessels:
            box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(64), padding=[dp(10), dp(6)])
            colored(box, BG)
            info = BoxLayout(orientation='vertical')
            info.add_widget(Label(text=f'{v.get("marking","—")}  ({v.get("cfr_number","—")})', bold=True, color=BLUE, size_hint_y=None, height=dp(26), halign='left'))
            info.add_widget(Label(text=f'Статус: {v.get("status","—")}  |  {v.get("length","—")}м', color=GRAY, size_hint_y=None, height=dp(20), halign='left'))
            box.add_widget(info)
            arrow = Button(text='>', size_hint=(0.12, 1), background_color=(0,0,0,0), color=BLUE, bold=True, font_size=dp(18))
            vid = v['id']; arrow.bind(on_press=lambda x, i=vid: self.go_vessel(i))
            box.add_widget(arrow); self.list.add_widget(box)

    def go_vessel(self, vid):
        self.manager.get_screen('vessel_detail').load(vid); self.manager.current = 'vessel_detail'


class VesselDetailScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self._back_to = 'vessel_list'; self.build_ui()

    def build_ui(self):
        sv = ScrollView()
        self.root = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(6), padding=[dp(15), dp(10)])
        self.root.bind(minimum_height=self.root.setter('height'))
        colored(self.root, WHITE); sv.add_widget(self.root)
        main = BoxLayout(orientation='vertical'); main.add_widget(sv); main.add_widget(back_btn(self)); self.add_widget(main)

    def load(self, vid):
        self.vid = vid; self.root.clear_widgets()
        data = api_get(f'/vessels/{vid}')
        if not data: self.root.add_widget(Label(text='Грешка при зареждане', color=RED, size_hint_y=None, height=dp(40))); return
        self.root.add_widget(header_bar(f'Кораб: {data.get("marking","—")}', BLUE_LIGHT))
        for l, v in [('CFR номер', data.get('cfr_number','—')), ('Позивна', data.get('call_sign','—')), ('Капитан', data.get('captain_name','—')), ('Статус', data.get('status','—')), ('Размери', f'{data.get("length","—")}м x {data.get("width","—")}м'), ('Тонаж', f'{data.get("gross_tonnage","—")} т'), ('Двигател', f'{data.get("engine_power","—")} kW'), ('Гориво', data.get('fuel_type','—')), ('Собственик', (data.get('owner') or {}).get('full_name','—'))]:
            self.root.add_widget(Label(text=f'{l}: {v}', size_hint_y=None, height=dp(22), color=(0.2, 0.2, 0.2, 1)))
        self.root.add_widget(Label(text='Разрешителни:', bold=True, color=BLUE, size_hint_y=None, height=dp(28)))
        for p in data.get('permits', []): self.root.add_widget(Label(text=f'{p["permit_number"]} — {p["status"]} (до {p.get("valid_until","")})', size_hint_y=None, height=dp(22), color=GRAY))
        if not data.get('permits'): self.root.add_widget(Label(text='Няма разрешителни', color=GRAY, size_hint_y=None, height=dp(22)))
        self.root.add_widget(Label(text='Действия:', bold=True, color=GREEN, size_hint_y=None, height=dp(28)))
        self.root.add_widget(menu_card('Нов акт', ORANGE, lambda x: self.create_act()))
        self.root.add_widget(menu_card('Нова глоба', RED, lambda x: self.create_fine()))

    def create_act(self):
        self.manager.get_screen('act_create').select_vessel(self.vid); self.manager.current = 'act_create'

    def create_fine(self):
        self.manager.get_screen('fine_create').select_vessel(self.vid); self.manager.current = 'fine_create'

class ActListScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self._back_to = 'inspector_dashboard'; self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation='vertical')
        root.add_widget(header_bar('Актове', ORANGE))
        top = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8), padding=[dp(10), dp(5)])
        self.spin = Spinner(text='Всички', values=('Всички', 'confirmed', 'cancelled', 'resolved'), size_hint_x=0.7, size_hint_y=None, height=dp(40))
        self.spin.bind(text=lambda s, _: self.load()); top.add_widget(self.spin)
        add = Button(text='+ Нов', size_hint_x=0.3, size_hint_y=None, height=dp(40), background_color=GREEN, color=WHITE, bold=True, font_size=dp(13))
        add.bind(on_press=lambda x: setattr(self.manager, 'current', 'act_create')); top.add_widget(add); root.add_widget(top)
        sv = ScrollView()
        self.list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4), padding=[dp(8), dp(4)])
        self.list.bind(minimum_height=self.list.setter('height')); sv.add_widget(self.list); root.add_widget(sv)
        root.add_widget(back_btn(self)); self.add_widget(root)

    def on_enter(self): self.load()

    def load(self):
        self.list.clear_widgets()
        s = f'?status={self.spin.text}' if self.spin.text != 'Всички' else ''
        acts = api_get(f'/acts{s}')
        if not acts: self.list.add_widget(Label(text='Няма актове', color=GRAY, size_hint_y=None, height=dp(50))); return
        for a in acts:
            st = a['status']; clr = GREEN if st == 'confirmed' else (ORANGE if st == 'resolved' else RED)
            box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(64), padding=[dp(10), dp(6)])
            colored(box, BG)
            info = BoxLayout(orientation='vertical')
            info.add_widget(Label(text=f'{a["act_number"][:20]}  [{st}]', bold=True, color=clr, size_hint_y=None, height=dp(26)))
            info.add_widget(Label(text=f'{a.get("vessel_marking","—")}  |  {a.get("location","—")}', color=GRAY, size_hint_y=None, height=dp(20)))
            box.add_widget(info)
            arrow = Button(text='>', size_hint=(0.12, 1), background_color=(0,0,0,0), color=clr, bold=True, font_size=dp(18))
            aid = a['id']; arrow.bind(on_press=lambda x, i=aid: self.open_act(i)); box.add_widget(arrow); self.list.add_widget(box)

    def open_act(self, aid):
        self.manager.get_screen('act_detail').load(aid); self.manager.current = 'act_detail'


class ActCreateScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self.preset_vessel = None; self.vessels = []; self.permits = []; self._back_to = 'act_list'; self.build_ui()

    def build_ui(self):
        sv = ScrollView()
        root = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8), padding=[dp(15), dp(10)])
        root.bind(minimum_height=root.setter('height'))
        colored(root, WHITE); root.add_widget(header_bar('Нов акт', ORANGE))
        self.vs = Spinner(text='Избери кораб', values=['Зареждане...'], size_hint_y=None, height=dp(44))
        self.vs.bind(text=self.on_vessel_change)
        root.add_widget(self.vs)
        self.ps = Spinner(text='— Без разрешително —', values=['— Без разрешително —'], size_hint_y=None, height=dp(44))
        root.add_widget(self.ps)
        self.loc = TextInput(hint_text='Локация на проверката', size_hint_y=None, height=dp(42), multiline=False, font_size=dp(14))
        root.add_widget(self.loc)
        self.find = TextInput(hint_text='Констатации от проверката', size_hint_y=None, height=dp(80), multiline=True, font_size=dp(13))
        root.add_widget(self.find)
        self.viol = TextInput(hint_text='Установени нарушения', size_hint_y=None, height=dp(80), multiline=True, font_size=dp(13))
        root.add_widget(self.viol)
        self.amt = TextInput(hint_text='Сума на глоба (0 = без глоба)', size_hint_y=None, height=dp(42), multiline=False, font_size=dp(13))
        root.add_widget(self.amt)
        root.add_widget(GradBtn('СЪЗДАЙ АКТ', ORANGE, (0.8, 0.4, 0.05, 1), on_press=self.submit))
        root.add_widget(GradBtn('ОТМЕНИ', GRAY, (0.5, 0.5, 0.5, 1), on_press=lambda x: setattr(self.manager, 'current', 'act_list')))
        sv.add_widget(root)
        main = BoxLayout(orientation='vertical'); main.add_widget(sv); main.add_widget(back_btn(self)); self.add_widget(main)

    def on_enter(self):
        vs = api_get('/vessels'); self.vessels = vs or []; self.vs.values = [f'{v["marking"]} ({v["cfr_number"]})' for v in self.vessels] or ['Няма кораби']
        if self.preset_vessel:
            for i, v in enumerate(self.vessels):
                if v['id'] == self.preset_vessel:
                    self.vs.text = self.vs.values[i]; break

    def select_vessel(self, vid): self.preset_vessel = vid

    def on_vessel_change(self, spinner, text):
        if text == 'Избери кораб' or text not in self.vs.values:
            self.ps.values = ['— Без разрешително —']; self.ps.text = '— Без разрешително —'; self.permits = []; return
        idx = self.vs.values.index(text)
        vid = self.vessels[idx]['id']
        self.permits = api_get(f'/vessels/{vid}/permits') or []
        self.ps.values = ['— Без разрешително —'] + [f'{p["permit_number"]} — важи до {p["valid_until"][:10]}' for p in self.permits]
        self.ps.text = '— Без разрешително —'

    def submit(self, _):
        if self.vs.text == 'Избери кораб': return
        idx = self.vs.values.index(self.vs.text) if self.vs.text in self.vs.values else -1
        if idx < 0: return
        vid = self.vessels[idx]['id']; amt = float(self.amt.text) if self.amt.text.strip() else 0
        permit_id = None
        if self.ps.text != '— Без разрешително —' and self.permits:
            pidx = self.ps.values.index(self.ps.text) - 1
            if 0 <= pidx < len(self.permits):
                permit_id = self.permits[pidx]['id']
        r = api_post('/acts', {'vessel_id': vid, 'permit_id': permit_id, 'location': self.loc.text, 'findings': self.find.text, 'violations': self.viol.text, 'fine_amount': amt if amt > 0 else None, 'violation_description': self.viol.text})
        if r.status_code == 201: self.manager.current = 'act_list'


class ActDetailScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self._back_to = 'act_list'; self.build_ui()

    def build_ui(self):
        sv = ScrollView()
        self.root = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(6), padding=[dp(15), dp(10)])
        self.root.bind(minimum_height=self.root.setter('height'))
        colored(self.root, WHITE); sv.add_widget(self.root)
        main = BoxLayout(orientation='vertical'); main.add_widget(sv); main.add_widget(back_btn(self)); self.add_widget(main)

    def load(self, aid):
        self.root.clear_widgets()
        data = api_get(f'/acts/{aid}')
        if not data: self.root.add_widget(Label(text='Грешка', color=RED, size_hint_y=None, height=dp(40))); return
        self.root.add_widget(header_bar(f'Акт {data.get("act_number","")}', ORANGE))
        vessel = data.get('vessel', {})
        if vessel: self.root.add_widget(Label(text=f'Кораб: {vessel.get("marking","")} ({vessel.get("cfr_number","")})', size_hint_y=None, height=dp(24), color=BLUE, bold=True))
        rp = data.get('related_permit')
        if rp: self.root.add_widget(Label(text=f'Разрешително: {rp.get("permit_number","")} ({rp.get("status","")})', size_hint_y=None, height=dp(22), color=(0.2, 0.2, 0.2, 1)))
        for l, v in [('Дата', data.get('inspection_date','—')), ('Статус', data.get('status','—')), ('Локация', data.get('location','—')), ('Констатации', data.get('findings','—')), ('Нарушения', data.get('violations','—'))]:
            self.root.add_widget(Label(text=f'{l}: {v}', size_hint_y=None, height=dp(22), color=(0.2, 0.2, 0.2, 1)))
        fines = data.get('fines', [])
        if fines:
            self.root.add_widget(Label(text='Глоби по акта:', bold=True, color=RED, size_hint_y=None, height=dp(28)))
            for f in fines: self.root.add_widget(Label(text=f'{f["fine_number"]} — {f["amount"]} лв ({f["status"]})', size_hint_y=None, height=dp(22), color=GRAY))

class FineListScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self._back_to = 'inspector_dashboard'; self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation='vertical')
        root.add_widget(header_bar('Глоби', RED))
        top = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8), padding=[dp(10), dp(5)])
        self.spin = Spinner(text='Всички', values=('Всички', 'approved', 'paid', 'rejected'), size_hint_x=0.7, size_hint_y=None, height=dp(40))
        self.spin.bind(text=lambda s, _: self.load()); top.add_widget(self.spin)
        add = Button(text='+ Нова', size_hint_x=0.3, size_hint_y=None, height=dp(40), background_color=RED, color=WHITE, bold=True, font_size=dp(13))
        add.bind(on_press=lambda x: setattr(self.manager, 'current', 'fine_create')); top.add_widget(add); root.add_widget(top)
        sv = ScrollView()
        self.list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4), padding=[dp(8), dp(4)])
        self.list.bind(minimum_height=self.list.setter('height')); sv.add_widget(self.list); root.add_widget(sv)
        root.add_widget(back_btn(self)); self.add_widget(root)

    def on_enter(self): self.load()

    def load(self):
        self.list.clear_widgets()
        s = f'?status={self.spin.text}' if self.spin.text != 'Всички' else ''
        fines = api_get(f'/fines{s}')
        if not fines: self.list.add_widget(Label(text='Няма глоби', color=GRAY, size_hint_y=None, height=dp(50))); return
        for f in fines:
            st = f['status']; clr = RED if st == 'approved' else (GREEN if st == 'paid' else GRAY)
            box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(64), padding=[dp(10), dp(6)])
            colored(box, BG)
            info = BoxLayout(orientation='vertical')
            info.add_widget(Label(text=f'{f["fine_number"][:18]}  [{st}]  {f["amount"]} лв', bold=True, color=clr, size_hint_y=None, height=dp(26)))
            info.add_widget(Label(text=f'{f.get("vessel_marking","—")}  |  {f.get("violation_description","")[:30]}', color=GRAY, size_hint_y=None, height=dp(20)))
            box.add_widget(info); self.list.add_widget(box)


class FineCreateScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self.preset_vessel = None; self.vessels = []; self.permits = []; self._back_to = 'fine_list'; self.build_ui()

    def build_ui(self):
        sv = ScrollView()
        root = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8), padding=[dp(15), dp(10)])
        root.bind(minimum_height=root.setter('height'))
        colored(root, WHITE); root.add_widget(header_bar('Нова глоба', RED))
        self.vs = Spinner(text='Избери кораб', values=['Зареждане...'], size_hint_y=None, height=dp(44))
        self.vs.bind(text=self.on_vessel_change)
        root.add_widget(self.vs)
        self.ps = Spinner(text='— Без разрешително —', values=['— Без разрешително —'], size_hint_y=None, height=dp(44))
        root.add_widget(self.ps)
        self.loc = TextInput(hint_text='Локация', size_hint_y=None, height=dp(42), multiline=False, font_size=dp(14))
        root.add_widget(self.loc)
        self.desc = TextInput(hint_text='Описание на нарушението', size_hint_y=None, height=dp(80), multiline=True, font_size=dp(13))
        root.add_widget(self.desc)
        self.basis = TextInput(hint_text='Правно основание', size_hint_y=None, height=dp(42), multiline=False, font_size=dp(13))
        root.add_widget(self.basis)
        self.amt = TextInput(hint_text='Сума (лв)', size_hint_y=None, height=dp(42), multiline=False, font_size=dp(13))
        root.add_widget(self.amt)
        root.add_widget(GradBtn('СЪЗДАЙ ГЛОБА', RED, (0.6, 0.1, 0.1, 1), on_press=self.submit))
        root.add_widget(GradBtn('ОТМЕНИ', GRAY, (0.5, 0.5, 0.5, 1), on_press=lambda x: setattr(self.manager, 'current', 'fine_list')))
        sv.add_widget(root)
        main = BoxLayout(orientation='vertical'); main.add_widget(sv); main.add_widget(back_btn(self)); self.add_widget(main)

    def on_enter(self):
        vs = api_get('/vessels'); self.vessels = vs or []; self.vs.values = [f'{v["marking"]} ({v["cfr_number"]})' for v in self.vessels] or ['Няма кораби']
        if self.preset_vessel:
            for i, v in enumerate(self.vessels):
                if v['id'] == self.preset_vessel: self.vs.text = self.vs.values[i]; break

    def select_vessel(self, vid): self.preset_vessel = vid

    def on_vessel_change(self, spinner, text):
        if text == 'Избери кораб' or text not in self.vs.values:
            self.ps.values = ['— Без разрешително —']; self.ps.text = '— Без разрешително —'; self.permits = []; return
        idx = self.vs.values.index(text)
        vid = self.vessels[idx]['id']
        self.permits = api_get(f'/vessels/{vid}/permits') or []
        self.ps.values = ['— Без разрешително —'] + [f'{p["permit_number"]} — важи до {p["valid_until"][:10]}' for p in self.permits]
        self.ps.text = '— Без разрешително —'

    def submit(self, _):
        if self.vs.text == 'Избери кораб' or not self.amt.text.strip(): return
        idx = self.vs.values.index(self.vs.text) if self.vs.text in self.vs.values else -1
        if idx < 0: return
        permit_id = None
        if self.ps.text != '— Без разрешително —' and self.permits:
            pidx = self.ps.values.index(self.ps.text) - 1
            if 0 <= pidx < len(self.permits):
                permit_id = self.permits[pidx]['id']
        r = api_post('/fines', {'vessel_id': self.vessels[idx]['id'], 'permit_id': permit_id, 'location': self.loc.text, 'amount': float(self.amt.text), 'violation_description': self.desc.text, 'legal_basis': self.basis.text})
        if r.status_code == 201: self.manager.current = 'fine_list'

class TraceSearchScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self._back_to = 'inspector_dashboard'; self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation='vertical')
        root.add_widget(header_bar('Проследимост', GREEN))
        top = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8), padding=[dp(10), dp(5)])
        self.srch = TextInput(hint_text='Номер на партида или вид риба...', size_hint_x=0.7, size_hint_y=None, height=dp(40), multiline=False, font_size=dp(13))
        btn = Button(text='Търси', size_hint_x=0.3, size_hint_y=None, height=dp(40), background_color=GREEN, color=WHITE, bold=True, font_size=dp(13))
        btn.bind(on_press=self.search); top.add_widget(self.srch); top.add_widget(btn); root.add_widget(top)
        sv = ScrollView()
        self.list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4), padding=[dp(8), dp(4)])
        self.list.bind(minimum_height=self.list.setter('height')); sv.add_widget(self.list); root.add_widget(sv)
        root.add_widget(back_btn(self)); self.add_widget(root)

    def search(self, _):
        self.list.clear_widgets(); q = self.srch.text.strip()
        if not q: return
        batches = api_get(f'/trace/batches/search?q={q}')
        if not batches: self.list.add_widget(Label(text='Няма резултати', color=GRAY, size_hint_y=None, height=dp(50))); return
        for b in batches:
            box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), padding=[dp(10), dp(6)])
            colored(box, BG)
            info = BoxLayout(orientation='vertical')
            info.add_widget(Label(text=f'{b["batch_number"]}  |  {b["species"]}  |  {b["quantity_kg"]} кг', bold=True, color=BLUE, size_hint_y=None, height=dp(26)))
            if b.get('landing_date'): info.add_widget(Label(text=f'Разтоварване: {b["landing_date"]}', color=GRAY, size_hint_y=None, height=dp(20)))
            box.add_widget(info)
            arrow = Button(text='>', size_hint=(0.12, 1), background_color=(0,0,0,0), color=GREEN, bold=True, font_size=dp(18))
            bid = b['id']; arrow.bind(on_press=lambda x, i=bid: self.open_batch(i)); box.add_widget(arrow); self.list.add_widget(box)

    def open_batch(self, bid):
        self.manager.get_screen('batch_detail').load(bid); self.manager.current = 'batch_detail'


class BatchDetailScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw); self._back_to = 'trace_search'; self.build_ui()

    def build_ui(self):
        sv = ScrollView()
        self.root = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(6), padding=[dp(15), dp(10)])
        self.root.bind(minimum_height=self.root.setter('height'))
        colored(self.root, WHITE); sv.add_widget(self.root)
        main = BoxLayout(orientation='vertical'); main.add_widget(sv); main.add_widget(back_btn(self)); self.add_widget(main)

    def load(self, bid):
        self.root.clear_widgets()
        data = api_get(f'/trace/batches/{bid}')
        if not data: self.root.add_widget(Label(text='Грешка', color=RED, size_hint_y=None, height=dp(40))); return
        self.root.add_widget(header_bar(f'Партида {data["batch_number"]}', GREEN))
        self.root.add_widget(Label(text=f'Вид: {data["species"]}  |  Количество: {data["quantity_kg"]} кг', font_size=dp(15), bold=True, color=BLUE, size_hint_y=None, height=dp(30)))
        landing = data.get('landing', {})
        if landing: self.root.add_widget(Label(text=f'Разтоварване: {landing.get("landing_date","")} — {landing.get("location","")}', size_hint_y=None, height=dp(24), color=(0.2, 0.2, 0.2, 1)))
        if data.get('notes'): self.root.add_widget(Label(text=f'Бележки: {data["notes"]}', size_hint_y=None, height=dp(24), color=GRAY))
        self.root.add_widget(Label(text='Движения:', bold=True, color=GREEN, size_hint_y=None, height=dp(28)))
        for m in data.get('movements', []):
            self.root.add_widget(Label(text=f'{m.get("movement_type","")}  {m.get("from_location","?")} -> {m.get("to_location","?")}', size_hint_y=None, height=dp(22), color=(0.2, 0.2, 0.2, 1)))
            if m.get('arrival_date'): self.root.add_widget(Label(text=f'   Пристигане: {m["arrival_date"]}', size_hint_y=None, height=dp(18), color=GRAY))
        if not data.get('movements'): self.root.add_widget(Label(text='Няма движения', color=GRAY, size_hint_y=None, height=dp(22)))
