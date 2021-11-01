import re
from typing import Optional

from kivy.uix.widget import WidgetException
from kivymd.uix.snackbar import Snackbar
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.layout import Layout
from kivy.uix.scrollview import ScrollView
from kivy.properties import ObjectProperty
from kivy.metrics import dp

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDFloatingActionButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import OneLineAvatarIconListItem, OneLineIconListItem
from kivymd.uix.snackbar import Snackbar
from kivy.uix.behaviors.focus import FocusBehavior
from kivy.uix.recycleview import RecycleView
from kivymd.uix.menu import MDDropdownMenu
from kivymd.app import MDApp

from datebase import ConnDB


def open_dialog(text):
    MDDialog(text=text).open()


def open_snackbar(text):
    Snackbar(text=text).open()


class GameScreen(BoxLayout):
    games_layout = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.add_game_dialog = ObjectProperty()

        self.table_games = MatchTable()

        # при первом включении необходимо показать контент
        self._create_main_page()

    def _create_main_page(self) -> None:
        self.games_layout.clear_widgets()
        self.games_layout.add_widget(self.table_games)

    def add_button_callback(self) -> None:
        """Вызывается при нажатии на MDFloatingActionButton.
         Открывает окно добавления новой игры."""
        self.pop_dialog_add_match()

    def pop_dialog_add_match(self) -> None:
        """Открывает Dialog для добавления новой игры."""
        self.add_game_dialog = AddDataWindow(type_="games", filled_field=None, caller=None)
        self.add_game_dialog.open()

    def update_db(self, event) -> None:
        """Вызывается при нажатии на кнопку ADD."""
        self.add_game_dialog.content_cls.update_db()

    def dismiss_dialog(self, event) -> None:
        """Закрывает Dialog."""
        self.add_game_dialog.dismiss()


class AddDataWindow(MDDialog):
    def __init__(self, type_: str, filled_field: Optional[dict], caller, **kwargs):
        title = " ".join(['Add', type_])
        self.caller_ = caller
        filled_field = filled_field if filled_field else {}

        self.auto_dismiss = False
        self.title = title
        self.type = "custom"
        self._set_content_cls(type_, filled_field)
        self.buttons = [MDFlatButton(text="CANCEL", on_release=self.dismiss),
                        MDFlatButton(text="ADD", on_release=self._add_button_click)]

        super(AddDataWindow, self).__init__(**kwargs)

    def _set_content_cls(self, type_: str, filled_field: Optional[dict]) -> None:
        if type_ == "games":
            self.content_cls = AddGameContent(filled_field, caller=self.caller_)
        if type_ == "referee":
            self.content_cls = AddRefereeContent(filled_field, caller=self.caller_)
        if type_ == "stadium":
            self.content_cls = AddStadiumContent(filled_field, caller=self.caller_)
        if type_ == "league":
            self.content_cls = AddLeagueContent(filled_field, caller=self.caller_)
        if type_ == "category":
            self.content_cls = AddCategoryContent(filled_field, caller=self.caller_)
        if type_ == "city":
            self.content_cls = AddCityContent(filled_field, caller=self.caller_)
        if type_ == "team":
            self.content_cls = AddTeamContent(filled_field, caller=self.caller_)

    def _add_button_click(self, event) -> None:
        """Вызывается при нажатии кнопки ADD"""
        success = self.content_cls.update_db()
        if success and self.caller_:
            self.caller_.parent.parent.set_focus()


class MatchTable(MDDataTable):
    """Класс таблицы для игр."""

    def __init__(self, **kwargs):
        self.elevation = 100
        self.rows_num = 10
        self.cell_size = dp(25)
        self.use_pagination = False
        self.check = False
        self.column_data = [('Дата', dp(20)),
                            ('Время', dp(12)),
                            ('Лига', self.cell_size),
                            ('Стадион', self.cell_size),
                            ('Хозяева', self.cell_size),
                            ('Гости', self.cell_size)]

        self.row_data = self._take_games()
        super(MatchTable, self).__init__(**kwargs)

    def update(self):
        """Обновляет таблицу"""
        self.row_data = self._take_games()

    def _take_games(self) -> list:
        """Возвращает преобразованные в табличные значения данные из БД."""
        games = DB.take_games()
        list_of_games = []
        for game_info in games:
            league, date, time_, stadium, team_home, team_guest = game_info[:6]

            date = self._date_list_in_str(date.split())
            time_ = self._time_int_in_str(time_)

            list_of_games.append([date, time_, league, stadium, team_home, team_guest])

        return list_of_games

    def _time_int_in_str(self, time_: int) -> str:
        """Преобразует значние времени взятое из базы данных в виде 4-х целых чисел в формат HH:MM."""
        hour, minute = time_ // 100, time_ % 100

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


