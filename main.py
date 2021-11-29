import re

from copy import deepcopy
from abc import ABC, ABCMeta, abstractmethod
from math import ceil

from typing import Optional, Any, Union, List, Tuple

from kivy.uix.widget import WidgetException, Widget
from kivymd.uix.banner import MDBanner
from kivymd.uix.snackbar import Snackbar
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.layout import Layout
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.properties import ObjectProperty
from kivy.metrics import dp

from kivy.utils import get_color_from_hex
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelOneLine
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.card import MDCard
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDFloatingActionButton, MDRaisedButton, MDTextButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.list import OneLineAvatarIconListItem, OneLineIconListItem
from kivymd.uix.snackbar import Snackbar
from kivy.uix.behaviors.focus import FocusBehavior
from kivymd.uix.behaviors import TouchBehavior
from kivy.uix.recycleview import RecycleView
from kivymd.uix.menu import MDDropdownMenu
from kivymd.app import MDApp

from database import *


def open_dialog(text):
    MDDialog(text=text).open()


def open_snackbar(text):
    Snackbar(text=text).open()


class AppScreen(BoxLayout):
    games_layout = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.add_game_dialog = ObjectProperty()
        self.games_screen = GameScreen(self.ids.games_box)

    def add_float_button_callback(self) -> None:
        """Вызывается при нажатии на MDFloatingActionButton."""
        self.games_screen.open_dialog_add_game()

    def menu_settings(self):
        print("menu")


class GameScreen:
    def __init__(self, box):
        self.add_game_dialog = ObjectProperty()

        self.box = box
        self.table_games = GamesTable()

        # при первом включении необходимо показать контент
        self._create_main_page()

    def open_dialog_add_game(self) -> None:
        """Открывает Dialog для добавления новой игры."""
        self.add_game_dialog = AddDialogWindow(type_="game")
        self.add_game_dialog.open()

    def _create_main_page(self) -> None:
        self.box.clear_widgets()
        self.box.add_widget(self.table_games)


class GamesTable(MDDataTable, TouchBehavior):
    """Класс таблицы для отображения записанных в БД игр."""

    def __init__(self):
        self.info_dialog = ObjectProperty()

        self.cell_size = dp(25)
        # ключи showed_data должны совпадать с именами атрибутов класса Game
        self.data_dict = {"date": ('Date', dp(20)),
                          "time": ('Time', dp(12)),
                          "league": ('League',),
                          "stadium": ('Stadium',),
                          "team_home": ('Home team',),
                          "team_guest": ('Guest team',),
                          "referee_chief": ('Referee',),
                          "status": ('Status', dp(30)),
                          }

        self.showed_data = ["date",
                            "time",
                            "stadium",
                            "status",
                            ]

        # проверка, если в будущем будет несколько таблиц с заданными показываемыми значениями
        # значения showed_data должны состоять из ключей data_dict
        assert all(map(lambda data: data in Game.attribute, self.showed_data)), "" \
                                                                                f"showed_data might be in {Game.attribute}"
        # копируем, чтобы при преобразовании имен данных для поиска в БД не изменять показываемые в таблицке дынные
        self.data_for_db = deepcopy(self.showed_data)

        self.elevation = 100
        self.rows_num = 10
        self.use_pagination = False
        self.check = False
        self.column_data = list(map(lambda data: self._set_column_name_and_size(data), self.showed_data))

        self.row_data = self._take_games()
        super(GamesTable, self).__init__()

        self.count_cell_in_row = len(self.column_data)

    def on_row_press(self, instance_cell_row):
        if self.list_of_games:  # без этой проверки при отсутствии игр вылетает ошибка
            # строка, в которой находится нажатая клетка
            row_cell = instance_cell_row.index // self.count_cell_in_row

            # игра, записанная в данной строке
            game = self.list_of_games[row_cell]
            self.info_dialog = InfoDialogWindow(type_="game", data_cls=game)
            self.info_dialog.open()

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
        """Возвращает преобразованные в табличные значения данные из БД."""
        games = DB.games
        return_table_data = []
        self.list_of_games = []

        for game_info in games:
            game = Game(**game_info)
            return_table_data.append(self._return_name_data_for_table(game))
            self.list_of_games.append(game)

        return return_table_data

    def _return_name_data_for_table(self, game):
        returned_list_of_data = []

        for name_data in self.showed_data:
            if name_data == "date":
                data_str = game.date.strftime("%d.%m.%Y")
            elif name_data == "time":
                data_str = game.date.strftime("%H:%M")

            elif name_data in ["league", "stadium"]:
                ls = getattr(game, name_data)
                data_str = take_one_data("name", name_data.title(), {"id": ls.id}) if ls else ""

            elif name_data in ["referee_chief", "referee_first", "referee_second", "referee_reserve"]:
                referee = getattr(game, name_data, None)
                data_str = referee.second_name if referee else ""

            elif name_data in ["team_home", "team_guest"]:
                team = getattr(game, name_data)
                data_str = take_one_data("name", "Team", {"id": team.id}) if team else ""

            elif name_data == "status":
                data_str = game.status

            else:
                game_attr = getattr(game, name_data, None)
                data_str = game_attr if game_attr else ""

            returned_list_of_data.append(data_str)

        return returned_list_of_data


