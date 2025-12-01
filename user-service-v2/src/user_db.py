import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "userdb")

mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client[MONGO_DB]
users_collection = db["users"]
