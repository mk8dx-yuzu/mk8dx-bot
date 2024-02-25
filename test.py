import pymongo

client = pymongo.MongoClient("mongodb://raspberrypi:27017/")
db = client["lounge"]
players = db["players"]
history = db["history"]


client.close()

one, two, three, four = 1, 2, 3, 4

print(one, two, three, four)