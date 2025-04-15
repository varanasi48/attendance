import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import face_recognition
import datetime
import os
import pickle
import pymongo
from dotenv import load_dotenv
from schema import add_attendance_entry, mongo_url  # Ensure to adjust the import as needed

# Load environment variables
load_dotenv()
MONGO_CONNECTION_STRING = mongo_url

# Load stored face data and attendance records
FACE_DATA_FILE = "faces.pkl"
ATTENDANCE_FILE = "attendance.pkl"
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
db = client["attendanceDB"]
attendance_collection = db["attendance"]

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

# Function to capture attendance using webcam
def capture_attendance():
    global video_capture, camera_canvas, exit_button_frame

    video_capture = cv2.VideoCapture(0)

    # Reduce resolution for faster load (e.g., 640x480)
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def update_frame():
        ret, frame = video_capture.read()
        if not ret:
            print("Failed to grab frame")
            return

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

        # Update the Canvas to display the frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        photo = tk.PhotoImage(data=cv2.imencode(".png", frame_rgb)[1].tobytes())
        camera_canvas.create_image(0, 0, anchor="nw", image=photo)
        camera_canvas.image = photo

        camera_canvas.after(10, update_frame)

    update_frame()

# Function to handle exit on camera screen
def exit_capture():
    video_capture.release()
    cv2.destroyAllWindows()
    print("Exited capture mode.")
    root.quit()

# Create the main application window
root = tk.Tk()
root.title("Attendance System")
root.geometry("600x400")  # Set window size
root.configure(bg="white")

# Apply material design-like styling
style = ttk.Style()
style.configure("TNotebook", background="#6200EE", borderwidth=0)
style.configure("TNotebook.Tab", background="#6200EE", padding=[10, 10], font=("Helvetica", 12, "bold"))
style.map("TNotebook.Tab", background=[("selected", "#3700B3")])

style.configure("TButton",
                font=("Helvetica", 10),
                relief="flat",
                padding=10,
                background="#6200EE",
                foreground="black")
style.map("TButton", background=[("active", "#3700B3")])

style.configure("TEntry", padding=10, font=("Helvetica", 12), relief="flat")

# Create tabs using ttk.Notebook
tab_control = ttk.Notebook(root)

# Create frames for each tab
register_tab = ttk.Frame(tab_control, padding=20, style="TFrame")
attendance_tab = ttk.Frame(tab_control, padding=20, style="TFrame")
mark_attendance_tab = ttk.Frame(tab_control, padding=20, style="TFrame")

# Add frames to the tab control
tab_control.add(register_tab, text="Register")
tab_control.add(attendance_tab, text="Attendance")
tab_control.add(mark_attendance_tab, text="Mark Attendance")

# Pack the tab control to make it visible
tab_control.pack(expand=1, fill="both")

# Register tab UI
tk.Label(register_tab, text="Name:", font=("Helvetica", 12), bg="white").grid(row=0, column=0, padx=10, pady=10, sticky="w")
name_entry = ttk.Entry(register_tab, style="TEntry")
name_entry.grid(row=0, column=1, padx=10, pady=10)

tk.Label(register_tab, text="Phone:", font=("Helvetica", 12), bg="white").grid(row=1, column=0, padx=10, pady=10, sticky="w")
phone_entry = ttk.Entry(register_tab, style="TEntry")
phone_entry.grid(row=1, column=1, padx=10, pady=10)

register_button = ttk.Button(register_tab, text="Register", style="TButton", command=register_user)
register_button.grid(row=2, column=0, columnspan=2, pady=20)

# Attendance tab UI
attendance_text = tk.Text(attendance_tab, wrap="word", height=15, width=60, font=("Helvetica", 12))
attendance_text.pack(padx=10, pady=10)

refresh_button = ttk.Button(attendance_tab, text="Refresh", style="TButton", command=refresh_attendance)
refresh_button.pack(pady=10)

# Mark Attendance tab UI
capture_button = ttk.Button(mark_attendance_tab, text="Capture Attendance", style="TButton", command=capture_attendance)
capture_button.pack(pady=20)

# Create a frame for the video feed
camera_frame = ttk.Frame(mark_attendance_tab)
camera_frame.pack(expand=1, fill="both", padx=10, pady=10)

# Add Canvas widget to display the camera feed
camera_canvas = tk.Canvas(camera_frame, bg="black", width=640, height=480)
camera_canvas.pack()

# Exit button for camera screen
exit_button_frame = ttk.Frame(mark_attendance_tab, bg="white", pady=10)
exit_button = ttk.Button(exit_button_frame, text="Exit", style="TButton", command=exit_capture)
exit_button.pack()
exit_button_frame.pack(side="bottom", fill="x")

# Start the Tkinter main loop
root.mainloop()
