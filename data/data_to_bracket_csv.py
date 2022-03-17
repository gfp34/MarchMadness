import csv

data_filename = "2021/fivethirtyeight_ncaa_forecasts_2021_final.csv"
data_csv = open(data_filename, 'r')
data_reader = csv.DictReader(data_csv)

bracket_filename = "2021/final_bracket_2021.csv"
bracket_csv = open(bracket_filename, 'w')
bracket_writer = csv.writer(bracket_csv, delimiter=',')

bracket_writer.writerow(["team_name", "team_seed", "team_rating", "team_region", "playin_flag", "team_id",
						 "rd1_win", "rd2_win", "rd3_win", "rd4_win", "rd5_win", "rd6_win", "rd7_win"])
for row in data_reader:
	new_row = [row["team_name"], int(row["team_seed"][:2]), float(row["team_rating"]),
			   row["team_region"], int(row["playin_flag"]), int(row["team_id"]),
			   int(float(row["rd1_win"])), int(float(row["rd2_win"])), int(float(row["rd3_win"])),
			   int(float(row["rd4_win"])), int(float(row["rd5_win"])),
			   int(float(row["rd6_win"])), int(float(row["rd7_win"]))]
	bracket_writer.writerow(new_row)
