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


class DropMenu(MDDropdownMenu):
    def __init__(self, **kwargs):
        super(DropMenu, self).__init__(**kwargs)
        self.width_mult = dp(56)

    def take_data(self, mode):
        if mode:
            db_method = f"take_{mode}()"
            try:
                data = eval("DB." + db_method)
                return data
            except AttributeError:
                print(f"\n!!!!!!!!!!!!!!!\n ConnDB has no {db_method}\n!!!!!!!!!!!!!!!\n")
        return []

    def set_items(self, text_list, list_items: list):
        if list_items:
            self.items = [{"text": f"{x}",
                           "viewclass": "OneLineListItem",
                           "on_release": lambda x=f"{x}": text_list.add_item_in_text_input(x),
                           } for x in list_items]
        else:
            self.items = [{"text": "No found",
                           "viewclass": "OneLineListItem",
                           "on_release": lambda: text_list.drop_menu.dismiss()}]


class TextField(MDTextField):
    def __init__(self, name, scroll, **kwargs):
        super(TextField, self).__init__(**kwargs)

        # функция on_focus() объекта TextInput срабатывает при фокусе на объект и разфокусе
        # данный check помогает вызывать необходимые функции только при фокусе на объект
        self.check_text_focus = False

        self.do_open_menu = None

        self.hint_text = name
        self.parent_scroll = scroll

    def on_focus_(self):
        if not self.check_text_focus:
            self.on_focus__()
        else:
            self.check_text_focus = False

    def on_focus__(self):
        pass

    def on_cursor_(self):
        pass

    def enter_press(self):
        self.add_item_in_text_input("enter")


class NoDateTF(TextField):
    def __init__(self, name, scroll, **kwargs):
        super(NoDateTF, self).__init__(name, scroll, **kwargs)

        self.do_open_menu = True
        self.drop_menu = DropMenu()

    def add_item_in_text_input(self, text_item):
        self.drop_menu.caller.text = text_item
        self.drop_menu.dismiss()

    def on_focus__(self):
        """Открытие всплывающего меню"""
        self.text = ""

        # устанавливаем для всплывающего меню поле ввода, откуда его вызывали
        self.drop_menu.caller = self

        # берем текст вызывающего поля ввода для определения строк в всплывающем меню
        type_data = self._take_type_data(self.drop_menu.caller.hint_text)
        items = self.drop_menu.take_data(type_data)
        self.drop_menu.set_items(self, [i[0] for i in items])

        if items:
            self.drop_menu_open()

        self.check_text_focus = True

    def on_cursor_(self):
        """Обновление всплывающего меню"""
        if self.do_open_menu:
            if self.check_text_focus:
                self.drop_menu.dismiss()

                matching_items = []

                # берем текст вызывающего поля ввода для определения строк в всплывающем меню
                type_data = self._take_type_data(self.drop_menu.caller.hint_text)
                items = self.drop_menu.take_data(type_data)

                for item in items:
                    if self.text.lower() in item[0].lower():
                        matching_items.append(item)

                self.drop_menu.set_items(self, [i[0] for i in matching_items])

            self.drop_menu.open()

    def drop_menu_open(self):
        if self.do_open_menu:
            self.drop_menu.open()

    @staticmethod
    def _take_type_data(hint_text: str):
        hint_text_list = hint_text.lower().split()

        if hint_text_list[0] == "date":
            return None

        if len(hint_text_list) == 2:
            return hint_text_list[1]

        elif len(hint_text_list) == 1:
            return hint_text_list[0]

        else:
            return None


class DateTF(TextField):
    def __init__(self, name, scroll, **kwargs):
        super(DateTF, self).__init__(name, scroll, **kwargs)

        self.do_open_menu = False

        self.text = "dd.mm.yyyy HH:MM"

    def on_focus__(self):
        self.text = "  .  .       :  "

    def on_cursor_(self):
        print(self.cursor_index())


class AddMatch(ScrollView):
    def __init__(self, **kwargs):
        super(AddMatch, self).__init__(**kwargs)

        text_fields = [
            "Stadium", "Date and time", "League", "Home team", "Guest team", "Chief referee", "First referee",
            "Second referee", "Reserve referee"
        ]

        for name in text_fields:
            if name == "Date and time":
                self.ids.box.add_widget(DateTF(name, self))
            else:
                self.ids.box.add_widget(NoDateTF(name, self))


class MatchTable(MDDataTable):
    @property
    def take_games(self):
        games = DB.take_games()

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
        month = self._change_if_less_ten(month)

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
        print("\ncheck for phone...", end="")
        if instance.icon == "cookie-plus-outline":
            print("done\n")
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
                     MDFlatButton(text="ADD", on_release=self.update_match_db), ]
        )

        self.dialog.open()

    def update_match_db(self, event):
        print(self.dialog.content_cls.children)

    def dismiss_dialog(self, event):
        print(main)
        self.dialog.dismiss()


class MainApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.theme_style = "Dark"

        return GameScreen()


if __name__ == "__main__":
    main = MainApp()
    DB = ConnDB()
    main.run()
