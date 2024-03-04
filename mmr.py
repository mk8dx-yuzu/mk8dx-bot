"""import pymongo

client = pymongo.MongoClient("mongodb://raspberrypi:27017/")
db = client["lounge"]
players = db["players"]
history = db["history"]

client.close()
 """

import trueskill
from trueskill import Rating, rate, global_env, setup
from collections import OrderedDict

global_env()
setup(
    mu=2000,
    sigma=200,
    beta=1200,
    tau=350,
    draw_probability=0.05,
    backend=None,
    env=None,
)

mu = 2000
sigma = 200
beta = 1200
tau = 350

racers = [
    [
        Rating(5448, sigma),
        Rating(3763, sigma),
    ],
    [
        Rating(2638, sigma),
        Rating(2355, sigma),
    ],
    [
        Rating(2320, sigma),
        Rating(2189, sigma),
    ],
    [
        Rating(2802, sigma),
        Rating(2647, sigma),
    ],
    [
        Rating(1658, sigma),
        Rating(1495, sigma),
    ],
    [
        Rating(2000, sigma),
        Rating(1971, sigma),
    ],
]

placements = [6, 2, 1, 4, 5, 3]

new_ratings = rate(racers, placements)

new_mmr = []
for team in new_ratings:
    new_mmr.append([round(player.mu) for player in team])

teams_with_positions = OrderedDict(zip(tuple(new_mmr), tuple(placements)))

sorted_teams = sorted(teams_with_positions.items(), key=lambda item: item[1])

sorted_teams_list = [team for team, _ in sorted_teams]

print(sorted_teams_list)