import random
import csv

CHALK = 'Chalk'
SIMULATED = 'Simulated'

NUM_GAMES = 67
REGION_OFFSET = {
    "West": 31,
    "East": 39,
    "South": 47,
    "Midwest": 55
}
BRACKET_INDEX = {
    1:  0,
    16: 0,
    8:  1,
    9:  1,
    5:  2,
    12: 2,
    4:  3,
    13: 3,
    6:  4,
    11: 4,
    3:  5,
    14: 5,
    7:  6,
    10: 6,
    2:  7,
    15: 7
}
PLAYIN_INDEX = {
    "West": {
        16: 63,
        11: 64
    }, "East": {
        16: 65,
        11: 66
    }
}


def main():
    teams = read_teams_file("data/fivethirtyeight_ncaa_forecasts.csv")
    b = Bracket(teams, SIMULATED)
    print(str(b), '\n')
    b.play()
    print(str(b))


class Bracket:

    def __init__(self, teams, picker):
        self.bracket_heap = [Game(picker) for _ in range(NUM_GAMES)]
        for team in teams:
            if team.playin_flag:
                self.bracket_heap[PLAYIN_INDEX[team.region][team.seed]].add_team(team)
            else:
                self.bracket_heap[BRACKET_INDEX[team.seed] + REGION_OFFSET[team.region]].add_team(team)
        self.winner = None

    def play(self):
        # Play the first four
        for game in self.bracket_heap[63:]:
            winner = game.pick_winner()
            self.bracket_heap[BRACKET_INDEX[winner.seed] + REGION_OFFSET[winner.region]].add_team(winner)

        def play_game(i):
            # TODO
            if not(self.bracket_heap[i].is_ready()):
                self.bracket_heap[i].add_team(play_game(2 * i + 1))
                self.bracket_heap[i].add_team(play_game(2 * i + 2))
            return self.bracket_heap[i].pick_winner()

        self.winner = play_game(0)

    def __str__(self):
        s = ""
        rounds = {
            63: "PLAY-IN",
            31: "1ST ROUND",
            15: "2ND ROUND",
            7: "SWEET 16",
            3: "ELITE EIGHT",
            1: "FINAL FOUR",
            0: "CHAMPIONSHIP"
        }

        def add_round(start, end):
            tmp = ""
            for game in self.bracket_heap[start:end]:
                tmp += str(game) + '\n'
            return tmp

        for i in range(len(rounds)):
            s += rounds[list(rounds)[i]] + '\n'
            if i == 0:
                s += add_round(list(rounds)[i], len(self.bracket_heap))
            else:
                s += add_round(list(rounds)[i], list(rounds)[i-1])
            s += '\n'

        if self.winner is None:
            s += "WINNER: TBD"
        else:
            s += "WINNER: " + str(self.winner)

        return s


class Game:

    def __init__(self, picker):
        self.picker = picker
        self.teams = []
        self.win_prob = None

    def add_team(self, team):
        self.teams += [team]
        if len(self.teams) == 2:
            if self.picker == SIMULATED:
                self.win_prob = 1 / (1 + 10 ** -((self.teams[0].rating - self.teams[1].rating) * 30.464 / 400))
            else:
                self.win_prob = 1 if self.teams[0].seed <= self.teams[1].seed else 0

    def is_ready(self):
        return len(self.teams) == 2

    def random_winner(self):
        # self.win_prob = 1 / (1 + 10 ** -((self.teams[0].rating - self.teams[1].rating) * 30.464 / 400))
        if random.random() < self.win_prob:
            return self.teams[0]
        else:
            return self.teams[1]

    def chalk_winner(self):
        if self.teams[0].seed <= self.teams[1].seed:
            # self.win_prob = 1
            return self.teams[0]
        else:
            # self.win_prob = 0
            return self.teams[1]

    def pick_winner(self):
        if self.picker == SIMULATED:
            return self.random_winner()
        else:
            return self.chalk_winner()

    def __str__(self):
        if len(self.teams) == 0:
            return "TBD vs. TBD"
        elif len(self.teams) == 1:
            return f"{self.teams[0]} vs. TBD"
        else:
            return f"{self.teams[0]} ({self.win_prob:.2%}) vs. {self.teams[1]} ({1 - self.win_prob:.2%})"

    def __eq__(self, other):
        return type(other) == Game and self.teams[0] == other.teams[0] and self.teams[1] == other.teams[1]


class Team:

    def __init__(self, name, rating, seed, region, playin_flag, team_id):
        self.name = name
        self.rating = rating
        self.seed = seed
        self.region = region
        self.playin_flag = playin_flag
        self.team_id = team_id

    def __str__(self):
        return f"({self.seed}){self.name}"


def read_teams_file(filename):
    try:
        csv_file = open(filename, 'r')
        csv_reader = csv.DictReader(csv_file)
        teams_csv = list(csv_reader)
        teams = []
        for team in teams_csv:
            if team["gender"] == "mens":
                teams += [Team(team["team_name"], float(team["team_rating"]), int(team["team_seed"][:2]),
                               team["team_region"], bool(int(team["playin_flag"])), int(team["team_id"]))]
        return teams
    except FileExistsError:
        err_message = "Error: " + filename + " does not exist"
        print(err_message)
        return None


if __name__ == "__main__":
    main()
