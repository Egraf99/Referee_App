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
    def open_drop_menu(self, field):
        print(field)


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
    games_layout = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.create_main_page()

    def create_main_page(self):
        self.games_layout.clear_widgets()

        self.games_layout.add_widget(MatchTable())

    def callback(self, instance):
        if instance.icon == "cookie-plus-outline":
            self.pop_dialog_add_match()
        elif instance.icon == "":
            pass
        elif instance.icon == "":
            pass

    def pop_dialog_add_match(self):
        self._make_dropmenu()

        self.dialog = MDDialog(
            auto_dismiss=False,
            title="Add game",
            type="custom",
            content_cls=AddMatch(),
            buttons=[MDFlatButton(text="CANCEL", on_release=self.dismiss_dialog),
                     MDFlatButton(text="ADD"), ]
        )

        self.dialog.open()

    def _make_dropmenu(self):
        menu_items = [
            {
                "text": f"Item 5",
                "viewclass": "OneLineListItem",
                "on_release": lambda x='5': self.menu_callback(x),
            }
        ]
        self.drop_menu = MDDropdownMenu(
            items=menu_items,
            width_mult=dp(56),
            max_height=dp(180),
        )

    def menu_callback(self, text_item):
        self.drop_menu.caller.text = text_item
        self.drop_menu.dismiss()

    def dismiss_dialog(self, event):
        self.dialog.dismiss()


class MainApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.theme_style = "Dark"

        self.game_screen = GameScreen()

        # функция on_focus() объекта TextInput срабатывает при фокусе на объект и разфокусе
        # данный check помогает вызывать необходимые функции только при фокусе на объект
        self.check_text_focus = False

        return self.game_screen

    def open_drop_menu(self, field):
        if not self.check_text_focus:
            self.game_screen.drop_menu.caller = field

            if self.game_screen.drop_menu.caller.hint_text == "City":
                print('city')
            elif self.game_screen.drop_menu.caller.hint_text == "Street":
                print('street')
            elif self.game_screen.drop_menu.caller.hint_text == "Date":
                print('date')

            self.check_text_focus = True
            self.game_screen.drop_menu.open()

        else:
            self.check_text_focus = False


if __name__ == "__main__":
    main = MainApp()
    main.run()
