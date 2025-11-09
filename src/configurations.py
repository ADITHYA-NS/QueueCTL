from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Create a new client and connect to the server
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())


db = client.queueCLI
collection = db["jobs"]
dlq_collection = db["dlq"]  

config = {
    "max_retries": 3,   # default max retries
    "base_delay": 2.0,  # default exponential backoff base
}
