import psycopg2
from psycopg2 import sql
from typing import Optional, Union, Any, Dict, List
from kivymd.color_definitions import colors

from config import Passwords


def _request(query, mode: str, values: Union[tuple, list] = None,  one_value: bool = False):
    conn = psycopg2.connect(dbname='referee',
                            user=Passwords.user,
                            password=Passwords.password,
                            host='localhost',
                            )
    cursor = conn.cursor()

    def select():
        if one_value:
            return cursor.fetchone()
        else:
            return cursor.fetchall()

    def commit():
        conn.commit()

    try:
        if values:
            cursor.execute(query, values)
        else:
            cursor.execute(query)

        if mode == "select":
            return select()
        elif mode in ["insert",
                      "delete",
                      "commit",
                      "update",
                      ]:
            commit()
        else:
            raise AttributeError("Attribute 'mode' must be select, insert, delete or commit")

    finally:
        cursor.close()
        conn.close()


def _convert_order(order) -> str:
    order_query = []
    for key in order:
        assert key in ["ASC", "DESC"], "order keys must be 'ASC' or 'DESC'"
        assert type(order[key]) == list, "order value type must be list"

        order_query.append(f"{', '.join(order[key])} {key}")
    return ", ".join(order_query)


def games() -> List[dict]:
    """Возвращает все данные по всем играм в виде списка словарей."""

    column_names = ("id",
                    "league_id",
                    "stadium_id",
                    "team_home",
                    "team_guest",
                    "referee_chief",
                    "referee_first",
                    "referee_second",
                    "referee_reserve",
                    "game_passed",
                    "payment",
                    "pay_done",
                    "datetime",
                    "team_home_year",
                    "team_guest_year",
                    )

    query = 'SELECT * FROM public."Games"'

    games_dict_of_kwargs = []
    return_select_request = _request(query, "select")
    for r in return_select_request:
        games_dict_of_kwargs.append(dict(zip(column_names, r)))

    return games_dict_of_kwargs


def take_name_order(table: str) -> Union[str, list]:
    """Возвращает колонку name в таблице table в алфавитном порядке.

        Parameter:
            table(str) - имя таблицы."""

    if table == "Referee":
        query = sql.SQL(
            '''SELECT second_name, first_name, third_name
                 FROM {}
                ORDER BY second_name, first_name, third_name
            ''').format(sql.Identifier("Referee"))
    else:
        query = sql.SQL("SELECT name FROM {} ORDER BY name ASC").format(
            sql.Identifier(table))

    return _request(query, "select")


def take_all_by_id(table: str, id_: int):
    """Возвращает имя из таблицы table по заданному id."""
    query = sql.SQL("SELECT * FROM {} WHERE id=%s").format(
        sql.Identifier(table)
    )

    return _request(query, "select", values=(id_,), one_value=True)[1:]  # except id


def take_id_by_condition(table: str, condition: dict) -> int:
    query = sql.SQL("SELECT id FROM {} WHERE {}").format(
        sql.Identifier(table),
        _request_from_conditions(condition.keys(), " AND ")
    )
    return _request(query, "select", list(condition.values()), one_value=True)[0]


def _request_from_conditions(condition, sep: str = ", "):
    """Создает часть запроса проверки на равенство из списка и сепаратора.

        Пример:
            _request_from_conditions(['foo', 'bar'], ' AND ') -> 'foo=%s AND bar=%s."""
    # список всех пар ключей и их значений
    pairs = []
    for key in condition:
        pairs.append(
            sql.SQL("=").join(
                (sql.Identifier(key),
                 sql.Placeholder(),)
            )
        )

    # соединяем все пары в один запрос
    where_query = sql.SQL(sep).join(pairs)
    return where_query


def _add_where_construction(query, conditions: dict, values: list):
    if conditions:
        query = sql.SQL(" ").join((
            query,
            sql.SQL("WHERE"),
            _request_from_conditions(conditions.keys(), " AND "),
        ))  # first bracket - call func, second - make tuple

        values.append(*conditions.values())
        return query


def insert(table: str, data: dict) -> None:
    """Добавляет в БД заданные данные."""
    query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, data.keys())),
        sql.SQL(", ").join(sql.Placeholder() * len(data))
    )

    print(query, data.values())
    _request(query, "insert", list(data.values()))


def update(table: str, data: dict, conditions: dict):
    """Обновляет БД."""
    values = list(data.values())

    query = sql.SQL("UPDATE {} SET {}").format(
        sql.Identifier(table),
        _request_from_conditions(data.keys(), ", "),
    )
    query = _add_where_construction(query, conditions, values)

    print(query, values)
    _request(query, "update", values)


def delete(table: str, conditions: dict, columns: list = None):
    values = []
    query = sql.SQL("DELETE {} FROM {}").format(
        sql.SQL(", ").join(columns) if columns else sql.SQL(""),
        sql.Identifier(table),
    )

    query = _add_where_construction(query, conditions, values)

    print(query, values)
    _request(query, "delete", values)


