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


def open_dialog(text):
    MDDialog(text=text).open()


class GameScreen(BoxLayout):
    games_layout = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.add_game_dialog = ObjectProperty()

        # при первом включении необходимо показать контент
        self._create_main_page()

    def _create_main_page(self):
        self.games_layout.clear_widgets()
        self.games_layout.add_widget(MatchTable())

    def add_button_callback(self, instance):
        """Вызывается при нажатии на одну из кнопок MDFloatingActionButtonSpeedDial.
         Проверяет нажатую кнопку и открывает необходимый Dialog."""

        # пока что работает одна кнопка из трех
        if instance.icon == "cookie-plus-outline":
            self.pop_dialog_add_match()

    def pop_dialog_add_match(self):
        """Открывает Dialog для добавления новой игры."""
        self.add_game_dialog = MDDialog(
            auto_dismiss=False,
            title="Add game",
            type="custom",
            content_cls=AddDataContent(type_="game"),
            buttons=[MDFlatButton(text="CANCEL", on_release=self.dismiss_dialog),
                     MDFlatButton(text="ADD", on_release=self.update_db)]
        )

        self.add_game_dialog.open()

    def update_db(self, event):
        """Вызывается при нажатии на кнопку ADD."""
        self.add_game_dialog.content_cls.update_db()

    def dismiss_dialog(self, event):
        """Закрывает Dialog."""
        self.add_game_dialog.dismiss()


class MatchTable(MDDataTable):
    """Класс таблицы для игр."""

    def __init__(self, **kwargs):
        self.cell_size = dp(25)
        self.use_pagination = False
        self.check = True
        self.column_data = [('Дата', dp(28)),
                            ('Время', dp(12)),
                            ('Лига', self.cell_size),
                            ('Стадион', self.cell_size),
                            ('Хозяева', self.cell_size),
                            ('Гости', self.cell_size)]

        self.row_data = self._take_games
        super(MatchTable, self).__init__(**kwargs)

    @property
    def _take_games(self) -> list:
        """Возвращает преобразованные в табличные значения данные из БД."""
        games = DB.take_games()

        list_of_games = []
        for game_info in games:
            league, date, time, stadium, team_home, team_guest = game_info[:6]

            date = self._date_list_in_str(date.split())
            time = self._time_int_in_str(time)

            list_of_games.append([date, time, league, stadium, team_home, team_guest])

        return list_of_games

    def _time_int_in_str(self, time: int) -> str:
        """Преобразует значние времени взятое из базы данных в виде 4-х целых чисел в формат HH:MM."""
        hour, minute = time // 100, time % 100

        hour = self._change_if_less_ten(hour)
        minute = self._change_if_less_ten(minute)

        return f'{hour}:{minute}'

    def _date_list_in_str(self, date: list) -> str:
        """Преобразует значние даты взятое из базы данных в виде 4-х целых чисел в формат DD.MM.YYYY."""
        year, month, day = date

        day = self._change_if_less_ten(day)
        month = self._change_if_less_ten(month)

        return f'{day}.{month}.{year}'

    @staticmethod
    def _change_if_less_ten(number):
        """Преобразует значение меньше 10 в формат 0_."""
        if int(number) < 10:
            number = f'0{number}'

        return number


class DropMenu(MDDropdownMenu):
    def __init__(self, **kwargs):
        super(DropMenu, self).__init__(**kwargs)
        self.width_mult = dp(56)
        self.box = BoxLayout(orientation="vertical")

    @staticmethod
    def take_data(name_table: str):
        """Возвращает значение из БД с помощью функций класса DB.

         :argument name_table (str) - из какой таблицы брать значения. В классе DB должен быть метод take_{mode}."""

        if name_table:
            db_method = f"take_{name_table}()"
            try:
                data = eval("DB." + db_method)
                return data
            except AttributeError:
                print(f"\n!!!!!!!!!!!!!!!\n ConnDB has no {db_method}\n!!!!!!!!!!!!!!!\n")
        return []

    def set_items(self, text_list, list_items: list):
        """Добавляет items в DropMenu."""
        if list_items:
            self.items = [{"text": f"{x}",
                           "viewclass": "OneLineListItem",
                           "on_release": lambda x=f"{x}": text_list.add_item_in_text_input(x),
                           } for x in list_items]
        else:
            self.items = [{"text": "Add in base",
                           "viewclass": "OneLineListItem",
                           "on_release": lambda: text_list._dropmenu_add_data_in_db_and_close()}]


