from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi
MONGO_URI = "mongodb+srv://adithyaaaig04_db_user:AE233FlFM7ZFmMhY@queuecli.uqfdrhl.mongodb.net/?appName=queueCLI"

# Create a new client and connect to the server
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())


db = client.queueCLI
collection = db["jobs"]
dlq_collection = db["dlq"]  

config = {
    "max_retries": 3,   # default max retries
    "base_delay": 2.0,  # default exponential backoff base
}
