from flask import Flask, render_template, request, jsonify, Response, redirect, url_for
import cv2
import face_recognition_models
import face_recognition
import os
import pickle
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from dotenv import load_dotenv
from datetime import datetime
import datetime  # Ensure correct import of datetime module

# Load environment variables
load_dotenv()
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")

app = Flask(__name__)

# File paths
FACE_DATA_FILE = "faces.pkl"
FACES_DIR = "faces"
os.makedirs(FACES_DIR, exist_ok=True)

# MongoDB connection setup
try:
    client = MongoClient(MONGO_CONNECTION_STRING, serverSelectionTimeoutMS=5000)
    db = client["attendanceDB"]
    attendance_collection = db["attendance"]
    client.server_info()  # Test the connection
    print("✅ Connected to MongoDB Atlas successfully.")
except ServerSelectionTimeoutError as e:
    print(f"❌ Error connecting to MongoDB Atlas: {e}")
    attendance_collection = None

# Load stored face data
known_face_encodings = []
known_face_names = []
if os.path.exists(FACE_DATA_FILE):
    with open(FACE_DATA_FILE, "rb") as f:
        known_face_encodings, known_face_names = pickle.load(f)

# Initialize webcam
camera = cv2.VideoCapture(0)
if not camera.isOpened():
    print("❌ Failed to initialize the webcam.")

@app.route("/")
def home():
    """Render the home page and ensure the camera is turned off."""
    if camera.isOpened():
        camera.release()  # Turn off the camera
    return redirect(url_for("register"))

@app.route("/video_feed")
def video_feed():
    """Stream the webcam feed."""
    def generate_frames():
        while True:
            success, frame = camera.read()
            if not success:
                break
            else:
                # Encode the frame as JPEG
                _, buffer = cv2.imencode(".jpg", frame)
                frame = buffer.tobytes()
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        camera.release()  # Release the camera when done

    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        print("✅ Rendered register.html")
        return render_template("register.html")

    try:
        # Get form data
        name = request.form.get("name")
        phone = request.form.get("phone")
        print(f"Received form data: name={name}, phone={phone}")

        # Validate form data
        if not name or not phone:
            print("❌ Missing name or phone.")
            return jsonify({"status": "error", "message": "Name and phone are required."}), 400

        # Capture a frame from the webcam
        success, frame = camera.read()
        if not success:
            print("❌ Failed to access webcam.")
            return jsonify({"status": "error", "message": "Failed to access webcam."}), 500

        # Process the frame (e.g., detect faces)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        print(f"Detected face locations: {face_locations}")
        if not face_locations:
            print("❌ No face detected.")
            return jsonify({"status": "error", "message": "No face detected. Please try again."}), 400

        # Save user data and face encoding
        face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
        known_face_encodings.append(face_encoding)
        known_face_names.append(name)

        with open(FACE_DATA_FILE, "wb") as f:
            pickle.dump((known_face_encodings, known_face_names), f)

        cv2.imwrite(os.path.join(FACES_DIR, f"{name}.jpg"), frame)

        # Save user details to the database
        now = datetime.now()
        date = now.strftime("%d-%m-%Y %H:%M:%S")
        record = attendance_collection.find_one({"name": name})
        if record:
            attendance_collection.update_one(
                {"name": name},
                {
                    "$set": {"phone": phone},
                    "$push": {"attendance": {"date": date, "status": "registered"}}
                }
            )
        else:
            attendance_collection.insert_one({
                "name": name,
                "phone": phone,
                "attendance": [{"date": date, "status": "registered"}]
            })

        print(f"✅ {name} registered successfully!")
        return jsonify({"status": "success", "message": f"{name} registered successfully!"})
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

@app.route("/mark_attendance", methods=["GET", "POST"])
def mark_attendance():
    """Render the attendance marking page and handle attendance."""
    if request.method == "GET":
        if not camera.isOpened():
            print("🔄 Reinitializing the webcam...")
            camera.open(0)  # Ensure the camera is turned on
        return render_template("mark_attendance.html")
    
    success, frame = camera.read()
    if not success:
        return jsonify({"status": "error", "message": "Failed to access webcam."}), 500

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Stranger"
        if True in matches:
            idx = matches.index(True)
            name = known_face_names[idx]

            # Check if attendance is already marked for today
            now = datetime.datetime.now()
            today_date = now.strftime("%d-%m-%Y")
            current_time = now.strftime("%H:%M:%S")
            record = attendance_collection.find_one({"name": name})
            if record:
                attendance_today = any(
                    entry.get("date") == today_date for entry in record.get("attendance", [])
                )
                if attendance_today:
                    return jsonify({"status": "info", "message": f"Attendance already marked for {name} today."})

            # Mark attendance for today
            attendance_entry = {"date": today_date, "time": current_time, "status": "present"}
            attendance_collection.update_one(
                {"name": name},
                {"$push": {"attendance": attendance_entry}},
                upsert=True
            )
            return jsonify({"status": "success", "message": f"✅ Attendance marked for {name} at {current_time}."})
    return jsonify({"status": "error", "message": "No recognized faces found."})

@app.route("/mark_absentees", methods=["POST"])
def mark_absentees():
    """Mark registered users as absent if they did not mark attendance for the day."""
    now = datetime.now()
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
    return jsonify({"status": "success", "message": "Absentees marked successfully."})

@app.route("/reports")
def reports():
    """Render the reports page."""
    if camera.isOpened():
        camera.release()  # Turn off the camera when accessing the reports page

    now = datetime.datetime.now()
    today_date = now.strftime("%d-%m-%Y")

    # Fetch all registered users
    all_users = attendance_collection.find()
    report_data = []
    for user in all_users:
        name = user.get("name", "Unknown")
        phone = user.get("phone", "Unknown")
        attendance = user.get("attendance", [])
        attendance_today = next(
            (entry for entry in attendance if entry.get("date") == today_date and entry.get("status") == "present"), None
        )
        if attendance_today:
            status = "Present"
            time = attendance_today.get("time", "N/A")
        else:
            status = "Absent"
            time = "N/A"

        report_data.append({
            "name": name,
            "phone": phone,
            "status": status,
            "date": today_date,
            "time": time
        })

    return render_template("reports.html", report_data=report_data, error=None)

if __name__ == "__main__":
    app.run(debug=True)
