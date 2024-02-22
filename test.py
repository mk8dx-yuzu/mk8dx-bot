import pymongo

# Replace these with your details
client = pymongo.MongoClient("mongodb://raspberrypi:27017/")
db = client["admin"]
collection = db["mk8dx"]

""" collection.insert_one({
    "name": "test",
    "mmr": 3932,
    "wins": 5,
    "losses": 0
}) """

docs = collection.find()
for doc in docs:
    print(doc)

client.close()