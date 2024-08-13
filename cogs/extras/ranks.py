import math

def calcRank(mmr):
    ranks = [
        {"name": "Wood", "range": (-math.inf, 1)},
        {"name": "Bronze", "range": (2, 1499)},
        {"name": "Silver", "range": (1400, 2999)},
        {"name": "Gold", "range": (3000, 5099)},
        {"name": "Platinum", "range": (5100, 6999)},
        {"name": "Diamond", "range": (7000, 9499)},
        {"name": "Master", "range": (9500, math.inf)},
    ]
    for range_info in ranks:
        start, end = range_info["range"]
        if start <= mmr <= end:
            return range_info["name"]
    return "---"

ranks = [
        {"name": "Wood", "range": (-math.inf, 1)},
        {"name": "Bronze", "range": (2, 1499)},
        {"name": "Silver", "range": (1400, 2999)},
        {"name": "Gold", "range": (3000, 5099)},
        {"name": "Platinum", "range": (5100, 6999)},
        {"name": "Diamond", "range": (7000, 9499)},
        {"name": "Master", "range": (9500, math.inf)},
    ]