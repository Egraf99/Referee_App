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


class TextField(ScrollView):
    pass


class Dialog(MDDialog):
    but = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.but = [MDFlatButton(text="CANCEL")]

    def take_textfield(self):
        return TextField()

    def take_button(self):
        return [MDFlatButton(text="CANCEL", ), MDFlatButton(text="ADD"), ]


class MatchTable(MDDataTable):
    @property
    def take_games(self):
        db = ConnDB()
        games = db.take_games()
        db.close()

        list_of_games = []
        for game_info in games:
            league, date, time, stadium, team_home, team_guest, referee = game_info[:7]
            date = self._date_list_in_str(date.split())
            time = self._time_int_in_str(time)
            list_of_games.append([date, time, league, stadium, team_home, team_guest, referee])
        return list_of_games

    def _time_int_in_str(self, time: int) -> str:
        hour, minute = time // 100, time % 100
        hour = self._change_if_less_ten(hour)
        minute = self._change_if_less_ten(minute)

        return f'{hour}:{minute}'

    def _date_list_in_str(self, date: list) -> str:
        year, month, day = date
        day = self._change_if_less_ten(day)

        return f'{day}.{month}.{year}'

    @staticmethod
    def _change_if_less_ten(number):
        if int(number) < 10:
            number = f'0{number}'

        return number


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

        self.games_layout.add_widget(MatchTable())

    def callback(self, instance):
        if instance.icon == "cookie-plus-outline":
            self.pop_dialog_add_match()

    def pop_dialog_add_match(self):
        if not self.dialog:
            self.dialog = MDDialog(
                auto_dismiss=False,
                title="Add game",
                type="custom",
                content_cls=TextField(),
                buttons=[MDFlatButton(text="CANCEL", on_release=self.dismiss_dialog),
                         MDFlatButton(text="ADD"), ]
            )
        self.dialog.open()

    def dismiss_dialog(self, event):
        self.dialog.dismiss()


class MainApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.theme_style = "Dark"
        return GameScreen()


if __name__ == "__main__":
    main = MainApp()
    main.run()
