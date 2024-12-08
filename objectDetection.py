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

# Load pre-trained MobileNet SSD model
net = cv2.dnn.readNetFromCaffe(cv2.data.dnn + 'deploy.prototxt', cv2.data.dnn + 'mobilenet_iter_73000.caffemodel')

# Define the classes for MobileNet SSD (class 0: background, 15: cell phone)
class_names = {0: 'background', 15: 'cell phone'}

# Initialize camera
cap = cv2.VideoCapture(0)

# Student information
student_name = "Nadeem Sheriff"
student_roll_number = "221401050"

# Parameters for peeping detection and alerts
tilt_threshold = 30  # Sensitivity for significant horizontal movement
max_alerts = 3  # Maximum alerts allowed before booking the student

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

        # Prepare the image for MobileNet SSD
        blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5, 127.5, 127.5, False)
        net.setInput(blob)
        detections = net.forward()

        # Iterate through detections
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]

            # Only consider detections with confidence above a threshold
            if confidence > 0.2:
                class_id = int(detections[0, 0, i, 1])
                if class_id == 15:  # Check if it's a cell phone (class 15 in MobileNet SSD)
                    # Draw bounding box and label
                    box = detections[0, 0, i, 3:7] * np.array([frame.shape[1], frame.shape[0], frame.shape[1], frame.shape[0]])
                    (x, y, x2, y2) = box.astype("int")
                    cv2.rectangle(frame, (x, y), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, "Electronic Device Detected", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    # Send an alert for electronic device detection
                    alert_count += 1
                    if alert_count <= max_alerts:
                        send_alert(student_id=student_roll_number, room="A102", evidence="Electronic Device Detected", count=alert_count)

                # You can add more conditions here for other objects you want to detect (e.g., peeping)

        # Encode the frame as a JPEG image
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def home():
    return "Welcome to the Video Feed! Go to /video_feed to view the stream."

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
