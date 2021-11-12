import re
from math import ceil

from typing import Optional, Any, Union, List, Tuple

from kivy.uix.widget import WidgetException, Widget
from kivymd.uix.snackbar import Snackbar
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.layout import Layout
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.properties import ObjectProperty
from kivy.metrics import dp

from kivymd.color_definitions import colors
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelOneLine
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.card import MDCard
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDFloatingActionButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivy.uix.label import Label
from kivymd.uix.list import OneLineAvatarIconListItem, OneLineIconListItem
from kivymd.uix.snackbar import Snackbar
from kivy.uix.behaviors.focus import FocusBehavior
from kivymd.uix.behaviors import TouchBehavior
from kivy.uix.recycleview import RecycleView
from kivymd.uix.menu import MDDropdownMenu
from kivymd.app import MDApp

from database import ConnDB


def open_dialog(text):
    MDDialog(text=text).open()


def open_snackbar(text):
    Snackbar(text=text).open()


class AppScreen(BoxLayout):
    games_layout = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.add_game_dialog = ObjectProperty()

        self.table_games = GamesTable()

        # при первом включении необходимо показать контент
        self._create_main_page()

    def _create_main_page(self) -> None:
        self.games_layout.clear_widgets()
        self.games_layout.add_widget(self.table_games)

    def add_button_callback(self) -> None:
        """Вызывается при нажатии на MDFloatingActionButton.
         Открывает окно добавления новой игры."""
        self.pop_dialog_add_game()

    def pop_dialog_add_game(self) -> None:
        """Открывает Dialog для добавления новой игры."""
        self.add_game_dialog = DialogWindow(type_="games")
        self.add_game_dialog.open()

    def menu_settings(self):
        print("menu")

    def update_db(self, event) -> None:
        """Вызывается при нажатии на кнопку ADD."""
        self.add_game_dialog.content_cls.update_db()

    def dismiss_dialog(self, event) -> None:
        """Закрывает Dialog."""
        self.add_game_dialog.dismiss()


class GamesTable(MDDataTable, TouchBehavior):
    """Класс таблицы для отображения записанных в БД игр."""

    def __init__(self):
        self.cell_size = dp(25)
        # ключи showed_data должны совпадать с именами атрибутов класса Game
        self.data_dict = {"date": ('Дата', dp(20)),
                          "time": ('Время', dp(12)),
                          "league": ('Лига',),
                          "stadium": ('Стадион',),
                          "team_home": ('Хозяева',),
                          "team_guest": ('Гости',),
                          "status": ('Статус', dp(30))}

        self.showed_data = ["date", "time", "stadium", "status"]

        # проверка, если в будущем будет несколько таблиц с заданными показываемыми значениями
        # значения showed_data должны состоять из ключей data_dict
        assert all(map(lambda data: data in Game.attribute, self.showed_data)), "" \
                                                                                f"showed_data might be in {Game.attribute}"

        self.elevation = 100
        self.rows_num = 10
        self.use_pagination = False
        self.check = False
        self.column_data = list(map(lambda data: self._set_column_name_and_size(data), self.showed_data))

        self.row_data = self._take_games()
        super(GamesTable, self).__init__()

        self.count_cell_in_row = len(self.column_data)

        self.touched_cell = None

    def on_row_press(self, instance_cell_row):
        """Necessary for saving touched Cell"""
        self.touched_cell = instance_cell_row

    def on_long_touch(self, touch, *args):
        # строка, в которой находится нажатая клетка
        row_cell = self.touched_cell.index // self.count_cell_in_row

        # игра, записанная в данной строке
        game = self.list_of_games[row_cell]
        print(game.status_key)

    def _set_column_name_and_size(self, data: str):
        if data in self.data_dict:
            data_dict = self.data_dict[data]
            if len(data_dict) == 1:
                name = self.data_dict.get(data)[0]
                cell_size = self.cell_size
            elif len(data_dict) == 2:
                name, cell_size = self.data_dict.get(data)
            else:
                raise IndexError("len(item) in data_dict should be 1 or 2")

        else:
            name, cell_size = data, self.cell_size

        return name, cell_size

    def update(self):
        """Обновляет таблицу"""
        self.row_data = self._take_games()

    def _take_games(self) -> list:
        """Возвращает преобразованные в табличные значения данные из БД.

            Return:
                list_of_games(list) - список игр, взятых из БД."""

        games = DB.take_games()
        self.list_of_games = []
        return_list = []
        for game_info in games:
            game = Game(*game_info)

            self.list_of_games.append(game)
            return_list.append(list(map(lambda data: getattr(game, data), self.showed_data)))

        return return_list


