from pymongo import MongoClient
from env import MONGO_CONNECTION_STRING

# MongoDB connection setup
client = MongoClient(MONGO_CONNECTION_STRING)
db = client["attendanceDB"]

# Define schema for the "attendance" collection
def initialize_collections():
    attendance_collection = db["attendance"]

    # Create indexes for faster queries
    attendance_collection.create_index("name", unique=True)

    # Update existing documents to match the schema
    for record in attendance_collection.find():
        update_fields = {}
        if "phone" not in record:
            update_fields["phone"] = None  # Add a default phone field
        if "attendance" not in record or not isinstance(record["attendance"], list):
            update_fields["attendance"] = []  # Ensure attendance is a list
        elif isinstance(record["attendance"], list):
            # Ensure all entries in the attendance list are dictionaries with lat/long
            update_fields["attendance"] = [
                {
                    **entry,
                    "latitude": entry.get("latitude", None),
                    "longitude": entry.get("longitude", None)
                }
                if isinstance(entry, dict) else {"date": entry, "status": "present", "latitude": None, "longitude": None}
                for entry in record["attendance"]
            ]
        if update_fields:
            attendance_collection.update_one({"_id": record["_id"]}, {"$set": update_fields})

    print("✅ MongoDB schema initialized and updated.")

# Function to add attendance entry
def add_attendance_entry(name, phone, date, status, latitude=None, longitude=None):
    attendance_collection = db["attendance"]
    attendance_collection.update_one(
        {"name": name},
        {
            "$set": {"phone": phone},
            "$push": {"attendance": {"date": date, "status": status, "latitude": latitude, "longitude": longitude}}
        },
        upsert=True
    )

if __name__ == "__main__":
    initialize_collections()