class DialogWindow(MDDialog):
    def __init__(self):
        self.caller_ = None
        self.auto_dismiss = True
        self.type = "custom"
        super(DialogWindow, self).__init__()

    @abstractmethod
    def _set_content_cls(self, type_, **kwargs):
        pass


class InfoDialogWindow(DialogWindow):
    def __init__(self, **kwargs):
        """Parameters:
            type_(str) - тип создаваемого MDDialog. type_ может принимать значения:
                                                        games, referee, stadium, league, category, city, team."""

        type_ = kwargs.pop('type_')

        title = " ".join(['Info', type_])
        self.title = title

        self._set_content_cls(type_, **kwargs)
        self.buttons = [MDFlatButton(text="CANCEL", on_release=self.dismiss, theme_text_color="Custom",
                                     text_color=app.theme_cls.primary_color)]

        self.size_hint = (None, None)
        self.width = dp(500)
        self.height = dp(650)

        super(InfoDialogWindow, self).__init__()

    def _set_content_cls(self, type_, **kwargs):
        if type_ == "game":
            self.content_cls = InfoGameContent(**kwargs)
        else:
            raise AttributeError("Incorrect type_")


class AddDialogWindow(DialogWindow):
    def __init__(self, **kwargs):
        """Parameters:
                type_(str) - тип создаваемого MDDialog. type_ может принимать значения: 
                                                            games, referee, stadium, league, category, city, team."""
        type_ = kwargs.pop('type_')

        title = " ".join(['Add', type_])
        self.title = title

        self._set_content_cls(type_, **kwargs)
        self.buttons = [MDFlatButton(text="CANCEL", on_release=self.dismiss, theme_text_color="Custom",
                                     text_color=app.theme_cls.primary_color),
                        MDRaisedButton(text="ADD",
                                       on_release=self._add_button_click,
                                       md_bg_color=app.theme_cls.primary_dark)]

        super(AddDialogWindow, self).__init__()

    def _set_content_cls(self, type_, **kwargs) -> None:
        if type_ == "game":
            self.content_cls = AddGameContent()
        elif type_.startswith("referee"):
            self.content_cls = AddRefereeContent(**kwargs)
        elif type_ == "stadium":
            self.content_cls = AddStadiumContent(**kwargs)
        elif type_ == "league":
            self.content_cls = AddLeagueContent(**kwargs)
        elif type_ == "category":
            self.content_cls = AddCategoryContent(**kwargs)
        elif type_ == "city":
            self.content_cls = AddCityContent(**kwargs)
        elif type_.startswith("team"):
            self.content_cls = AddTeamContent(**kwargs)
        else:
            raise AttributeError(f"Incorrect type_ {type_}")

    def _add_button_click(self, event) -> None:
        """Вызывается при нажатии кнопки ADD"""
        success = self.content_cls.update_db()
        if success and self.caller_:
            self.caller_.parent.parent.set_focus()


