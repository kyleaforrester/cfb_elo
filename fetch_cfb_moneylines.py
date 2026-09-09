#!/usr/bin/env python3

import re
import sys
import urllib.request

URL = 'https://www.vegasinsider.com/college-football/odds/las-vegas/'
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
            away = translate_team_name(teams[0])
            home = translate_team_name(teams[1])
            away_ml = moneylines[0]
            home_ml = moneylines[1]
            if away != None and home != None:
                print('{},V,{},{},H,{}'.format(away, away_ml, home, home_ml))

def translate_team_name(name):
    translate_dict = {'Villanova': None, 'Richmond': None, 'Oklahoma State': 'Oklahoma St.', 'Appalachian State': 'App State', 'Penn State': 'Penn St.', 'Arizona State': 'Arizona St.', 'South Florida': 'South Fla.', 'Army': 'Army West Point', 'Washington State': 'Washington St.', 'Kansas State': 'Kansas St.', 'Wofford': None, 'Colgate': None, 'Holy Cross': None, 'Stony Brook': None, 'Robert Morris': None, 'Weber State': None, 'Sacred Heart': None, 'Central Connecticut State': None, 'Alabama State': None, 'Northern Colorado': None, 'UC Davis': None, 'Gardner-Webb': None, 'Monmouth': None, 'Illinois State': None, 'Southern Utah': None, 'Lindenwood': None, 'Fordham': None, 'Texas Southern': None, 'Cal Poly': None, 'Montana State': None, 'Hawai\'i': 'Hawaii', 'Utah State': 'Utah St.', 'Texas State': 'Texas St.', 'Eastern Michigan': 'Eastern Mich.', 'Michigan State': 'Michigan St.', 'Mississippi State': 'Mississippi St.', 'Boise State': 'Boise St.', 'Jacksonville State': 'Jacksonville St.', 'Georgia State': 'Georgia St.', 'Kennesaw State': 'Kennesaw St.', 'San Diego State': 'San Diego St.', 'Iowa State': 'Iowa St.', 'Ohio State': 'Ohio St.', 'Oregon State': 'Oregon St.', 'North Dakota State': 'North Dakota St.', 'Louisiana-Monroe': 'ULM', 'Florida International': 'FIU', 'Middle Tennessee': 'Middle Tenn.', 'Georgia Southern': 'Ga. Southern', 'Florida Atlantic': 'Fla. Atlantic', 'Southern Miss': 'Southern Miss.', 'Sacramento State': 'Sacramento St.', 'Fresno State': 'Fresno St.', 'USC': 'Southern California', 'New Mexico State': 'New Mexico St.', 'Florida State': 'Florida St.'}
    if name in translate_dict:
        return translate_dict[name]
    else:
        return name

if __name__ == '__main__':
    format_moneylines()
