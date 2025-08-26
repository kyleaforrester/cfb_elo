def generate_html(elo_ratings, history, win50_elo_past, win50_elo_present, home_field_elo_boosts, name):
    html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{NAME}}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f9;
        }
        header {
            background-color: #004d99;
            color: white;
            padding: 10px 20px;
            text-align: center;
        }
        table {
            width: 80%;
            margin: 20px auto;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #0066cc;
            color: white;
        }
        tr:hover {
            background-color: #f1f1f1;
        }
        .subtable {
            display: none;
            background-color: #f9f9f9;
            border-top: 1px solid #ddd;
        }
        .subtable td {
            padding: 5px 10px;
        }
    </style>
    <script>
        function toggleSubtable(row) {
            const subtable = row.nextElementSibling;
            if (subtable && subtable.classList.contains('subtable')) {
                subtable.style.display = subtable.style.display === 'table-row' ? 'none' : 'table-row';
            }
        }
    </script>
</head>
<body>
    <header>
        <h1>{{NAME}}</h1>
    </header>
    <table>
        <thead>
            <tr>
                <th>Rank</th>
                <th>Team Name</th>
                <th>Elo Rating</th>
                <th>Home Field Adv</th>
                <th>Win 50 Past</th>
                <th>Win 50 Present</th>
                <th>Change Since Last Game</th>
                <th>Change Since 3 Games</th>
                <th>Change Since Season Start</th>
            </tr>
        </thead>
        <tbody>
{{TEAMS_HTML}}
        </tbody>
    </table>
</body>
</html>'''

    teams_html = ''
    for team in enumerate(sorted(list(elo_ratings.keys()), key=lambda x: elo_ratings[x][-1], reverse=True)):
        elo_list = elo_ratings[team[1]]
        rating = round(elo_list[-1])
        home_field_adv = round(home_field_elo_boosts[team[1]])
        my_team_win50_past = round(win50_elo_past[team[1]])
        my_team_win50_present = round(win50_elo_present[team[1]])

        change_since_1 = None
        if len(elo_list) >= 2:
            change_since_1 = round(elo_list[-1] - elo_list[-2])

        change_since_3 = None
        if len(elo_list) >= 4:
            change_since_3 = round(elo_list[-1] - elo_list[-4])

        change_since_season = round(elo_list[-1] - elo_list[-1 - len(history[team[1]])])

        teams_html += '''
            <tr onclick="toggleSubtable(this)">
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
            </tr>'''.format(team[0] + 1, team[1], rating, home_field_adv, my_team_win50_past, my_team_win50_present, change_since_1, change_since_3, change_since_season)

        teams_html += '''
            <tr class="subtable">
                <td colspan="9">
                    <table>
                        <thead>
                            <tr>
                                <th>Elo</th>
                                <th>Opponent</th>
                                <th>Opponent Elo</th>
                                <th>Home Field Adv</th>
                                <th>Win Chance</th>
                                <th>Score</th>
                                <th>Result</th>
                                <th>Elo Change</th>
                            </tr>
                        </thead>
                        <tbody>'''
        for game in history[team[1]]:
            home_field = round(game[0] - game[3], 1)
            elo = round(game[1], 1)
            opponent = game[2]
            opponent_elo = round(game[4], 1)
            win_chance = round(game[5], 3)
            score = game[6]
            result = round(game[7], 3)
            elo_change = round(game[8], 1)

            teams_html += '''
                            <tr>
                                <td>{}</td>
                                <td>{}</td>
                                <td>{}</td>
                                <td>{}</td>
                                <td>{:.3f}</td>
                                <td>{}</td>
                                <td>{}</td>
                                <td>{}</td>
                            </tr>'''.format(elo, opponent, opponent_elo, home_field, win_chance, score, result, elo_change)

        teams_html += '''
                        </tbody>
                    </table>
                </td>
            </tr>'''

    html = html.replace('{{NAME}}', name)
    return html.replace('{{TEAMS_HTML}}', teams_html)

def generate_bets_html(bets, elo_ratings, name):
    html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{NAME}} Hunches</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f9;
        }
        header {
            background-color: #004d99;
            color: white;
            padding: 10px 20px;
            text-align: center;
        }
        table {
            width: 80%;
            margin: 20px auto;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #0066cc;
            color: white;
        }
        tr:hover {
            background-color: #f1f1f1;
        }
    </style>
</head>
<body>
    <header>
        <h1>{{NAME}} Hunches</h1>
    </header>
    <table>
        <thead>
            <tr>
                <th>Rank</th>
                <th>Winning Team</th>
                <th>Winning Team Elo</th>
                <th>Home Field Adv</th>
                <th>Opponent</th>
                <th>Opponent Elo</th>
                <th>Line</th>
                <th>Vegas Winchance</th>
                <th>Actual Winchance</th>
                <th>Payout</th>
            </tr>
        </thead>
        <tbody>
{{BETS_HTML}}
        </tbody>
    </table>
</body>
</html>'''

    bets_html = ''
    for enum_bet in enumerate(bets):
        bet = enum_bet[1]
        home_field_adv = round(bet.home_field_adv)
        winning_team_elo = round(elo_ratings[bet.winning_team][-1])
        opponent_elo = round(elo_ratings[bet.opponent_team][-1])
        vegas_winchance = round(bet.vegas_winchance, 3)
        actual_winchance = round(bet.actual_winchance, 3)
        payout = round(bet.payout, 3)
        bets_html += '''
            <tr>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
            </tr>'''.format(enum_bet[0] + 1, bet.winning_team, winning_team_elo, home_field_adv, bet.opponent_team, opponent_elo, bet.line, vegas_winchance, actual_winchance, payout)

    html = html.replace('{{NAME}}', name)
    return html.replace('{{BETS_HTML}}', bets_html)