class Game:
    """Класс, определяющий игру из БД."""
    # dict of status icon, color, name
    status_icn = {"not_passed": ("calendar-alert", colors["Yellow"]["800"], "Не проведена"),
                  "passed": ("calendar-check", colors["Green"]["300"], "Проведена"),
                  "pay_done": ("calendar-check", colors["Green"]["500"], "Оплачено")}
    # list future attribute
    attribute = ["id_in_db",
                 "league", "date", "time", "stadium",
                 "team_home",
                 "team_guest",
                 "referee_chief",
                 "referee_first",
                 "referee_second",
                 "referee_reserve", "game_passed",
                 "pay_done",
                 "payment",
                 "status",
                 ]

    def __init__(self, id_in_db: int, league: str, year: int, month: int, day: int, time_: int,
                 stadium: str, team_home: str, team_guest: str,
                 game_passed: Optional[int], pay_done: Optional[int], payment: int):
        self.id_in_db = id_in_db
        self.league = league
        self.date = self._date_list_in_str(year, month, day)
        self.time = self._time_int_in_str(time_)
        self.stadium = stadium
        self.team_home = team_home
        self.team_guest = team_guest
        self.referee_chief = self._take_referee("chief").strip()
        self.referee_first = self._take_referee("first").strip()
        self.referee_second = self._take_referee("second").strip()
        self.referee_reserve = self._take_referee("reserve")
        self.game_passed = bool(game_passed)
        self.pay_done = bool(pay_done)
        self.payment = payment
        self.status_key = self._get_status(self.game_passed, self.pay_done)
        self.status = self.status_icn[self.status_key]

    def _take_referee(self, position: str) -> str:
        """Возвращает ФИО судьи из БД.

            Parameters:
                position(str) - позиция судьи, может быть [chief, first, second, reserve].

            Return:
                name(str) - имя (если есть), фамилия (если есть), отчество (если есть) судьи."""

        table = f"games INNER JOIN referee ON games.referee_{position} = referee.id"
        first_name = DB.take_data("referee.first_name", table, conditions={"games.id": self.id_in_db}, one_value=True)
        second_name = DB.take_data("referee.second_name", table, conditions={"games.id": self.id_in_db}, one_value=True)
        third_name = DB.take_data("referee.third_name", table, conditions={"games.id": self.id_in_db}, one_value=True)

        name = [f"{name[0]} " if name and name[0] else '' for name in [first_name, second_name, third_name]]
        name = "".join(name)

        return name

    def _time_int_in_str(self, time_: int) -> str:
        """Преобразует значние времени взятое из базы данных в виде 4-х целых чисел в формат HH:MM."""
        hour, minute = time_ // 100, time_ % 100

        hour = self._change_if_less_ten(hour)
        minute = self._change_if_less_ten(minute)

        return f'{hour}:{minute}'

    def _date_list_in_str(self, year: int, month: int, day: int) -> str:
        """Преобразует значние года, месяца и года в формат DD.MM.YYYY."""
        day = self._change_if_less_ten(day)
        month = self._change_if_less_ten(month)

        return f'{day}.{month}.{year}'

    @staticmethod
    def _get_status(game_passed: bool, pay_done: bool) -> Union[str, tuple]:
        """Возвращает статус игры от переданных условий (проведена и оплачена ли игра).

            Parameters:
                game_passed(bool) - (не) прошла игра.
                pay_done(bool) - (не) оплачена игра.

            Return:
                status(str) - текущий статус игры."""

        if game_passed and pay_done:
            return "pay_done"
        elif game_passed and not pay_done:
            return "passed"
        elif not game_passed:
            return "not_passed"

    @staticmethod
    def _change_if_less_ten(number):
        """Преобразует значение меньше 10 в формат 0_."""
        if int(number) < 10:
            number = f'0{number}'

        return number


