#!/usr/bin/env python3

import sys
import math
import generate_html

HOME_FIELD_ELO = 50
MAX_ELO_CHANGE = 150

def parse_input_file():
    if len(sys.argv) < 2:
        print('Incorrect usage.')
        print('Example usage: ./myscript.py input.txt')
        sys.exit(1)

    return [l.strip() for l in open(sys.argv[1]).readlines() if len(l.strip()) > 0]

def add_team(instr, elo_ratings, home_field_elo_boosts, games_played, history):
    team_elo = instr.split('#add ')[1].split(',')
    team = team_elo[0]
    elo = team_elo[1]
    elo_ratings[team] = [int(elo)]
    home_field_elo_boosts[team] = HOME_FIELD_ELO
    # games_played is a tuple of [fbs_games, fcs_games]
    games_played[team] = [0,0]
    history[team] = []

def predict_winchance(my_rating, enemy_rating):
    return 1 / (1 + 2**((enemy_rating - my_rating)/100))

def result_winchance_integer_instances(my_score, enemy_score, scoring_instances):
    my_ratio = my_score / (my_score + enemy_score)
    enemy_ratio = 1 - my_ratio

    if scoring_instances == 0:
        return my_ratio

    my_sum = 0
    for i in range(int(round(scoring_instances/2 + 0.1, 0)), scoring_instances + 1):
        # Calculate the chance I win exactly i of the scoring_instances
        # the math.comb function computes the permutations using the stars and bars combinatorics method
        chance = math.comb(scoring_instances, scoring_instances - i) * my_ratio**i * enemy_ratio**(scoring_instances - i)
        if i == int(round(scoring_instances / 2 + 0.1, 0)) and scoring_instances % 2 == 0:
            # Should a tied instance count be equal to my_ratio or 0.5?
            # If 0.5, no differences between odd and even instances
            # If my_ratio, no differences between even and odd instances
            # Let's set it to be between 0.5 and my_ratio, so instances matter
            chance *= (0.5 + my_ratio) / 2
        my_sum += chance

    return my_sum

def result_winchance(my_score, enemy_score):
    td_fg_ratio = 2
    points_per_score = (7*td_fg_ratio + 3) / (1 + td_fg_ratio)
    scoring_instances = (my_score + enemy_score) / points_per_score

    floor = math.floor(scoring_instances)
    ceil = math.ceil(scoring_instances)

    if floor == ceil:
        return result_winchance_integer_instances(my_score, enemy_score, floor)
    else:
        floor_fraction = (ceil - scoring_instances) * result_winchance_integer_instances(my_score, enemy_score, floor)
        ceil_fraction = (scoring_instances - floor) * result_winchance_integer_instances(my_score, enemy_score, ceil)
        return floor_fraction + ceil_fraction

def elo_change(games_played, winchance_diff, learning_rate):
    new_rate = (learning_rate - 1) * (1/2)**games_played + 1

    return winchance_diff * MAX_ELO_CHANGE * new_rate

def calculate_elo_changes(instr, elo_ratings, home_field_elo_boosts, games_played, learning_rate, history):
    split_string = instr.split(',')
    a_name = split_string[0]
    a_home = split_string[1] == 'H'
    a_score = int(split_string[2])
    b_name = split_string[3]
    b_home = split_string[4] == 'H'
    b_score = int(split_string[5])

    if a_name not in elo_ratings or b_name not in elo_ratings:
        if a_name in games_played:
            games_played[a_name][1] += 1
        if b_name in games_played:
            games_played[b_name][1] += 1
        print('Skipping game {} vs {}'.format(a_name, b_name), file=sys.stderr)
        return

    a_home_field = 0
    if a_home:
        a_home_field = home_field_elo_boosts[a_name]
    b_home_field = 0
    if b_home:
        b_home_field = home_field_elo_boosts[b_name]

    a_expected_winchance = predict_winchance(elo_ratings[a_name][-1] + a_home_field, elo_ratings[b_name][-1] + b_home_field)
    b_expected_winchance = 1 - a_expected_winchance

    a_result_winchance = result_winchance(a_score, b_score)
    b_result_winchance = 1 - a_result_winchance

    a_elo_change = elo_change(games_played[a_name][0], a_result_winchance - a_expected_winchance, learning_rate)
    b_elo_change = elo_change(games_played[b_name][0], b_result_winchance - b_expected_winchance, learning_rate)

    elo_ratings[a_name].append(elo_ratings[a_name][-1] + a_elo_change)
    elo_ratings[b_name].append(elo_ratings[b_name][-1] + b_elo_change)

    if a_home:
        new_val = home_field_elo_boosts[a_name] + 5 * (a_elo_change / MAX_ELO_CHANGE)
        home_field_elo_boosts[a_name] = max(0, new_val)
    if b_home:
        new_val = home_field_elo_boosts[b_name] + 5 * (b_elo_change / MAX_ELO_CHANGE)
        home_field_elo_boosts[b_name] = max(0, new_val)

    games_played[a_name][0] += 1
    games_played[b_name][0] += 1

    history[a_name].append([a_home_field, elo_ratings[a_name][-2], b_name, b_home_field, elo_ratings[b_name][-2], a_expected_winchance, str(a_score) + ' - ' + str(b_score), a_result_winchance, a_elo_change])
    history[b_name].append([b_home_field, elo_ratings[b_name][-2], a_name, a_home_field, elo_ratings[a_name][-2], b_expected_winchance, str(b_score) + ' - ' + str(a_score), b_result_winchance, b_elo_change])

