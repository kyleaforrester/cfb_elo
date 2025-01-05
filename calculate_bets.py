#!/usr/bin/env python3

import calculate_elos
import generate_html
import sys

class Bet:
    def __init__(self, line, winning_team, win_home, opponent_team, opponent_home):
        self.line = int(line)
        self.winning_team = winning_team
        self.winning_home = win_home == 'H'
        self.opponent_team = opponent_team
        self.opponent_home = opponent_home == 'H'

    def calculate_payout(self, elo_ratings):
        self.winning_elo = elo_ratings[self.winning_team][-1]
        self.opponent_elo = elo_ratings[self.opponent_team][-1]

        self.actual_winchance = calculate_elos.predict_winchance(self.winning_elo, self.winning_home, self.opponent_elo, self.opponent_home)

        if self.line > 0:
            self.vegas_winchance = 100 / (self.line + 100)
            won = self.line * self.actual_winchance
            lost = 100 * (1 - self.actual_winchance)
        else:
            self.vegas_winchance = self.line / (self.line - 100)
            won = 100 * self.actual_winchance
            lost = -self.line * (1 - self.actual_winchance)

        self.payout = won / lost

def parse_betting_file():
    if len(sys.argv) < 3:
        print('Incorrect usage.')
        print('Example usage: ./myscript.py history.txt bets.txt')
        sys.exit(1)

    lines = [l.strip().split(',') for l in open(sys.argv[2]).readlines() if len(l.strip()) > 0]

    bets = []
    for l in lines:
        bets.append(Bet(l[2], l[0], l[1], l[3], l[4]))
        bets.append(Bet(l[5], l[3], l[4], l[0], l[1]))
    return bets

if __name__ == '__main__':
    elo_ratings, history, win_50_elo_past, win_50_elo_present = calculate_elos.calculate_elos()

    bets = parse_betting_file()
    for bet in bets:
        bet.calculate_payout(elo_ratings)
    bets = sorted(bets, key=lambda x: x.payout, reverse=True)
    print(generate_html.generate_bets_html(bets, elo_ratings))