def take_name_from_db(table: str) -> list:
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
        raise AttributeError(f"ConnDB has no table '{table}'")


class DropMenu(MDDropdownMenu):
    def __init__(self):
        self.width_mult = dp(4)
        self.max_height = dp(250)

        super(DropMenu, self).__init__()

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
                           "on_release": lambda: text_list.drop_menu_add_data_and_close()}]

    def update(self):
        self.set_menu_properties()
        if not self.parent:
            self.open()


class DialogWindow(MDDialog):
    def __init__(self, **kwargs):
        """Parameters:
                type_(str) - тип создаваемого MDDialog. type_ может принимать значения: 
                                                            games, referee, stadium, league, category, city, team."""
        type_ = kwargs.pop('type_')
        assert type_ in ["games", "referee", "stadium", "league", "category", "city", "team"], '\
                    parameter type_ must be in ["games", "referee", "stadium", "league", "category", "city", "team"]'

        self.caller_ = None

        title = " ".join(['Add', type_])

        self.auto_dismiss = True
        self.title = title
        self.type = "custom"
        self._set_content_cls(type_, **kwargs)
        self.buttons = [MDFlatButton(text="CANCEL", on_release=self.dismiss, theme_text_color="Custom",
                                     text_color=app.theme_cls.error_color),
                        MDRaisedButton(text="ADD",
                                       on_release=self._add_button_click,
                                       md_bg_color=app.theme_cls.primary_dark)]

        super(DialogWindow, self).__init__()

    def _set_content_cls(self, type_, **kwargs) -> None:
        if type_ == "games":
            self.content_cls = AddGameContent()
        if type_ == "referee":
            self.content_cls = AddRefereeContent(**kwargs)
        if type_ == "stadium":
            self.content_cls = AddStadiumContent(**kwargs)
        if type_ == "league":
            self.content_cls = AddLeagueContent(**kwargs)
        if type_ == "category":
            self.content_cls = AddCategoryContent(**kwargs)
        if type_ == "city":
            self.content_cls = AddCityContent(**kwargs)
        if type_ == "team":
            self.content_cls = AddTeamContent(**kwargs)

    def _add_button_click(self, event) -> None:
        """Вызывается при нажатии кнопки ADD"""
        success = self.content_cls.update_db()
        if success and self.caller_:
            self.caller_.parent.parent.set_focus()


