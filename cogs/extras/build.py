import random
from itertools import combinations

def shuffle_teams(players: list[dict], format: int) -> list[dict]:
    def team_score(team):
        return sum(player["mmr"] for player in team)

    best_teams = None
    min_score_diff = float("inf")

    for teams in combinations(players, format):
        remaining_players = [p for p in players if p not in teams]
        for other_teams in combinations(remaining_players, format):
            team1_score = team_score(teams)
            team2_score = team_score(other_teams)
            score_diff = abs(team1_score - team2_score)
            if score_diff < min_score_diff:
                min_score_diff = score_diff
                best_teams = [teams, other_teams]

    return [[f"<@{player['discord']}>" for player in team] for team in best_teams]