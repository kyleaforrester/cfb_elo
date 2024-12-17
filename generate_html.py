def generate_html(elo_ratings):
    html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>College Football Elo Ratings</title>
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
        <h1>College Football Elo Ratings</h1>
    </header>
    <table>
        <thead>
            <tr>
                <th>Rank</th>
                <th>Team Name</th>
                <th>Elo Rating</th>
                <th>Change Since Last Game</th>
                <th>Change Since 3 Games</th>
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
        rating = int(round(elo_list[-1],0))

        change_since_1 = None
        if len(elo_list) >= 2:
            change_since_1 = int(round(elo_list[-1] - elo_list[-2],0))

        change_since_3 = None
        if len(elo_list) >= 4:
            change_since_3 = int(round(elo_list[-1] - elo_list[-4],0))

        teams_html += '''
            <tr>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
            </tr>'''.format(team[0] + 1, team[1], rating, change_since_1, change_since_3)

    return html.replace('{{TEAMS_HTML}}', teams_html)