class DialogContent(RecycleView):
    def __init__(self, **kwargs):
        """Parameters:
                caller_ (Any) - объект, создавший и вызвавший этот класс.
                filled_field (dict[str, str]) - словарь уже заполненных полей, где
                                      ключом является название TextField, в которое нужно добавить текст, а
                                      значением является добавляемый текст."""

        self.caller_ = kwargs.pop('caller_', None)
        self.filled_field = kwargs.pop('filled_field', {})

        super(DialogContent, self).__init__(**kwargs)

        self.children_ = []
        self._add_items_in_box(self.items, self.ids.box)

    def _add_items_in_box(self, items: list, box):
        """Добавляет items в главный BoxLayout.

        Parameters:
            items (list)- список добавляемых объектов. Список может содержать в себе словарь или новый список.
                - Если объект словарь, то объект занимает всю ширину Content.
                - Если объект список, то все объекты внутри этого списка занимают ширину Content
                                                                                    в новом горизонтальном BoxLayout.
                  Ширина отдельного объекта зависит от значения 'size_hint_x' в словаре.

            box (BoxLayout)- контейнер для добавления объектов."""

        # отступ с правой стороны
        box.padding[2] = 20

        for item in items:
            if type(item) == list:
                self._add_items_in_box(item, box)

            elif type(item) == dict:
                class_ = item.setdefault('class', '')
                type_ = item.setdefault('type', '')

                if class_ == "boxlayout":
                    new_box = MDBoxLayout(orientation=item.setdefault("orientation", "vertical"),
                                          spacing=item.setdefault("spacing", 0),
                                          padding=item.setdefault("padding", 0)
                                          )
                    box.add_widget(new_box)
                    box = new_box

                elif class_ == "gridlayout":
                    box_ = MDGridLayout(padding=[0, 10, 0, 0],
                                        spacing=10,
                                        rows=item.setdefault("cols", 1),
                                        cols=item.setdefault("rows", 1))
                    box.add_widget(box_)
                    box = box_

                elif class_ == "gridlayout":
                    box_ = MDGridLayout(rows=item.setdefault("cols", 1),
                                        cols=item.setdefault("rows", 1))
                    box.add_widget(box_)
                    box = box_

                elif class_ == "expansionpanel":
                    box_ = MDGridLayout(padding=[0, 10, 0, 0],
                                        spacing=10,
                                        cols=item.setdefault("cols", 1),
                                        adaptive_height=True)
                    panel = ExpansionPanel(self,
                                           panel_cls=MDExpansionPanelOneLine(text=item.setdefault("panel_text", "")),
                                           content=box_)
                    box.add_widget(panel)
                    box = box_

                elif class_ == "textfield":
                    # заполняет уже имеющиеся данные в строке, если есть
                    text = self.filled_field.pop(item['data_key'], '')

                    self._add_textfield(type_, box, parent_=self, instruction=item, text=text)

                elif class_ == "checkbox":
                    self._add_checkbutton(item, box)

                elif class_ == "label":
                    self._add_label(item, box)

    def _add_textfield(self, type_, box, **kwargs):
        if type_ == 'date':
            self._add_widget(DateTF(**kwargs), box)
        elif type_ == 'time':
            self._add_widget(TimeTF(**kwargs), box)
        elif type_ == 'phone':
            self._add_widget(PhoneTF(**kwargs), box)
        elif type_ == 'age':
            self._add_widget(YearTF(**kwargs), box)
        elif type_ == 'payment':
            self._add_widget(PaymentTF(**kwargs), box)
        elif type_ == 'with_dropmenu':
            self._add_widget(TFWithDrop(**kwargs), box)
        else:
            self._add_widget(TFWithoutDrop(**kwargs), box)

    def _add_checkbutton(self, instr: dict, box: Layout):
        self._add_widget(GamePassedCheck(instruction=instr), box)

    def _add_label(self, instr: dict, box: Layout):
        size_hint_x = instr.setdefault('size_hint_x', 1)
        text = instr.setdefault('text', '')

        self._add_widget(Label(text=text, size_hint_x=size_hint_x), box)

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
        height = len(self.items) * 70
        height = 1000 if height > 1000 else height
        return dp(height)

    def _get_box_height(self):
        """Устанавливает высоту BoxLayout в зависимости от количества items и их заданной высоты."""
        # высота item, если она не указана
        self.default_item_height = 62
        self.default_box_height = self._get_items_height(len(self.items))

        return dp(self.default_box_height)

    def increase_box_height(self, count_items: int):
        self.ids.box.height += self._get_items_height(count_items)

    def reduce_box_height(self, count_items: int):
        self.ids.box.height -= self._get_items_height(count_items)

    def set_default_box_height(self):
        self.ids.box.height = self.default_box_height

    def _get_items_height(self, count_items: int):
        return self.default_item_height * count_items

    def update_db(self) -> bool:
        """Обрабатывает полученные из полей данные и отправляет на обновление БД.

            Return:
                success(bool) - успех добавления в БД."""

        children = self.children_

        not_fill_fields = []
        caller_field_text = ""
        data = {}

        for child in children:
            if isinstance(child, TextField):
                data_, cft, required_not_fill = self._check_text_field(child)
                data.update(data_)
                if cft:
                    caller_field_text = " ".join([caller_field_text, cft])
                if required_not_fill:
                    not_fill_fields.append(child.hint_text)

            elif isinstance(child, CheckBox):
                data.update(self._check_checkbox(child))

        if not_fill_fields:  # если есть незаполненные необходимые поля вызывает подсказку и возвращает неуспех
            not_filled = "\n".join(f"   - {text}" for text in not_fill_fields)
            open_dialog(f"The fields:\n{not_filled}\n is not filled on")
            return False

        DB.insert(self.data_table, data)

        # self.parent - BoxLayout, self.parent.parent - MDCard, self.parent.parent.parent - DialogWindow
        self.parent.parent.parent.dismiss()

        if not self.caller_:
            open_dialog("Successfully added")
            app.app_screen.table_games.update()

        else:
            self.caller_.text = caller_field_text.strip()
            open_snackbar(f"{self.caller_.name.title()} {self.caller_.text} successfully added")

        return True

    @staticmethod
    def _check_text_field(field) -> Tuple[dict, Optional[str], bool]:
        """Анализирует field и возвращает его данные.

            Parameter:
                field(TextField) - проверяемое поле.

            Return:
                data(dict) - словарь, где ключ - поле в БД, куда записываются данные с данного field,
                                        а значение - записываемые данные.
                caller_field_text(str) - строка, отображающая текст,
                                        который будет записан из этого field в родительское field.
                required_not_fill(bool) - заполненно ли field (только если field обязательно заполняется)."""

        data = {}
        caller_field_text = None
        required_not_fill = False

        if field.add_text_in_parent:
            # запоминает текст из полей, данные из которых будут записаны в вызывающем поле
            caller_field_text = field.text

        if field.required and not field.text:  # ищет необходимые не заполненные поля
            required_not_fill = True

        elif field.text and field.have_drop_menu:  # поле, имеющее всплывающее окно записываются в БД через id
            # если полей заполнения несколько, разбивает строку по пробелу
            all_conditions = field.text.split(' ') if len(field.what_fields_child_fill) > 1 else [field.text]
            conditions_dict = {}

            # составляет словарь, где ключ - поле в БД, по которому искать, значение - фильтрующее значение
            for inx, condition in enumerate(all_conditions):
                try:
                    conditions_dict[field.what_fields_child_fill[inx]] = condition
                except IndexError:
                    continue

            # запрашивает id исходя из условий
            try:
                id_ = DB.take_data("id", field.data_table, conditions_dict, one_value=True)[0]
                data[field.data_key] = id_
            except TypeError:
                open_dialog(f'Name "{field.text}" is not found in the table {field.data_table.capitalize()}')

        elif field.text:  # поля не пустые, текст из которых прямо идет в БД
            data[field.data_key] = field.text

        return data, caller_field_text, required_not_fill

    @staticmethod
    def _check_checkbox(checkbox) -> dict:
        """Анализирует checkbox и возвращает его данные.

                    Parameter:
                        checkbox(CheckBox) - проверяемый checkbox.

                    Return:
                        data(dict) - словарь, где ключ - поле в БД, куда булевое значение checkbox.active."""

        data = 1 if checkbox.active else 0

        return {checkbox.data_key: data}

    def set_next_focus(self, previous_widget):
        """Устанавливает фокус на слудующем виджете, если он не заполнен."""
        widgets = self.children_

        for inx, widget in enumerate(widgets):
            if widget is previous_widget:
                try:
                    widgets[inx + 1]
                except IndexError:
                    continue

                if not widgets[inx + 1].text and widgets[inx + 1].visible:
                    next_widget = widgets[inx + 1]
                    next_widget.focus = True
                    self.scroll_to(next_widget)


