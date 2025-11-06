from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://adithyaaaig04_db_user:AE233FlFM7ZFmMhY@queuecli.uqfdrhl.mongodb.net/?appName=queueCLI"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

db = client.queueCLI
collection = db["jobs"]