def take_name(table: str) -> list:
    """Возвращает значение из БД с помощью функций класса DB.

    Parameters:
        table (str) - из какой таблицы брать значения. В классе DB должен быть метод take_{mode}.

    Return:
        data (list) - список полученных имен из БД."""

    try:
        if table == "referee":
            data = DB.take_data("second_name||' '||first_name", table)
        else:
            data = DB.take_data("name", table)

        return data

    except AttributeError:
        print(f"\n!!!!!!!!!!!!!!!\n ConnDB has no table '{table}'\n!!!!!!!!!!!!!!!\n")
        return []


class DropMenu(MDDropdownMenu):
    def __init__(self, **kwargs):
        self.width_mult = dp(4)
        self.max_height = dp(250)

        super(DropMenu, self).__init__(**kwargs)

    def set_items(self, text_list, list_items: list, added_item=None):
        """Добавляет items в DropMenu."""
        if list_items:
            self.items = [{"text": f"{x}",
                           "viewclass": "OneLineListItem",
                           "on_release": lambda x=f"{x}": text_list.add_item_in_text_input(x),
                           } for x in list_items]
        else:
            self.items = [{"text": f'Add "{added_item}" in base',
                           "viewclass": "OneLineListItem",
                           "on_release": lambda: text_list._drop_menu_add_data_and_close()}]

    def update(self):
        self.set_menu_properties()
        if not self.parent:
            self.open()


