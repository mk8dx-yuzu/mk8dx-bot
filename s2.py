import os
import math
from dotenv import load_dotenv
import pymongo
from pymongo import collection, database

load_dotenv()

client = pymongo.MongoClient(f"mongodb://{os.getenv('MONGODB_HOST')}:27017/")

db = client["lounge"]
players: collection.Collection = db["players"]

def NewSeasonMMR(mmr):
  if (mmr <= 1):
    return 1500
  elif (mmr < 2000):
    return math.ceil(1500 + mmr / 4)
  elif (mmr == 2000):
    return 2000
  else:
    return math.ceil(1000 + mmr / 2)

all_players = players.find()
for player in all_players:
  new_mmr = NewSeasonMMR(player["mmr"])
  players.update_one({"discord": player["discord"]}, {"$set": {
    "mmr": new_mmr,
    "wins": 0,
    "losses": 0,
    "history": []
    }})