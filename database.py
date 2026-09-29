import os
import logging
from urllib.parse import urlsplit
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()
logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI environment variable is required.")

MONGODB_HOST = urlsplit(MONGODB_URI).hostname or "unknown"

# Fail sooner when the configured MongoDB deployment cannot be reached.
client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
)
db = client.get_default_database()

# Collections
contracts_collection = db["contracts"]
analysis_collection = db["analysis"]


def init_db():
    try:
        logger.info("Connecting to MongoDB host %s, database %s.", MONGODB_HOST, db.name)
        # Verify connection to server
        client.admin.command("ping")

        # Create indexes
        contracts_collection.create_index("filename", unique=True)
        analysis_collection.create_index("contract_id", unique=True)
        logger.info("Connected to MongoDB and created indexes.")
    except PyMongoError as e:
        logger.exception(
            "MongoDB initialization failed for host %s, database %s (%s): %s",
            MONGODB_HOST,
            db.name,
            type(e).__name__,
            e,
        )
        raise RuntimeError(
            "Failed to initialize MongoDB. Check MONGODB_URI, Atlas Network Access, "
            "and cluster availability."
        ) from e


def close_db():
    client.close()
    logger.info("MongoDB connection closed.")
