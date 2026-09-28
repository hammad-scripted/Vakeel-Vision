import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

load_dotenv()

MONGODB_URI = os.getenv(
    "MONGODB_URI", "mongodb://root:password@localhost:27017/vakeel_db?authSource=admin"
)

# Initialize client
client= MongoClient(MONGODB_URI)
db = client["vakeel_db"]

# Collections
contracts_collection = db["contracts"]
analysis_collection = db["analysis"]


def init_db():
    try:
        # Verify connection to server
        client.admin.command("ping")

        # Create indexes
        contracts_collection.create_index("filename", unique=True)
        analysis_collection.create_index("contract_id", unique=True)
        print(" Successfully connected to MongoDB and created indexes.")
    except ConnectionFailure as e:
        print(f" Failed to connect to MongoDB: {e}")
        sys.exit(1)


def close_db():
    client.close()
    print(" MongoDB connection closed.")