class Content(RecycleView):
    def __init__(self, **kwargs):
        super(Content, self).__init__(**kwargs)

    def _get_height(self):
        """Устанавливает высоту Content в зависимости от количества items."""
        height = len(self.items) * 50

        if height > 300:
            height = 300

        return dp(height)

    def _get_box_height(self):
        """Устанавливает высоту BoxLayout в зависимости от количества items."""
        height = len(self.items) * 53
        return dp(height)


class AddDataContent(Content):
    def __init__(self, type_, **kwargs):
        super(AddDataContent, self).__init__(**kwargs)

        self.data_table = type_

        self._set_items()

        self._add_item_in_boxlayout()

        self.height = self._get_height()
        self.ids.box.height = self._get_box_height()

    def _set_items(self):
        """Устанавливает items в зависимости от названия таблицы БД, которая будт обновляться."""
        if self.data_table == "game":
            self.items = [
                {'name': 'Stadium', 'type': 'textfield',
                 'data_table': 'stadium', 'data_key': 'stadium_id', 'drop_menu': True, 'notnull': True},
                {'name': 'Data and Time', 'type': 'textfield',
                 'data_table': None, 'data_key': 'date_and_time', 'drop_menu': False, 'notnull': True},
                {'name': 'League', 'type': 'textfield',
                 'data_table': 'league', 'data_key': 'league_id', 'drop_menu': True, 'notnull': True},
                {'name': 'Home team', 'type': 'textfield',
                 'data_table': 'team', 'data_key': 'team_home', 'drop_menu': True, 'notnull': True},
                {'name': 'Guest team', 'type': 'textfield',
                 'data_table': 'team', 'data_key': 'team_guest', 'drop_menu': True, 'notnull': True},
                {'name': 'Chief referee', 'type': 'textfield',
                 'data_table': 'referee', 'data_key': 'referee_chief', 'drop_menu': True, 'notnull': True},
                {'name': 'First referee', 'type': 'textfield',
                 'data_table': 'referee', 'data_key': 'referee_first', 'drop_menu': True, 'notnull': False},
                {'name': 'Second referee', 'type': 'textfield',
                 'data_table': 'referee', 'data_key': 'referee_second', 'drop_menu': True, 'notnull': False},
                {'name': 'Reserve referee', 'type': 'textfield',
                 'data_table': 'referee', 'data_key': 'referee_reserve', 'drop_menu': True, 'notnull': False}
            ]
        elif self.data_table == "stadium":
            self.items = [
                {'name': 'Name', 'type': 'textfield',
                 'data_table': None, 'data_key': 'name', 'drop_menu': False, 'notnull': True},
                {'name': 'City', 'type': 'textfield',
                 'data_table': 'city', 'data_key': 'city_id', 'drop_menu': True, 'notnull': True},
                {'name': 'Address', 'type': 'textfield',
                 'data_table': None, 'data_key': 'address', 'drop_menu': False, 'notnull': True},
            ]

        elif self.data_table == "referee":
            self.items = [
                {'name': 'Fist name', 'type': 'textfield',
                 'data_table': None, 'data_key': 'first_name', 'drop_menu': False, 'notnull': True},
                {'name': 'Second name', 'type': 'textfield',
                 'data_table': None, 'data_key': 'second_name', 'drop_menu': False, 'notnull': True},
                {'name': 'Third name', 'type': 'textfield',
                 'data_table': None, 'data_key': 'third_name', 'drop_menu': False, 'notnull': False},
                {'name': 'Phone', 'type': 'textfield',
                 'data_table': None, 'data_key': 'phone', 'drop_menu': False, 'notnull': True},
                {'name': 'Category', 'type': 'textfield',
                 'data_table': 'category', 'data_key': 'category_id', 'drop_menu': True, 'notnull': True}
            ]

        elif self.data_table in ["league", "team", "category", "city"]:
            self.items = [{'name': 'Name', 'type': 'textfield',
                           'data_table': None, 'data_key': 'name', 'drop_menu': False, 'notnull': True}]

        else:
            raise AttributeError(f"Для добавления {self.data_table} не известны названия полей")

    def _add_item_in_boxlayout(self):
        """Добавляет items в BoxLayout."""
        for item in self.items:
            if item['name'] == 'Data and Time':
                self.ids.box.add_widget(DateAndTimeTF(item))
            elif item['name'] == 'Phone':
                self.ids.box.add_widget(PhoneTF(item))
            elif item['drop_menu']:
                self.ids.box.add_widget(TFWithDrop(item))
            else:
                self.ids.box.add_widget(TFWithoutDrop(item))

    def update_db(self):
        """Обрабатывает полученные из полей данные и отправляет на обновление БД."""
        fields = self.ids.box.children

        data = {}
        for field in fields:

            if field.is_notnull and not field.text:  # необходимые поля не заполнены
                open_dialog(f'The "{field.name}" field is not filled on')
                return

            elif field.set_id:
                # поле, имеющее всплывающее окно записываются в БД через id
                if field.data_table == 'referee':
                    # в таблице referee нет отдельного поля "name", как в других таблицах, поэтому делаем отдельный
                    # запрос с именем и фамилией
                    name = field.text.split(' ')
                    if name[0]:  # введено ли значение в поле
                        second_name, first_name = name[:2]
                        data[field.data_key] = DB.take_id_from_referee(field.data_table, first_name, second_name)[0]
                else:
                    data[field.data_key] = DB.take_id(field.data_table, field.text)[0]

            else:  # поля не пустые, текст из которых прямо идет в БД
                data[field.data_key] = field.text

        DB.insert(self.data_table, data)

        open_dialog("Successfully added")
        self.parent.parent.parent.dismiss()

    def set_next_focus(self, previous_widget):
        widgets = self.ids.box.children

        for inx, widget in enumerate(widgets):
            if widget is previous_widget:
                #  в списке Widget.parent последние добавленные виджеты лежат в начале,
                # поэтому отнимаем индекс
                widgets[inx - 1].focus = True