class DialogContent(RecycleView):
    def __init__(self):
        self.size_hint_y = None
        self.height = self._get_height()
        super(DialogContent, self).__init__()

        self.box = BoxLayout(spacing=dp(10),
                             orientation='vertical',
                             size_hint_y=None,
                             height=self._get_box_height(),
                             )
        self.add_widget(self.box)

        self.children_ = []
        self._add_items_in_box(self.items, self.box)

    def increase_box_height(self, count_items: int):
        self.box.height += self._get_items_height(count_items)

    def reduce_box_height(self, count_items: int):
        self.box.height -= self._get_items_height(count_items)

    def set_default_box_height(self):
        self.box.height = self.default_box_height

    def _get_height(self):
        """Устанавливает высоту Content в зависимости от количества items."""
        height = len(self.items) * 70
        height = 400 if height > 400 else height
        return dp(height)

    def _get_box_height(self):
        """Устанавливает высоту BoxLayout в зависимости от количества items и их заданной высоты."""
        # высота item, если она не указана
        self.default_item_height = getattr(self, "default_item_height", 62)
        self.default_box_height = self._get_items_height(len(self.items))

        return dp(self.default_box_height)

    def _get_items_height(self, count_items: int):
        return self.default_item_height * count_items

    @abstractmethod
    def on_tf_text_validate(self, caller):
        """Вызывается при вводе текста в дочерних полях ввода."""

    def on_checkbox_active(self, checkbox, value):
        """Вызывается при установлении флажка в CheckBox."""

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
            if type(item) == tuple:
                # рекурсия с новым box'ом
                self._add_items_in_box(item, box)

            elif type(item) == dict:
                if isinstance(box, ExpansionGridLayout):
                    # скрываем виджеты, если они в ExpansionPanel
                    item["visible"] = False

                class_ = item.pop('class', '')
                type_ = item.pop('type', '')
                item.setdefault('parent', self)

                if class_ == "boxlayout":
                    new_box = MDBoxLayout(orientation=item.pop("orientation", "vertical"),
                                          spacing=dp(item.pop("spacing", 0)),
                                          padding=dp(item.pop("padding", 0))
                                          )
                    box.add_widget(new_box)
                    box = new_box

                elif class_ == "expansionpanel":
                    new_box = ExpansionGridLayout(padding=[0, 10, 0, 0],
                                                  spacing=10,
                                                  cols=item.pop("cols", 1),
                                                  adaptive_height=True)
                    panel = ExpansionPanel(self,
                                           panel_cls=MDExpansionPanelOneLine(text=item.pop("name", "")),
                                           content=new_box)
                    box.add_widget(panel)
                    box = new_box

                elif class_ == "textfield":
                    self._add_textfield(type_, box, **item)

                elif class_ == "checkbox":
                    self._add_checkbutton(box, **item)

                elif class_ == "label":
                    self._add_label(item, box)

                elif class_ == "label_with_change":
                    self._add_label_with_change(type_, box, **item)
        self._reformat_items(box)

    def _reformat_items(self, box):
        """Форматирует items (например, размер или положение) после добавления всех items."""

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
        elif type_ == 'stadium':
            self._add_widget(StadiumTF(**kwargs), box)
        elif type_ == 'referee':
            self._add_widget(RefereeTF(**kwargs), box)
        elif type_ == 'team':
            self._add_widget(TeamTF(**kwargs), box)
        elif type_ == 'league':
            self._add_widget(LeagueTF(**kwargs), box)
        elif type_ == 'category':
            self._add_widget(CategoryTF(**kwargs), box)
        elif type_ == 'city':
            self._add_widget(CityTF(**kwargs), box)
        elif type_ == 'payment':
            self._add_widget(PaymentTF(**kwargs), box)
        elif type_ == 'with_dropmenu':
            self._add_widget(TFWithDrop(**kwargs), box)
        else:
            self._add_widget(TFWithoutDrop(**kwargs), box)

    def _add_checkbutton(self, box: Layout, **kwargs):
        value = 'down' if hasattr(self, 'game') and getattr(self.game, kwargs.get('data_key')) else 'normal'
        self._add_widget(GameCheck(**kwargs, state=value), box)

    def _add_label(self, instr: dict, box: Layout):
        size_hint_x = instr.pop('size_hint_x', 1)
        text = instr.pop('text', '')

        colored = {}
        if instr.pop('colored', False):
            colored = {'theme_text_color': "Custom", 'text_color': app.theme_cls.primary_color}
            # TODO: add several colors in text color

        self._add_widget(MDLabel(text=text, size_hint_x=size_hint_x, **colored), box)

    def _add_label_with_change(self, type_, box: Layout, **kwargs):
        if type_ == "date":
            self._add_widget(DataLWC(game=self.game, **kwargs), box)
        elif type_ == "time":
            self._add_widget(TimeLWC(game=self.game, **kwargs), box)
        elif type_ == "stadium":
            self._add_widget(StadiumLWC(game=self.game, **kwargs), box)
        elif type_ == "team":
            self._add_widget(TeamLWC(game=self.game, **kwargs), box)
        elif type_ == "year":
            year_lwc = YearLWC(game=self.game, **kwargs)
            if year_lwc.is_filled():
                self._add_widget(year_lwc, box)
        elif type_ == "referee":
            self._add_widget(RefereeLWC(game=self.game, **kwargs), box)
        else:
            raise TypeError(f"Incorrect type: {type_}")

    def _add_widget(self, widget, box: Layout):
        box.add_widget(widget)
        self.children_.append(widget)


class InfoDialogContent(DialogContent):
    def __init__(self, **kwargs):
        self.default_item_height = 70
        super(InfoDialogContent, self).__init__()

    def on_tf_text_validate(self, caller):
        caller.parent.parent.click_add()

    def on_checkbox_active(self, checkbox, value):
        data = 1 if value else 0
        DB.update('Games', {checkbox.data_key: data}, {'id': self.game.id_in_db})
        app.app_screen.games_screen.table_games.update()

    def _reformat_items(self, box):
        self._clear_empty_box(box)
        for item in self.children_:
            try:
                item.label_name.width = item.label_width
            except AttributeError:
                pass

    def _clear_empty_box(self, box):
        if len(box.children) == 0:
            self.box.remove_widget(box)


