#!/usr/bin/env python3

# This script takes, as input, the Ctrl-A highlighted text copied from the rendered browser 
# of the NCAA website for college football scores.  Example website URL that is manually copied
# and pasted as input to this script:
# https://www.ncaa.com/scoreboard/football/fbs/2024/07/all-conf

import re
import sys

def format_website():
    text = sys.stdin.read()
    pattern = re.compile("\n\n    [0-9]*([a-zA-Z\.\'\- \(\)\&]+)([0-9]*)\n    [0-9]*([a-zA-Z\.\'\- \(\)\&]+)([0-9]*)\n", re.MULTILINE)

    for match in re.finditer(pattern, text):
        visit_team, visit_score, home_team, home_score = match.groups()

        # Remove leading AP rankings attached to team names
        if visit_team[0].isdigit():
            visit_team = ' '.join(visit_team.split(' ')[1:])
        if home_team[0].isdigit():
            home_team = ' '.join(home_team.split(' ')[1:])

        visit_team = visit_team.replace('Northern Ill.', 'NIU')
        home_team = home_team.replace('Northern Ill.', 'NIU')

        print('{},V,{},{},H,{}'.format(visit_team, visit_score, home_team, home_score))

if __name__=='__main__':
    format_website()
