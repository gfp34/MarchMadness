import csv
import os
import random
import shutil

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
PARENT = lambda i: (i - 1) // 2
LEFT_CHILD = lambda i: (i * 2) + 1
RIGHT_CHILD = lambda i: (i * 2) + 2


def main():
	teams = read_teams_file("data/fivethirtyeight_ncaa_forecasts_2021.csv")
	generate_brackets(100, teams, folder_name="100_brackets")
	b = Bracket(teams)
	b.play(SIMULATED)
	print(b)
	b.save('random.csv')

	loaded_bracket = Bracket(teams)
	loaded_bracket.load("random.csv")
	print(loaded_bracket)


def generate_brackets(num, teams, folder_name):
	try:
		os.mkdir(folder_name)
	except FileExistsError:
		shutil.rmtree(folder_name)
		os.mkdir(folder_name)
	os.mkdir(folder_name + "/csv")
	for i in range(num):
		b = Bracket(teams)
		b.play(SIMULATED)
		b.save(f"{folder_name}/csv/bracket_{i}.csv")
		print("Saved bracket:", i)


class Bracket:

	def __init__(self, teams):
		self.teams = teams
		self.bracket_heap = [Game() for _ in range(NUM_GAMES)]
		for team in teams:
			if team.playin_flag:
				self.bracket_heap[PLAYIN_INDEX[team.region][team.seed]].add_team(team)
			else:
				self.bracket_heap[BRACKET_INDEX[team.seed] + REGION_OFFSET[team.region]].add_team(team)

	def play(self, picker):
		# Play the first four
		for game in self.bracket_heap[63:]:
			winner = game.pick_winner(picker)
			self.bracket_heap[BRACKET_INDEX[winner.seed] + REGION_OFFSET[winner.region]].add_team(winner)

		# Play the rest of the bracket
		def play_game(i):
			if not (self.bracket_heap[i].is_ready()):
				self.bracket_heap[i].add_team(play_game(LEFT_CHILD(i)))
				self.bracket_heap[i].add_team(play_game(RIGHT_CHILD(i)))
			return self.bracket_heap[i].pick_winner(picker)

		play_game(0)

	def save(self, filename):
		bracket_csv = open(filename, 'w')
		bracket_writer = csv.writer(bracket_csv, delimiter=',')
		bracket_writer.writerow(["team_name", "team_seed", "team_rating", "team_region", "playin_flag", "team_id",
								 "rd1_win", "rd2_win", "rd3_win", "rd4_win", "rd5_win", "rd6_win", "rd7_win"])
		bracket_sections = {1: 63, 2: 31, 3: 15, 4: 7, 5: 3, 6: 1, 7: 0}
		for team in self.teams:
			team_data = [team.name, str(team.seed) + (team.playin_id if team.playin_id is not None else ""),
						 team.rating, team.region, int(team.playin_flag), team.team_id]
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
		bracket_reader = csv.DictReader(bracket_csv)
		for row in bracket_reader:
			# Read teams and wins from csv
			team = Team(row["team_name"], float(row["team_rating"]), int(row["team_seed"][:2]),
						row["team_region"], bool(int(row["playin_flag"])), int(row["team_id"]))
			wins = [bool(int(row[f"rd{i}_win"])) for i in range(1, 8)]

			for i, game in enumerate(self.bracket_heap[31:]):
				if team in game:
					bracket_index = 31 + i
					break

			if not team.playin_flag:
				# Skip the first round win if not a playin team
				wins = wins[1:]
			for won_game in wins:
				if won_game:
					self.bracket_heap[bracket_index].winner = team
					bracket_index = PARENT(bracket_index)
					self.bracket_heap[bracket_index].add_team(team)
				else:
					break

			if wins[-1]:
				self.bracket_heap[0].winner = team

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

	def __init__(self):
		self.teams = []
		self.win_prob = None
		self.winner = None

	def add_team(self, team):
		self.teams += [team]

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

	def pick_winner(self, picker):
		if picker == SIMULATED:
			self.win_prob = 1 / (1 + 10 ** -((self.teams[0].rating - self.teams[1].rating) * 30.464 / 400))
		else:
			if self.teams[0].playin_flag and self.teams[1].playin_flag:
				self.win_prob = 1 if self.teams[0].playin_id < self.teams[1].playin_id else 0
			else:
				self.win_prob = 1 if self.teams[0].seed <= self.teams[1].seed else 0
		if picker == SIMULATED:
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
			self.win_prob = 1 / (1 + 10 ** -((self.teams[0].rating - self.teams[1].rating) * 30.464 / 400))
			game_str = f"{self.teams[0]} ({self.win_prob:.2%}) vs. {self.teams[1]} ({1 - self.win_prob:.2%})"
			return game_str + (f" -> {self.winner}" if self.winner is not None else "")

	def __eq__(self, other):
		return type(other) == Game and self.teams[0] == other.teams[0] and self.teams[1] == other.teams[1]

	def __contains__(self, item):
		return type(item) == Team and item in self.teams


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
