from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
from env import MONGO_CONNECTION_STRING  # Import connection string from env.py

# MongoDB connection setup
try:
    client = MongoClient(
        MONGO_CONNECTION_STRING,
        serverSelectionTimeoutMS=5000,
        tls=True,
        tlsAllowInvalidCertificates=False
    )
    db = client["attendanceDB"]
    attendance_collection = db["attendance"]
    client.server_info()  # Test the connection
    print("✅ Connected to MongoDB successfully.")
except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    attendance_collection = None

def mark_attendance_in_db(name, phone, latitude, longitude, is_registration=False):
    """Mark attendance or register a user in the MongoDB database."""
    if attendance_collection is None:
        print("⚠️ MongoDB connection unavailable.")
        return

    now = datetime.now()
    date = now.strftime("%d-%m-%y %H:%M")

    if is_registration:
        # Handle user registration
        record = attendance_collection.find_one({"name": name})
        if record:
            print(f"ℹ️ User {name} is already registered.")
        else:
            attendance_collection.insert_one({
                "name": name,
                "phone": phone,
                "attendance": []
            })
            print(f"✅ User {name} registered successfully.")
    else:
        # Handle attendance marking
        record = attendance_collection.find_one({"name": name})
        if record:
            if any(entry["date"] == date for entry in record.get("attendance", [])):
                print(f"⚠️ Attendance already marked for {name} at {date}.")
            else:
                attendance_collection.update_one(
                    {"name": name},
                    {"$push": {"attendance": {
                        "date": date,
                        "status": "present",
                        "latitude": latitude,
                        "longitude": longitude
                    }}}
                )
                print(f"✅ Marked attendance for {name}.")
        else:
            print(f"⚠️ User {name} not found. Please register first.")