class AddDialogContent(DialogContent):
    def __init__(self, **kwargs):
        """Parameters:
                        caller_ (Any) - объект, создавший и вызвавший этот класс.
                        filled_field (dict[str, str]) - словарь уже заполненных полей, где
                                              ключом является название TextField, в которое нужно добавить текст, а
                                              значением является добавляемый текст."""

        self.caller_ = kwargs.pop('caller_', None)
        filled_field = kwargs.pop('filled_field', {})

        super(AddDialogContent, self).__init__()
        self._filled_children_field(filled_field)

    def _filled_children_field(self, filled_field: dict):
        for widget in self.children_:
            if isinstance(widget, TextField) and widget.name_ in filled_field:
                widget.text = filled_field[widget.name_]

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
                data_, cft, required_not_fill = self._check_text_fields(child)
                data.update(data_)
                if cft:
                    caller_field_text = " ".join([caller_field_text, cft])
                if required_not_fill:
                    not_fill_fields.append(child.hint_text)

            elif isinstance(child, GameCheck):
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
            app.app_screen.games_screen.table_games.update()

        else:
            self.caller_.text = caller_field_text.strip()
            open_snackbar(f"{self.caller_.hint_text.title()} {self.caller_.text} successfully added")

        return True

    def on_tf_text_validate(self, caller):
        """Устанавливает фокус на следующем виджете, если он не заполнен и виден на экране."""
        widgets = self.children_
        start_inx = widgets.index(caller)

        for inx, widget in enumerate(widgets[start_inx:]):
            inx += start_inx

            try:
                widgets[inx + 1]
            except IndexError:
                continue

            if isinstance(widgets[inx + 1], TextField) \
                    and widgets[inx + 1].visible and not widgets[inx + 1].text:
                next_widget = widgets[inx + 1]
                next_widget.focus = True
                self.scroll_to(next_widget)
                break

    @staticmethod
    def _check_text_fields(field) -> Tuple[dict, Optional[str], bool]:
        """Анализирует field и возвращает его данные.

            Parameter:
                field(TextField) - проверяемое поле.

            Return:
                data(dict) - словарь, где ключ - поле в БД, куда записываются данные с данного field,
                                        а значение - записываемые данные.
                caller_field_text(str) - строка, отображающая текст,
                                        который будет записан из этого field в родительское field.
                required_not_fill(bool) - заполненно ли field (только если field обязательно заполняется)."""

        data = None
        # запоминает текст из полей, данные из которых будут записаны в вызывающем родительском поле
        caller_field_text = field.text if field.add_text_in_parent else None

        # заполненно ли обязательное поле
        required_not_fill = field.required_not_fill()

        # записывающиеся в БД данные
        if field.text:
            data = field.return_data()

        data = data if data else {}

        return data, caller_field_text, required_not_fill

    @staticmethod
    def _check_checkbox(checkbox) -> dict:
        """Анализирует checkbox и возвращает его данные.

                    Parameter:
                        checkbox(CheckBox) - проверяемый checkbox.

                    Return:
                        data(dict) - словарь, где ключ - поле в БД, куда булевое значение checkbox.active."""

        return checkbox.return_data()


class InfoGameContent(InfoDialogContent):
    def __init__(self, **kwargs):
        self.game = kwargs["data_cls"]
        self.items = (
            (
                {'class': 'boxlayout', 'orientation': 'horizontal', 'spacing': 10},
                {'class': 'checkbox', 'data_key': 'game_passed', 'size_hint_x': 0.1},
                {'class': 'label', 'text': 'Game passed', 'size_hint_x': 0.2, 'colored': True},
                {'class': 'label', 'size_hint_x': 0.2},
                {'class': 'checkbox', 'data_key': 'pay_done', 'size_hint_x': 0.1},
                {'class': 'label', 'text': 'Pay done', 'size_hint_x': 0.2, 'colored': True},
            ),
            (
                {'class': 'boxlayout', 'orientation': 'horizontal', 'spacing': 10},
                {'name': 'Date', 'class': 'label_with_change', 'type': 'date'},
                {'name': 'Time', 'class': 'label_with_change', 'type': 'time'},
            ),
            {'name': 'Stadium', 'class': 'label_with_change', 'type': 'stadium'},
            (
                {'class': 'boxlayout', 'orientation': 'horizontal', 'spacing': 10},
                {'name': 'T. home', 'class': 'label_with_change', 'type': 'team', 'data_key': 'team_home',
                 'halign': 'center'},
                {'text': 'vs.', 'class': 'label', 'size_hint_x': 0.2},
                {'name': 'T. guest', 'class': 'label_with_change', 'type': 'team', 'data_key': 'team_guest',
                 'halign': 'center'},
            ),
            (
                {'class': 'boxlayout', 'orientation': 'horizontal', 'padding': 0},
                {'name': 'T.H. year', 'class': 'label_with_change', 'type': 'year', 'data_key': 'team_home',
                 'halign': 'center'},
                {'name': 'T.G. year', 'class': 'label_with_change', 'type': 'year', 'data_key': 'team_guest',
                 'halign': 'center'},
            ),
            {'name': 'R. chief', 'class': 'label_with_change', 'type': 'referee', 'data_key': 'referee_chief'},
            {'name': 'R. first', 'class': 'label_with_change', 'type': 'referee', 'data_key': 'referee_first'},
            {'name': 'R. second', 'class': 'label_with_change', 'type': 'referee',
             'data_key': 'referee_second'},
            {'name': 'R. reserve', 'class': 'label_with_change', 'type': 'referee',
             'data_key': 'referee_reserve'},
        )

        super(InfoGameContent, self).__init__(**kwargs)