class AddDataContent(RecycleView):
    def __init__(self, filled_field, caller, **kwargs):
        super(AddDataContent, self).__init__(**kwargs)

        # объект, создавший и вызвавший этот класс
        self.caller_ = caller

        self.children_ = []
        self._add_items_in_box(self.items, self.ids.box, filled_field)

        Clock.schedule_once(self.set_focus, .5)

    def _add_items_in_box(self, items: list, box: Layout, filled_field: dict = None):
        """Добавляет items в главный BoxLayout.

        Parameters:
            items (list)- список добавляемых объектов. Список может содержать в себе словарь или новый список.
                - Если объект словарь, то объект занимает всю ширину Content.
                - Если объект список, то все объекты внутри этого списка занимают ширину Content
                                                                                    в новом горизонтальном BoxLayout.
                  Ширина отдельного объекта зависит от значения 'size_hint_x' в словаре.

            box (BoxLayout)- контейнер для добавления объектов.
            filled_field (dict)- словарь, где ключи соответствуют названиям полей, а
                                              значения - текстом, которым их надо заполнять."""
        for item in items:
            if type(item) == list:
                hor_box = BoxLayout(orientation="horizontal", spacing=dp(10))
                box.add_widget(hor_box)
                self._add_items_in_box(item, hor_box, filled_field)

            elif type(item) == dict:
                # заполняет уже имеющиеся данные в строке, если есть
                text = filled_field.pop(item['data_key'], '')
                class_ = item.setdefault('class', '')
                type_ = item.setdefault('type', '')

                if class_ == "textfield":
                    self._add_textfield(type_, item, text, box)
                elif class_ == "checkbutton":
                    self._add_checkbutton()

    def _add_textfield(self, type_, instr, text, box):
        size_hint_x = instr.setdefault('size_hint_x', 1)

        if type_ == 'date_and_time':
            self._add_widget(DateAndTimeTF(size_hint_x=size_hint_x, parent=self, instruction=instr, text=text), box)
        elif type_ == 'phone':
            self._add_widget(PhoneTF(size_hint_x=size_hint_x, parent=self, instruction=instr, text=text), box)
        elif type_ == 'age':
            self._add_widget(AgeTF(size_hint_x=size_hint_x, parent=self, instruction=instr, text=text), box)
        elif instr.setdefault('drop_menu', False):
            self._add_widget(TFWithDrop(size_hint_x=size_hint_x, parent=self, instruction=instr, text=text), box)
        else:
            self._add_widget(TFWithoutDrop(size_hint_x=size_hint_x, parent=self, instruction=instr, text=text), box)

    def _add_checkbutton(self):
        pass

    def _add_widget(self, widget, box: Layout):
        box.add_widget(widget)
        self.children_.append(widget)

    def set_focus(self, dt=None):
        for field in self.children_:
            if not field.text:
                field.focus = True
                break

    def _get_height(self):
        """Устанавливает высоту Content в зависимости от количества items."""
        height = len(self.items) * 55

        if height > 300:
            height = 300

        return dp(height)

    def _get_box_height(self):
        """Устанавливает высоту BoxLayout в зависимости от количества items."""
        height = len(self.items) * 63.5
        return dp(height)

    def update_db(self):
        """Обрабатывает полученные из полей данные и отправляет на обновление БД."""
        fields = self.children_

        not_fill_fields = []
        caller_field_text = ""
        data = {}

        for field in fields:
            if field.add_text_in_parent:
                # запоминаем текст из полей, данные из которых будут записаны в вызывающем поле
                caller_field_text = " ".join([caller_field_text, field.text])

            if field.required and not field.text:  # ищем необходимые не заполненные поля
                not_fill_fields.append(field.hint_text)
            elif field.text and field.have_drop_menu:  # поле, имеющее всплывающее окно записываются в БД через id
                # если полей заполнения несколько, разбиваем строку по пробелу
                all_conditions = field.text.split(' ') if len(field.what_fields_child_fill) > 1 else [field.text]
                conditions_dict = {}

                # составляем словарь, где ключ - поле в БД, по которому искать, значение - фильтрующее значение
                for inx, condition in enumerate(all_conditions):
                    try:
                        conditions_dict[field.what_fields_child_fill[inx]] = condition
                    except IndexError:
                        continue

                # запрашиваем id исходя из условий
                try:
                    id_ = DB.take_data("id", field.data_table, conditions_dict, one_value=True)[0]
                    data[field.data_key] = id_
                except TypeError:
                    open_dialog(f'Name "{field.text}" is not found in the table {field.data_table.capitalize()}')

            elif field.text:  # поля не пустые, текст из которых прямо идет в БД
                data[field.data_key] = field.text

        if not_fill_fields:  # если есть незаполненные поля вызываем подсказку и возвращаем неуспех
            not_filled = "\n".join(f"   - {text}" for text in not_fill_fields)
            open_dialog(f"The fields:\n{not_filled}\n is not filled on")
            return False

        DB.insert(self.data_table, data)

        # self.parent - BoxLayout, self.parent.parent - MDCard, self.parent.parent.parent - AddDataWindow
        self.parent.parent.parent.dismiss()

        if not self.caller_:
            open_dialog("Successfully added")
            main.game_screen.table_games.update()

        else:
            self.caller_.text = caller_field_text.strip()
            open_snackbar(f"{self.caller_.name.title()} {self.caller_.text} successfully added")

        return True

    def set_next_focus(self, previous_widget):
        """Устанавливает фокус на слудующем виджете, если он не заполнен."""
        widgets = self.children_

        for inx, widget in enumerate(widgets):
            if widget is previous_widget:
                try:
                    widgets[inx + 1]
                except IndexError:
                    continue
                if not widgets[inx + 1].text:
                    next_widget = widgets[inx + 1]
                    next_widget.focus = True
                    self.scroll_to(next_widget)


