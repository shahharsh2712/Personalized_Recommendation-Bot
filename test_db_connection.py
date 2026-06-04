import os
import sys

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

load_dotenv()

TIMEOUT_MS = 5000


def main():
    mongo_uri = os.getenv("MONGODB_URI") or "mongodb://localhost:27017/"
    db_name = os.getenv("RECOMMENDATION_DB_NAME") or "app_recommendations"

    print(f"Connecting to {mongo_uri} (timeout {TIMEOUT_MS}ms)...")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=TIMEOUT_MS)

    try:
        client.admin.command("ping")
        print(f"MongoDB OK — database: {db_name}")
    except ServerSelectionTimeoutError:
        print(
            "MongoDB is not reachable. Start MongoDB locally or set MONGODB_URI in .env "
            "to a MongoDB Atlas connection string.",
            file=sys.stderr,
        )
        return 1
    finally:
        client.close()

    from storage.database import Database

    db = Database()
    db.close()
    print("Database collections initialized.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