class AddGameContent(AddDialogContent):
    def __init__(self):
        self.data_table = "games"
        self.items = (
            (
                {'class': 'boxlayout', 'orientation': 'horizontal', 'spacing': 10},
                {'name': 'Date', 'class': 'textfield', 'type': 'date', 'notnull': True, 'size_hint_x': 0.5},
                {'name': 'Time', 'class': 'textfield', 'type': 'time', 'notnull': True, 'size_hint_x': 0.5},
                {'name': 'Stadium', 'class': 'textfield', 'type': 'stadium', 'notnull': True},
            ),
            {'name': 'Chief referee', 'class': 'textfield', 'type': 'referee', 'data_key': 'referee_chief',
             'notnull': True},
            (
                {'class': 'expansionpanel', 'name': 'Team', 'cols': 2},
                (
                    {'name': 'Home team', 'class': 'textfield', 'type': 'team', 'data_key': 'team_home'},
                    {'name': 'Age home team', 'class': 'textfield', 'type': 'age', 'data_key': 'team_home_year',
                     'size_hint_x': 0.35},

                ),
                (
                    {'name': 'Guest team', 'class': 'textfield', 'type': 'team', 'data_key': 'team_guest'},
                    {'name': 'Age guest team', 'class': 'textfield', 'type': 'age', 'data_key': 'team_guest_year',
                     'size_hint_x': 0.35}
                ),
                {'name': 'League', 'class': 'textfield', 'type': 'league', 'size_hint_x': 0.8},
            ),
            (
                {'class': 'expansionpanel', 'name': 'Referee'},
                {'name': 'First referee', 'class': 'textfield', 'type': 'referee',
                 'data_key': 'referee_first'},
                {'name': 'Second referee', 'class': 'textfield', 'type': 'referee',
                 'data_key': 'referee_second'},
                {'name': 'Reserve referee', 'class': 'textfield', 'type': 'referee',
                 'data_key': 'referee_reserve'}
            ),
            (
                {'class': 'boxlayout', 'orientation': 'horizontal', 'spacing': 10},
                {'class': 'checkbox', 'data_key': 'game_passed', 'size_hint_x': 0.1},
                {'class': 'label', 'text': 'Game passed', 'size_hint_x': 0.3},
                {'class': 'label', 'size_hint_x': 0.69}
            ),
            (
                {'class': 'boxlayout', 'orientation': 'horizontal', 'spacing': 10},
                {'class': 'checkbox', 'data_key': 'pay_done', 'size_hint_x': 0.1},
                {'class': 'label', 'text': 'Pay done', 'size_hint_x': 0.3},
                {'class': 'label', 'size_hint_x': 0.19},
                {'class': 'textfield', 'type': 'payment', 'name': 'Payment', 'data_key': 'payment', 'size_hint_x': 0.5}
            )
        )

        super(AddGameContent, self).__init__()


class AddRefereeContent(AddDialogContent):
    def __init__(self, **kwargs):
        self.data_table = "referee"
        self.items = (
            {'name': 'Second name', 'class': 'textfield', 'data_key': 'second_name', 'notnull': True,
             'add_text_in_parent': True},
            {'name': 'Fist name', 'class': 'textfield', 'data_key': 'first_name', 'add_text_in_parent': True},
            {'name': 'Third name', 'class': 'textfield', 'data_key': 'third_name'},
            {'name': 'Phone', 'class': 'textfield', 'type': 'phone', 'data_key': 'phone'},
            {'name': 'Category', 'class': 'textfield', 'type': 'category'}
        )

        super(AddRefereeContent, self).__init__(**kwargs)


class AddStadiumContent(AddDialogContent):
    def __init__(self, **kwargs):
        self.data_table = "stadium"
        self.items = (
            {'name': 'Name', 'class': 'textfield', 'data_key': 'name', 'notnull': True, 'add_text_in_parent': True},
            {'name': 'City', 'class': 'textfield', 'type': 'city', 'notnull': True},
            {'name': 'Address', 'class': 'textfield', 'data_key': 'address'},
        )

        super(AddStadiumContent, self).__init__(**kwargs)


class AddLeagueContent(AddDialogContent):
    def __init__(self, **kwargs):
        self.data_table = "league"
        self.items = (
            {'name': 'Name', 'class': 'textfield', 'data_key': 'name', 'notnull': True, 'add_text_in_parent': True})

        super(AddLeagueContent, self).__init__(**kwargs)


class AddTeamContent(AddDialogContent):
    def __init__(self, **kwargs):
        self.data_table = "team"
        self.items = (
            {'name': 'Name', 'class': 'textfield', 'data_key': 'name', 'notnull': True, 'add_text_in_parent': True})

        super(AddTeamContent, self).__init__(**kwargs)


class AddCategoryContent(AddDialogContent):
    def __init__(self, **kwargs):
        self.data_table = "category"
        self.items = (
            {'name': 'Name', 'class': 'textfield', 'data_key': 'name', 'notnull': True, 'add_text_in_parent': True})

        super(AddCategoryContent, self).__init__(**kwargs)


class AddCityContent(AddDialogContent):
    def __init__(self, **kwargs):
        self.data_table = "city"
        self.items = (
            {'name': 'Name', 'class': 'textfield', 'data_key': 'name', 'notnull': True, 'add_text_in_parent': True})

        super(AddCityContent, self).__init__(**kwargs)


class ExpansionPanel(MDExpansionPanel):
    def __init__(self, parent, **kwargs):
        self.parent_ = parent
        self.name_ = kwargs['panel_cls'].text
        super(ExpansionPanel, self).__init__(**kwargs)

    def __repr__(self):
        return f"{__class__.__name__} of {self.name_!r}"

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
            child.visible = False

    def set_child_focus(self, inx_child: int):
        self.content.children[inx_child].focus = True


class ExpansionGridLayout(MDGridLayout):
    """Класс создан для разделения отдельного GridLayout и в составе ExpansionPanel."""


class DropMenu(MDDropdownMenu):
    def __init__(self, parent_):
        self.width_mult = dp(4)
        self.max_height = dp(250)
        self.name_ = parent_.name_

        super(DropMenu, self).__init__()

    def __repr__(self):
        return f"{__class__.__name__} of {self.name_!r}"

    def set_items(self, text_list, list_items: list, added_item=None):
        """Добавляет items в DropMenu."""
        if list_items:
            self.items = [{"text": f"{item}",
                           "viewclass": "OneLineListItem",
                           "on_release": lambda x=f"{item}": text_list.add_item_in_text_input(x),
                           } for item in list_items]
        else:
            self.items = [{"text": f'Add "{added_item}" in base',
                           "viewclass": "OneLineListItem",
                           "on_release": lambda: text_list.drop_menu_add_data()}]

    def update(self):
        self.set_menu_properties()
        if not self.parent:
            self.open()