class AddGameContent(AddDataContent):
    def __init__(self, filled_field, caller=None, **kwargs):
        self.data_table = "games"
        self.items = [
            {'name': 'Stadium', 'class': 'textfield', 'what_fields_child_fill': ['name'],
             'data_table': 'stadium', 'data_key': 'stadium_id', 'drop_menu': True, 'notnull': True},
            {'name': 'Data and Time', 'class': 'textfield', 'type': 'date_and_time', 'data_key': 'date_and_time', 'notnull': True},
            {'name': 'League', 'class': 'textfield', 'what_fields_child_fill': ['name'],
             'data_table': 'league', 'data_key': 'league_id', 'drop_menu': True, 'notnull': True},
            [
                {'name': 'Home team', 'class': 'textfield', 'what_fields_child_fill': ['name'],
                 'data_table': 'team', 'data_key': 'team_home', 'drop_menu': True, 'notnull': True},
                {'name': 'Age home team', 'class': 'textfield', 'type': 'age', 'data_key': 'team_home_year', 'size_hint_x': 0.35}
            ],
            [
                {'name': 'Guest team', 'class': 'textfield', 'what_fields_child_fill': ['name'],
             'data_table': 'team', 'data_key': 'team_guest', 'drop_menu': True, 'notnull': True},
                {'name': 'Age guest team', 'class': 'textfield', 'type': 'age', 'data_key': 'team_guest_year', 'size_hint_x': 0.35}
            ],
            {'name': 'Chief referee', 'class': 'textfield',
             'what_fields_child_fill': ['second_name', 'first_name', 'third_name'],
             'data_table': 'referee', 'data_key': 'referee_chief', 'drop_menu': True, 'notnull': True},
            {'name': 'First referee', 'class': 'textfield',
             'what_fields_child_fill': ['second_name', 'first_name', 'third_name'],
             'data_table': 'referee', 'data_key': 'referee_first', 'drop_menu': True},
            {'name': 'Second referee', 'class': 'textfield',
             'what_fields_child_fill': ['second_name', 'first_name', 'third_name'],
             'data_table': 'referee', 'data_key': 'referee_second', 'drop_menu': True},
            {'name': 'Reserve referee', 'class': 'textfield',
             'what_fields_child_fill': ['second_name', 'first_name', 'third_name'],
             'data_table': 'referee', 'data_key': 'referee_reserve', 'drop_menu': True}
        ]

        super(AddGameContent, self).__init__(filled_field, caller, **kwargs)


class AddRefereeContent(AddDataContent):
    def __init__(self, filled_field, caller=None, **kwargs):
        self.data_table = "referee"
        self.items = [
            {'name': 'Second name', 'class': 'textfield', 'data_key': 'second_name', 'notnull': True,
             'add_text_in_parent': True},
            {'name': 'Fist name', 'class': 'textfield', 'data_key': 'first_name', 'notnull': True,
             'add_text_in_parent': True},
            {'name': 'Third name', 'class': 'textfield', 'data_key': 'third_name'},
            {'name': 'Phone', 'class': 'textfield', 'type': 'phone', 'data_key': 'phone'},
            {'name': 'Category', 'class': 'textfield', 'what_fields_child_fill': ['name'],
             'data_table': 'category', 'data_key': 'category_id', 'drop_menu': True}
        ]

        super(AddRefereeContent, self).__init__(filled_field, caller, **kwargs)


class AddStadiumContent(AddDataContent):
    def __init__(self, filled_field, caller=None, **kwargs):
        self.data_table = "stadium"
        self.items = [
            {'name': 'Name', 'class': 'textfield', 'data_key': 'name', 'notnull': True, 'add_text_in_parent': True},
            {'name': 'City', 'class': 'textfield', 'what_fields_child_fill': ['name'],
             'data_table': 'city', 'data_key': 'city_id', 'drop_menu': True, 'notnull': True},
            {'name': 'Address', 'class': 'textfield', 'data_key': 'address', 'notnull': True},
        ]

        super(AddStadiumContent, self).__init__(filled_field, caller, **kwargs)


class AddLeagueContent(AddDataContent):
    def __init__(self, filled_field, caller=None, **kwargs):
        self.data_table = "league"
        self.items = [
            {'name': 'Name', 'class': 'textfield', 'data_key': 'name', 'notnull': True, 'add_text_in_parent': True}]

        super(AddLeagueContent, self).__init__(filled_field, caller, **kwargs)


class AddTeamContent(AddDataContent):
    def __init__(self, filled_field, caller=None, **kwargs):
        self.data_table = "team"
        self.items = [
            {'name': 'Name', 'class': 'textfield', 'data_key': 'name', 'notnull': True, 'add_text_in_parent': True}]

        super(AddTeamContent, self).__init__(filled_field, caller, **kwargs)


class AddCategoryContent(AddDataContent):
    def __init__(self, filled_field, caller=None, **kwargs):
        self.data_table = "category"
        self.items = [
            {'name': 'Name', 'class': 'textfield', 'data_key': 'name', 'notnull': True, 'add_text_in_parent': True}]

        super(AddCategoryContent, self).__init__(filled_field, caller, **kwargs)


