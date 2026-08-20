# Elo Rating System for Sports

A self-contained Elo rating engine for any sport, applied to college football (FBS) and the NFL. Given a chronological ledger of games (just team names and final scores), the system produces a continuously updated rating for every team, a per-team home field advantage, a strength-of-schedule-adjusted ranking, and even betting suggestions against Vegas moneylines.

The repository also includes a parameter tuner that searches for the model settings that best fit historical results, and HTML generators that render the ratings into browsable rankings with per-game detail.

---

## Table of Contents

1. [The Elo Rating System — and How This Implementation Differs](#1-the-elo-rating-system--and-how-this-implementation-differs)
2. [Only the Final Score Matters](#2-only-the-final-score-matters)
3. [From Final Score to Result Winchance — and the Rating Adjustment](#3-from-final-score-to-result-winchance--and-the-rating-adjustment)
4. [Home Field Advantage, Learned Per Team](#4-home-field-advantage-learned-per-team)
5. [A New Season: Squashing Ratings and Resetting Uncertainty](#5-a-new-season-squashing-ratings-and-resetting-uncertainty)
6. [How Uncertainty Decays — and How Upsets Renew It](#6-how-uncertainty-decays--and-how-upsets-renew-it)
7. [Strengths of the System](#7-strengths-of-the-system)
8. [Drawbacks and Limitations](#8-drawbacks-and-limitations)
9. [The Parameter Tuner](#9-the-parameter-tuner)
10. [Additional Details](#10-additional-details)

---

## 1. The Elo Rating System — and How This Implementation Differs

Classical Elo (originally for chess) rates players with a single number and predicts the chance of one player beating another with a logistic curve. This implementation keeps that core idea but uses a different scale:

```
predict_winchance(my_rating, enemy_rating) = 1 / (1 + 2 ** ((enemy_rating - my_rating) / 100))
```

Two changes from the chess standard (which uses `1 / (1 + 10 ** ((enemy - my) / 400))`):

1. **Base 2 instead of base 10.** The rating gap that corresponds to a 2:1 win probability is defined directly by the base. Here, a team rated **100 points higher** than an opponent wins with chance `1 / (1 + 2^-1) = 2/3`, while the underdog wins with chance `1/3`. A 100-point gap therefore means a **2-fold increase in win chance** (2:1 odds). In the chess standard, a 400-point gap gives 10:1 odds; this system uses 100 points for 2:1 odds instead, so the ratings move on a more intuitive scale.
2. **Zero is the mean.** All teams are added with an initial rating of `0` (see `#add` in the ledger files), and `0` is the "average" rating. Positive ratings are above average, negative ratings are below average. The `#squash` command (Section 5) regresses ratings toward exactly this mean.

The win chance formula is symmetric: a team's win chance plus its opponent's win chance always sum to 1, and a team rated equal to its opponent (after home field adjustments) has a 50% win chance.

---

## 2. Only the Final Score Matters

The system ingests nothing but the final score of every game. This is a deliberate design choice, not a limitation:

> `calculate_elos.py` processes one line per game: `TeamA,V,20,TeamB,H,35` — name, venue flag, score, name, venue flag, score.

The key insight is that **every meaningful on-field stat is already encoded in the final score.** Yards gained, turnovers, time of possession, third-down conversions, red-zone efficiency, penalties — all of these are simply inputs to the scoring process. The final score is the *output* of every play of the game, so it is a compressed, complete summary of what happened. Two teams that played statistically identical games will have produced the same final score; the model needs nothing else.

This has a huge practical advantage: final scores are the single most reliable, complete, and unbiased piece of data available for every game. No stats databases, no home/away splits of box scores, no per-game per-team stat sheets to merge or clean. The model is therefore trivially applicable to any sport — college football, the NFL, or anything else with a scoreboard — and is immune to "stat availability bias" (e.g., FCS games where detailed stats don't exist).

The trade-off is that the final score is a *lossy* summary of team quality (see Section 8).

---

## 3. From Final Score to Result Winchance — and the Rating Adjustment

Elo works in *winchance space*. Before a game, the model has a **prediction** for each team — the expected winchance based on their ratings (plus home field boosts, Section 4):

```
a_expected_winchance = predict_winchance(a_rating + a_home_boost, b_rating + b_home_boost)
b_expected_winchance = 1 - a_expected_winchance
```

After the game, the model needs an equivalent 0–1 number describing *what actually happened* — the **result winchance**. The final score is converted into this number by `result_winchance_sigmoid`:

```python
diff  = my_score - enemy_score
total = my_score + enemy_score

numerator   = VAR_A * diff**2  + VAR_B * diff  + VAR_C
denominator = VAR_D * total**2 + VAR_E * total + VAR_F

return 1 / (1 + 2 ** (-numerator / denominator))
```

This is a **logistic (sigmoid) curve over both the point differential AND the total points scored in the game**:

- **Point differential (`diff`)** drives the numerator. The bigger the margin of victory, the closer the result winchance gets to 1.0 for the winner. Because the numerator is a *second-degree* polynomial, margins are amplified: a 30-point win is treated as far more than "3x" a 10-point win — it is, rightly, seen as a near-total dominance.
- **Total points (`total`)** scales the denominator. The more points scored in the game, the more the result winchance is pulled back toward the neutral 0.5. This is the model's way of measuring *how decisive the margin actually was*:
  - A **14-point win in a 17–3 defensive slugfest** is enormously decisive — that score was produced by a dominant defense, and the model's result winchance for the winner is very close to 1.0.
  - A **14-point win in a 55–41 shootout** is far less decisive — in a high-scoring, high-variance game, that margin is "cheap" and could easily have flipped; the result winchance is much closer to 0.5.

  In other words, the same margin counts for less when both teams are scoring at will, and more when the game is tight and low-scoring. The tuner chooses the `VAR_A`–`VAR_F` constants per sport so this contextualization matches real-world predictability.

The function also handles the edge cases: a **tie** is exactly `0.5`, a **shutout win** is exactly `1.0` (you literally cannot lose that game), and losses are computed symmetrically via recursion (`result = 1 - result_of_the_reverse_game`).

The result winchance is now directly comparable to the prediction, because both live on the same 0–1 "probability of winning" scale:

```
a_error = a_result_winchance - a_expected_winchance   # in (-1, 1)
```

The **error** is the model's mistake: positive when the team beat expectations, negative when it fell short. The rating adjustment is:

```
a_elo_change = uncertainty_multiplier[a] * a_error * MAX_ELO_CHANGE
```

- `a_error` is a winchance in (-1, 1), so it is bounded — an upset can never move a rating by more than `MAX_ELO_CHANGE`.
- `MAX_ELO_CHANGE` is the cap on a single game's movement (default 150; tuned to ~28 for CFB, ~21 for the NFL). It is the "how much does one game count" knob.
- `uncertainty_multiplier[a]` is the per-team learning-rate scaling factor described in Sections 5 and 6 — a team the model is unsure about gets moved more aggressively.

Each team's rating is then updated: `elo_ratings[team].append(prev_rating + elo_change)`. If the model predicted a 75% chance and the team had a shutout win (equal to 100% result winchance), the error is `+0.25` and the rating rises by `0.25 * uncertainty * MAX_ELO_CHANGE`; if the model predicted 75% and the team was shutout in a loss, the error is `-0.75` and the rating falls roughly three times as much — the model learns more from surprising results than from expected ones.

---

## 4. Home Field Advantage, Learned Per Team

Home field advantage is **not** a single global constant — every team carries its own home field value, initialized to `HOME_FIELD_ELO` (default 50, tuned to ~42 for CFB and ~24 for the NFL).

During a game, each team's rating is boosted by its own home field value before the prediction is made:

```
a_expected_winchance = predict_winchance(a_rating + a_home_boost, b_rating + b_home_boost)
```

The boost is **added to the prediction but never to the stored rating** — it is a game-time situational adjustment, not a change in true team strength. (The "Win 50" and strength-of-schedule calculations in Section 10 carefully add/subtract these boosts to isolate pure team strength.)

After every game, the home team's boost is itself updated from the same prediction error:

```
home_field_boost[team] = max(0, home_field_boost[team] + HOME_FIELD_MULTIPLIER * error)
```

- A home team that **beat expectations** (error > 0) sees its home field value **increase** — this stadium is more of a factor than we thought.
- A home team that **underperformed** (error < 0) sees its home field value **decrease** — its crowd isn't worth as much as we assumed.
- The value is clamped at 0 — a team can't have a *negative* home field advantage (a neutral-site floor).

Over time the model learns that, for example, one program is a completely different animal in its own stadium while another wins equally well anywhere. `HOME_FIELD_MULTIPLIER` (tuned to ~5.1 for CFB, ~1.0 for NFL) controls how quickly the per-team values adapt. This also means neutral-site games (`V` vs `V`) get no boost for either side, and the boost differences between two teams in the same game simply cancel to their net effect.

---

## 5. A New Season: Squashing Ratings and Resetting Uncertainty

A football team in September is not the same team that played in November. Roster turnover (graduation, transfers, NFL draft), coaching changes, scheme changes, and player development all mean that *last season's ratings are stale information*. Three ledger commands handle this at each `// <season>` boundary:

**`#squash <fraction>` — regression toward the mean.**
Every team's rating is moved a fraction of the way back to the mean of `0`:

```
new_elo = old_elo + squash_fraction * (0 - old_elo)
```

This shrinks the rating spread between seasons, because the spread reflects last year's teams, not this year's. A positive fraction (e.g. 0.32, as tuned for the NFL) is classic mean reversion — big ratings shrink toward average. Interestingly, the tuned CFB value is *negative* (-0.087), which pushes ratings *away* from 0, counteracting the tendency for a season of close, score-driven games to compress everyone toward the middle. Either way, `squash_fraction` is the tuner's choice of "how much of last year do we keep?"

**`#newseason` — reset the slate.**
Clears each team's game history (which drives the display tables and the strength-of-schedule "Win 50" math in Section 10) and resets the fake-game counters. Ratings themselves persist — this is a fresh season built on a squashed foundation, not a memory wipe.

**`#setrate <value>` — uncertainty spike.**
Sets every team's `uncertainty_multiplier` to the given value (tuned to ~7.8 for CFB, ~2.5 for the NFL). Because this multiplier is multiplied into every Elo change (Section 3), ratings **swing much harder early in the season** — exactly what you want when last year's squashed ratings are a poor guide to this year's teams. The system knows it knows little right now, and lets the first few games do a lot of the work.

---

## 6. How Uncertainty Decays — and How Upsets Renew It

The `uncertainty_multiplier` is a per-team learning rate: how much of each game's prediction error should be written into the rating. It starts high at the beginning of a season (via `#setrate`, Section 5) and is designed to **decay toward exactly 1.0** as the season goes on:

```
uncertainty = (old_uncertainty - 1) * LEARNING_RATE_DECAY
            + UNCERTAINTY_INCREASE * abs(error) ** UNCERTAINTY_ERROR_SENSITIVITY
            + 1
```

Reading this piece by piece:

1. **The decay term.** `(old_uncertainty - 1) * LEARNING_RATE_DECAY` pulls the multiplier toward its floor of 1.0 after every game the team plays. `LEARNING_RATE_DECAY` (tuned to ~0.79 for CFB, ~0.86 for the NFL) sets the speed: each game erases a chunk of the surplus uncertainty. After enough games, the team's multiplier is effectively 1.0 — the model now has a large, reliable sample of that team's games and treats each new game at face value (`error * MAX_ELO_CHANGE`).

2. **The surprise term.** `UNCERTAINTY_INCREASE * abs(error) ** UNCERTAINTY_ERROR_SENSITIVITY` is *added* back into the multiplier. The bigger the prediction error — i.e., the more unexpected the result — the more uncertainty the team keeps going forward. A team that gets blown out when the model was confident they'd win by three scores has just told the model "you don't actually know me," so the model should keep its guard up and be willing to make large corrections in that team's future games. A comfortable win exactly as predicted adds almost nothing back.

The result is a beautifully adaptive system:

- **Early season:** uncertainty ~7.8 → every game moves ratings ~7.8x more than a mature team's game. Upstarts shoot up and overhyped teams crash down quickly.
- **Mid season:** uncertainty decaying steadily toward 1.0 as each team accrues games; the model trusts its picture more and more.
- **Any time, any team:** an upset — or any result far from the prediction — *renews* that specific team's uncertainty, so the model can correct its estimate of them with a large swing next game instead of stubbornly chipping away.

Note that `LEARNING_RATE_DECAY`, `UNCERTAINTY_INCREASE`, and `UNCERTAINTY_ERROR_SENSITIVITY` are all globally tunable per ledger (via `#setratedecay`, `#uncertaintyincrease`, `#uncertaintyerrorsensitivity`).

---

## 7. Strengths of the System

- **Extremely lean data requirements.** Only final scores are needed, so the system is complete, cheap, and instantly portable to any sport (see the CFB and NFL ledgers). There is no dependency on proprietary stats or per-game box-score databases.
- **Margin-of-victory aware.** Unlike classical Elo (win/loss only), a blowout is rewarded far more than a one-score nail-biter.
- **Context-aware margin.** The total-points term means a 14-point win in a 3–17 slugfest and a 14-point win in a 41–55 shootout are weighted very differently — the model knows *how decisive* the margin was, not just its size.
- **Everything is a winchance.** Predictions, results, and errors are all probabilities on the same 0–1 scale, so the numbers are intuitive, bounded, and directly comparable to Vegas moneylines.
- **Self-correcting and adaptive.** Ratings are updated to make the next prediction better; the uncertainty mechanism (Sections 5–6) lets the model deliberately distrust its own stale view and recover quickly when it's wrong.
- **Per-team home field advantage.** No universal constant forced on every team — stadium effects are learned from each team's own home results.
- **Seasonal handling of roster turnover.** Squash + uncertainty reset acknowledges that ratings describe last year's team, not this year's.
- **Strength-of-schedule adjusted ranking.** The "Win 50" calculations (Section 10) answer "how good do you have to be to go .500 against *this* team's actual schedule?" — a fairer cross-team comparison than raw ratings, which reward playing tough opponents.
- **Tuned per sport.** `tune_values.py` (Section 9) searches for the parameters (K-factor, home field, uncertainty decay, sigmoid shape) that minimize prediction error against real historical results, so CFB and the NFL get their own settings.
- **Betting integration.** `calculate_bets.py` converts moneylines into implied Vegas winchances and computes the expected value of every bet per the model, flagging favorable wagers.

---

## 8. Drawbacks and Limitations

**Off-field factors the model cannot see.** The system has no eyes for the thousands of things that shape a game but aren't a final score:

- Injuries and suspensions — a star QB out for a week, a defense decimated mid-season.
- Coaching changes and coordinator turnover mid-season.
- Motivation, spotlights, rivalry games, letdown spots, and playoff/eligibility stakes.
- Travel distance, altitude, weather (rain, wind, heat), and kickoff time.
- Roster talent quality that would inform preseason priors (e.g., recruiting rankings) — every team starts from a squashed value of last year's final rating and must earn its rating from games.

**Only using the final score has real costs.** Because the score is a lossy summary of quality:

- **Garbage time distorts margins.** A 28-point blowout where the loser scored 14 meaningless points against backups looks identical to a 28-point game that was competitive for 58 minutes.
- **When points are scored doesn't matter.** A team that dominates for 59 minutes and loses on a last-second Hail Mary is punished exactly as much as a team that was outplayed all day but kept it close. The model can't distinguish "better team, bad luck" from "worse team."
- **Lucky bounces and fluky plays are treated as real signal.** A pick-six, a muffed punt, a missed chip-shot field goal — all permanently move ratings as if they revealed team strength.

**Structural assumptions.** Elo assumes each team has a single, stable, transitive strength number; it doesn't model *matchups* (a team can be elite vs. the run and hopeless vs. the pass), offensive vs. defensive strength separately, or home/away *ratings* as distinct things. The model predicts *winchances*, not margins, so it can't directly produce point spreads without extra work.

---

## 9. The Parameter Tuner

The system has fourteen tuned parameters — `MAX_ELO_CHANGE`, `HOME_FIELD_ELO`, `HOME_FIELD_MULTIPLIER`, `VAR_A`–`VAR_F`, `LEARNING_RATE_INITIAL`, `LEARNING_RATE_DECAY`, `UNCERTAINTY_INCREASE`, and `UNCERTAINTY_ERROR_SENSITIVITY` — and tuning them by hand would be a guessing game. `tune_values.py` automates this with a stochastic hill-climber that searches for the parameter set that best fits historical results.

### The objective function: cross-entropy

After running every game in the ledger through `calculate_elos.py`, the tuner loops over each team's game history and accumulates **cross-entropy error**:

```python
if team_won:
    cross_entropy += -log(predicted_winchance)       # high chance → small penalty; low chance → huge penalty
else:
    cross_entropy += -log(1 - predicted_winchance)
```

Cross-entropy is the standard information-theoretic cost function for binary classification. For each game it asks "how many bits of surprise did the model incur?" A prediction of 90% for a team that won is only `-log(0.90) ≈ 0.11` bits of penalty; a prediction of 10% for that same win is `-log(0.10) ≈ 2.30` bits — a massive punishment. This makes cross-entropy far more sensitive to confident-but-wrong predictions than a plain squared error would be, which spreads its penalty evenly regardless of confidence. The net effect is that the tuner optimizes for well-calibrated probabilities, not just getting the right winner, and it strongly discourages the model from making confident calls on outcomes it can't actually predict.

As auxiliary diagnostics (tracked but not used in optimization), the tuner also reports:

- **Average linear error:** the mean absolute winchance miss per game — a simple "how far off was I on average?" metric.
- **Percent correct:** the raw win/loss accuracy — of every game in the ledger, how many had the model's winchance > 50% for the team that actually won?

### The search algorithm

The tuner is a **single-parameter stochastic hill climber** — not gradient descent, not genetic algorithms. It works like this:

1. **Pick one parameter** to mutate. Parameters are chosen probabilistically, weighted inversely by a `base` value that tracks how volatile each parameter is — parameters that have been harder to improve are mutated more aggressively.
2. **Mutate it.** The current value is multiplied by two random ratios, effectively stretching or shrinking it by a random factor that is always positive (the ratio is always positive, so the sign of a parameter is preserved). A small chance of sign-flip is allowed when the value is very close to zero, in case the optimum is slightly negative.
3. **Evaluate.** The entire ledger is replayed with the new parameter set; cross-entropy is calculated.
4. **Keep or discard.** If the new cross-entropy is strictly lower than the current best, the mutation is accepted; otherwise the old parameters are kept.

Every **1,000 iterations**, the `base` for each parameter is adjusted:
- If a parameter has received mostly failed mutations (base grows), the mutation scale widens — the tuner searches more broadly.
- If a parameter improves frequently (base shrinks), the mutation scale tightens — the tuner searches more locally around a productive region.
- Parameters that see almost no successful mutations have their bases doubled, effectively deprioritizing them.

The run terminates when every parameter's base exceeds 1,000,000 — meaning the tuner has exhausted its ability to find improvements at any scale.

### Why not gradient descent?

The Elo engine is not a smooth, differentiable function in its parameters. The `#squash`/`#setrate`/uncertainty system, the per-game sequential updates, and the home field interactions all mean that small parameter changes can have unpredictable effects downstream. The stochastic hill climber sidesteps this entirely — it just asks "is the new parameter set better than the old one?" — and the random perturbations naturally explore the space without needing derivatives.

The tuned parameter block that appears at the top of each ledger file (the `// Error: ...` comment and the following `#maxelochange`, `#var_*`, etc.) is the direct output of a `tune_values.py` run over that ledger's historical data.

---

## 10. Additional Details

### File layout

| File | Purpose |
|------|---------|
| `calculate_elos.py` | The engine. Parses the ledger and computes ratings, home field boosts, uncertainty, history, and Win-50 metrics. |
| `calculate_bets.py` | Reads a ledger plus a moneyline file and computes model winchance vs. Vegas implied winchance per bet, outputting expected-value-ranked HTML. |
| `tune_values.py` | Stochastic parameter tuner (Section 9). Mutates one parameter at a time and keeps improvements; minimizes cross-entropy prediction error over the ledger (the "Error: ..." comments in the ledgers are its output). |
| `generate_html.py` | Renders the rankings table (expandable per-team game history) and the bets table. |
| `format_ncaa_games.py` | Clipboard-scraper that turns highlighted scoreboard text from ncaa.com into ledger game lines. |
| `format_cbssports_nfl_games.py` | Same, for the CBS Sports NFL scoreboard. |
| `cfb_ledger_input.txt` / `nfl_ledger_input.txt` | The chronological game ledgers (2017–present), including tuned parameters and per-season squash/setrate commands. |
| `*.html` | Generated output: current rankings (`*_elos.html`) and betting hunches. |

### Ledger input format

Blank lines and `//` comments are ignored. Commands are processed in file order, so games must be listed chronologically:

| Command | Effect |
|---------|--------|
| `#add TeamName,0` | Register a team at rating 0 (the mean). |
| `TeamA,V,20,TeamB,H,35` | A game: `name, V/H, score, name, V/H, score`. The venue flag is `H` for home, `V` for away/neutral. |
| `#newseason` | Clear per-team game history and fake-game counters. |
| `#squash <f>` | Move all ratings a fraction of the way to 0. |
| `#setrate <v>` | Set all teams' uncertainty multiplier to `v`. |
| `#homefieldelo <v>` | Global starting home field boost. |
| `#homefieldmultiplier <v>` | Per-game learning rate for a home team's boost. |
| `#maxelochange <v>` | Cap on a single game's rating change. |
| `#setratedecay <v>` | Uncertainty decay factor. |
| `#uncertaintyincrease <v>` | How much a surprise result adds back to uncertainty. |
| `#uncertaintyerrorsensitivity <v>` | Exponent on the error in the uncertainty term. |
| `#var_a` … `#var_f` | The six constants of the result-winchance sigmoid. |
| `#name <s>` | Title shown in generated HTML. |
| `#end` | Stop processing (later games are ignored). |

The tuned parameter block at the top of each ledger (e.g. `// Error: 2038.3` followed by `#maxelochange 28.285`, `#homefieldelo 42.443`, the six `#var_*` values, and the three `#uncertainty*` values) comes straight out of `tune_values.py`.

### Fake games and strength of schedule

Games involving teams that were never added to the rating pool (e.g. an FCS opponent, or a team not on the ledger) are skipped, but the registered team is credited with a **fake game**, counted as an automatic win for schedule purposes. This ensures that a team's win percentage is measured against the number of games they actually played without letting unregistered (unrateable) opponents distort ratings. This is only useful for the Win 50 strength of schedule report described below.

### Win 50 Elo

For every team the engine computes the hypothetical rating that would yield exactly a 50% expected win percentage against the exact slate of opponents that team actually faced (home/away boosts included). This statistic has no relevance to rating adjustments, it is calculated just for fun. Opponent strength is inherently included in all prediction percentages already, so strength of schedule has already been accounted for in the actual ratings.  Here are the two Win 50 statistics provided:

- **Win 50 (past):** uses each opponent's rating *at game time*.
- **Win 50 (present):** uses each opponent's *current* rating.

A team that played only elite opponents needs a very high Win-50 rating to go .500 against them; a team that feasted on cupcakes needs a much lower one. It's a cleaner strength-of-schedule-adjusted estimate of "how good is this team, really" than the raw rating, which mechanically rewards beating (and being exposed to) good teams.

### The betting calculator

`calculate_bets.py` reads a moneyline file (`Team,V,-380,Opponent,V,+300`) and converts each American moneyline into an implied Vegas winchance (`100/(line+100)` for underdogs, `line/(line-100)` for favorites). It compares that to the model's winchance and computes the expected payout of each bet, ranking the best edges. The default betting file format expects both sides of each game listed.

### A note on dead code

`result_winchance` (and the `POINTS_PER_SCORE` constant it references) is a leftover combinatorial "stars and bars" approach from an earlier version of the system. `POINTS_PER_SCORE` is never defined, so that function is not callable — the live code path uses `result_winchance_sigmoid` exclusively, as confirmed by git history ("Rehaul winchance calculation to use sigmoid curve instead of pointsperscore"). The dead function can be safely ignored or removed.