class AddGameContent(DialogContent):
    def __init__(self):
        self.data_table = "games"
        self.items = [
            [
                {'class': 'boxlayout', 'orientation': 'horizontal', 'spacing': 10},
                {'name': 'Date', 'class': 'textfield', 'type': 'date', 'data_key': 'date',
                 'notnull': True, 'size_hint_x': 0.5},
                {'name': 'Time', 'class': 'textfield', 'type': 'time', 'data_key': 'time',
                 'notnull': True, 'size_hint_x': 0.5},
                {'name': 'Stadium', 'class': 'textfield', 'type': 'with_dropmenu', 'what_fields_child_fill': ['name'],
                 'data_table': 'stadium', 'data_key': 'stadium_id', 'notnull': True},
            ],
            {'name': 'Chief referee', 'class': 'textfield', 'type': 'with_dropmenu',
             'what_fields_child_fill': ['second_name', 'first_name', 'third_name'],
             'data_table': 'referee', 'data_key': 'referee_chief', 'notnull': True},
            [
                {'class': 'expansionpanel', 'panel_text': 'Team', 'cols': 2},
                [
                    {'name': 'Home team', 'class': 'textfield', 'type': 'with_dropmenu',
                     'what_fields_child_fill': ['name'],
                     'data_table': 'team', 'data_key': 'team_home'},
                    {'name': 'Year home team', 'class': 'textfield', 'type': 'age', 'data_key': 'team_home_year',
                     'size_hint_x': 0.35},

                ],
                [
                    {'name': 'Guest team', 'class': 'textfield', 'type': 'with_dropmenu',
                     'what_fields_child_fill': ['name'],
                     'data_table': 'team', 'data_key': 'team_guest'},
                    {'name': 'Year guest team', 'class': 'textfield', 'type': 'age', 'data_key': 'team_guest_year',
                     'size_hint_x': 0.35}
                ],
                {'name': 'League', 'class': 'textfield', 'type': 'with_dropmenu', 'size_hint_x': 0.8,
                 'what_fields_child_fill': ['name'],
                 'data_table': 'league', 'data_key': 'league_id'},
            ],
            [
                {'class': 'expansionpanel', 'panel_text': 'Referee'},
                {'name': 'First referee', 'class': 'textfield', 'type': 'with_dropmenu',
                 'what_fields_child_fill': ['second_name', 'first_name', 'third_name'],
                 'data_table': 'referee', 'data_key': 'referee_first', 'visible': False},
                {'name': 'Second referee', 'class': 'textfield', 'type': 'with_dropmenu',
                 'what_fields_child_fill': ['second_name', 'first_name', 'third_name'],
                 'data_table': 'referee', 'data_key': 'referee_second', 'visible': False},
                {'name': 'Reserve referee', 'class': 'textfield', 'type': 'with_dropmenu',
                 'what_fields_child_fill': ['second_name', 'first_name', 'third_name'],
                 'data_table': 'referee', 'data_key': 'referee_reserve', 'visible': False}
            ],
            [
                {'class': 'boxlayout', 'orientation': 'horizontal', 'spacing': 10},
                {'class': 'checkbox', 'data_key': 'game_passed', 'size_hint_x': 0.1},
                {'class': 'label', 'text': 'Game passed', 'size_hint_x': 0.2},
                {'class': 'label', 'text': '', 'size_hint_x': 0.19},
                {'class': 'textfield', 'type': 'payment', 'name': 'Payment', 'data_key': 'payment', 'size_hint_x': 0.5}
            ],
        ]

        super(AddGameContent, self).__init__()