class AddCityContent(AddDataContent):
    def __init__(self, filled_field, caller=None, **kwargs):
        self.data_table = "city"
        self.items = [
            {'name': 'Name', 'class': 'textfield', 'data_key': 'name', 'notnull': True, 'add_text_in_parent': True}]

        super(AddCityContent, self).__init__(filled_field, caller, **kwargs)


class TextField(MDTextField):
    def __init__(self, parent, instr: dict, text: str, **kwargs):
        super(TextField, self).__init__(**kwargs)
        self.parent_ = parent

        self.set_text(self, text)

        self.name = self.hint_text = instr.setdefault('name').capitalize()
        self.required = instr.setdefault('notnull', False)
        self.helper_text_mode = "on_error"

        self.data_key = instr.setdefault('data_key')
        self.data_table = instr.setdefault('data_table')
        self.what_fields_child_fill = instr.setdefault('what_fields_child_fill')
        self.add_text_in_parent = instr.setdefault('add_text_in_parent', False)

        self.have_drop_menu = False
        self.change_focus = False

    def on_focus_(self):
        pass

    def on_double_tap(self):
        self.text = ""

    def on_cursor_(self):
        pass

    def on_text_validate(self):
        """После ввода текста устанавливает фокус на слудующем поле ввода."""
        super(TextField, self).on_text_validate()
        self.set_next_focus()

    def set_next_focus(self):
        if self.change_focus:
            self.parent_.set_next_focus(self)


class TFWithoutDrop(TextField):
    def __init__(self, parent, instruction, text='', **kwargs):
        super(TFWithoutDrop, self).__init__(parent, instruction, text, **kwargs)

    def on_text_validate(self):
        super(TextField, self).on_text_validate()
        self.change_focus = True
        self.set_next_focus()


class PhoneTF(TFWithoutDrop):
    def __init__(self, parent, instruction, **kwargs):
        super(PhoneTF, self).__init__(parent, instruction, **kwargs)

        self.helper_text = "X(XXX)XXX-XX-XX"
        self.helper_text_mode = "persistent"

    def insert_text(self, substring, from_undo=False):
        """Фильтрует ввод текста под формат номера телефона."""
        cursor = self.cursor_col

        substring = re.sub('[^0-9+]', '', substring)

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

    def do_backspace(self, from_undo=False, mode='bkspc'):
        cursor = self.cursor_col

        if self.text.startswith("+"):
            cursor -= 1

        doble_bkspc = False
        if cursor in [3, 7, 11, 14]:
            doble_bkspc = True

        if doble_bkspc:
            super(PhoneTF, self).do_backspace(from_undo=from_undo, mode='bkspc')
        super(PhoneTF, self).do_backspace(from_undo=from_undo, mode='bkspc')

    def on_text_validate(self):
        pat = "^(\+7|8)\([0-9]{3}\)[0-9]{3}(-[0-9]{2}){2}$"

        if not re.match(pat, self.text):
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # делаем красным очищаем и не меняем фокус
            self.text = ""

        super(PhoneTF, self).on_text_validate()


class DateAndTimeTF(TFWithoutDrop):
    def __init__(self, parent, instruction, **kwargs):
        super(DateAndTimeTF, self).__init__(parent, instruction, **kwargs)

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

    def do_backspace(self, from_undo=False, mode='bkspc'):
        cursor = self.cursor_col
        doble_bkspc = False
        if cursor in [3, 6, 11, 14, 17]:
            # стираем символ два раза, чтобы удалить еще и разделяющий символ (. или :)
            doble_bkspc = True

        if doble_bkspc:
            super(DateAndTimeTF, self).do_backspace(from_undo=from_undo, mode='bkspc')
        super(DateAndTimeTF, self).do_backspace(from_undo=from_undo, mode='bkspc')

    def on_text_validate(self):
        pat = "^(0?[1-9]|[12][0-9]|3[01]).(0?[0-9]|1[012]).(19|20)?[0-9]{2} ([01][1-9]|2[0-4]):[0-6][0-9]$"

        if not re.match(pat, self.text):
            self.text = ""

        super(DateAndTimeTF, self).on_text_validate()


