import csv
import io
import os
import random
import shutil

from PyPDF2 import PdfFileReader
from PyPDF2 import PdfFileWriter
from reportlab.pdfgen import canvas

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
    1: 0,
    16: 0,
    8: 1,
    9: 1,
    5: 2,
    12: 2,
    4: 3,
    13: 3,
    6: 4,
    11: 4,
    3: 5,
    14: 5,
    7: 6,
    10: 6,
    2: 7,
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
ROUND_SECTIONS = {
    1: (63, 67),
    2: (31, 63),
    3: (15, 31),
    4: (7, 15),
    5: (3, 7),
    6: (1, 3),
    7: (0, 1)
}
TOP_ROW_TEAM_IDS = [2450, 2724, 116, 127]


def main():
    teams = read_teams_file("data/fivethirtyeight_ncaa_forecasts.csv")
    # generate_brackets(100, teams, folder_name="100_brackets")
    b = Bracket(teams, CHALK)
    b.play()
    print(b)
    b.draw_pdf("data/blank2021.pdf", "chalk.pdf")
    b.save("chalk.csv")


def generate_brackets(num, teams, folder_name):
    try:
        os.mkdir(folder_name)
    except FileExistsError:
        shutil.rmtree(folder_name)
        os.mkdir(folder_name)
    os.mkdir(folder_name + "/csv")
    os.mkdir(folder_name + "/pdf")
    for i in range(num):
        b = Bracket(teams, SIMULATED)
        b.play()
        b.save(f"{folder_name}/csv/bracket_{i}.csv")
        b.draw_pdf("data/blank2021.pdf", f"{folder_name}/pdf/bracket_{i}.pdf")
        print("Saved bracket:", i)