class AddRefereeContent(DialogContent):
    def __init__(self, **kwargs):
        self.data_table = "referee"
        self.items = [
            {'name': 'Second name', 'class': 'textfield', 'data_key': 'second_name', 'notnull': True,
             'add_text_in_parent': True},
            {'name': 'Fist name', 'class': 'textfield', 'data_key': 'first_name', 'notnull': True,
             'add_text_in_parent': True},
            {'name': 'Third name', 'class': 'textfield', 'data_key': 'third_name'},
            {'name': 'Phone', 'class': 'textfield', 'type': 'phone', 'data_key': 'phone'},
            {'name': 'Category', 'class': 'textfield', 'type': 'with_dropmenu', 'what_fields_child_fill': ['name'],
             'data_table': 'category', 'data_key': 'category_id'}
        ]

        super(AddRefereeContent, self).__init__(**kwargs)


class AddStadiumContent(DialogContent):
    def __init__(self, **kwargs):
        self.data_table = "stadium"
        self.items = [
            {'name': 'Name', 'class': 'textfield', 'data_key': 'name', 'notnull': True, 'add_text_in_parent': True},
            {'name': 'City', 'class': 'textfield', 'type': 'with_dropmenu', 'what_fields_child_fill': ['name'],
             'data_table': 'city', 'data_key': 'city_id', 'notnull': True},
            {'name': 'Address', 'class': 'textfield', 'data_key': 'address', 'notnull': True},
        ]

        super(AddStadiumContent, self).__init__(**kwargs)


