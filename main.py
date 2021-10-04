from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.stacklayout import StackLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.metrics import dp

from kivymd.uix.datatables import MDDataTable
from kivymd.app import MDApp

from datebase import ConnDB


class GameScreen(BoxLayout):
    label = ObjectProperty()
    main_box = ObjectProperty()
    games_layout = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_page()

    def check_menu_button_click(self, button):
        for bn in self.buttons:
            if button is bn:
                bn.disabled = True
            else:
                bn.disabled = False

    def main_page(self):
        # self.check_menu_button_click(button)

        self.games_layout.clear_widgets()

        # self.top_bn.text = button.text

        my_games = self.take_games()

        game_table = MDDataTable(
            use_pagination=True,
            check=True,
            column_data=[
                ('Дата', dp(30)),
                ('Лига', dp(30)),
                ('Стадион', dp(30)),
                ('Хозяева', dp(30)),
                ('Гости', dp(30)),
                ('Фамилия', dp(30))
            ],
            row_data=my_games
            )

        self.games_layout.add_widget(game_table)

    def int_to_date(self):
        pass

    def from_db_to_list(self) -> list:
        pass

    def change_label(self, button, text):
        self.check_menu_button_click(button)

        self.label.text = text

    def take_games(self):
        db = ConnDB()
        games = db.take_games()
        db.close()

        list_of_games = []
        for game_info in games:
            league, date, stadium, team_home, team_guest, referee = game_info[:6]
            list_of_games.append([date, league, stadium, team_home, team_guest, referee])
        return list_of_games


class MainApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.theme_style = "Dark"
        return GameScreen()


if __name__ == "__main__":
    main = MainApp()
    main.run()
