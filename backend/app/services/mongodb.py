from pymongo import AsyncMongoClient

from app.config import settings


mongo_client = AsyncMongoClient(settings.mongodb_url)

db = mongo_client[settings.mongodb_database]

payments_collection = db["payments"]
recoveries_collection = db["recoveries"]