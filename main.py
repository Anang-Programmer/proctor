import cv2
import mediapipe as mp
import time
import os
from ultralytics import YOLO

# --- Setup ---
mp_pose = mp.solutions.pose
mp_face = mp.solutions.face_detection
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
face = mp_face.FaceDetection(min_detection_confidence=0.5)

# Load YOLO untuk deteksi objek
model = YOLO("yolov8n.pt")  # versi nano (ringan)

# Folder untuk simpan screenshot
output_dir = "suspicious_shots"
os.makedirs(output_dir, exist_ok=True)

# Camera
cap = cv2.VideoCapture(0)

last_warning_time = 0
cooldown = 3  # detik

def give_warning(msg, frame=None, screenshot=False):
    """Kirim peringatan, screenshot hanya untuk benda mencurigakan"""
    global last_warning_time
    if time.time() - last_warning_time > cooldown:
        print(f"[WARNING] {msg}")
        if screenshot and frame is not None:
            filename = os.path.join(output_dir, f"suspicious_{int(time.time())}.jpg")
            cv2.imwrite(filename, frame)
            print(f"Screenshot saved: {filename}")
        last_warning_time = time.time()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # --- Pose detection ---
    # --- Pose detection ---
    pose_results = pose.process(rgb)
    if pose_results.pose_landmarks:
        landmarks = pose_results.pose_landmarks.landmark
        h, w, _ = frame.shape

        # Data bahu
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

        # Konversi ke pixel
        l_x, l_y = int(left_shoulder.x * w), int(left_shoulder.y * h)
        r_x, r_y = int(right_shoulder.x * w), int(right_shoulder.y * h)

        # --- Bahu terlihat? ---
        if (left_shoulder.visibility < 0.5 or right_shoulder.visibility < 0.5 or
            l_x <= 0 or l_x >= w or l_y <= 0 or l_y >= h or
            r_x <= 0 or r_x >= w or r_y <= 0 or r_y >= h):
            give_warning("Bahu tidak terlihat dengan jelas!")

        # --- Indikasi nyontek (kepala nengok) ---
        nose = landmarks[mp_pose.PoseLandmark.NOSE.value]
        nose_x = int(nose.x * w)

        margin = int(w * 0.25)  # area tengah 50% layar
        if nose_x < margin:
            give_warning("Kepala terlalu sering nengok ke kiri (indikasi nyontek)")
        elif nose_x > w - margin:
            give_warning("Kepala terlalu sering nengok ke kanan (indikasi nyontek)")




    # --- Face detection ---
    # --- Face detection ---
    face_results = face.process(rgb)
    if face_results.detections:
        if len(face_results.detections) > 1:
            give_warning("Terdeteksi wajah orang lain!")
    else:
        give_warning("Wajah tidak terdeteksi!")


    # --- Gerakan mencurigakan (contoh placeholder, bisa dikembangkan) ---
    # Console only
    # print("[WARNING] Gerakan mencurigakan terdeteksi!")

    # --- Deteksi benda mencurigakan dengan YOLO ---
    results = model.predict(source=frame, conf=0.5, verbose=False)
    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            label = model.names[cls]

            if label in ["cell phone", "book", "laptop"]:  # objek terlarang
                give_warning(f"Benda mencurigakan terdeteksi: {label}", frame, screenshot=True)

            # Gambarkan bounding box
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # Tampilkan frame
    cv2.imshow("Proctor Ujian", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("Proctoring session ended. Check log file: {}".format(output_dir))