import os.path
import sqlite3
import datetime
from typing import Optional, Union, Any, Dict, List

from kivy.utils import platform
from kivymd.color_definitions import colors


def take_one_data(what_return: str, table: str, condition: Dict[str, Any] = None, order: dict = None) -> str:
    """Возвращает одно (первое) значение из БД.

        Parameters:
            what_return(str) - строка, содержащая название возвращаемых столбцов.
            table(str) - название таблицы.
            condition(dict) - словарь условий. SELECT ... WHERE X = Y (X - ключ, Y - значение).
            order(dict) - словарь сортировки. Доступные ключи - ASC и DESC.
                            ORDER BY Y X (X - ключ, Y - значения).

        Return:
            name - возвращаемое значение."""

    name = ConnDB().take_data(what_return, table, condition, one_value=True, order=order)
    return name[0] if name and name[0] else None


def take_many_data(what_return: str, table: str, condition: Dict[str, Any] = None, order: dict = None) -> list:
    """Возвращает все значения из БД, подходящие по условиям.

            Parameters:
                what_return(str) - строка, содержащая название возвращаемых столбцов.
                table(str) - название таблицы.
                condition(dict) - словарь условий. SELECT ... WHERE X = Y (X - ключ, Y - значение).
                order(dict) - словарь сортировки. Доступные ключи - ASC и DESC.
                            ORDER BY Y X (X - ключ, Y - значения).

            Return:
                name - список возвращаемых значений."""

    return ConnDB().take_data(what_return, table, condition, one_value=False, order=order)


def take_name_from_db(table: str) -> list:
    """Возвращает значение из БД с помощью функций класса DB.

    Parameters:
        table (str) - из какой таблицы брать значения. В классе DB должен быть метод take_{mode}.

    Return:
        data (list) - список кортежей полученных имен из БД."""

    try:
        if table == "Referee":
            data = take_many_data("id", "Referee",
                                  order={"ASC": ["second_name", "first_name", "third_name"]})
            name_list = []
            for id_ in data:
                name_list.append((Referee(*id_).get_name('second', 'first'),))

            return name_list
        else:
            data = take_many_data("name", table, order={"ASC": ["name"]})
            return data

    except AttributeError:
        raise AttributeError(f"ConnDB has no table '{table}'")


class ConnDB:
    def __init__(self):
        if platform == "android":
            self.path_db = os.path.join(os.environ["ANDROID_STORAGE"], "emulated", "0", "referee.db")
        else:
            self.path_db = os.path.join(os.path.expanduser("~"), "PycharmProjects", "Referee_App", "referee.db")

        with open(self.path_db, "a"):
            with sqlite3.connect(self.path_db) as conn:
                cursor = conn.cursor()
                cursor.execute("""CREATE TABLE IF NOT EXISTS Games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                league_id INTEGER,
                stadium_id INTEGER NOT NULL,
                team_home INTEGER,
                team_guest INTEGER,
                referee_chief INTEGER NOT NULL,
                referee_first INTEGER,
                referee_second INTEGER,
                referee_reserve INTEGER,
                game_passed INTEGER,
                payment INTEGER,
                pay_done INTEGER,
                year INTEGER,
                month INTEGER,
                day INTEGER,
                time INTEGER,
                team_home_year INTEGER,
                team_guest_year INTEGER,
                FOREIGN KEY (league_id) REFERENCES League(id),
                FOREIGN KEY (stadium_id) REFERENCES Stadium(id),
                FOREIGN KEY (team_home) REFERENCES Team(id),
                FOREIGN KEY (team_guest) REFERENCES Team(id),
                FOREIGN KEY (referee_chief) REFERENCES Referee(id),
                FOREIGN KEY (referee_first) REFERENCES Referee(id),
                FOREIGN KEY (referee_second) REFERENCES Referee(id),
                FOREIGN KEY (referee_reserve) REFERENCES Referee(id),
                CHECK (year > 0 AND month > 0 AND month <= 12 AND day > 0 AND day <= 31
                 AND game_passed IN (0, 1) AND pay_done IN (0, 1))
                )""")
                
                cursor.execute("""CREATE TABLE IF NOT EXISTS Category (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name CHAR (30)
                )""")
                
                cursor.execute("""CREATE TABLE IF NOT EXISTS City (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name CHAR (30)
                )""")
                
                cursor.execute("""CREATE TABLE IF NOT EXISTS League (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name CHAR(30)
                )""")
                
                cursor.execute("""CREATE TABLE IF NOT EXISTS Referee (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name CHAR(30),
                second_name CHAR(30),
                third_name CHAR(30),
                phone CHAR(15),
                category_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES Category(id)
                )""")

                cursor.execute("""CREATE TABLE IF NOT EXISTS Team (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name CHAR(30)
                )""")

                cursor.execute("""CREATE TABLE IF NOT EXISTS Stadium (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT(30),
                address TEXT,
                city_id INTEGER,
                FOREIGN KEY (city_id) REFERENCES City(id)
                )""")

                conn.commit()

    @property
    def games(self) -> List[dict]:
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
                        "year",
                        "month",
                        "day",
                        "time",
                        "team_home_year",
                        "team_guest_year",
                        )

        sql = f'''SELECT * FROM Games ORDER BY year DESC, month DESC, day DESC, time ASC'''

        games_dict_of_kwargs = []
        return_request = self._select_request(sql)
        for r in return_request:
            games_dict_of_kwargs.append(dict(zip(column_names, r)))

        return games_dict_of_kwargs

    def take_data(self, what_return: str, table: str,
                  conditions: dict = None,
                  one_value: bool = False, order: dict = None) -> Union[str, list]:
        values = None
        if conditions:
            conditions_str, values = self._convert_conditions(conditions)
            sql = f'''SELECT {what_return} FROM {table} WHERE {conditions_str}'''

        else:
            sql = f'''SELECT {what_return} FROM {table}'''

        if order:
            order_str = self._convert_order(order)
            sql += f''' ORDER BY {order_str}'''
        # #print(sql)
        return self._select_request(sql, values, one_value=one_value)

    def insert(self, table: str, data: dict) -> None:
        """Добавляет в БД заданные данные."""
        # #print(data)
        for k, v in data.items():
            data[k] = int(v) if type(v) == str and v.isdigit() else v

        column = ','.join(d for d in data.keys())
        count_values = ','.join('?' * len(data.values()))
        values = [d for d in data.values()]

        sql = f'''INSERT INTO {table}({column}) VALUES ({count_values}); '''

        # #print(sql, values)
        self._request(sql, values)

    def update(self, table: str, data: dict, conditions: dict):
        """Обновляет БД."""

        for k, v in data.items():
            data[k] = int(v) if type(v) == str and v.isdigit() else v

        column = ','.join(f'{d}=?' for d in data.keys())
        values = [d for d in data.values()]

        if conditions:
            conditions_str, conditions_value = self._convert_conditions(conditions)
            values.append(*conditions_value)
            sql = f'''UPDATE {table} SET {column} WHERE {conditions_str}'''
        else:
            sql = f'''UPDATE {table} SET {column}'''

        self._request(sql, values)

    def delete(self, table: str, conditions: dict, columns: list = None):
        columns = ", ".join(columns) if columns else ''
        values = []

        if conditions:
            conditions_str, conditions_value = self._convert_conditions(conditions)
            values.append(*conditions_value)
            sql = f'''DELETE {columns} FROM {table} WHERE {conditions_str}'''

        else:
            sql = f'''DELETE {columns} FROM {table}'''

        #print("Delete")
        #print(sql, values)
        #print()
        self._request(sql, values)

    @staticmethod
    def _convert_order(order) -> str:
        order_sql = []
        for key in order:
            assert key in ["ASC", "DESC"], "order keys must be 'ASC' or 'DESC'"
            assert type(order[key]) == list, "order value type must be list"

            order_sql.append(f"{', '.join(order[key])} {key}")
        return ", ".join(order_sql)

    @staticmethod
    def _convert_conditions(conditions: dict):
        name_list = []
        values = []
        for name in conditions:
            name_list.append(f'{name} = ?')
            values.append(conditions[name])

        return " AND ".join(name_list), values

    def _select_request(self, sql: str, values: Optional[list] = None, one_value: bool = False) -> list:
        self.cursor = sqlite3.connect(self.path_db).cursor()
        if values:
            self.cursor.execute(sql, values)
        else:
            self.cursor.execute(sql)

        if one_value:
            data = self.cursor.fetchone()
        else:
            data = self.cursor.fetchall()

        #print("Select")
        #print(sql, values)
        #print()
        self.cursor.close()

        return data

    def _request(self, sql, values):
        self.conn = sqlite3.connect(self.path_db)
        self.cur = self.conn.cursor()
        self.cur.execute(sql, values)
        self.conn.commit()


