import pymongo

# Replace these with your details
client = pymongo.MongoClient("mongodb://raspberrypi:27017/")
db = client["lounge"]
collection = db["players"]

""" collection.insert_one({
    "name": "test",
    "mmr": 3932,
    "wins": 5,
    "losses": 0
}) """

docs = collection.find()
for doc in docs:
    print(doc)

player_mmr = collection.find_one({"name": "probablyjassin"}, {"_id": 0, "mmr": 1})
print(player_mmr)


client.close()