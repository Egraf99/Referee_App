import sqlite3


class ConnDB:
    def __init__(self):
        self.cursor = sqlite3.connect('referee.db').cursor()

    def take_games(self):
        sql = '''SELECT league.name, date, 
                        (SELECT name 
                           FROM Game 
                                INNER JOIN Team ON Game.team_home = Team.id) AS team_home,
                        (SELECT name 
                           FROM Game 
                                INNER JOIN Team ON Game.team_guest = Team.id) AS team_guest,
                        (SELECT first_name||" "|| second_name
                           FROM Game 
                                INNER JOIN Referee ON Game.referee_chief = Referee.id) AS referee_chief,
                        (SELECT first_name||" "||second_name
                           FROM Game 
                                INNER JOIN Referee ON Game.referee_first = Referee.id) AS referee_first,
                        (SELECT first_name||" "||second_name 
                           FROM Game 
                                INNER JOIN Referee ON Game.referee_second = Referee.id) AS referee_second,
                        (SELECT first_name||" "||second_name 
                           FROM Game 
                                INNER JOIN Referee ON Game.referee_reserve = Referee.id) AS referee_reserve,
                        game_passed, payment, pay_done
                 FROM Game INNER JOIN League ON Game.league_id = League.id'''
        self.cursor.execute(sql)
        return self.cursor.fetchall()


if __name__ == '__main__':
    print(ConnDB().take_games())