class TextField(MDTextField):
    def __init__(self, name, **kwargs):
        self.parent_ = kwargs.pop('parent_', None)
        text = kwargs.pop('text', '')
        self.visible = kwargs.pop("visible", True)

        super(TextField, self).__init__()

        self.hint_text = name
        self.size_hint_x = kwargs.pop('size_hint_x', 1)

        self.set_text(self, text)

        self.required = kwargs.pop('notnull', False)
        self.helper_text_mode = "on_error"

        self.add_text_in_parent = kwargs.pop('add_text_in_parent', False)

        self.have_drop_menu = False

        self.check_pattern = "^.+$"

    def __repr__(self):
        return f"{__class__.__name__} of {self.hint_text!r}"

    def check_input(self):
        """Проверяет введеный текст."""
        if not re.match(self.check_pattern, self.text):
            return False
        return True

    def on_focus_(self):
        pass

    def on_double_tap(self):
        self.text = ''

    def on_cursor_(self):
        pass

    def on_text_validate(self):
        """После ввода текста устанавливает фокус на следующем поле ввода."""
        super(TextField, self).on_text_validate()
        self.parent_.on_tf_text_validate(self)

    def return_data(self) -> Optional[dict]:
        """Возвращает корректные данные для взаимодействия с БД (текст или id)."""
        if self.required and not self.text:
            return
        else:
            return self.return_data_()

    @abstractmethod
    def return_data_(self) -> dict:
        """Возвращает данные для взаимодействия с БД (текст или id)."""

    def required_not_fill(self):
        return all([self.required, not self.text])


class TFWithDrop(TextField):
    def __init__(self, **kwargs):
        super(TFWithDrop, self).__init__(**kwargs)
        self.add_data_dialog = ObjectProperty()
        self.have_drop_menu = True

        assert hasattr(self, "name_"), "TFWithDrop must have attribute 'name_'"
        self.drop_menu = DropMenu(parent_=self)

    def add_item_in_text_input(self, text_item):
        self.text = text_item
        self.drop_menu.dismiss()
        super(TFWithDrop, self).on_text_validate()

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
            self.drop_menu_add_data()
            self.text = ''

        else:
            self.text = text_dropmenu

        self.drop_menu.dismiss()
        super(TFWithDrop, self).on_text_validate()

    def _make_dict_filled_field_in_children(self) -> dict:
        """Создает словарь заволненных полей.
            Ключи - self.what_fields_child_fill,
            Значения - self.text."""
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

    def drop_menu_add_data(self):
        """Создает Dialog для добавления новых данных в БД."""
        filled_fields = self._make_dict_filled_field_in_children()
        self.drop_menu.dismiss()

        self.add_data_dialog = AddDialogWindow(type_=self.name_, filled_field=filled_fields, caller_=self)
        self.add_data_dialog.open()

    def return_data_(self):
        # поле, имеющее всплывающее окно записываются в БД через id
        # если полей заполнения несколько, разбивает строку по пробелу
        all_conditions_values = self.text.split(' ') if len(self.what_fields_child_fill) > 1 else [self.text]
        conditions_dict = {}

        # составляет словарь, где ключ - поле в БД, по которому искать, значение - фильтрующее значение
        for inx, condition in enumerate(all_conditions_values):
            try:
                conditions_dict[self.what_fields_child_fill[inx]] = condition
            except IndexError:
                continue

        # запрашивает id исходя из условий
        try:
            id_ = take_one_data("id", self.data_table, conditions_dict)
            return {self.data_key: id_}
        except TypeError:
            open_dialog(f'Name "{self.text}" is not found in the table {self.data_table.capitalize()}')


class TFWithoutDrop(TextField):
    def __init__(self, **kwargs):
        super(TFWithoutDrop, self).__init__(**kwargs)
        self.name_ = self.data_key = kwargs.get("data_key")
        assert hasattr(self, "name_"), "TFWithoutDrop must have attribute 'name_'"

    def return_data_(self):
        return {self.data_key: self.text}


class PhoneTF(TFWithoutDrop):
    def __init__(self, **kwargs):
        super(PhoneTF, self).__init__(**kwargs)

        self.check_pattern = "^(\+7|8)\([0-9]{3}\)[0-9]{3}(-[0-9]{2}){2}$"
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
        self.check_input()
        super(PhoneTF, self).on_text_validate()

    def return_data_(self):
        digits = re.sub("\D", "", self.text)
        return {self.data_key: int(digits)}


class DateTF(TFWithoutDrop):
    def __init__(self, **kwargs):
        super(DateTF, self).__init__(**kwargs)

        self.name_ = self.data_key = 'date'
        self.check_pattern = "^(0?[1-9]|[12][0-9]|3[01]).(0?[0-9]|1[012]).(19|20)?[0-9]{2}$"
        self.helper_text = "DD.MM.YYYY"
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
        self.check_input()
        super(DateTF, self).on_text_validate()

    def return_data_(self):
        day, month, year = map(lambda text: re.sub("\D", "", text), self.text.split("."))
        _data = {'day': int(day), 'month': int(month), 'year': int(year)}
        date = {}
        for i in _data:
            date[i] = _data[i]

        return date


