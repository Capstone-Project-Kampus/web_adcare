import cv2
import mediapipe as mp
import numpy as np
import time

# Inisialisasi mediapipe Pose model
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False,  # Mode dinamis (untuk deteksi video)
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Variabel untuk melacak gerakan tubuh (meraih mainan)
prev_nose_position = None
head_movement_count = 0
last_movement_time = time.time()  # Waktu terakhir gerakan terdeteksi
focus_time = 0  # Waktu fokus pada satu objek
max_focus_time = 3  # Maksimal waktu fokus pada objek dalam detik

# Fungsi untuk mendeteksi pergerakan meraih (reaching) berdasarkan sudut tubuh (Bending Angle)
def detect_posture_status(frame):
    """Detect shoulder, neck, and head posture from webcam frame"""
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Konversi frame ke RGB
    results = pose.process(image_rgb)
    
    if not results.pose_landmarks:
        return "unknown", 0  # Jika tidak ada deteksi

    landmarks = results.pose_landmarks
    
    # Get key points (shoulders and neck)
    left_shoulder = landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
    right_shoulder = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
    nose = landmarks.landmark[mp_pose.PoseLandmark.NOSE]
    
    # Hitung jarak pergerakan kepala berdasarkan posisi hidung
    global prev_nose_position, head_movement_count, last_movement_time, focus_time
    if prev_nose_position is None:
        prev_nose_position = (nose.x, nose.y)  # Set initial position
    
    # Periksa pergerakan hidung
    movement_threshold = 0.05  # Threshold pergerakan lebih besar untuk mendeteksi gerakan signifikan
    movement = np.linalg.norm(np.array([nose.x - prev_nose_position[0], nose.y - prev_nose_position[1]]))
    
    # Jika gerakan terdeteksi, update jumlah pergerakan
    if movement > movement_threshold:
        head_movement_count += 1
        last_movement_time = time.time()  # Reset timer ketika ada gerakan
        focus_time = 0  # Reset waktu fokus jika ada gerakan
    
    prev_nose_position = (nose.x, nose.y)

    # Hitung postur berdasarkan posisi bahu
    tilt_ratio = abs(left_shoulder.x - right_shoulder.x)
    posture = "miring" if tilt_ratio > 0.05 else "lurus"
    
    return posture, head_movement_count

# Open the webcam
cap = cv2.VideoCapture(0)

# Monitor gerakan anak
while cap.isOpened():
    ret, frame = cap.read()
    
    if not ret:
        print("Tidak dapat menangkap frame")
        break
    
    # Deteksi postur dari frame yang diambil
    posture, head_movement_count = detect_posture_status(frame)
    
    # Deteksi waktu meraih mainan anak (secara individu)
    current_time = time.time()

    # Deteksi gerakan yang sangat cepat atau impulsif
    if head_movement_count > 5:  # Deteksi gerakan berlebihan
        status = "ADHD - Gerakan Impulsif"
    elif focus_time > max_focus_time:  # Jika anak terlalu lama fokus pada satu objek
        status = "ADHD - Fokus Terlalu Lama pada Satu Objek"
    else:
        status = "Normal"

    # Debugging output untuk memeriksa gerakan dan status
    print(f"Gerakan Kepala: {head_movement_count}, Status: {status}")

    # Menampilkan status postur dan hitung gerakan kepala di layar
    cv2.putText(frame, f"Postur: {posture}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Gerakan Kepala: {head_movement_count}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Status: {status}", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Menampilkan video hasil deteksi di jendela OpenCV
    cv2.imshow("Webcam Feed", frame)

    # Tekan 'q' untuk keluar dari loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Setelah selesai, lepaskan objek video capture dan tutup jendela OpenCV
cap.release()
cv2.destroyAllWindows()