class Bracket:

    def __init__(self, teams, picker):
        self.teams = teams
        self.bracket_heap = [Game(picker) for _ in range(NUM_GAMES)]
        for team in teams:
            if team.playin_flag:
                self.bracket_heap[PLAYIN_INDEX[team.region][team.seed]].add_team(team)
            else:
                self.bracket_heap[BRACKET_INDEX[team.seed] + REGION_OFFSET[team.region]].add_team(team)

    def play(self):
        # Play the first four
        for game in self.bracket_heap[63:]:
            winner = game.pick_winner()
            self.bracket_heap[BRACKET_INDEX[winner.seed] + REGION_OFFSET[winner.region]].add_team(winner)

        # Play the rest of the bracket
        def play_game(i):
            if not (self.bracket_heap[i].is_ready()):
                self.bracket_heap[i].add_team(play_game(2 * i + 1))
                self.bracket_heap[i].add_team(play_game(2 * i + 2))
            return self.bracket_heap[i].pick_winner()

        play_game(0)

    def save(self, filename):
        bracket_csv = open(filename, 'w')
        bracket_writer = csv.writer(bracket_csv, delimiter=',')
        bracket_writer.writerow(["team_name", "team_seed", "team_rating", "team_region", "playin_flag", "team_id"
                                                                                                        "rd1_win",
                                 "rd2_win", "rd3_win", "rd4_win", "rd5_win", "rd6_win", "rd7_win"])
        bracket_sections = {1: 63, 2: 31, 3: 15, 4: 7, 5: 3, 6: 1, 7: 0}
        for team in self.teams:
            team_data = [team.name, str(team.seed) + (team.playin_id if team.playin_id is not None else ""),
                         team.rating, team.region, int(team.playin_flag)]
            wins = []
            for i in bracket_sections:
                if i == 1 and not team.playin_flag:
                    wins += [1]
                else:
                    start, end = bracket_sections[i], len(self.bracket_heap) if i == 1 else bracket_sections[i - 1]
                    # Check if team is in this rounds section of game winners
                    wins += [int(team in [g.winner for g in self.bracket_heap[start:end]])]
            bracket_writer.writerow(team_data + wins)
        bracket_csv.close()

    def load(self, filename):
        bracket_csv = open(filename, 'r')
        bracket_reader = csv.DictReader(bracket_csv, delimiter=',')
        for row in bracket_reader:
            if row["gender"] == "mens":
                team = [Team(row["team_name"], float(row["team_rating"]), int(row["team_seed"][:2]),
                             row["team_region"], bool(int(row["playin_flag"])), int(row["team_id"]))]
                wins = [row[f"rd{i}_win"] for i in range(1, 8)]
                # TODO

    def draw_pdf(self, blank_filename, filename):
        tmp_pdf = io.BytesIO()
        can = canvas.Canvas(tmp_pdf)
        can.setFontSize(7)

        # Box first 4 winners
        xs = [154, 260, 452, 560]
        y = 490
        h = 79
        w = 10
        for game, x in zip(self.bracket_heap[ROUND_SECTIONS[1][0]:ROUND_SECTIONS[1][1]], xs):
            if game.winner.team_id in TOP_ROW_TEAM_IDS:
                can.rect(x, y, h, w)
            else:
                can.rect(x, y-14, 79, 10)

        bracket_pdf_points = {
            # left start point, right start point, dy val, switch value
            1: ((0, 463), (763, 463), 25, 16),
            2: ((127, 456), (607, 456), 29, 16),
            3: ((187, 442), (555, 442), 58, 8),
            4: ((237, 413), (507, 413), 116, 4),
            5: ((286, 357), (460, 357), 234, 2),
            6: ((290, 235), (442, 235), 0, 1)
        }

        # Put win prob on first round
        x, y = bracket_pdf_points[1][0]
        dy = 25
        switch = bracket_pdf_points[1][3]
        for i in range(ROUND_SECTIONS[2][0], ROUND_SECTIONS[2][1], 1):
            if switch == 0:
                x, y = bracket_pdf_points[1][1]
                switch = bracket_pdf_points[1][3]
                dy = 25
            can.drawString(x, y, f"({self.bracket_heap[i].win_prob:.2%})")
            can.drawString(x, y - dy/2, f"({1 - self.bracket_heap[i].win_prob:.2%})")
            y -= dy
            if switch == bracket_pdf_points[1][3]/2:
                y -= 10
                dy = 33
            switch -= 1

        # Fill in rounds
        for r in range(2, 7):
            x, y = bracket_pdf_points[r][0]
            switch = bracket_pdf_points[r][3]
            for i in range(ROUND_SECTIONS[r][0], ROUND_SECTIONS[r][1]):
                if switch == 0:
                    x, y = bracket_pdf_points[r][1]
                    switch = bracket_pdf_points[r][3]
                win_prob = self.bracket_heap[(i-1)//2].win_prob
                if self.bracket_heap[(i-1)//2].teams[1] == self.bracket_heap[i].winner:
                    win_prob = 1 - win_prob
                can.drawString(x, y, str(self.bracket_heap[i].winner) + f" ({win_prob:.2%})")
                y -= bracket_pdf_points[r][2]
                switch -= 1
        # Fill in winner
        can.drawString(363, 235, str(self.bracket_heap[0].winner))

        can.save()

        watermark = PdfFileReader(tmp_pdf)

        out_pdf = PdfFileWriter()
        blank_pdf = PdfFileReader(open(blank_filename, 'rb'))

        blank_page = blank_pdf.getPage(0)
        blank_page.mergePage(watermark.getPage(0))
        out_pdf.addPage(blank_page)

        with open(filename, 'wb') as out_stream:
            out_pdf.write(out_stream)

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
                s += add_round(list(rounds)[i], list(rounds)[i - 1])
            s += '\n'

        if self.bracket_heap[0].winner is None:
            s += "WINNER: TBD"
        else:
            s += "WINNER: " + str(self.bracket_heap[0].winner)

        return s


class Game:

    def __init__(self, picker):
        self.picker = picker
        self.teams = []
        self.win_prob = None
        self.winner = None

    def add_team(self, team):
        self.teams += [team]
        if len(self.teams) == 2:
            if self.picker == SIMULATED:
                self.win_prob = 1 / (1 + 10 ** -((self.teams[0].rating - self.teams[1].rating) * 30.464 / 400))
            else:
                if self.teams[0].playin_flag and self.teams[1].playin_flag:
                    self.win_prob = 1 if self.teams[0].playin_id < self.teams[1].playin_id else 0
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
        if self.teams[0].playin_flag and self.teams[1].playin_flag:
            if self.teams[0].playin_id <= self.teams[1].playin_id:
                return self.teams[0]
            else:
                return self.teams[1]
        if self.teams[0].seed <= self.teams[1].seed:
            # self.win_prob = 1
            return self.teams[0]
        else:
            # self.win_prob = 0
            return self.teams[1]

    def pick_winner(self):
        if self.picker == SIMULATED:
            self.winner = self.random_winner()
        else:
            self.winner = self.chalk_winner()
        return self.winner

    def __str__(self):
        if len(self.teams) == 0:
            return "TBD vs. TBD"
        elif len(self.teams) == 1:
            return f"{self.teams[0]} vs. TBD"
        else:
            if self.winner is not None:
                return f"{self.teams[0]} ({self.win_prob:.2%}) vs. {self.teams[1]} ({1 - self.win_prob:.2%}) -> {self.winner}"
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
        self.playin_id = None

    def __str__(self):
        return f"({self.seed}){self.name}"

    def __eq__(self, other):
        return type(other) == Team and self.team_id == other.team_id


def read_teams_file(filename):
    try:
        csv_file = open(filename, 'r')
        csv_reader = csv.DictReader(csv_file)
        teams_csv = list(csv_reader)
        teams = []
        for team in teams_csv:
            if team["gender"] == "mens":
                tmp = Team(team["team_name"], float(team["team_rating"]), int(team["team_seed"][:2]),
                               team["team_region"], bool(int(team["playin_flag"])), int(team["team_id"]))
                if tmp.playin_flag:
                    tmp.playin_id = team["team_seed"][2:]
                teams += [tmp]
        csv_file.close()
        return teams
    except FileExistsError:
        err_message = "Error: " + filename + " does not exist"
        print(err_message)
        return None


if __name__ == "__main__":
    main()
