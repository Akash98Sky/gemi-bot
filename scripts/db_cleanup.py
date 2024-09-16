from pymongo import MongoClient
from dotenv import load_dotenv
from os import getenv

load_dotenv()

client = MongoClient(getenv("MONGODB_URL"))

db = client.get_default_database()

for collection_name in db.list_collection_names():
    coll = db.get_collection(collection_name)

    # truncate collection
    coll.delete_many({})
