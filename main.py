import re

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
from kivy.uix.behaviors.focus import FocusBehavior
from kivy.uix.recycleview import RecycleView
from kivymd.uix.menu import MDDropdownMenu
from kivymd.app import MDApp

from datebase import ConnDB


def add_data_in_db(table, data):
    DB.insert(table, data)


def take_id_from_name(table, name):
    return DB.take_id(table, name)


def is_drop_text_field(name) -> bool:
    """Проверяет, нужно ли для данного поля всплывающее меню"""
    #  - часть "drop" или "id" значит, что при взаимодействии с полем ввода открывается всплывающее окно
    return True if re.search('( id)|( drop)', name) else False


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
        self.add_game_dialog = MDDialog(
            auto_dismiss=False,
            title="Add game",
            type="custom",
            content_cls=AddMatch(),
            buttons=[MDFlatButton(text="CANCEL", on_release=self.dismiss_dialog),
                     MDFlatButton(text="ADD", on_release=self.update_match_db), ]
        )

        self.add_game_dialog.open()

    def update_match_db(self, event):
        print(self.add_game_dialog.content_cls.children)

    def dismiss_dialog(self, event):
        print(main)
        self.add_game_dialog.dismiss()


class MatchTable(MDDataTable):
    def __init__(self, **kwargs):
        self.cell_size = dp(25)
        self.use_pagination = False
        self.check = True
        self.column_data = [('Дата', dp(28)),
                            ('Время', dp(12)),
                            ('Лига', self.cell_size),
                            ('Стадион', self.cell_size),
                            ('Хозяева', self.cell_size),
                            ('Гости', self.cell_size),
                            ('Фамилия', self.cell_size)]

        self.row_data = self.take_games
        super(MatchTable, self).__init__(**kwargs)

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


class DropMenu(MDDropdownMenu):

    def __init__(self, **kwargs):
        super(DropMenu, self).__init__(**kwargs)
        self.width_mult = dp(56)

    @staticmethod
    def take_data(mode):
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
            self.items = [{"text": "Add in base",
                           "viewclass": "OneLineListItem",
                           "on_release": lambda: text_list.dropmenu_add_data_in_db(text_list)}]


class Content(RecycleView):

    def __init__(self, **kwargs):
        super(Content, self).__init__(**kwargs)

    def _get_height(self):
        height = len(self.items) * 50

        if height > 300:
            height = 300

        return dp(height)

    def _get_box_height(self):
        height = len(self.items) * 53
        return dp(height)


class AddDataContent(Content):
    def __init__(self, mode, **kwargs):
        super(AddDataContent, self).__init__(**kwargs)

        if mode == "stadium":
            self.items = ["Name", "City id drop", "Address"]

        elif mode == "referee":
            self.items = ["First name", "Second name", "Third name", "Phone", "Category id drop"]

        elif mode in ["league", "team", "category", "city"]:
            self.items = ["Name"]

        else:
            raise AttributeError(f"Для добавления {mode} не известны названия полей")

        for name in self.items:
            if is_drop_text_field(name):
                self.ids.box.add_widget(TFWithDrop(name))
            else:
                self.ids.box.add_widget(TFWithoutDrop(name))

        self.height = self._get_height()
        self.ids.box.height = self._get_box_height()


class AddMatch(Content):
    def __init__(self, **kwargs):
        super(AddMatch, self).__init__(**kwargs)

        self.items = [
            "Stadium drop id", "Date and time", "League drop id", "Home team drop id",
            "Guest team drop id", "Chief referee drop id", "First referee drop id",
            "Second referee drop id", "Reserve referee drop id"
        ]

        for name in self.items:
            if name == "Date and time":
                self.ids.box.add_widget(DateAndTimeTF(name))
            elif is_drop_text_field(name):
                self.ids.box.add_widget(TFWithDrop(name))
            else:
                self.ids.box.add_widget(TFWithoutDrop(name))

        self.height = self._get_height()
        self.ids.box.height = self._get_box_height()


class TextField(MDTextField):

    def __init__(self, name, **kwargs):
        super(TextField, self).__init__(**kwargs)

        # print(self.focus_next)
        # print(self.focus_previous)

        # функция on_focus() объекта TextInput срабатывает при фокусе на объект и разфокусе
        # данный check помогает вызывать необходимые функции только при фокусе на объект
        self.check_text_focus = False

        # убираем "id" и "drop", если есть
        self.hint_text = re.sub('( id)|( drop)', '', name)

    def check_focus(self):
        if not self.check_text_focus:
            self.on_focus_()

        else:
            self.check_text_focus = False

    def on_focus_(self):
        pass

    def on_cursor_(self):
        pass


