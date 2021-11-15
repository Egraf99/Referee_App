import sqlite3
import datetime
from typing import Optional, Union, Any
from kivymd.color_definitions import colors


def take_one_data(what_return: str, table: str, condition: dict[str, Any] = None) -> str:
    """Возвращает одно (первое) значение из БД.

        Parameters:
            what_return(str) - строка, содержащая название возвращаемых столбцов.
            table(str) - название таблицы.
            condition(dict) - словарь условий. SELECT ... WHERE X = Y (X - ключ, Y - значение).

        Return:
            name - возвращаемое значение."""

    name = ConnDB()._take_data(what_return, table, condition, one_value=True)
    return name[0] if name and name[0] else None


def take_many_data(what_return: str, table: str, condition: dict[str, Any] = None) -> list:
    """Возвращает все значения из БД, подходящие по условиям.

            Parameters:
                what_return(str) - строка, содержащая название возвращаемых столбцов.
                table(str) - название таблицы.
                condition(dict) - словарь условий. SELECT ... WHERE X = Y (X - ключ, Y - значение).

            Return:
                name - список возвращаемых значений."""

    return ConnDB()._take_data(what_return, table, condition, one_value=False)


def take_name_from_db(table: str) -> list:
    """Возвращает значение из БД с помощью функций класса DB.

    Parameters:
        table (str) - из какой таблицы брать значения. В классе DB должен быть метод take_{mode}.

    Return:
        data (list) - список полученных имен из БД."""

    try:
        if table == "referee":
            data = take_many_data("second_name||' '||first_name", table)
        else:
            data = take_many_data("name", table)

        return data

    except AttributeError:
        raise AttributeError(f"ConnDB has no table '{table}'")


class ConnDB:
    @property
    def games(self) -> list[dict]:
        """Возвращает все данные по всем играм в виде списка словарей."""

        column_names = ["id", "league_id", "stadium_id", "team_home", "team_guest",
                        "referee_chief", "referee_first", "referee_second", "referee_reserve",
                        "game_passed", "payment", "pay_done", "year", "month", "day", "time",
                        "team_home_year", "team_guest_year"]

        sql = f'''SELECT * FROM Games ORDER BY year, month, day ASC, time DESC'''

        games_dict_of_kwargs = []
        return_request = self._select_request(sql)
        for r in return_request:
            games_dict_of_kwargs.append(dict(zip(column_names, r)))

        return games_dict_of_kwargs

    def _take_data(self, what_return: str, table: str,
                   conditions: Optional[dict] = None,
                   one_value: bool = False) -> Union[str, list]:
        values = None
        if conditions:
            name_list = []
            values = []
            for name in conditions:
                name_list.append(f'{name} = ?')
                values.append(conditions[name])

            conditions_str = " AND ".join(name_list)

            sql = f'''SELECT {what_return} FROM {table} WHERE {conditions_str}'''

        else:
            sql = f'''SELECT {what_return} FROM {table}'''

        # print(sql, values)
        return self._select_request(sql, values, one_value=one_value)

    def insert(self, table: str, data: dict) -> None:
        """Добавляет в БД заданные данные."""

        self._convert_special_date(data)

        for k, v in data.items():
            data[k] = int(v) if type(v) == str and v.isdigit() else v

        column = ','.join(d for d in data.keys())
        count_values = ','.join('?' * len(data.values()))
        values = [d for d in data.values()]

        sql = f'''INSERT INTO {table}({column}) VALUES ({count_values}); '''

        print(sql, values)

        self._insert_request(sql, values)

    @staticmethod
    def _convert_special_date(data: dict) -> None:
        """Преаобразует специальные поля (дата, время, телефон) в формат значений БД."""
        if "date" in data.keys():
            date = data.pop("date").split(" ")
            day, month, year = map(lambda d: int(d), date[0].split("."))

            _data = {'day': day, 'month': month, 'year': year}
            for i in _data:
                data[i] = _data[i]

        if "time" in data.keys():
            time = data.pop("time")
            time = int(time.replace(":", ""))
            data["time"] = time

        if "phone" in data.keys():
            # в телефоне оставляем только числа
            phone_ = ''
            phone = data.pop("phone")
            for symbol in phone:
                if symbol.isdigit():
                    phone_ += symbol

            data['phone'] = int(phone_)

    def _select_request(self, sql: str, values: Optional[list] = None, one_value: bool = False) -> list:
        self.cursor = sqlite3.connect('referee.db').cursor()
        if values:
            self.cursor.execute(sql, values)
        else:
            self.cursor.execute(sql)

        if one_value:
            data = self.cursor.fetchone()
        else:
            data = self.cursor.fetchall()

        self.cursor.close()

        return data

    def _insert_request(self, sql, values):
        self.conn = sqlite3.connect('referee.db')
        self.cur = self.conn.cursor()
        self.cur.execute(sql, values)
        self.conn.commit()


class Game:
    """Класс, определяющий игру из БД."""
    # dict of status icon, color, name
    status_icn = {"not_passed": ("calendar-alert", colors["Yellow"]["800"], "Не проведена"),
                  "passed": ("calendar-check", colors["LightGreen"]["400"], "Проведена"),
                  "pay_done": ("calendar-check", colors["Green"]["700"], "Оплачено")}
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
                 "status"]

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
            team_obj = Team(team_id) if team_id else None
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

    def _get_attr_from_db(self):
        return take_many_data("first_name, second_name, third_name, phone, category_id",
                              "Referee", {"id": self.id})


class League:
    def __init__(self, id_: int):
        self.id = id_
        self.name = self._get_name_from_db

    def _get_name_from_db(self):
        return take_one_data("name", "League", {"id": self.id})


class Stadium:
    def __init__(self, id_: int):
        self.id = id_
        self.name, self.address, city_id = self._get_attr_from_db()[0]
        self.city = City(city_id)

    def _get_attr_from_db(self):
        return take_many_data("name, address, city_id", "Stadium", {"id": self.id})


class Team:
    def __init__(self, id_: int):
        self.id = id_
        self.name = self._get_name_from_db

    def _get_name_from_db(self):
        return take_one_data("name", "Team", {"id": self.id})


class Category:
    def __init__(self, id_: int):
        self.id = id_
        self.name = self._get_name_from_db

    def _get_name_from_db(self):
        return take_one_data("name", "Category", {"id": self.id})


class City:
    def __init__(self, id_: int):
        self.id = id_
        self.name = self._get_name_from_db

    def _get_name_from_db(self):
        return take_one_data("name", "City", {"id": self.id})


if __name__ == '__main__':
    # print(Referee(1).first_name())
    print("не тот файл, дурачок :)")