class TimeTF(TFWithoutDrop):
    def __init__(self, **kwargs):
        super(TimeTF, self).__init__(**kwargs)

        self.name_ = self.data_key = 'time'
        self.check_pattern = "^([01][1-9]|2[0-4]):[0-6][0-9]$"
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
        self.check_input()
        super(TimeTF, self).on_text_validate()

    def return_data_(self):
        digits = re.sub("\D", "", self.text)
        return {self.data_key: int(digits)}


class YearTF(TFWithoutDrop):
    def __init__(self, **kwargs):
        super(YearTF, self).__init__(**kwargs)

        self.name_ = self.data_key = kwargs.pop("data_key")
        self.check_pattern = "^(19|20)[0-9]{2}$"

    def insert_text(self, substring, from_undo=False):
        cursor = self.cursor_col
        substring = re.sub('[^0-9]', '', substring)
        if cursor > 3:
            substring = ''
        return super(YearTF, self).insert_text(substring, from_undo=from_undo)

    def on_text_validate(self):
        self.check_input()
        super(YearTF, self).on_text_validate()


class StadiumTF(TFWithDrop):
    def __init__(self, **kwargs):
        self.name_ = "stadium"
        super(StadiumTF, self).__init__(**kwargs)

        self.data_key = "stadium_id"
        self.data_table = "Stadium"
        self.what_fields_child_fill = ['name']


class RefereeTF(TFWithDrop):
    def __init__(self, **kwargs):
        self.name_ = self.data_key = kwargs.pop('data_key')
        super(RefereeTF, self).__init__(**kwargs)

        self.data_table = "Referee"
        self.what_fields_child_fill = ['second_name', 'first_name', 'third_name']


class TeamTF(TFWithDrop):
    def __init__(self, **kwargs):
        self.name_ = self.data_key = kwargs.pop('data_key')
        super(TeamTF, self).__init__(**kwargs)

        self.data_table = "Team"
        self.what_fields_child_fill = ['name']


class LeagueTF(TFWithDrop):
    def __init__(self, **kwargs):
        self.name_ = "league"
        super(LeagueTF, self).__init__(**kwargs)

        self.data_key = "league_id"
        self.data_table = "League"
        self.what_fields_child_fill = ['name']


class CategoryTF(TFWithDrop):
    def __init__(self, **kwargs):
        self.name_ = "category"
        super(CategoryTF, self).__init__(**kwargs)

        self.data_key = "category_id"
        self.data_table = "Category"
        self.what_fields_child_fill = ['name']


class CityTF(TFWithDrop):
    def __init__(self, **kwargs):
        self.name_ = "city"
        super(CityTF, self).__init__(**kwargs)

        self.data_key = "city_id"
        self.data_table = "City"
        self.what_fields_child_fill = ['name']


class PaymentTF(TFWithoutDrop):
    def __init__(self, **kwargs):
        super(PaymentTF, self).__init__(**kwargs)

        self.name_ = self.data_key = 'payment'
        self.check_pattern = "^[^0][0-9]*$"

    def insert_text(self, substring, from_undo=False):
        substring = re.sub('[^0-9]', '', substring)
        return super(PaymentTF, self).insert_text(substring, from_undo=from_undo)

    def on_text_validate(self):
        self.check_input()
        super(PaymentTF, self).on_text_validate()


class GameCheck(CheckBox):
    def __init__(self, **kwargs):
        self.parent_ = kwargs.pop('parent')
        self.name_ = self.data_key = kwargs.pop("data_key")
        self.size_hint_x = kwargs.pop('size_hint_x', 1)
        self.bind(active=self.on_checkbox_active)
        # self.color = app.theme_cls.primary_color

        super(GameCheck, self).__init__(**kwargs)

    def __repr__(self):
        return f"{__class__.__name__} of {self.name_!r}"

    def check(self):
        pass

    def return_data(self):
        data = 1 if self.active else 0
        return {self.data_key: data}

    def on_checkbox_active(self, checkbox, value):
        self.parent_.on_checkbox_active(checkbox, value)


