from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.properties import ObjectProperty
from kivy.metrics import dp

from kivymd.uix.datatables import MDDataTable
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import OneLineAvatarIconListItem
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.menu import MDDropdownMenu
from kivymd.app import MDApp

from datebase import ConnDB


class AddMatch(ScrollView):
    def __init__(self, **kwargs):
        super(AddMatch, self).__init__(**kwargs)

        # функция on_focus() объекта TextInput срабатывает при фокусе на объект и разфокусе
        # данный check помогает вызывать необходимые функции только при фокусе на объект
        self.check_text_focus = False

        self.drop_menu = MDDropdownMenu(
            width_mult=dp(56),
            max_height=dp(180),
        )

    def take_stadiums(self):
        stadiums = ConnDB().take_stadium()
        return stadiums

    def add_item_in_text_input(self, text_item):
        self.drop_menu.caller.text = text_item
        self.drop_menu.dismiss()

    def open_drop_menu(self, field):
        drop_open = False
        if not self.check_text_focus:
            self.drop_menu.caller = field

            if self.drop_menu.caller.hint_text == "Stadium":
                stadiums = self.take_stadiums()

                self.drop_menu.items = [
                    {
                        "text": f"{x[0]}",
                        "viewclass": "OneLineListItem",
                        "on_release": lambda x=f"{x[0]}": self.add_item_in_text_input(x),
                    } for x in stadiums
                ]

                drop_open = True
            elif self.drop_menu.caller.hint_text == "Date and time":
                self.drop_menu.items = []
            elif self.drop_menu.caller.hint_text == "Date":
                print('date')

            if drop_open:
                self.drop_menu.open()

            self.check_text_focus = True

        else:
            self.check_text_focus = False


class MatchTable(MDDataTable):
    @property
    def take_games(self):
        games = ConnDB().take_games()

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
    games_layout = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.create_main_page()

    def create_main_page(self):
        self.games_layout.clear_widgets()

        self.games_layout.add_widget(MatchTable())

    def add_button_callback(self, instance):
        if instance.icon == "cookie-plus-outline":
            self.pop_dialog_add_match()
        elif instance.icon == "":
            pass
        elif instance.icon == "":
            pass

    def pop_dialog_add_match(self):
        self.dialog = MDDialog(
            auto_dismiss=False,
            title="Add game",
            type="custom",
            content_cls=AddMatch(),
            buttons=[MDFlatButton(text="CANCEL", on_release=self.dismiss_dialog),
                     MDFlatButton(text="ADD", on_release=self.print_release), ]
        )

        self.dialog.open()

    def print_release(self, event):
        print(self.dialog.content_cls.children)

    def dismiss_dialog(self, event):
        self.dialog.dismiss()


class MainApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.theme_style = "Dark"

        self.game_screen = GameScreen()

        return self.game_screen


if __name__ == "__main__":
    main = MainApp()
    main.run()
