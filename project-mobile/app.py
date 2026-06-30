import os
os.environ['KIVY_NO_ARGS'] = '1'

from kivy.config import Config
Config.set('graphics', 'resizable', True)
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '750')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window

from screens.auth import LoginScreen, RegisterScreen
from screens.user import HomeScreen
from screens.profile import ProfileScreen
from screens.inspector import (
    InspectorDashboard,
    VesselListScreen, VesselDetailScreen,
    ActListScreen, ActCreateScreen, ActDetailScreen,
    FineListScreen, FineCreateScreen,
    TraceSearchScreen, BatchDetailScreen,
    LocationListScreen, LocationDetailScreen,
)
from screens.user_tickets import TicketListScreen, TicketBuyScreen, TicketDetailScreen
from screens.user_logbook import LogbookListScreen, LogbookCreateScreen, LogbookDetailScreen


class IARAApp(App):
    def build(self):
        Window.size = (400, 750)
        Window.title = 'ИАРА'
        Window.clearcolor = (1, 1, 1, 1)

        sm = ScreenManager()
        for screen in [
            LoginScreen(name='login'),
            RegisterScreen(name='register'),
            HomeScreen(name='home'),
            ProfileScreen(name='profile'),
            InspectorDashboard(name='inspector_dashboard'),
            VesselListScreen(name='vessel_list'),
            VesselDetailScreen(name='vessel_detail'),
            ActListScreen(name='act_list'),
            ActCreateScreen(name='act_create'),
            ActDetailScreen(name='act_detail'),
            FineListScreen(name='fine_list'),
            FineCreateScreen(name='fine_create'),
            TraceSearchScreen(name='trace_search'),
            BatchDetailScreen(name='batch_detail'),
            LocationListScreen(name='location_list'),
            LocationDetailScreen(name='location_detail'),
            TicketListScreen(name='ticket_list'),
            TicketBuyScreen(name='ticket_buy'),
            TicketDetailScreen(name='ticket_detail'),
            LogbookListScreen(name='logbook_list'),
            LogbookCreateScreen(name='logbook_create'),
            LogbookDetailScreen(name='logbook_detail'),
        ]:
            sm.add_widget(screen)
        return sm


if __name__ == '__main__':
    IARAApp().run()