def calculate_expected_win_percentage(games_played, my_elo, opponent_elos):
    # FCS games are considered an automatic win
    avg_wins_sum = games_played[1]
    for o_e in opponent_elos:
        # Homes and aways already built into opponent_elos
        avg_wins_sum += predict_winchance(my_elo, o_e)
    return avg_wins_sum / sum(games_played)

def calculate_win_50_elo(games_played, opponent_elos):
    # Returns the hypothetical elo required to win exactly 50% of games
    # Calculate a binary search in the elo space to find the win50 elo
    # Stop once you are within 0.001 of the ideal expected_win_percentage
    min_elo = min(opponent_elos) - 2000
    max_elo = max(opponent_elos)
    guess_elo = (min_elo + max_elo) / 2
    expected_win_percentage = calculate_expected_win_percentage(games_played, guess_elo, opponent_elos)
    while expected_win_percentage < 0.49999 or expected_win_percentage > 0.50001:
        if expected_win_percentage < 0.49999:
            min_elo = guess_elo
        elif expected_win_percentage > 0.50001:
            max_elo = guess_elo
        guess_elo = (min_elo + max_elo) / 2
        expected_win_percentage = calculate_expected_win_percentage(games_played, guess_elo, opponent_elos)

    # Expected_wins is now within 0.01 of the mathematical value
    return guess_elo
        

def calculate_win_50_elo_past(games_played, history):
    win_50 = {}
    for team in history.keys():
        opponent_elos = []
        for h in history[team]:
            enemy_elo = h[4]
            # Home Field Advantage
            enemy_elo += h[3] - h[0]
            opponent_elos.append(enemy_elo)
        win_50[team] = calculate_win_50_elo(games_played[team], opponent_elos)
    return win_50

def calculate_win_50_elo_present(games_played, history, elo_ratings, home_field_elo_boosts):
    win_50 = {}
    for team in history.keys():
        opponent_elos = []
        for h in history[team]:
            enemy_elo = elo_ratings[h[2]][-1]
            if h[0] > 0:
                enemy_elo -= home_field_elo_boosts[team]
            if h[3] > 0:
                enemy_elo += home_field_elo_boosts[h[2]]
            opponent_elos.append(enemy_elo)
        win_50[team] = calculate_win_50_elo(games_played[team], opponent_elos)
    return win_50

def calculate_elos():
    instructions = parse_input_file()

    learning_rate = 1
    games_played = {}
    elo_ratings = {}
    home_field_elo_boosts = {}
    history = {}
    for instr in instructions:
        if instr.startswith('//'):
            continue
        elif len(instr) == 0:
            continue
        elif instr.startswith('#newseason'):
            for key in history.keys():
                history[key] = []
            for key in games_played.keys():
                games_played[key] = [0,0]
        elif instr.startswith('#squash '):
            squash_amount = float(instr.split('#squash ')[1])
            for team in elo_ratings.keys():
                old_elo = elo_ratings[team][-1]
                new_elo = old_elo + squash_amount*(0 - old_elo)
                elo_ratings[team].append(new_elo)
        elif instr.startswith('#homefieldelo '):
            global HOME_FIELD_ELO
            elo_amount = int(instr.split('#homefieldelo ')[1])
            HOME_FIELD_ELO = elo_amount
            for team in home_field_elo_boosts.keys():
                home_field_elo_boosts[team] = elo_amount
        elif instr.startswith('#setrate '):
            learning_rate = int(instr.split('#setrate ')[1])
        elif instr.startswith('#add '):
            add_team(instr, elo_ratings, home_field_elo_boosts, games_played, history)
        elif instr.startswith('#end'):
            break
        elif len(instr.split(',')) == 6:
            # Calculate elo changes
            calculate_elo_changes(instr, elo_ratings, home_field_elo_boosts, games_played, learning_rate, history)
        else:
            print('Invalid command: {}'.format(instr))
            continue

    win_50_elo_past = calculate_win_50_elo_past(games_played, history)
    win_50_elo_present = calculate_win_50_elo_present(games_played, history, elo_ratings, home_field_elo_boosts)

    return [elo_ratings, history, win_50_elo_past, win_50_elo_present, home_field_elo_boosts]

if __name__ == '__main__':
    elo_ratings, history, win_50_elo_past, win_50_elo_present, home_field_elo_boosts = calculate_elos()
    print(generate_html.generate_html(elo_ratings, history, win_50_elo_past, win_50_elo_present, home_field_elo_boosts))