class TFWithoutDrop(TextField):
    def __init__(self, name, **kwargs):
        super(TFWithoutDrop, self).__init__(name, **kwargs)

    def on_focus_(self):
        self.text = ""


class DateAndTimeTF(TFWithoutDrop):
    def __init__(self, name, **kwargs):
        super(DateAndTimeTF, self).__init__(name, **kwargs)

        self.helper_text = "dd.mm.yyyy HH:MM"
        self.helper_text_mode = "persistent"

    def insert_text(self, substring, from_undo=False):
        cursor = self.cursor_col
        if cursor == 0:
            s = re.sub('[^0-3]', '', substring)
        elif cursor in [1, 4]:
            s = re.sub('[^0-9]', '', substring) + "."
        elif cursor == 3:
            s = re.sub('[^0|1]', '', substring)
        elif 5 < cursor <= 8:
            s = re.sub('[^0-9]', '', substring)
        elif cursor == 9:
            s = re.sub('[^0-9]', '', substring) + " "
        elif cursor == 11:
            s = re.sub('[^0-2]', '', substring)
        elif cursor == 12:
            s = re.sub('[^0-9]', '', substring) + ":"
        elif cursor == 13:
            s = re.sub('^[0-6]', '', substring)
        elif cursor in [14, 15]:
            s = re.sub('[^0-9]', '', substring)
        else:
            s = ''
        return super(DateAndTimeTF, self).insert_text(s, from_undo=from_undo)

    def on_text_validate(self):
        # функция on_focus() объекта TextInput срабатывает при фокусе на объект и разфокусе
        # данный check помогает вызывать необходимые функции только при фокусе на объект
        self.check_text_focus = True

        pat = "^(0?[1-9]|[12][0-9]|3[01]).(0?[0-9]|1[012]).(19|20)?[0-9]{2} ([01][1-9]|2[0-4]):[0-6][0-9]$"

        if not re.match(pat, self.text):
            self.text = "incorrect data or time"

    def on_focus_(self):
        self.text = ""


class TFWithDrop(TextField):
    def __init__(self, name, **kwargs):
        super(TFWithDrop, self).__init__(name, **kwargs)

        self.drop_menu = DropMenu()

    def add_item_in_text_input(self, text_item):
        self.text = text_item
        self.drop_menu.dismiss()

    def on_focus_(self):
        """Открытие всплывающего меню"""
        self.text = ""

        # устанавливаем для всплывающего меню поле ввода, откуда его вызывали
        self.drop_menu.caller = self

        # берем текст вызывающего поля ввода для определения строк в всплывающем меню
        type_data = self._take_type_data(self.drop_menu.caller.hint_text)
        items = self.drop_menu.take_data(type_data)
        self.drop_menu.set_items(self, [i[0] for i in items])

        if items:
            self.drop_menu.open()
        self.check_text_focus = True

    def insert_text(self, substring, from_undo=False):
        """Обновление всплывающего меню"""
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
            super(TFWithDrop, self).insert_text(substring, from_undo=from_undo)

    def on_text_validate(self):
        # виджет вызывает on_focus() несколько раз,
        # чтобы всплывающее меню не появлялось снова
        self.check_text_focus = True
        print('press')

        text = self.drop_menu.items[0]["text"]
        if text.split()[0] == "Add":
            self.dropmenu_add_data_in_db()
        else:
            self.text = text

        self.drop_menu.dismiss()

    def dropmenu_add_data_in_db(self):
        mode = self._take_type_data(self.hint_text)

        title = "Add " + self.hint_text.lower()

        self.add_data_dialog = MDDialog(
            title=title,
            type="custom",
            content_cls=AddDataContent(mode),
            buttons=[MDFlatButton(text="CANCEL", on_release=self.dropmenu_dismiss),
                     MDFlatButton(text="ADD", on_release=self.dropmenu_add_press)]
        )
        self.add_data_dialog.open()

    def dropmenu_add_press(self, event):
        db_table = self.add_data_dialog.title.split()[-1]
        data = self.collect_data()

        add_data_in_db(table=db_table, data=data)

        self.add_data_dialog.dismiss()

    def collect_data(self):
        text_fields = self.add_data_dialog.content_cls.ids.box.children
        data = {}
        for tf in text_fields:
            if tf.id:  # необходимо добавить в базу данных id, а не text
                value = take_id_from_name(tf.hint_text.lower(), tf.text)
                data[tf.hint_text] = value[0]
            else:
                data[tf.hint_text] = tf.text

        return data

    def dropmenu_dismiss(self, event):
        self.add_data_dialog.dismiss()

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


class MainApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.theme_style = "Dark"

        return GameScreen()


if __name__ == "__main__":
    main = MainApp()
    DB = ConnDB()
    main.run()
