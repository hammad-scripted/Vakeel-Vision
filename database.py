import os
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

load_dotenv()
logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv(
    "MONGODB_URI", "mongodb+srv://hammadscripted_db_user:KBtx9OZcdHVzYpPN@cluster0.xte0cab.mongodb.net/vakil_db?retryWrites=true&w=majority"
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
        logger.info("Connected to MongoDB and created indexes.")
    except ConnectionFailure as e:
        logger.exception("Failed to connect to MongoDB")
        raise RuntimeError("Failed to initialize MongoDB") from e


def close_db():
    client.close()
    logger.info("MongoDB connection closed.")
