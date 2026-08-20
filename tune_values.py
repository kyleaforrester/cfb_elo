#!/usr/bin/env python3

import calculate_elos
import random
import math

def calculate_error(params):
    calculate_elos.MAX_ELO_CHANGE = params['MAX_ELO_CHANGE']
    calculate_elos.HOME_FIELD_MULTIPLIER = params['HOME_FIELD_MULTIPLIER']
    calculate_elos.LEARNING_RATE_DECAY = params['LEARNING_RATE_DECAY']
    calculate_elos.UNCERTAINTY_INCREASE = params['UNCERTAINTY_INCREASE']
    calculate_elos.UNCERTAINTY_ERROR_SENSITIVITY= params['UNCERTAINTY_ERROR_SENSITIVITY']
    calculate_elos.VAR_A = params['VAR_A']
    calculate_elos.VAR_B = params['VAR_B']
    calculate_elos.VAR_C = params['VAR_C']
    calculate_elos.VAR_D = params['VAR_D']
    calculate_elos.VAR_E = params['VAR_E']
    calculate_elos.VAR_F = params['VAR_F']

    instructions = calculate_elos.parse_input_file()

    uncertainty_multiplier = {}
    fake_games_played = {}
    elo_ratings = {}
    home_field_elo_boosts = {}
    history = {}
    season = 0
    for instr in instructions:
        if instr.startswith('//'):
            continue
        elif len(instr) == 0:
            continue
        elif instr.startswith('#newseason'):
            season += 1
            if season == 2:
                for key in history.keys():
                    history[key] = []
        elif instr.startswith('#squash '):
            squash_amount = params['SQUASH_FRACTION']
            for team in elo_ratings.keys():
                old_elo = elo_ratings[team][-1]
                new_elo = old_elo + squash_amount*(0 - old_elo)
                elo_ratings[team].append(new_elo)
        elif instr.startswith('#homefieldelo '):
            elo_amount = params['HOME_FIELD_ELO']
            calculate_elos.HOME_FIELD_ELO = elo_amount
            for team in home_field_elo_boosts.keys():
                home_field_elo_boosts[team] = elo_amount
        elif instr.startswith('#maxelochange '):
            continue
        elif instr.startswith('#homefieldmultiplier '):
            continue
        elif instr.startswith('#var_a '):
            continue
        elif instr.startswith('#var_b '):
            continue
        elif instr.startswith('#var_c '):
            continue
        elif instr.startswith('#var_d '):
            continue
        elif instr.startswith('#var_e '):
            continue
        elif instr.startswith('#var_f '):
            continue
        elif instr.startswith('#setrate '):
            for team in uncertainty_multiplier.keys():
                uncertainty_multiplier[team] = params['LEARNING_RATE_INITIAL']
        elif instr.startswith('#setratedecay '):
            continue
        elif instr.startswith('#uncertaintyincrease '):
            continue
        elif instr.startswith('#uncertaintyerrorsensitivity '):
            continue
        elif instr.startswith('#add '):
            calculate_elos.add_team(instr, elo_ratings, home_field_elo_boosts, uncertainty_multiplier, fake_games_played, history)
        elif instr.startswith('#name '):
            continue
        elif instr.startswith('#end'):
            break
        elif len(instr.split(',')) == 6:
            # Calculate elo changes
            calculate_elos.calculate_elo_changes(instr, elo_ratings, home_field_elo_boosts, uncertainty_multiplier, fake_games_played, history)
        else:
            print('Invalid command: {}'.format(instr))
            continue

    total_error = 0
    total_squared_error = 0
    total_cross_entropy = 0
    total_correct = 0
    games = 0
    for team in history.keys():
        for entry in history[team]:
            if entry[7] > 0.5:
                total_cross_entropy += -math.log(entry[5])
                error = (1.0 - entry[5])
                if entry[5] > 0.5:
                    total_correct += 1
            else:
                total_cross_entropy += -math.log(1.0 - entry[5])
                error = entry[5]
                if entry[5] < 0.5:
                    total_correct += 1

            total_error += error
            games += 1

    return total_cross_entropy, total_error / games, total_correct / games


# Parameters for [MAX_ELO_CHANGE, HOME_FIELD_ELO, SQUASH_FRACTION]
parameters = {'MAX_ELO_CHANGE': 15, 'HOME_FIELD_ELO': 30, 'HOME_FIELD_MULTIPLIER': 2, 'VAR_A': 1, 'VAR_B': 1, 'VAR_C': 1, 'VAR_D': 1, 'VAR_E': 1, 'VAR_F': 1, 'LEARNING_RATE_INITIAL': 2, 'LEARNING_RATE_DECAY': 0.75, 'UNCERTAINTY_INCREASE': 1, 'UNCERTAINTY_ERROR_SENSITIVITY': 1, 'SQUASH_FRACTION': 0.1}

parameters = {'MAX_ELO_CHANGE': 30, 'HOME_FIELD_ELO': 40, 'HOME_FIELD_MULTIPLIER': 5, 'VAR_A': 1, 'VAR_B': 1, 'VAR_C': 1, 'VAR_D': 1, 'VAR_E': 1, 'VAR_F': 1, 'LEARNING_RATE_INITIAL': 7, 'LEARNING_RATE_DECAY': 0.75, 'UNCERTAINTY_INCREASE': 10, 'UNCERTAINTY_ERROR_SENSITIVITY': 2, 'SQUASH_FRACTION': -0.1}
bases = {}
improvements = {}
for k in parameters.keys():
    bases[k] = 9
    improvements[k] = [0, 0]

error, avg_error, pct_correct = calculate_error(parameters)
print('Iteration -1. Parameters: {}, Total Cross Entropy Error: {}, Average Linear Error: {}, Percent Correct: {}'.format(parameters, error, avg_error, pct_correct))
i = 0
while True:
    new_parameters = {}
    keys = list(parameters.keys())
    weights = [1/bases[k] for k in keys]
    modified_parameter = random.choices(keys, weights=weights)[0]
    for key in keys:
        if key == modified_parameter:
            new_parameters[key] = parameters[key] * (random.random() + bases[key]) / (random.random() + bases[key])
            if abs(new_parameters[key]) < 0.0000000001 and random.random() < 0.1:
                new_parameters[key] *= -1
        else:
            new_parameters[key] = parameters[key]

    new_error, new_avg_error, new_pct_correct = calculate_error(new_parameters)
    if new_error < error:
        print('Iteration {}. New parameters: {}, new total cross entropy error: {}, new avg linear error: {}, new pct correct: {}'.format(i, new_parameters, new_error, new_avg_error, new_pct_correct))
        parameters = new_parameters
        error = new_error
        improvements[modified_parameter][0] += 1
    else:
        improvements[modified_parameter][1] += 1

    if i > 0 and i % 1000 == 0:
        for key in parameters.keys():
            if improvements[key][0] == 0 and improvements[key][1] < 4:
                pass
            elif improvements[key][0] == 0 and improvements[key][1] >= 4:
                bases[key] *= 2
            else:
                adjustment = 0.25 / (improvements[key][0] / (improvements[key][0] + improvements[key][1]))
                bases[key] *= min(max(0.5, adjustment), 2.0)
            if bases[key] < 1:
                bases[key] = 1

            improvements[key] = [0, 0]
        print('Iteration {} concluded. New bases: {}'.format(i, bases))

    if all(map(lambda x: bases[x] > 1000000, list(parameters.keys()))):
        print('Run complete. Bases have exceeded 1000000: {}'.format(bases))
        break
    i += 1
