#!/usr/bin/env python3

import re
import sys
import urllib.request

URL = 'https://www.vegasinsider.com/nfl/odds/las-vegas/'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
DRAFTKINGS_INDEX = 3

def fetch_page():
    req = urllib.request.Request(URL, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8', errors='replace')

def format_moneylines():
    html = fetch_page()

    tbody_match = re.search(r'<tbody id="odds-table-moneyline--0".*?</tbody>', html, re.DOTALL)
    if not tbody_match:
        print('Could not find the moneyline odds table.', file=sys.stderr)
        sys.exit(1)
    tbody = tbody_match.group(0)

    game_starts = [m.start() for m in re.finditer(r'<td class="game-time" data-role="clipboard"', tbody)]
    if not game_starts:
        print('Could not find any games in the moneyline odds table.', file=sys.stderr)
        sys.exit(1)

    for i, start in enumerate(game_starts):
        end = game_starts[i + 1] if i + 1 < len(game_starts) else len(tbody)
        block = tbody[start:end]

        teams = re.findall(r'class="team-name "[^>]*> <span> ([^<]+) </span> </a>', block)

        moneylines = []
        for row in re.split(r'<tr class="(?:divided|footer)[ "~]', block)[1:]:
            vals = re.findall(r'class="data-moneyline">\s*([+-]?\d+)\s*<', row)
            if len(vals) > DRAFTKINGS_INDEX:
                moneylines.append(int(vals[DRAFTKINGS_INDEX]))

        if len(teams) >= 2 and len(moneylines) >= 2:
            away = teams[0]
            home = teams[1]
            away_ml = moneylines[0]
            home_ml = moneylines[1]
            print('{},V,{},{},H,{}'.format(away, away_ml, home, home_ml))

if __name__ == '__main__':
    format_moneylines()