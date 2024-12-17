#!/usr/bin/env python3

import sys
import math
import generate_html

def parse_input_file():
    if len(sys.argv) != 2:
        print('Incorrect usage.')
        print('Example usage: ./myscript.py input.txt')
        sys.exit(1)

    return [l.strip() for l in open(sys.argv[1]).readlines() if len(l.strip()) > 0]

def add_team(instr, elo_ratings, games_played):
    team_elo = instr.split('#add ')[1].split(',')
    team = team_elo[0]
    elo = team_elo[1]
    elo_ratings[team] = [int(elo)]
    games_played[team] = 0

def predict_winchance(my_rating, my_home, enemy_rating, enemy_home):
    if my_home == True:
        my_rating += 50
    if enemy_home == True:
        enemy_rating += 50

    return 1 / (1 + 2**((enemy_rating - my_rating)/100))

def result_winchance(my_score, enemy_score):
    scoring_instances = int((my_score + enemy_score) / 5)
    my_ratio = my_score / (my_score + enemy_score)
    enemy_ratio = 1 - my_ratio

    if scoring_instances == 0:
        return my_ratio

    my_sum = 0
    for i in range(int(round(scoring_instances/2 + 0.1, 0)), scoring_instances + 1):
        # Calculate the chance I win exactly i of the scoring_instances
        # the math.comb function computes the permutations using the stars and bars combinatorics method
        chance = math.comb(scoring_instances, scoring_instances - i) * my_ratio**i * enemy_ratio**(scoring_instances - i)
        if i == int(scoring_instances / 2):
            # Break ties if it's the same number of instances for each team
            chance *= my_ratio
        my_sum += chance

    return my_sum

def elo_change(games_played, winchance_diff, learning_rate):
    new_rate = (learning_rate - 1) * (1/2)**games_played + 1

    return winchance_diff * 150 * new_rate

def calculate_elo_changes(instr, elo_ratings, games_played, learning_rate):
    split_string = instr.split(',')
    a_name = split_string[0]
    a_home = split_string[1] == 'H'
    a_score = int(split_string[2])
    b_name = split_string[3]
    b_home = split_string[4] == 'H'
    b_score = int(split_string[5])

    if a_name not in elo_ratings or b_name not in elo_ratings:
        print('Skipping game {} vs {}'.format(a_name, b_name), file=sys.stderr)
        return

    a_expected_winchance = predict_winchance(elo_ratings[a_name][-1], a_home, elo_ratings[b_name][-1], b_home)
    b_expected_winchance = 1 - a_expected_winchance

    a_result_winchance = result_winchance(a_score, b_score)
    b_result_winchance = 1 - a_result_winchance

    a_elo_change = elo_change(games_played[a_name], a_result_winchance - a_expected_winchance, learning_rate)
    b_elo_change = elo_change(games_played[b_name], b_result_winchance - b_expected_winchance, learning_rate)

    elo_ratings[a_name].append(elo_ratings[a_name][-1] + a_elo_change)
    elo_ratings[b_name].append(elo_ratings[b_name][-1] + b_elo_change)

    games_played[a_name] += 1
    games_played[b_name] += 1

    follow_team = ''
    if a_name == follow_team or b_name == follow_team:
        print('{} {} at {} {}. Expected result: {}'.format(a_name, elo_ratings[a_name][-2], b_name, elo_ratings[b_name][-2], a_expected_winchance))
        print('Result: {} to {}. Result winchance: {}'.format(a_score, b_score, a_result_winchance))
        print('{} change of {}, {} change of {}'.format(a_name, a_elo_change, b_name, b_elo_change))

if __name__ == '__main__':
    instructions = parse_input_file()

    learning_rate = 1
    games_played = {}
    elo_ratings = {}
    for instr in instructions:
        if instr.startswith('//'):
            continue
        elif len(instr) == 0:
            continue
        elif instr.startswith('#setrate '):
            learning_rate = int(instr.split('#setrate ')[1])
            for key in games_played.keys():
                games_played[key] = 0
        elif instr.startswith('#add '):
            add_team(instr, elo_ratings, games_played)
        elif instr.startswith('#end'):
            break
        elif len(instr.split(',')) == 6:
            # Calculate elo changes
            calculate_elo_changes(instr, elo_ratings, games_played, learning_rate)
        else:
            print('Invalid command: {}'.format(instr))
            continue

    print(generate_html.generate_html(elo_ratings))
