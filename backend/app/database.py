from app.config import settings
from motor.motor_asyncio import AsyncIOMotorClient

mongo_client = AsyncIOMotorClient(settings.mongodb_uri)

database = mongo_client[settings.mongodb_database]

recovery_collection = database["recoveries"]