class AgeTF(TFWithoutDrop):
    def __init__(self, parent, instruction, **kwargs):
        super(AgeTF, self).__init__(parent, instruction, **kwargs)

    def insert_text(self, substring, from_undo=False):
        cursor = self.cursor_col
        substring = re.sub('[^0-9]', '', substring)
        if cursor > 3:
            substring = ''
        return super(AgeTF, self).insert_text(substring, from_undo=from_undo)

    def on_text_validate(self):
        pat = "^(19|20)[0-9]{2}$"

        if not re.match(pat, self.text):
            self.text = ""

        super(AgeTF, self).on_text_validate()


class TFWithDrop(TextField):
    def __init__(self, parent, instruction, text='', **kwargs):
        super(TFWithDrop, self).__init__(parent, instruction, text, **kwargs)

        self.have_drop_menu = True

        self.drop_menu = DropMenu()  # header_cls=MenuHeader()

    def add_item_in_text_input(self, text_item):
        self.text = text_item
        self.drop_menu.dismiss()
        self.change_focus = True
        self.set_next_focus()

    def on_focus_(self):
        """Открытие всплывающего меню."""
        # устанавливаем для всплывающего меню поле ввода, откуда его вызывали
        self.drop_menu.caller = self

        # берем текст вызывающего поля ввода для определения строк в всплывающем меню
        items = take_name(self.data_table)
        self.drop_menu.set_items(self, [i[0] for i in items])

        if items:
            try:
                Clock.schedule_once(self.open_drop_menu, 0.1)
            except WidgetException:
                # всплывающее окно уже открыто
                pass

    def open_drop_menu(self, dp=None):
        if not self.drop_menu.parent and self.focus:
            self.drop_menu.open()

    def do_backspace(self, from_undo=False, mode='bkspc'):
        """Обновляет всплывающее меню при удалении текста."""
        super(TFWithDrop, self).do_backspace(from_undo=from_undo, mode=mode)
        self.update_drop_menu()

    def insert_text(self, substring, from_undo=False):
        """Обновляет всплывающее меню при вводе текста."""
        super(TFWithDrop, self).insert_text(substring, from_undo=from_undo)
        self.update_drop_menu()

    def update_drop_menu(self):
        """Обновление items всплывающего меню, которые подходят по набранному тексту."""
        matching_items = []

        # берем текст вызывающего поля ввода для определения строк в всплывающем меню
        items = take_name(self.data_table)

        for item in items:
            if self.text.lower() in item[0].lower():
                matching_items.append(item)

        self.drop_menu.set_items(self, [i[0] for i in matching_items], added_item=self.text)
        self.drop_menu.update()

    def on_text_validate(self):
        """При нажатии кнопки Enter вводит текст выбранного item в строку или открывает меню добавления, если item'ов
        нет."""
        text_dropmenu = self.drop_menu.items[0]["text"]

        if text_dropmenu.split()[0] == "Add":
            filled_fields = self._make_dict_filled_field_in_children()
            self.text = ''
            self._drop_menu_add_data(filled_fields)

        else:
            self.text = text_dropmenu
            self.change_focus = True

        self.drop_menu.dismiss()
        super(TFWithDrop, self).on_text_validate()

    def _make_dict_filled_field_in_children(self) -> dict:
        filled_fields = {}

        if len(self.what_fields_child_fill) == 1:
            filled_fields.update({self.what_fields_child_fill[0]: self.text})
        elif len(self.what_fields_child_fill) > 1:
            text_fields = self.text.split()
            for inx, field in enumerate(self.what_fields_child_fill):
                try:
                    filled_fields.update({field: text_fields[inx]})
                except IndexError:
                    continue

        return filled_fields

    def _drop_menu_add_data_and_close(self):
        self._drop_menu_add_data()
        self.drop_menu.dismiss()

    def _drop_menu_add_data(self, filled_fields=None):
        """Создает Dialog для добавления новых данных в БД."""
        self.add_data_dialog = AddDataWindow(self.data_table, filled_field=filled_fields, caller=self)
        self.add_data_dialog.open()


class MainApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.theme_style = "Dark"

        self.game_screen = GameScreen()

        return self.game_screen


if __name__ == "__main__":
    main = MainApp()
    DB = ConnDB()
    main.run()
