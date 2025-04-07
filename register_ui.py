from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
import cv2
import face_recognition
import os
import pickle
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
import os
from kivy.graphics.texture import Texture  # Import Texture for video rendering
import datetime  # Import datetime for attendance marking
from kivy.uix.popup import Popup  # Import Popup for displaying messages

# Load environment variables
load_dotenv()
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")

# MongoDB connection setup
try:
    client = MongoClient(MONGO_CONNECTION_STRING, serverSelectionTimeoutMS=5000)
    db = client["attendanceDB"]
    attendance_collection = db["attendance"]
    client.server_info()  # Test the connection
    print("✅ Connected to MongoDB Atlas successfully.")
except ConnectionFailure as e:
    print(f"❌ Error connecting to MongoDB Atlas: {e}")
    attendance_collection = None

# File paths
FACE_DATA_FILE = "faces.pkl"
FACES_DIR = "faces"
os.makedirs(FACES_DIR, exist_ok=True)

# Load stored face data
known_face_encodings = []
known_face_names = []
if os.path.exists(FACE_DATA_FILE):
    with open(FACE_DATA_FILE, "rb") as f:
        known_face_encodings, known_face_names = pickle.load(f)

class RegisterScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        # Name input
        self.name_label = Label(text="Enter Name:")
        self.add_widget(self.name_label)
        self.name_input = TextInput(multiline=False)
        self.add_widget(self.name_input)

        # Phone input
        self.phone_label = Label(text="Enter Phone Number:")
        self.add_widget(self.phone_label)
        self.phone_input = TextInput(multiline=False)
        self.add_widget(self.phone_input)

        # Video feed display
        self.video_feed = Label(text="Webcam feed will appear here.")
        self.add_widget(self.video_feed)

        # Register button
        self.register_button = Button(text="Register and Capture Face")
        self.register_button.bind(on_press=self.start_video_feed)
        self.add_widget(self.register_button)

        # Status label
        self.status_label = Label(text="")
        self.add_widget(self.status_label)

        self.cap = None
        self.frame_event = None

    def start_video_feed(self, instance):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.status_label.text = "❌ Webcam access failed."
            return
        self.status_label.text = "📸 Starting webcam..."
        self.frame_event = Clock.schedule_interval(self.update_video_feed, 1.0 / 30)

    def update_video_feed(self, dt):
        ret, frame = self.cap.read()
        if not ret:
            self.status_label.text = "❌ Failed to read from webcam."
            self.stop_video_feed()
            return

        # Convert frame to RGB for face detection
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # Draw bounding boxes and names around detected faces
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Stranger"
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = None

            if True in matches:
                best_match_index = matches.index(True)
                name = known_face_names[best_match_index]

            # Draw bounding box
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            # Draw name above the bounding box
            if best_match_index is not None:
                cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Convert frame to texture for Kivy
        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt="bgr")
        texture.blit_buffer(buf, colorfmt="bgr", bufferfmt="ubyte")
        self.video_feed.texture = texture

    def stop_video_feed(self):
        if self.frame_event:
            Clock.unschedule(self.frame_event)
            self.frame_event = None
        if self.cap:
            self.cap.release()
            self.cap = None

    def register_user(self, instance):
        name = self.name_input.text.strip()
        phone = self.phone_input.text.strip()
        if not name or not phone:
            self.status_label.text = "Please fill in all fields."
            return
        self.status_label.text = "Capturing face..."
        Clock.schedule_once(lambda dt: self.capture_face(name, phone), 0)

    def capture_face(self, name, phone):
        if not self.cap or not self.cap.isOpened():
            self.status_label.text = "❌ Webcam is not active."
            return

        ret, frame = self.cap.read()
        if not ret:
            self.status_label.text = "Failed to access webcam."
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        if not face_locations:
            self.status_label.text = "No face detected. Try again."
            return

        face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
        known_face_encodings.append(face_encoding)
        known_face_names.append(name)

        with open(FACE_DATA_FILE, "wb") as f:
            pickle.dump((known_face_encodings, known_face_names), f)

        cv2.imwrite(os.path.join(FACES_DIR, f"{name}.jpg"), frame)
        self.status_label.text = f"{name} registered successfully!"
        self.stop_video_feed()

class AttendanceScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        # Status label
        self.status_label = Label(text="Click below to mark attendance")
        self.add_widget(self.status_label)

        # Video feed display
        self.video_feed = Label(text="Webcam feed will appear here.")
        self.add_widget(self.video_feed)

        # Mark attendance button
        self.attend_button = Button(text="Mark Attendance")
        self.attend_button.bind(on_press=self.start_video_feed)
        self.add_widget(self.attend_button)

        self.cap = None
        self.frame_event = None

    def start_video_feed(self, instance):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.status_label.text = "❌ Webcam access failed."
            return
        self.status_label.text = "📸 Starting webcam..."
        self.frame_event = Clock.schedule_interval(self.update_video_feed, 1.0 / 30)

    def update_video_feed(self, dt):
        ret, frame = self.cap.read()
        if not ret:
            self.status_label.text = "❌ Failed to read from webcam."
            self.stop_video_feed()
            return

        # Convert frame to RGB for face detection
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # Draw bounding boxes and names around detected faces
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Stranger"
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = None

            if True in matches:
                best_match_index = matches.index(True)
                name = known_face_names[best_match_index]

            # Draw bounding box
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            # Draw name above the bounding box
            if best_match_index is not None:
                cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Convert frame to texture for Kivy
        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt="bgr")
        texture.blit_buffer(buf, colorfmt="bgr", bufferfmt="ubyte")
        self.video_feed.texture = texture

    def stop_video_feed(self):
        if self.frame_event:
            Clock.unschedule(self.frame_event)
            self.frame_event = None
        if self.cap:
            self.cap.release()
            self.cap = None

    def capture_attendance(self, instance):
        if not self.cap or not self.cap.isOpened():
            self.status_label.text = "❌ Webcam is not active."
            return

        ret, frame = self.cap.read()
        if not ret:
            self.status_label.text = "Failed to access webcam."
            return

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
                today_date = now.strftime("%Y-%m-%d")
                record = attendance_collection.find_one({"name": name})
                if record:
                    attendance_today = any(
                        entry.get("date") == today_date for entry in record.get("attendance", [])
                    )
                    if attendance_today:
                        self.show_popup("Attendance Already Marked", f"Attendance already marked for {name} today.")
                        return

                # Mark attendance for today
                attendance_entry = {"date": today_date, "status": "present"}
                attendance_collection.update_one(
                    {"name": name},
                    {"$push": {"attendance": attendance_entry}},
                    upsert=True
                )
                self.show_popup("Attendance Marked", f"✅ Attendance marked for {name}.")
            else:
                self.show_popup("Unrecognized Face", "⚠️ Unrecognized face. Please register first.")

        # Stop camera after detection
        if face_encodings:
            self.stop_video_feed()

    def show_popup(self, title, message):
        """Display a popup with the given title and message."""
        popup_content = BoxLayout(orientation="vertical")
        popup_content.add_widget(Label(text=message))
        close_button = Button(text="Close")
        popup_content.add_widget(close_button)

        popup = Popup(title=title, content=popup_content, size_hint=(0.6, 0.4))
        close_button.bind(on_press=popup.dismiss)
        popup.open()
