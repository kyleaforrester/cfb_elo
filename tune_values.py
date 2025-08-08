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
    for instr in instructions:
        if instr.startswith('//'):
            continue
        elif len(instr) == 0:
            continue
        elif instr.startswith('#newseason'):
            for key in games_played.keys():
                games_played[key] = [0,0]
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
parameters = {'MAX_ELO_CHANGE': random.random() * 15 + 50, 'HOME_FIELD_ELO': random.random() * 52 - 12, 'HOME_FIELD_MULTIPLIER': random.random() * 13 + 12, 'POINTS_PER_SCORE': random.random() * 7 + 2, 'LEARNING_RATE_INITIAL': random.random() * 4 + 0.3, 'LEARNING_RATE_DECAY': random.random()*0.3 + 0.5, 'SQUASH_FRACTION': random.random() * 0.22 - 0.12}

error = calculate_error(parameters)
print('Iteration -1. Parameters: {}, Error: {}'.format(parameters, error))
i = 0
while True:
    new_parameters = {}
    for key in parameters.keys():
        new_parameters[key] = parameters[key] * (random.random() + 99) / (random.random() + 99)

    new_error = calculate_error(new_parameters)
    if new_error < error:
        print('Iteration {}. New parameters: {}, new error: {}'.format(i, new_parameters, new_error))
        parameters = new_parameters
        error = new_error
    if i % 1000 == 0:
        print('Iteration {} concluded.'.format(i))
    i += 1