class AddLeagueContent(DialogContent):
    def __init__(self, **kwargs):
        self.data_table = "league"
        self.items = [
            {'name': 'Name', 'class': 'textfield', 'data_key': 'name', 'notnull': True, 'add_text_in_parent': True}]

        super(AddLeagueContent, self).__init__(**kwargs)


class AddTeamContent(DialogContent):
    def __init__(self, **kwargs):
        self.data_table = "team"
        self.items = [
            {'name': 'Name', 'class': 'textfield', 'data_key': 'name', 'notnull': True, 'add_text_in_parent': True}]

        super(AddTeamContent, self).__init__(**kwargs)


class AddCategoryContent(DialogContent):
    def __init__(self, **kwargs):
        self.data_table = "category"
        self.items = [
            {'name': 'Name', 'class': 'textfield', 'data_key': 'name', 'notnull': True, 'add_text_in_parent': True}]

        super(AddCategoryContent, self).__init__(**kwargs)


class AddCityContent(DialogContent):
    def __init__(self, **kwargs):
        self.data_table = "city"
        self.items = [
            {'name': 'Name', 'class': 'textfield', 'data_key': 'name', 'notnull': True, 'add_text_in_parent': True}]

        super(AddCityContent, self).__init__(**kwargs)


class ExpansionPanel(MDExpansionPanel):
    def __init__(self, parent, **kwargs):
        self.parent_ = parent
        super(ExpansionPanel, self).__init__(**kwargs)

    @property
    def content_columns(self):
        return ceil(len(self.content.children) / self.content.cols)

    def on_open(self):
        self.parent_.increase_box_height(self.content_columns)
        self.set_children_visible()

    def on_close(self):
        self.parent_.set_default_box_height()
        self.set_children_invisible()

    def set_children_visible(self):
        for child in self.content.children:
            child.visible = True

    def set_children_invisible(self):
        for child in self.content.children:
            child.visible = True

    def set_child_focus(self, inx_child: int):
        self.content.children[inx_child].focus = True

    def _set_first_child_focus(self, dp=None):
        self.set_child_focus(-1)


class TextField(MDTextField):
    def __init__(self, **kwargs):
        self.parent_dialog = kwargs.pop('parent_')
        text = kwargs.pop('text')
        instr = kwargs.pop('instruction')
        self.size_hint_x = instr.setdefault('size_hint_x', 1)

        super(TextField, self).__init__()

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

        self.visible = instr.setdefault("visible", True)

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
            self.parent_dialog.set_next_focus(self)


class TFWithoutDrop(TextField):
    def on_text_validate(self):
        super(TextField, self).on_text_validate()
        self.change_focus = True
        self.set_next_focus()


class PhoneTF(TFWithoutDrop):
    def __init__(self, **kwargs):
        super(PhoneTF, self).__init__(**kwargs)

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


class DateTF(TFWithoutDrop):
    def __init__(self, **kwargs):
        super(DateTF, self).__init__(**kwargs)

        self.helper_text = "dd.mm.yyyy HH:MM"
        self.helper_text_mode = "persistent"

    def insert_text(self, substring, from_undo=False):
        cursor = self.cursor_col
        substring = re.sub('[^0-9]', '', substring)
        if cursor in [1, 4]:
            substring += "."
        elif cursor > 9:
            substring = ""
        return super(DateTF, self).insert_text(substring, from_undo=from_undo)

    def do_backspace(self, from_undo=False, mode='bkspc'):
        cursor = self.cursor_col
        doble_bkspc = False
        if cursor in [3, 6, 11]:
            # стираем символ два раза, чтобы удалить разделяющий символ .
            doble_bkspc = True

        if doble_bkspc:
            super(DateTF, self).do_backspace(from_undo=from_undo, mode='bkspc')
        super(DateTF, self).do_backspace(from_undo=from_undo, mode='bkspc')

    def on_text_validate(self):
        pat = "^(0?[1-9]|[12][0-9]|3[01]).(0?[0-9]|1[012]).(19|20)?[0-9]{2}$"

        if not re.match(pat, self.text):
            self.text = ""

        super(DateTF, self).on_text_validate()


