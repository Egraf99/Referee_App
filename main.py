from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.properties import ObjectProperty
from kivy.metrics import dp

from kivymd.uix.datatables import MDDataTable
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import OneLineAvatarIconListItem
from kivymd.app import MDApp

from datebase import ConnDB

class TextField(BoxLayout):
    pass


class GameScreen(BoxLayout):
    label = ObjectProperty()
    main_box = ObjectProperty()
    games_layout = ObjectProperty()
    dialog = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_page()

    def main_page(self):
        self.games_layout.clear_widgets()

        my_games = self.take_games

        game_table = MDDataTable(
            use_pagination=False,
            check=True,
            column_data=[
                ('Дата', dp(30)),
                ('Время', dp(30)),
                ('Лига', dp(30)),
                ('Стадион', dp(30)),
                ('Хозяева', dp(30)),
                ('Гости', dp(30)),
                ('Фамилия', dp(30))
            ],
            row_data=my_games
        )

        self.games_layout.add_widget(game_table)

    @property
    def take_games(self):
        db = ConnDB()
        games = db.take_games()
        db.close()

        list_of_games = []
        for game_info in games:
            league, date, time, stadium, team_home, team_guest, referee = game_info[:7]
            date = date.split()
            date = f'{date[2]}.{date[1]}.{date[0]}'
            time = f'{time // 100}:{time % 100}'
            list_of_games.append([date, time, league, stadium, team_home, team_guest, referee])
        return list_of_games

    def callback(self, instance):
        if instance.icon == "language-python":
            self.pop_dialog_add_match()

    def pop_dialog_add_match(self):
        if not self.dialog:
            print('ok')
            self.dialog = MDDialog(
                title="something work",
                type="custom",
                content_cls=TextField(),
                buttons=[MDFlatButton(text="CANCEL"),
                         MDFlatButton(text="DISCARD"), ]
            )
        self.dialog.open()


class MainApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.theme_style = "Dark"
        return GameScreen()


if __name__ == "__main__":
    main = MainApp()
    main.run()
