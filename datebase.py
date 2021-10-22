import sqlite3


class ConnDB:
    def take_games(self):
        sql = '''SELECT league.name, year||' '||month||' '||day AS date,
                        time, stadium.name, th.name, tg.name
                   FROM Games 
                        INNER JOIN League ON Games.league_id = League.id
                        INNER JOIN Stadium ON Games.stadium_id = Stadium.id
                        INNER JOIN Team AS th ON Games.team_home = th.id
                        INNER JOIN Team AS tg ON Games.team_guest = tg.id
                  ORDER BY day, month, year ASC, time DESC'''

        return self.select_request(sql)

    def take_stadium(self):
        sql = '''SELECT name FROM stadium
                  ORDER BY name ASC'''

        return self.select_request(sql)

    def take_referee(self):
        sql = '''SELECT second_name||' '||first_name AS name
                   FROM referee
                  ORDER BY name ASC'''
        return self.select_request(sql)

    def take_team(self):
        sql = '''SELECT name FROM team
                  ORDER BY name ASC'''
        return self.select_request(sql)

    def take_league(self):
        sql = '''SELECT name FROM league
                  ORDER BY name ASC'''
        return self.select_request(sql)

    def take_category(self):
        sql = '''SELECT name FROM category
                  ORDER BY name ASC'''
        return self.select_request(sql)

    def take_city(self):
        sql = '''SELECT name FROM city
                ORDER BY name ASC'''

        return self.select_request(sql)

    def take_id(self, table, name_dict):
        name_list = []
        for name in name_dict:
            name_list.append(f'{name} = "{name_dict[name]}"')

        conditions = " AND ".join(name_list)
        sql = f'''SELECT id FROM {table} WHERE {conditions}'''

        # print(sql)

        return self.select_request(sql, one=True)

    def insert(self, table, data: dict):
        self._convert_special_date(data)

        column = ','.join(d for d in data.keys())
        count_values = ','.join('?' * len(data.values()))
        values = [d for d in data.values()]

        sql = f'''INSERT INTO {table}({column}) VALUES ({count_values}); '''

        print(sql, values)

        self.insert_request(sql, values)

    @staticmethod
    def _convert_special_date(data):
        """Преаобразует специальные поля (дата, время, телефон) в формат значений БД."""
        if "date_and_time" in data.keys():
            # year, day, month, time
            date = data.pop("date_and_time").split(" ")
            day, month, year = date[0].split(".")
            time = date[1].replace(':', '')

            _data = {'day': day, 'month': month, 'year': year, 'time': time}
            for i in _data:
                data[i] = _data[i]

        if "phone" in data.keys():
            # в телефоне оставляем только числа
            phone_ = ''
            phone = data.pop("phone")
            for symbol in phone:
                if symbol.isdigit():
                    phone_ += symbol

            data['phone'] = int(phone_)

    def select_request(self, sql, one=False):
        self.cursor = sqlite3.connect('referee.db').cursor()
        self.cursor.execute(sql)
        if one:
            games = self.cursor.fetchone()
        else:
            games = self.cursor.fetchall()

        self.cursor.close()

        return games

    def insert_request(self, sql, values):
        self.conn = sqlite3.connect('referee.db')
        self.cur = self.conn.cursor()
        self.cur.execute(sql, values)
        self.conn.commit()


if __name__ == '__main__':
    ConnDB().insert('game',
                          {'chief_referee': 'Ходин Егор', 'guest_team': 'Смена-2', 'home_team': 'Смена-2',
                           'league': 'ЛФК А',
                           'date_and_time': '12.04.2021 15:00', 'stadium': 'Сапсан Арена'})
