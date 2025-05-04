import base64
import os
import tempfile
import time
import cv2
import numpy as np
from flask import jsonify
from flask_jwt_extended import jwt_required
import mediapipe as mp

# Inisialisasi MediaPipe Pose model
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False,  # Mode dinamis untuk deteksi video
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Variabel untuk melacak gerakan tubuh (meraih mainan)
prev_nose_position = None
head_movement_count = 0
last_movement_time = time.time()
focus_time = 0
max_focus_time = 3

# Fungsi untuk mendeteksi gerakan dan postur tubuh
def detect_posture_status(frame):
    """Detect shoulder, neck, and head posture from webcam frame"""
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Konversi frame ke RGB
    results = pose.process(image_rgb)

    if not results.pose_landmarks:
        return "unknown", 0, 0  # Jika tidak ada deteksi

    landmarks = results.pose_landmarks

    # Get key points (shoulders, neck, and torso)
    left_shoulder = landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
    right_shoulder = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
    nose = landmarks.landmark[mp_pose.PoseLandmark.NOSE]
    left_hip = landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP]

    # Hitung pergerakan kepala berdasarkan posisi hidung
    global prev_nose_position, head_movement_count, last_movement_time, focus_time
    if prev_nose_position is None:
        prev_nose_position = (nose.x, nose.y)  # Set initial position

    # Periksa pergerakan hidung
    movement_threshold = 0.05
    movement = np.linalg.norm(np.array([nose.x - prev_nose_position[0], nose.y - prev_nose_position[1]]))

    if movement > movement_threshold:
        head_movement_count += 1
        last_movement_time = time.time()
        focus_time = 0

    prev_nose_position = (nose.x, nose.y)

    # Menghitung postur berdasarkan posisi bahu dan pinggul
    torso_movement = abs(left_hip.x - right_hip.x) + abs(left_shoulder.x - right_shoulder.x)
    movement_type = "fidgeting" if torso_movement > 0.05 else "diam"

    # Menghitung SR (Stationary Ratio)
    stationary_ratio = 0
    if movement_type == "fidgeting":
        stationary_ratio = 1

    return movement_type, head_movement_count, stationary_ratio


