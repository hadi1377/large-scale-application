import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from urllib.parse import urlparse

# MongoDB connection
client: Optional[AsyncIOMotorClient] = None
database = None


async def connect_to_mongo():
    """Create database connection"""
    global client, database
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/product_db")
    client = AsyncIOMotorClient(mongodb_url)
    
    # Extract database name from URL
    parsed_url = urlparse(mongodb_url)
    db_name = parsed_url.path.lstrip('/').split('?')[0] if parsed_url.path else 'product_db'
    if not db_name:
        db_name = 'product_db'
    
    database = client[db_name]
    print(f"Connected to MongoDB: {database.name}")


async def close_mongo_connection():
    """Close database connection"""
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")


def get_database():
    """Get database instance"""
    return database

