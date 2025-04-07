import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Access environment variables
# Use 'mongodb://' for standalone or replica set MongoDB instances
MONGO_CONNECTION_STRING = "mongodb://<username>:<password>@<host>:<port>/<database>?retryWrites=true&w=majority"
if not MONGO_CONNECTION_STRING:
    raise ValueError("Environment variable 'MONGO_CONNECTION_STRING' is not set.")
