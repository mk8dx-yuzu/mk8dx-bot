"""import pymongo

client = pymongo.MongoClient("mongodb://raspberrypi:27017/")
db = client["lounge"]
players = db["players"]
history = db["history"]

client.close()
 """

import trueskill
from trueskill import Rating, rate, global_env, setup

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

placements = [i for i in range(1, 7)]

new_ratings = rate(racers, placements)

print(new_ratings)

[
    "(trueskill.Rating(mu=5524.414, sigma=393.889),)",
    "(trueskill.Rating(mu=3870.975, sigma=388.235),)",
    "(trueskill.Rating(mu=2779.996, sigma=386.267),)",
    "(trueskill.Rating(mu=2471.141, sigma=385.523),)",
    "(trueskill.Rating(mu=2395.339, sigma=385.193),)",
    "(trueskill.Rating(mu=2237.702, sigma=385.048),)",
    "(trueskill.Rating(mu=2750.875, sigma=385.023),)",
    "(trueskill.Rating(mu=2571.628, sigma=385.103),)",
    "(trueskill.Rating(mu=1638.649, sigma=385.321),)",
    "(trueskill.Rating(mu=1446.243, sigma=385.695),)",
    "(trueskill.Rating(mu=1849.516, sigma=386.411),)",
    "(trueskill.Rating(mu=1749.525, sigma=388.860),)",
]

[
    (
        trueskill.Rating(mu=5469.860, sigma=400.461),
        trueskill.Rating(mu=3784.860, sigma=400.461),
    ),
    (
        trueskill.Rating(mu=2726.283, sigma=396.781),
        trueskill.Rating(mu=2443.283, sigma=396.781),
    ),
    (
        trueskill.Rating(mu=2367.787, sigma=395.896),
        trueskill.Rating(mu=2236.787, sigma=395.896),
    ),
    (
        trueskill.Rating(mu=2751.169, sigma=395.811),
        trueskill.Rating(mu=2596.169, sigma=395.811),
    ),
    (
        trueskill.Rating(mu=1658.962, sigma=396.235),
        trueskill.Rating(mu=1495.962, sigma=396.235),
    ),
    (
        trueskill.Rating(mu=1891.940, sigma=397.486),
        trueskill.Rating(mu=1862.940, sigma=397.486),
    ),
]
