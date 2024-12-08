from flask import Flask, Response
from flask_cors import CORS
import cv2
import pymongo
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# MongoDB setup
mongo_client = pymongo.MongoClient("mongodb+srv://nadeemsheriff18:nadeem01@database.qnufz.mongodb.net/?retryWrites=true&w=majority&appName=Database")
db = mongo_client["Database"]
alerts_collection = db["alerts"]  # Create or access the alerts collection

# Load the pre-trained face detector model from OpenCV
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Student information
student_name = "Nadeem Sheriff"
student_roll_number = "221401050"

# Initialize camera
cap = cv2.VideoCapture(0)

# Parameters for peeping detection and alerts
tilt_threshold = 30  # Sensitivity for significant horizontal movement
max_alerts = 5  # Maximum alerts allowed before booking the student

# Variables to track previous center and alert state
prev_center_x = None
alert_count = 0  # Total number of alerts sent
student_booked = False  # Flag indicating if the student is booked

def generate_frames():
    global prev_center_x, alert_count, student_booked

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert frame to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

        for (x, y, w, h) in faces:
            # Determine the bounding box color (red if booked, green otherwise)
            box_color = (0, 0, 255) if student_booked else (0, 255, 0)

            # Draw the bounding box around the detected face
            cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)

            # Display student's name and roll number
            cv2.putText(frame, f"{student_name} | Roll: {student_roll_number}", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Calculate the center of the bounding box for the face
            center_x = x + w // 2

            # Check for peeping (significant horizontal movement between frames)
            if prev_center_x is not None and not student_booked:
                movement_x = center_x - prev_center_x

                # Trigger alert if significant horizontal movement is detected
                if abs(movement_x) > tilt_threshold:
                    alert_count += 1

                    if alert_count <= max_alerts:
                        send_alert(student_id=student_roll_number, room="A102", evidence="Peeping Detected", count=alert_count)

                    # Show alert in video feed for the first and second alerts
                    if alert_count == 1 or alert_count == 2:
                        cv2.putText(frame, f"Alert {alert_count}: Peeping Detected!", (50, 100),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

                    # On the third alert (max limit), display "Booked" message
                    if alert_count == max_alerts:
                        student_booked = True  # Student is booked after max alerts

            # Update the previous center position
            prev_center_x = center_x

        # Show "Booked" alert text on the frame
        if student_booked:
            cv2.putText(frame, "STUDENT BOOKED: Exam Terminated", (30, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

        # Encode the frame as a JPEG image
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def home():
    return "Welcome to the Video Feed! Go to /video_feed to view the stream."

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def send_alert(student_id, room, evidence, count):
    # Check if an alert for this student already exists in the database
    existing_alert = alerts_collection.find_one({"studentId": student_id})

    if existing_alert:
        # Update the count for the existing alert
        alerts_collection.update_one({"studentId": student_id}, {"$set": {"count": count}})
        print(f"ALERT UPDATED: {student_id} - Count: {count}")
    else:
        # Create a new alert document for the first alert
        alert = {
            "studentId": student_id,
            "room": room,
            "session": "AN",  # Assuming AN stands for an anomaly or alert status
            "evidence": evidence,
            "count": count,
            "timestamp": datetime.now()
        }
        alerts_collection.insert_one(alert)
        print(f"ALERT SENT: {student_id} - Count: {count}, Evidence: {evidence}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
