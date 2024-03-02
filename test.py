import pymongo

client = pymongo.MongoClient("mongodb://raspberrypi:27017/")
db = client["lounge"]
players = db["players"]
history = db["history"]

client.close()
