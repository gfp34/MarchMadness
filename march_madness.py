import random
import copy

MAX_DEPTH = 5

CHALK = 'Chalk'
SIMULATED = 'Simulated'


def main():
    teams = read_teams_file("data/2019/Teams2019.dat")
    b1 = Bracket(copy.copy(teams), picker=SIMULATED)
    b1.sim()
    print(b1)


class Bracket:

    def __init__(self, teams, picker=CHALK, name=None):
        self.name = name
        if name is None:
            self.name = picker
        self.teams = teams
        self.picker = picker

        self.final_game = self.new_game()
        self.winner = None

    def sim(self):
        self.winner = self.final_game.pick_winner()

    def new_game(self, layer=0):
        if layer == MAX_DEPTH:
            return Game(self.picker, teams=(self.teams.pop(0), self.teams.pop(0)))
        else:
            return Game(self.picker, prev_games=(self.new_game(layer + 1), self.new_game(layer + 1)))

    def __str__(self):
        tmp = f"{self.name}:\n"
        for i in range(MAX_DEPTH, -1, -1):
            tmp += f"{self._str(self.final_game, 0, i)}\n"
        tmp += f"{self.winner}"
        return tmp

    def _str(self, cur_game, cur_layer, des_layer):
        if cur_layer == des_layer:
            return f"{str(cur_game)}\n"
        else:
            return f"{self._str(cur_game.prev_games[0], cur_layer + 1, des_layer)}" \
                   f"{self._str(cur_game.prev_games[1], cur_layer + 1, des_layer)}"

    def __eq__(self, other):
        return type(other) == Bracket and self.final_game == other.final_game and self.winner == other.winner


class Game:

    def __init__(self, picker, teams=None, prev_games=None):
        self.picker = picker
        self.prev_games = prev_games
        if teams is not None:
            # This is a first round game
            self.teams = teams
        else:
            # Not a first round game
            self.teams = None

        self.win_prob = None

    def random_winner(self):
        if self.win_prob is None:
            self.win_prob = 1 / (1 + 10 ** -((self.teams[0].elo - self.teams[1].elo) * 30.464/400))

        if random.random() < self.win_prob:
            return self.teams[0]
        else:
            return self.teams[1]

    def chalk_winner(self):
        if self.teams[0].seed <= self.teams[1].seed:
            self.win_prob = 1
            return self.teams[0]
        else:
            self.win_prob = 0
            return self.teams[1]

    def pick_winner(self):
        if self.teams is None:
            self.teams = (self.prev_games[0].pick_winner(), self.prev_games[1].pick_winner())
        if self.picker == SIMULATED:
            return self.random_winner()
        else:
            return self.chalk_winner()

    def __str__(self):
        if self.teams is None:
            return "TBD"
        else:
            return f"{self.teams[0]} ({self.win_prob:.2%}) vs. {self.teams[1]} ({1 - self.win_prob:.2%})"

    def __eq__(self, other):
        return type(other) == Game and self.teams[0] == other.teams[0] and self.teams[1] == other.teams[1]


class Team:

    def __init__(self, name, elo, seed):
        self.name = name
        self.elo = elo
        self.seed = seed

    def __str__(self):
        return f"({self.seed}){self.name}"

    def __eq__(self, other):
        if type(other) == Team:
            return self.name == other.name and self.seed == other.seed and self.elo == other.elo
        else:
            return False


def read_teams_file(filename):
    try:
        teams = []
        with open(filename) as file:
            for line in file:
                data = line.split(' ')
                if len(data) > 1:
                    name = ""
                    for i in range(2, len(data)):
                        name += f"{data[i]} "
                    name = name.strip()
                    teams.append(Team(name, float(data[1]), int(data[0])))
        return teams
    except FileExistsError:
        err_message = "Error: " + filename + " does not exist"
        print(err_message)
        return None


if __name__ == "__main__":
    main()