class Game:
    """Класс, определяющий игру из БД."""
    # dict of status icon, color, name
    status_icn = {"not_passed": ("calendar-alert", colors["Red"]["800"], ""),
                  "passed": ("calendar-check", colors["Yellow"]["300"], ""),
                  "pay_done": ("calendar-check", colors["Green"]["700"], ""),
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

        year = kwargs.pop("year", None)
        month = kwargs.pop("month", None)
        day = kwargs.pop("day", None)
        time_ = kwargs.pop("time", None)
        hour, minute = int(time_) // 100, int(time_) % 100
        self.date = datetime.datetime(year, month, day, hour=hour, minute=minute)

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
        self.first_name, self.second_name, self.third_name, self.phone, category_id = self._get_attr_from_db()[0]
        self.category = Category(category_id)

    def __repr__(self):
        return f"{__class__.__name__} {self.second_name!r} {self.first_name!r}"

    def _get_attr_from_db(self):
        return take_many_data("first_name, second_name, third_name, phone, category_id",
                              "Referee", {"id": self.id})

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
        return take_one_data("name", "League", {"id": self.id})


class Stadium:
    def __init__(self, id_: int):
        self.id = id_
        self.name, self.address, city_id = self._get_attr_from_db()[0]
        self.city = City(city_id)

    def __repr__(self):
        return f"{__class__.__name__} {self.name!r}"

    def _get_attr_from_db(self):
        return take_many_data("name, address, city_id", "Stadium", {"id": self.id})


class Team:
    def __init__(self, id_: int, age: int):
        self.id = id_
        self.name = self._get_name_from_db()
        self.age = age

    def __repr__(self):
        return f"{__class__.__name__} {self.name!r}"

    def _get_name_from_db(self):
        return take_one_data("name", "Team", {"id": self.id})


class Category:
    def __init__(self, id_: int):
        self.id = id_
        self.name = self._get_name_from_db()

    def __repr__(self):
        return f"{__class__.__name__} {self.name!r}"

    def _get_name_from_db(self):
        return take_one_data("name", "Category", {"id": self.id})


class City:
    def __init__(self, id_: int):
        self.id = id_
        self.name = self._get_name_from_db()

    def __repr__(self):
        return f"{__class__.__name__} {self.name!r}"

    def _get_name_from_db(self):
        return take_one_data("name", "City", {"id": self.id})


if __name__ == '__main__':
    # ConnDB().delete('Games', {'id': 2}, ['id', 'team_home', 'referee_chief'])
    print("не тот файл, дурачок :)")
