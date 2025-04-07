import ollama
import cv2
import face_recognition
import numpy as np
import os
import pickle
import datetime
from dotenv import load_dotenv  # Import load_dotenv from dotenv
import pymongo
from schema import add_attendance_entry  # Removed initialize_collections import
import tkinter as tk
from tkinter import ttk, messagebox  # Added messagebox for warnings

# Load environment variables
load_dotenv()
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")

# Load stored face data and attendance records
FACE_DATA_FILE = "faces.pkl"
ATTENDANCE_FILE = "attendance.pkl"  # File to store attendance records
known_face_encodings = []
known_face_names = []
attendance_records = {}

if os.path.exists(FACE_DATA_FILE):
    with open(FACE_DATA_FILE, "rb") as f:
        known_face_encodings, known_face_names = pickle.load(f)

if os.path.exists(ATTENDANCE_FILE):
    with open(ATTENDANCE_FILE, "rb") as f:
        attendance_records = pickle.load(f)

# MongoDB connection setup
client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
db = client["attendanceDB"]  # Database name
attendance_collection = db["attendance"]  # Collection name

# Function to save attendance records
def save_attendance():
    with open(ATTENDANCE_FILE, "wb") as f:
        pickle.dump(attendance_records, f)

# Function to mark attendance in MongoDB
def mark_attendance_in_mongo(name, phone, latitude, longitude):
    now = datetime.datetime.now()
    date = now.strftime("%d-%m-%y %H:%M")
    record = attendance_collection.find_one({"name": name})
    if record:
        # Ensure the attendance field is a list of dictionaries
        if not isinstance(record.get("attendance", []), list):
            attendance_collection.update_one({"name": name}, {"$set": {"attendance": []}})
            record["attendance"] = []
        elif isinstance(record["attendance"], list):
            record["attendance"] = [
                entry if isinstance(entry, dict) else {"date": entry, "status": "present", "latitude": None, "longitude": None}
                for entry in record["attendance"]
            ]
            attendance_collection.update_one({"name": name}, {"$set": {"attendance": record["attendance"]}})

        if record.get("phone") != phone:
            attendance_collection.update_one({"name": name}, {"$set": {"phone": phone}})
            print(f"ℹ️ Updated phone number for {name} to {phone}.")

        if any(entry["date"] == date for entry in record["attendance"]):
            print(f"⚠️ Attendance already marked for {name} at {date}.")
        else:
            add_attendance_entry(name, phone, date, "present", latitude, longitude)
            print(f"✅ Attendance marked for {name} at {date}.")
    else:
        add_attendance_entry(name, phone, date, "present", latitude, longitude)
        print(f"✅ Attendance marked for new user {name} at {date}.")

# AI Conversation using Ollama's Gemma 2B
def get_gemma_response(text):
    response = ollama.chat(model="gemma:2b", messages=[{"role": "user", "content": text}])
    return response["message"]["content"] if "message" in response else "I couldn't process that."

# Function to capture attendance using webcam
def capture_attendance():
    video_capture = cv2.VideoCapture(0)
    try:
        while True:
            ret, frame = video_capture.read()
            if not ret:
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Stranger"

                if True in matches:
                    match_index = matches.index(True)
                    name = known_face_names[match_index]

                    record = attendance_collection.find_one({"name": name})
                    phone = record["phone"] if record and "phone" in record else "Unknown"
                    latitude, longitude = 12.9716, 77.5946  # Replace with actual GPS
                    mark_attendance_in_mongo(name, phone, latitude, longitude)

                    print(f"Hello {name}, good to see you again!")

                else:
                    print("I see a new face. Please register first.")
                    messagebox.showwarning("Warning", "Unrecognized face. Please register first.")

                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            cv2.imshow("Face Recognition", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("Exiting attendance capture...")
                break

    finally:
        video_capture.release()
        cv2.destroyAllWindows()
        print("Attendance capture closed.")

def mark_absentees():
    """Mark registered users as absent if they did not mark attendance for the day."""
    now = datetime.datetime.now()
    today_date = now.strftime("%Y-%m-%d")

    # Fetch all registered users
    all_users = attendance_collection.find()
    for user in all_users:
        name = user.get("name", "Unknown")
        attendance = user.get("attendance", [])

        # Check if attendance is already marked for today
        attendance_today = any(entry.get("date") == today_date for entry in attendance)
        if not attendance_today:
            # Mark the user as absent for today
            attendance_collection.update_one(
                {"name": name},
                {"$push": {"attendance": {"date": today_date, "status": "absent"}}}
            )
            print(f"❌ Marked {name} as absent for {today_date}.")

# Call this function at the end of the day or as part of a scheduled task
mark_absentees()

# Create the main application window
root = tk.Tk()
root.title("Attendance System")

# Create tabs
tab_control = ttk.Notebook(root)
register_tab = ttk.Frame(tab_control)
attendance_tab = ttk.Frame(tab_control)
mark_attendance_tab = ttk.Frame(tab_control)
tab_control.add(register_tab, text="Register")
tab_control.add(attendance_tab, text="Attendance")
tab_control.add(mark_attendance_tab, text="Mark Attendance")
tab_control.pack(expand=1, fill="both")

# Register tab UI
tk.Label(register_tab, text="Name:").grid(row=0, column=0, padx=10, pady=10)
name_entry = tk.Entry(register_tab)
name_entry.grid(row=0, column=1, padx=10, pady=10)

tk.Label(register_tab, text="Phone:").grid(row=1, column=0, padx=10, pady=10)
phone_entry = tk.Entry(register_tab)
phone_entry.grid(row=1, column=1, padx=10, pady=10)

register_button = tk.Button(register_tab, text="Register", command=lambda: print("Register functionality"))
register_button.grid(row=2, column=0, columnspan=2, pady=10)

# Attendance tab UI
attendance_text = tk.Text(attendance_tab, wrap="word", height=20, width=50)
attendance_text.pack(padx=10, pady=10)

refresh_button = tk.Button(attendance_tab, text="Refresh", command=lambda: print("Refresh functionality"))
refresh_button.pack(pady=5)

# Mark Attendance tab UI
capture_button = tk.Button(mark_attendance_tab, text="Capture Attendance", command=capture_attendance)
capture_button.pack(pady=20)

# Start the application
root.mainloop()
