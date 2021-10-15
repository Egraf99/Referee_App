import sqlite3


class ConnDB:
    def take_games(self):
        sql = '''SELECT league.name, year||' '||month||' '||day AS date,
                        time, stadium.name, th.name, tg.name,
                        rc.first_name||' '||rc.second_name AS referee_chief,
                        rf.first_name||' '||rf.second_name AS referee_first,
                        rs.first_name||' '||rs.second_name AS referee_second,
                        rr.first_name||' '||rr.second_name AS referee_reserve,
                        game_passed, payment, pay_done
                   FROM Games 
                        INNER JOIN League ON Games.league_id = League.id
                        INNER JOIN Stadium ON Games.stadium_id = Stadium.id
                        INNER JOIN Team AS th ON Games.team_home = th.id
                        INNER JOIN Team AS tg ON Games.team_guest = tg.id
                        INNER JOIN Referee AS rc ON Games.referee_chief = rc.id
                        INNER JOIN Referee AS rf ON Games.referee_first = rf.id
                        INNER JOIN Referee AS rs ON Games.referee_second = rs.id
                        INNER JOIN Referee AS rr ON Games.referee_reserve = rr.id
                  ORDER BY date ASC'''

        return self.make_request(sql)

    def take_stadium(self):
        sql = '''SELECT name FROM stadium
                  ORDER BY name ASC'''

        return self.make_request(sql)

    def take_referee(self):
        sql = '''SELECT second_name||' '||first_name AS name
                   FROM referee
                  ORDER BY name ASC'''
        return self.make_request(sql)

    def take_team(self):
        sql = '''SELECT name FROM team
                  ORDER BY name ASC'''
        return self.make_request(sql)

    def take_league(self):
        sql = '''SELECT name FROM league
                  ORDER BY name ASC'''
        return self.make_request(sql)

    def make_request(self, sql):
        self.cursor = sqlite3.connect('referee.db').cursor()
        self.cursor.execute(sql)
        games = self.cursor.fetchall()

        self.cursor.close()

        return games


if __name__ == '__main__':
    print(ConnDB().take_games())