class LabelWithChange(BoxLayout, TouchBehavior):
    def __init__(self, game=None, **kwargs):
        self.id = 'box'
        self.orientation = "horizontal"
        self.padding = dp(10)
        self.game = game
        self.name_ = kwargs.pop("name", '')

        self.height = dp(5)
        super(LabelWithChange, self).__init__()

        self.label_box = ObjectProperty()
        self.label_name = ObjectProperty()
        self.label_value = ObjectProperty()
        self.text_field = ObjectProperty()
        self.btn_change = ObjectProperty()
        self.btn_add = ObjectProperty()
        self.btn_cancel = ObjectProperty()
        self.widgets_mode_view = ObjectProperty()
        self.widgets_mode_change = ObjectProperty()

    def __repr__(self):
        return f"{__class__.__name__} of {self.name_!r}"

    def show(self, without_label: bool = False):
        self._init_textfield()
        self.label_box = BoxLayout(orientation='horizontal')
        if not without_label:
            self.label_name = MDLabel(text=f"{self.name_}: ",
                                      halign='left',
                                      size_hint_x=None,
                                      # width=self._get_width_from_len(f"{self.name_}: "),
                                      theme_text_color="Custom",
                                      text_color=app.theme_cls.primary_color,
                                      )
            self.label_box.add_widget(self.label_name)

        self.label_value = MDLabel(text=f"{self.value}",
                                   halign='left',
                                   )

        self.label_box.add_widget(self.label_value)

        self.change_mode("view")
        self._update_max_label_width(f"{self.name_} +: ")

    def is_filled(self):
        return bool(self.value)

    def _init_textfield(self):
        self.box_tf = BoxLayout(orientation='horizontal')
        self.btn_add = MDIconButton(icon='check',
                                    on_release=self.click_add,
                                    theme_text_color="Custom",
                                    text_color=colors['Green']['700'],
                                    )
        self.btn_cancel = MDIconButton(icon='window-close',
                                       on_release=self.click_cancel,
                                       theme_text_color="Custom", text_color=colors['Red']['700'],
                                       )
        for widget in [self.btn_cancel, self.text_field, self.btn_add]:
            self.box_tf.add_widget(widget)

    label_width = 0

    @classmethod
    def _update_max_label_width(cls, text: str) -> float:
        """Обновляет ширину Label до максимальной с каждым созданием класса.

                Parameters:
                    text(str) - текст Label."""

        text_width = dp(len(text) * 6)
        if text_width > LabelWithChange.label_width:
            LabelWithChange.label_width = text_width
        return LabelWithChange.label_width

    @staticmethod
    def _get_width_from_len(text):
        """Возвращает ширину виджета по количеству символов."""
        return dp(len(text) * 8)

    def on_long_touch(self, touch, *args):
        self.change_mode("change")
        self.text_field.text = ''

    def change_mode(self, mode: str):
        assert mode in ["change", "view"]
        self.clear_widgets()

        if mode == "change":
            Clock.schedule_once(self._focus_textfield, 0.5)
            self.add_widget(self.box_tf)
        elif mode == "view":
            self.add_widget(self.label_box)
        else:
            raise AttributeError("mode must be 'change' or 'view'")

    def _focus_textfield(self, dp=None):
        self.text_field.focus = True

    def click_change(self, event=None):
        self.change_mode("change")

    def click_add(self, event=None):
        if not self.text_field.check_input() or all([self.text_field.required, not self.text_field.text]):
            self.text_field.text = ''
        else:
            DB.update("Games", self.text_field.return_data(), {"id": self.game.id_in_db})
            self.label_value.text = self.text_field.text
            self.change_mode('view')
            app.app_screen.games_screen.table_games.update()

    def click_cancel(self, event=None):
        self.change_mode("view")


class DataLWC(LabelWithChange):
    def __init__(self, **kwargs):
        super(DataLWC, self).__init__(**kwargs)
        self.text_field = DateTF(notnull=True, **kwargs)
        self.value = self.game.date.strftime("%d.%m.%Y")
        self.show()


class TimeLWC(LabelWithChange):
    def __init__(self, **kwargs):
        super(TimeLWC, self).__init__(**kwargs)
        self.text_field = TimeTF(notnull=True, **kwargs)
        self.value = self.game.date.strftime("%H:%M")
        self.show()


class StadiumLWC(LabelWithChange):
    def __init__(self, **kwargs):
        super(StadiumLWC, self).__init__(**kwargs)
        self.text_field = StadiumTF(notnull=True, **kwargs)
        self.value = self.game.stadium.name
        self.show()


class LeagueLWC(LabelWithChange):
    def __init__(self, **kwargs):
        super(LeagueLWC, self).__init__(**kwargs)
        self.text_field = LeagueTF(notnull=True, **kwargs)
        self.value = self.game.league.name if self.game.league else ''
        self.show()


class TeamLWC(LabelWithChange):
    def __init__(self, **kwargs):
        super(TeamLWC, self).__init__(**kwargs)
        self.text_field = TeamTF(notnull=True, **kwargs)
        team = getattr(self.game, kwargs.pop('data_key'))
        self.value = team.name if team and team.name else ''
        self.show(without_label=True)
        if self.is_filled():
            self.label_value.halign = kwargs.pop('halign', 'left')


class YearLWC(LabelWithChange):
    def __init__(self, **kwargs):
        super(YearLWC, self).__init__(**kwargs)
        self.text_field = YearTF(notnull=True, **kwargs)
        team = getattr(self.game, kwargs.pop('data_key'))
        self.value = team.age if getattr(team, 'age', None) else ''
        self.show(without_label=True)
        if self.is_filled():
            self.label_value.halign = kwargs.pop('halign', 'left')
        else:
            del self


class RefereeLWC(LabelWithChange):
    def __init__(self, **kwargs):
        super(RefereeLWC, self).__init__(**kwargs)
        self.text_field = RefereeTF(**kwargs)
        referee = getattr(self.game, kwargs.pop('data_key'))
        self.value = referee.get_name('second', 'first', 'third') if referee else ''
        self.show()


class MainApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Orange"
        self.theme_cls.primary_hue = "800"
        self.theme_cls.primary_darkhue = "900"
        self.theme_cls.primary_lighthue = "300"

        self.theme_cls.theme_style = "Dark"

        self.app_screen = AppScreen()

        return self.app_screen


if __name__ == "__main__":
    app = MainApp()
    DB = ConnDB()
    app.run()