class TextField(MDTextField):
    def __init__(self, instr, **kwargs):
        super(TextField, self).__init__(**kwargs)

        self.name = instr['name']
        self.data_key = instr['data_key']
        self.data_table = instr['data_table']
        self.is_notnull = instr['notnull']

        self.set_id = False

        self.hint_text = "! " + self.name if self.is_notnull else self.name

    def on_focus_(self):
        self.text = ""

    def on_cursor_(self):
        pass

    def on_text_validate(self):
        self.set_next_focus()
        super(TextField, self).on_text_validate()

    def set_next_focus(self):
        self.parent.parent.set_next_focus(self)


class TFWithoutDrop(TextField):
    def __init__(self, name, **kwargs):
        super(TFWithoutDrop, self).__init__(name, **kwargs)


class PhoneTF(TFWithoutDrop):
    def __init__(self, name, **kwargs):
        super(PhoneTF, self).__init__(name, **kwargs)

        self.helper_text = "X(XXX)XXX-XX-XX"
        self.helper_text_mode = "persistent"

    def insert_text(self, substring, from_undo=False):
        """Фильтрует ввод текста под формат номера телефона."""
        cursor = self.cursor_col

        substring = re.sub('[^0-9\+]', '', substring)

        if substring == "+":
            cursor = self.cursor_col - 1
        elif self.text.startswith("+"):
            cursor -= 1

        if cursor == 0:
            substring += "("
        elif cursor == 4:
            substring += ")"
        elif cursor == 8 or cursor == 11:
            substring += "-"
        elif cursor > 14:
            substring = ''
        return super(PhoneTF, self).insert_text(substring, from_undo=from_undo)

    def on_text_validate(self):
        pat = "^(\+7|8)\([0-9]{3}\)[0-9]{3}(-[0-9]{2}){2}$"

        if not re.match(pat, self.text):
            self.text = "incorrect phone"

        super(PhoneTF, self).on_text_validate()


