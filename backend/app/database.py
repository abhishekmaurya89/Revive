from pymongo import MongoClient

from app.config import settings


client = MongoClient(settings.mongodb_url)

db = client[settings.mongodb_database]

payments_collection = db["payments"]
recoveries_collection = db["recoveries"]