class Game:
    """Класс, определяющий игру из БД."""
    # dict of status icon, color, name
    status_icn = {"not_passed": ("calendar-alert", colors["Red"]["800"], "Не проведена"),
                  "passed": ("calendar-check", colors["Yellow"]["300"], "Проведена"),
                  "pay_done": ("calendar-check", colors["Green"]["700"], "Оплачено"),
                  }
    # list future attribute
    attribute = ("id_in_db",
                 "league", "date", "time", "stadium",
                 "team_home",
                 "team_home_year",
                 "team_guest",
                 "team_guest_year",
                 "referee_chief",
                 "referee_first",
                 "referee_second",
                 "referee_reserve", "game_passed",
                 "pay_done",
                 "payment",
                 "status",
                 )

    def __init__(self, **kwargs):
        self.id_in_db = kwargs.pop("id", None)
        self.referee_chief = self.referee_first = self.referee_second = self.referee_reserve \
            = self.league = self.stadium = self.team_home = self.team_guest = None

        self.date = kwargs.pop("datetime")

        self._set_referee(**kwargs)
        self._set_league(**kwargs)
        self._set_stadium(**kwargs)
        self._set_team(**kwargs)

        self.game_passed = bool(kwargs.pop("game_passed", None))
        self.pay_done = bool(kwargs.pop("pay_done", None))
        self.payment = kwargs.pop("payment", None)
        self.status_key = self._get_status(self.game_passed, self.pay_done)
        self.status = self.status_icn[self.status_key]

    def __repr__(self):
        return f"{__class__.__name__} with id {self.id_in_db!r}"

    def _set_referee(self, **kwargs):
        for referee in ["referee_chief", "referee_first", "referee_second", "referee_reserve"]:
            referee_id = kwargs.pop(referee, None)
            referee_obj = Referee(referee_id) if referee_id else None
            setattr(self, referee, referee_obj)

    def _set_league(self, **kwargs):
        league_id = kwargs.pop("league_id", None)
        league_obj = League(league_id) if league_id else None
        setattr(self, "league", league_obj)

    def _set_stadium(self, **kwargs):
        stadium_id = kwargs.pop("stadium_id", None)
        stadium_obj = Stadium(stadium_id) if stadium_id else None
        setattr(self, "stadium", stadium_obj)

    def _set_team(self, **kwargs):
        for team in ["team_home", "team_guest"]:
            team_id = kwargs.pop(team, None)
            team_age = kwargs.pop(f"{team}_year", None)
            team_obj = Team(team_id, team_age) if team_id else None
            setattr(self, team, team_obj)

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


class Referee:
    def __init__(self, id_: int):
        self.id = id_
        self.first_name, self.second_name, self.third_name, self.phone, category_id = self._get_attr_from_db()
        self.category = Category(category_id) if category_id else None

    def __repr__(self):
        return f"{__class__.__name__} {self.second_name!r} {self.first_name!r}"

    def _get_attr_from_db(self):
        return take_all_by_id("Referee", self.id)

    def get_name(self, *what_name):
        name = ''
        for order in what_name:
            if order in (1, '1', 'first', 'first_name'):
                name = " ".join((name, self.first_name)) if self.first_name else name
            elif order in (2, '2', 'second', 'second_name'):
                name = " ".join((name, self.second_name)) if self.second_name else name
            elif order in (3, '3', 'third', 'third_name'):
                name = " ".join((name, self.third_name)) if self.third_name else name
            else:
                raise TypeError("value in what_name must be:"
                                "\n\t1 or 'first' or 'first_name' - for first_name"
                                "\n\t2 or 'second' or 'second_name' - for second_name"
                                "\n\t3 or 'third' or 'third_name' - for third_name")
        return name.strip()


class League:
    def __init__(self, id_: int):
        self.id = id_
        self.name = self._get_name_from_db()

    def __repr__(self):
        return f"{__class__.__name__} {self.name!r}"

    def _get_name_from_db(self):
        return take_all_by_id("League", self.id)


class Stadium:
    def __init__(self, id_: int):
        self.id = id_
        self.name, self.address, city_id = self._get_attr_from_db()
        self.city = City(city_id)

    def __repr__(self):
        return f"{__class__.__name__} {self.name!r}"

    def _get_attr_from_db(self):
        return take_all_by_id("Stadium", self.id)


class Team:
    def __init__(self, id_: int, age: int):
        self.id = id_
        self.name = self._get_name_from_db()
        self.age = age

    def __repr__(self):
        return f"{__class__.__name__} {self.name!r}"

    def _get_name_from_db(self):
        return take_all_by_id("Team",  self.id)


class Category:
    def __init__(self, id_: int):
        self.id = id_
        self.name = self._get_name_from_db()

    def __repr__(self):
        return f"{__class__.__name__} {self.name!r}"

    def _get_name_from_db(self):
        return take_all_by_id("Category", self.id)


class City:
    def __init__(self, id_: int):
        self.id = id_
        self.name = self._get_name_from_db()

    def __repr__(self):
        return f"{__class__.__name__} {self.name!r}"

    def _get_name_from_db(self):
        return take_all_by_id("City", self.id)


if __name__ == '__main__':
    print(games())
    print("не тот файл, дурачок :)")
