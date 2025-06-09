import cv2
import mediapipe as mp
import numpy as np

# Setup MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Setup MediaPipe Hands
mp_hands = mp.solutions.hands

# Initialize MediaPipe solutions with improved detection parameters
hands = mp_hands.Hands(
    max_num_hands=1, 
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Drawing specs for face mesh
drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1, color=(0, 255, 0))
drawing_spec_lips = mp_drawing.DrawingSpec(thickness=2, circle_radius=1, color=(0, 0, 255))

# Landmark indices for smile detection
# Indices for lips and mouth area
UPPER_LIP = [
    61, 185, 40, 39, 37, 0, 267, 269, 270, 409
]
LOWER_LIP = [
    146, 91, 181, 84, 17, 314, 405, 321, 375, 291
]
LEFT_CORNER = 61
RIGHT_CORNER = 291
UPPER_LIP_CENTER = 0
LOWER_LIP_CENTER = 17

# Connect to camera
cap = cv2.VideoCapture(0)

# Garis batas Vertikal
line_x = 320
prev_x = None
gesture_count = 0
smile_detected = False
door_open = False
smile_confidence = 0.0

def detect_smile(landmarks, image_height, image_width):
    """
    Enhanced smile detection using multiple facial landmarks
    Returns both a boolean and a confidence score
    """
    if not landmarks:
        return False, 0.0
    
    # 1. Calculate mouth aspect ratio (width to height ratio)
    left_corner = landmarks[LEFT_CORNER]
    right_corner = landmarks[RIGHT_CORNER]
    upper_center = landmarks[UPPER_LIP_CENTER]
    lower_center = landmarks[LOWER_LIP_CENTER]
    
    # Get the coordinates
    left_x, left_y = int(left_corner.x * image_width), int(left_corner.y * image_height)
    right_x, right_y = int(right_corner.x * image_width), int(right_corner.y * image_height)
    upper_x, upper_y = int(upper_center.x * image_width), int(upper_center.y * image_height)
    lower_x, lower_y = int(lower_center.x * image_width), int(lower_center.y * image_height)
    
    # Calculate distance between mouth corners (width)
    mouth_width = np.sqrt((right_x - left_x)**2 + (right_y - left_y)**2)
    
    # Calculate distance between upper and lower lip (height)
    mouth_height = np.sqrt((upper_x - lower_x)**2 + (upper_y - lower_y)**2)
    
    # 2. Calculate mouth aspect ratio
    if mouth_height == 0:
        mouth_aspect_ratio = 0
    else:
        mouth_aspect_ratio = mouth_width / mouth_height
    
    # 3. Calculate the average height of upper and lower lips
    upper_lip_heights = []
    for i in UPPER_LIP:
        upper_lip_heights.append(landmarks[i].y * image_height)
    
    lower_lip_heights = []
    for i in LOWER_LIP:
        lower_lip_heights.append(landmarks[i].y * image_height)
    
    avg_upper_lip_height = sum(upper_lip_heights) / len(upper_lip_heights)
    avg_lower_lip_height = sum(lower_lip_heights) / len(lower_lip_heights)
    
    # 4. Calculate lips separation
    lips_separation = avg_lower_lip_height - avg_upper_lip_height
    
    # 5. Combine features to detect smile
    # Smiling typically means: high mouth_aspect_ratio and significant lips_separation
    confidence = (mouth_aspect_ratio * 0.6) + (lips_separation * 0.4)
    
    # Normalize confidence
    confidence = min(max(confidence / 5.0, 0), 1.0)
    
    # Threshold for smile detection
    is_smiling = mouth_aspect_ratio > 4.0 and lips_separation > 10.0
    
    return is_smiling, confidence

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)  # Mirror effect
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, _ = frame.shape

    # Process hands
    hand_result = hands.process(rgb)

    # Process face mesh
    face_result = face_mesh.process(rgb)

    # Deteksi tangan dan crossing dari kanan ke kiri
    if hand_result.multi_hand_landmarks:
        for hand_landmarks in hand_result.multi_hand_landmarks:
            # Draw hand landmarks
            mp_drawing.draw_landmarks(
                frame, 
                hand_landmarks, 
                mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
                mp_drawing.DrawingSpec(color=(250, 44, 250), thickness=2, circle_radius=2)
            )
            
            # Get hand center
            cx = int(hand_landmarks.landmark[9].x * w)  # Titik tengah tangan
            cy = int(hand_landmarks.landmark[9].y * h)
            
            # Draw hand center point
            cv2.circle(frame, (cx, cy), 10, (0, 255, 255), -1)

            # Track hand movement across line
            if prev_x is not None:
                # Crossing dari kanan ke kiri
                if prev_x > line_x and cx <= line_x:
                    gesture_count += 1
            prev_x = cx

    # Detect face and smile
    if face_result.multi_face_landmarks:
        for face_landmarks in face_result.multi_face_landmarks:
            # Draw the face mesh
            mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style()
            )
            
            # Draw lips with special highlight
            mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_LIPS,
                landmark_drawing_spec=None,
                connection_drawing_spec=drawing_spec_lips
            )
            
            # Detect smile
            smile_detected, smile_confidence = detect_smile(face_landmarks.landmark, h, w)

    # Cek kondisi untuk membuka pintu
    if gesture_count >= 7 and smile_detected and not door_open:
        door_open = True
        print("PINTU TERBUKA")

    # Display UI elements
    # Vertical boundary line
    cv2.line(frame, (line_x, 0), (line_x, h), (0, 255, 0), 2)
    
    # Gesture counter
    cv2.putText(frame, f"Gerakan: {gesture_count}", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    
    # Smile detection status and confidence
    smile_status = "Tersenyum" if smile_detected else "Tidak Tersenyum"
    smile_color = (0, 255, 0) if smile_detected else (0, 0, 255)
    cv2.putText(frame, f"Status: {smile_status}", (10, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, smile_color, 2)
    cv2.putText(frame, f"Confidence: {int(smile_confidence * 100)}%", (10, 130), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, smile_color, 2)
    
    # Door status
    if door_open:
        cv2.putText(frame, "PINTU TERBUKA", (w // 2 - 150, h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 4)

    # Show frame
    cv2.imshow("Sistem Keamanan Cerdas dengan Deteksi Wajah", frame)
    
    # Exit on 'q' press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