class TimeTF(TFWithoutDrop):
    def __init__(self, **kwargs):
        super(TimeTF, self).__init__(**kwargs)

        self.helper_text = "HH:MM"
        self.helper_text_mode = "persistent"

    def insert_text(self, substring, from_undo=False):
        cursor = self.cursor_col
        substring = re.sub('[^0-9]', '', substring)
        if cursor == 1:
            substring += ":"
        elif cursor > 4:
            substring = ''
        return super(TimeTF, self).insert_text(substring, from_undo=from_undo)

    def do_backspace(self, from_undo=False, mode='bkspc'):
        cursor = self.cursor_col
        doble_bkspc = False
        if cursor == 3:
            # стираем символ два раза, чтобы разделяющий символ :
            doble_bkspc = True

        if doble_bkspc:
            super(TimeTF, self).do_backspace(from_undo=from_undo, mode='bkspc')
        super(TimeTF, self).do_backspace(from_undo=from_undo, mode='bkspc')

    def on_text_validate(self):
        pat = "^([01][1-9]|2[0-4]):[0-6][0-9]$"

        if not re.match(pat, self.text):
            self.text = ""

        super(TimeTF, self).on_text_validate()


class YearTF(TFWithoutDrop):
    def insert_text(self, substring, from_undo=False):
        cursor = self.cursor_col
        substring = re.sub('[^0-9]', '', substring)
        if cursor > 3:
            substring = ''
        return super(YearTF, self).insert_text(substring, from_undo=from_undo)

    def on_text_validate(self):
        pat = "^(19|20)[0-9]{2}$"

        if not re.match(pat, self.text):
            self.text = ""

        super(YearTF, self).on_text_validate()


class PaymentTF(TFWithoutDrop):
    def insert_text(self, substring, from_undo=False):
        substring = re.sub('[^0-9]', '', substring)
        return super(PaymentTF, self).insert_text(substring, from_undo=from_undo)

    def on_text_validate(self):
        pat = "^[^0][0-9]*$"

        if not re.match(pat, self.text):
            self.text = ""

        super(PaymentTF, self).on_text_validate()


class TFWithDrop(TextField):
    def __init__(self, **kwargs):
        super(TFWithDrop, self).__init__(**kwargs)
        self.have_drop_menu = True

        self.drop_menu = DropMenu()

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
        items = take_name_from_db(self.data_table)
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
        items = take_name_from_db(self.data_table)

        for item in items:
            if self.text.lower() in item[0].lower():
                matching_items.append(item)

        self.drop_menu.set_items(self, [i[0] for i in matching_items], added_item=self.text)
        self.drop_menu.update()

    def on_text_validate(self):
        """При нажатии кнопки Enter вводит текст первого item в строку или открывает меню добавления, если item'ов
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

    def drop_menu_add_data_and_close(self):
        self._drop_menu_add_data()
        self.drop_menu.dismiss()

    def _drop_menu_add_data(self, filled_fields=None):
        """Создает Dialog для добавления новых данных в БД."""
        self.add_data_dialog = DialogWindow(type_=self.data_table, filled_field=filled_fields, caller_=self)
        self.add_data_dialog.open()


class GamePassedCheck(CheckBox):
    def __init__(self, **kwargs):
        instr = kwargs.pop('instruction')
        self.size_hint_x = instr.setdefault('size_hint_x', 1)
        self.data_key = instr.setdefault('data_key')
        self.color = app.theme_cls.accent_color

        super(GamePassedCheck, self).__init__()


class MainApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Orange"
        self.theme_cls.primary_hue = "500"
        self.theme_cls.primary_darkhue = "900"
        self.theme_cls.primary_lighthue = "300"

        self.theme_cls.theme_style = "Dark"

        self.app_screen = AppScreen()

        return self.app_screen


if __name__ == "__main__":
    app = MainApp()
    DB = ConnDB()
    app.run()
