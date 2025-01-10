#!/usr/bin/env python3

# This script takes, as input, the Ctrl-A highlighted text copied from the rendered browser 
# of the CBS Sports website for NFL scores.  Example website URL that is manually copied
# and pasted as input to this script:
# https://www.cbssports.com/nfl/scoreboard/2023/regular/1/

import re
import sys

def format_website():
    text = sys.stdin.read()
    pattern = re.compile("T\nnfl team logo\n[0-9]*\n*([a-zA-Z\.\'\-0-9 \(\)\&]+)\n.*\n[\t0-9]+\t([0-9]+)\nnfl team logo\n[0-9]*\n*([a-zA-Z\.\'\-0-9 \(\)\&]+)\n.*\n[\t0-9]+\t([0-9]+)\n", re.MULTILINE)

    for match in re.finditer(pattern, text):
        visit_team, visit_score, home_team, home_score = match.groups()

        print('{},V,{},{},H,{}'.format(visit_team, visit_score, home_team, home_score))

if __name__=='__main__':
    format_website()
