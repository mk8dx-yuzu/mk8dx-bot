import math

# MMR Formula from https://docs.google.com/document/d/1IowqAokeJqQWhjJ__TcQn5hbDqoK5irUVmvb441-90Q/edit
caps = {1: 60, 2: 120, 3: 180, 4: 240, 6: 300}
scaling_factors = {1: 9500, 2: 5500, 3: 5100, 4: 4800, 6: 4650}
offsets = {1: 2746.116, 2: 1589.856, 3: 1474.230, 4: 1387.511, 6: 1344.151}


def get_mmr_delta_when_won(team_size, winner_mmr, loser_mmr):
    return caps[team_size] / (1 + math.pow(11, -(loser_mmr - winner_mmr - offsets[team_size]) / scaling_factors[team_size]))


def get_mmr_delta_when_tied(team_size, mmr1, mmr2):
    return caps[team_size] / (1 + math.pow(11, -(abs(mmr1 - mmr2) - offsets[team_size]) / scaling_factors[team_size])) - (caps[team_size] / 3)


def calculate_mmr(mmrs, ranking, team_size):
    player_count = len(mmrs)
    teams = player_count // team_size

    if teams != len(ranking):
        return

    average_mmrs = []
    for i in range(teams):
        total = 0
        for j in range(team_size):
            total += mmrs[i * team_size + j]
        average_mmrs.append(total / team_size)

    mmr_deltas = []
    for i in range(teams):
        i_place = ranking[i]
        i_mmr = average_mmrs[i]

        total = 0
        for j in range(teams):
            j_place = ranking[j]
            j_mmr = average_mmrs[j]

            if i == j:
                continue
            elif i_place == j_place:
                total += (1 if i_mmr < j_mmr else -1) * \
                    get_mmr_delta_when_tied(team_size, i_mmr, j_mmr)
            elif i_place < j_place:
                total += get_mmr_delta_when_won(team_size, i_mmr, j_mmr)
            elif i_place > j_place:
                total -= get_mmr_delta_when_won(team_size, j_mmr, i_mmr)
        mmr_deltas.append(round(total))

    for i in range(player_count):
        delta = mmr_deltas[i // team_size]
        new_mmr = max(1, mmrs[i] + delta)
        delta = new_mmr - mmrs[i]

        delta_str = str(delta) if delta < 0 else "+" + str(delta)
        #print("Change player {}: {}".format(i + 1, delta_str))
        #print("New MMR player {}: {}".format(i + 1, new_mmr))

    return mmr_deltas


print( calculate_mmr([0, 777, 3447, 971], [4, 3, 1, 2], 1) )

#print( calculate_mmr([971, 0, 3447, 777], [2, 4, 1, 3], 1) )
