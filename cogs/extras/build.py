import random
from itertools import combinations, permutations

def shuffle_teams(players: list[dict], format: int) -> list[dict]:
    def team_score(team):
        return sum(player["mmr"] for player in team)

    num_teams = len(players) // format
    best_teams = None
    min_score_diff = float("inf")

    for team_combination in permutations(combinations(players, format), num_teams):
        used_players = set()
        valid_combination = True
        for team in team_combination:
            if any(player in used_players for player in team):
                valid_combination = False
                break
            used_players.update(team)
        
        if not valid_combination:
            continue

        scores = [team_score(team) for team in team_combination]
        score_diff = max(scores) - min(scores)
        if score_diff < min_score_diff:
            min_score_diff = score_diff
            best_teams = team_combination

    return [[f"<@{player['discord']}>" for player in team] for team in best_teams]