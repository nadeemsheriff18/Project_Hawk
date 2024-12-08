import cv2
import mediapipe as mp
import numpy as np

# Initialize Mediapipe Face Mesh and Drawing utilities
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

# Set up the Face Mesh model
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, min_detection_confidence=0.5)

# Start capturing video
cap = cv2.VideoCapture(0)

def calculate_head_tilt_angle(landmarks, img_shape):
    # Get landmark positions for eyes and nose
    left_eye = np.array([landmarks[33].x * img_shape[1], landmarks[33].y * img_shape[0]])  # Left eye corner
    right_eye = np.array([landmarks[263].x * img_shape[1], landmarks[263].y * img_shape[0]])  # Right eye corner
    nose_tip = np.array([landmarks[1].x * img_shape[1], landmarks[1].y * img_shape[0]])  # Nose tip

    # Calculate the angle between the eye line and the horizontal axis
    eye_line = right_eye - left_eye
    eye_angle = np.degrees(np.arctan2(eye_line[1], eye_line[0]))

    # Calculate head tilt based on the angle
    return eye_angle

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Ignoring empty camera frame.")
        continue

    # Convert the BGR image to RGB for face processing
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the image and find face landmarks
    results = face_mesh.process(rgb_frame)

    # Draw the face mesh annotations on the frame
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # Draw all landmarks on the face
            mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1)
            )

            # Calculate head tilt angle
            tilt_angle = calculate_head_tilt_angle(face_landmarks.landmark, frame.shape)
            
            # Display tilt angle for debugging
            cv2.putText(frame, f"Tilt Angle: {tilt_angle:.2f}", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Check if tilt angle exceeds threshold for alert
            tilt_threshold = 15  # Adjust this threshold as needed
            if abs(tilt_angle) > tilt_threshold:
                cv2.putText(frame, "ALERT: Head Tilt Detected!", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Display the resulting frame
    cv2.imshow('Exam Monitoring System', frame)

    # Break the loop on pressing 'q'
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

# Release the capture and destroy windows
cap.release()
cv2.destroyAllWindows()
