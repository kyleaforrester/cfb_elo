#!/usr/bin/env python3

import calculate_elos
import random
import math

def calculate_error(params):
    calculate_elos.MAX_ELO_CHANGE = params['MAX_ELO_CHANGE']
    calculate_elos.HOME_FIELD_MULTIPLIER = params['HOME_FIELD_MULTIPLIER']
    calculate_elos.POINTS_PER_SCORE = params['POINTS_PER_SCORE']
    calculate_elos.LEARNING_RATE_DECAY = params['LEARNING_RATE_DECAY']

    instructions = calculate_elos.parse_input_file()

    learning_rate = 1
    games_played = {}
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
            for key in games_played.keys():
                games_played[key] = [0,0]
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
        elif instr.startswith('#pointsperscore '):
            continue
        elif instr.startswith('#setrate '):
            learning_rate = params['LEARNING_RATE_INITIAL']
        elif instr.startswith('#setratedecay '):
            continue
        elif instr.startswith('#add '):
            calculate_elos.add_team(instr, elo_ratings, home_field_elo_boosts, games_played, history)
        elif instr.startswith('#name '):
            continue
        elif instr.startswith('#end'):
            break
        elif len(instr.split(',')) == 6:
            # Calculate elo changes
            calculate_elos.calculate_elo_changes(instr, elo_ratings, home_field_elo_boosts, games_played, learning_rate, history)
        else:
            print('Invalid command: {}'.format(instr))
            continue

    error = 0
    for team in history.keys():
        for entry in history[team]:
            if entry[7] > 0.5:
                error += (1.0 - entry[5])**2
            else:
                error += entry[5]**2

    return error


# Parameters for [MAX_ELO_CHANGE, HOME_FIELD_ELO, SQUASH_FRACTION]
parameters = {'MAX_ELO_CHANGE': 50, 'HOME_FIELD_ELO': 30, 'HOME_FIELD_MULTIPLIER': 10, 'POINTS_PER_SCORE': 3, 'LEARNING_RATE_INITIAL': 1, 'LEARNING_RATE_DECAY': 0.75, 'SQUASH_FRACTION': 0.1}

parameters = {'MAX_ELO_CHANGE': 50, 'HOME_FIELD_ELO': 35, 'HOME_FIELD_MULTIPLIER': 10, 'POINTS_PER_SCORE': 7, 'LEARNING_RATE_INITIAL': 5, 'LEARNING_RATE_DECAY': 0.75, 'SQUASH_FRACTION': -0.1}

bases = {}
improvements = {}
for k in parameters.keys():
    bases[k] = 99
    improvements[k] = [0, 0]

error = calculate_error(parameters)
print('Iteration -1. Parameters: {}, Error: {}'.format(parameters, error))
i = 0
while True:
    new_parameters = {}
    modified_parameter = ''
    for enum_key in enumerate(parameters.keys()):
        if i % len(parameters.keys()) == enum_key[0]:
            new_parameters[enum_key[1]] = parameters[enum_key[1]] * (random.random() + bases[enum_key[1]]) / (random.random() + bases[enum_key[1]])
            modified_parameter = enum_key[1]
            if abs(new_parameters[enum_key[1]]) < 0.0000000001 and random.random() < 0.1:
                new_parameters[enum_key[1]] *= -1
        else:
            new_parameters[enum_key[1]] = parameters[enum_key[1]]

    new_error = calculate_error(new_parameters)
    if new_error < error:
        print('Iteration {}. New parameters: {}, new error: {}'.format(i, new_parameters, new_error))
        parameters = new_parameters
        error = new_error
        improvements[modified_parameter][0] += 1
    else:
        improvements[modified_parameter][1] += 1

    if i > 0 and i % 1000 == 0:
        for key in parameters.keys():
            if improvements[key][0] == 0:
                bases[key] *= 2
            elif improvements[key][1] == 0:
                bases[key] /= 2
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