class DateAndTimeTF(TFWithoutDrop):
    def __init__(self, name, **kwargs):
        super(DateAndTimeTF, self).__init__(name, **kwargs)

        self.helper_text = "dd.mm.yyyy HH:MM"
        self.helper_text_mode = "persistent"

    def insert_text(self, substring, from_undo=False):
        cursor = self.cursor_col
        substring = re.sub('[^0-9]', '', substring)
        if cursor in [1, 4]:
            substring += "."
        elif cursor == 9:
            substring += " "
        elif cursor == 12:
            substring += ":"
        elif cursor > 15:
            substring = ''
        return super(DateAndTimeTF, self).insert_text(substring, from_undo=from_undo)

    def on_text_validate(self):
        pat = "^(0?[1-9]|[12][0-9]|3[01]).(0?[0-9]|1[012]).(19|20)?[0-9]{2} ([01][1-9]|2[0-4]):[0-6][0-9]$"

        if not re.match(pat, self.text):
            self.text = "incorrect data or time"


class TFWithDrop(TextField):
    def __init__(self, instr, **kwargs):
        super(TFWithDrop, self).__init__(instr, **kwargs)

        self.set_id = True

        self.drop_menu = DropMenu()

    def add_item_in_text_input(self, text_item):
        self.text = text_item
        self.drop_menu.dismiss()

    def on_focus_(self):
        """Открытие всплывающего меню."""
        self.text = ""

        # устанавливаем для всплывающего меню поле ввода, откуда его вызывали
        self.drop_menu.caller = self

        # берем текст вызывающего поля ввода для определения строк в всплывающем меню
        items = self.drop_menu.take_data(self.data_table)
        self.drop_menu.set_items(self, [i[0] for i in items])

        if items:
            self.drop_menu.open()

    def do_backspace(self, from_undo=False, mode='bkspc'):
        """Обновляет всплывающее меню при удалении текста."""
        self.update_dropmenu()
        super(TFWithDrop, self).do_backspace(from_undo=from_undo, mode=mode)

    def insert_text(self, substring, from_undo=False):
        """Обновляет всплывающее меню при вводе текста."""
        self.update_dropmenu()

        super(TFWithDrop, self).insert_text(substring, from_undo=from_undo)

    def update_dropmenu(self):
        """Устанавливает items всплывающего меню, которые подходят по набранному тексту."""
        self.drop_menu.dismiss()

        matching_items = []

        # берем текст вызывающего поля ввода для определения строк в всплывающем меню
        items = self.drop_menu.take_data(self.data_table)

        for item in items:
            if self.text.lower() in item[0].lower():
                matching_items.append(item)

        self.drop_menu.set_items(self, [i[0] for i in matching_items])
        self.drop_menu.open()

    def on_text_validate(self):
        """При нажатии кнопки Enter вводит текст выбранного item в строку или открывает меню добавления, если item'ов
        нет. """
        text = self.drop_menu.items[0]["text"]
        if text.split()[0] == "Add":
            self._dropmenu_add_data_in_db()
        else:
            self.text = text

        self.drop_menu.dismiss()

    def _dropmenu_add_data_in_db_and_close(self):
        self._dropmenu_add_data_in_db()
        self.drop_menu.dismiss()

    def _dropmenu_add_data_in_db(self):
        """Создает Dialog для добавления новых данных в БД."""
        title = "Add " + self.name.lower()

        self.add_data_dialog = MDDialog(
            title=title,
            type="custom",
            content_cls=AddDataContent(self.data_table),
            buttons=[MDFlatButton(text="CANCEL", on_release=self._dropmenu_dismiss),
                     MDFlatButton(text="ADD", on_release=self._update_match_db)]
        )
        self.add_data_dialog.open()

    def _update_match_db(self, event):
        """Вызывается при нажатии кнопки ADD"""
        self.add_data_dialog.content_cls.update_db()

    def _dropmenu_dismiss(self, event):
        self.add_data_dialog.dismiss()


class MainApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.theme_style = "Dark"

        return GameScreen()


if __name__ == "__main__":
    main = MainApp()
    DB = ConnDB()
    main.run()
