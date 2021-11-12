import sqlite3
from typing import Optional


class ConnDB:
    @property
    def games(self) -> list:
        column_names = ["id", "league_id", "stadium_id", "team_home", "team_guest",
                        "referee_chief", "referee_first", "referee_second", "referee_reserve",
                        "game_passed", "payment", "pay_done", "year", "month", "day", "time",
                        "team_home_year", "team_guest_year"]

        sql = f'''SELECT * FROM Games'''

        games_list_of_kwargs = []
        return_request = self.select_request(sql)
        for r in return_request:
            games_list_of_kwargs.append(dict(zip(column_names, r)))

        return games_list_of_kwargs

    def take_data(self, what_return: str, table: str,
                  conditions: Optional[dict] = None,
                  one_value: bool = False) -> list:
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
        return self.select_request(sql, values, one_value=one_value)

    def insert(self, table: str, data: dict) -> None:
        self._convert_special_date(data)

        for k, v in data.items():
            data[k] = int(v) if type(v) == str and v.isdigit() else v

        column = ','.join(d for d in data.keys())
        count_values = ','.join('?' * len(data.values()))
        values = [d for d in data.values()]

        sql = f'''INSERT INTO {table}({column}) VALUES ({count_values}); '''

        print(sql, values)

        self.insert_request(sql, values)

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

    def select_request(self, sql: str, values: Optional[list] = None, one_value: bool = False) -> list:
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

    def insert_request(self, sql, values):
        self.conn = sqlite3.connect('referee.db')
        self.cur = self.conn.cursor()
        self.cur.execute(sql, values)
        self.conn.commit()


if __name__ == '__main__':
    print("не тот файл, дурачок :)")
