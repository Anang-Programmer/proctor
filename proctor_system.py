import cv2
import mediapipe as mp
import time
import os
import json
from ultralytics import YOLO
from datetime import datetime
import threading
import queue

class ProctorSystem:
    def __init__(self, user_id, ujian_id, callback_function=None):
        self.user_id = user_id
        self.ujian_id = ujian_id
        self.callback_function = callback_function
        
        # Setup MediaPipe
        self.mp_pose = mp.solutions.pose
        self.mp_face = mp.solutions.face_detection
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.face = self.mp_face.FaceDetection(min_detection_confidence=0.5)
        
        # Load YOLO model
        self.model = YOLO("yolov8n.pt")
        
        # Proctor settings
        self.pelanggaran_count = 0
        self.max_pelanggaran = 3
        self.last_warning_time = 0
        self.cooldown = 3  # seconds
        
        # Screenshot directory
        self.screenshot_dir = "static/screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # Camera
        self.cap = None
        self.is_running = False
        self.frame_queue = queue.Queue(maxsize=2)
        
    def start_monitoring(self):
        """Mulai monitoring proctor"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Tidak dapat mengakses kamera")
            
            self.is_running = True
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self._monitor_loop)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            return True
        except Exception as e:
            print(f"Error starting proctor: {e}")
            return False
    
    def stop_monitoring(self):
        """Hentikan monitoring proctor"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
    
    def _monitor_loop(self):
        """Loop utama monitoring"""
        while self.is_running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            # Update frame queue
            if not self.frame_queue.full():
                self.frame_queue.put(frame)
            
            # Process frame
            self._process_frame(frame)
            
            time.sleep(0.1)  # Reduce CPU usage
    
    def get_current_frame(self):
        """Dapatkan frame terbaru untuk ditampilkan di web"""
        try:
            if not self.frame_queue.empty():
                return self.frame_queue.get_nowait()
            return None
        except:
            return None
    
    def _process_frame(self, frame):
        """Proses frame untuk deteksi pelanggaran"""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Pose detection
        self._detect_pose_violations(rgb, frame)
        
        # Face detection
        self._detect_face_violations(rgb, frame)
        
        # Object detection
        self._detect_object_violations(frame)
    
    def _detect_pose_violations(self, rgb, frame):
        """Deteksi pelanggaran pose"""
        pose_results = self.pose.process(rgb)
        if pose_results.pose_landmarks:
            landmarks = pose_results.pose_landmarks.landmark
            h, w, _ = frame.shape
            
            # Check shoulder visibility
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            
            l_x, l_y = int(left_shoulder.x * w), int(left_shoulder.y * h)
            r_x, r_y = int(right_shoulder.x * w), int(right_shoulder.y * h)
            
            if (left_shoulder.visibility < 0.5 or right_shoulder.visibility < 0.5 or
                l_x <= 0 or l_x >= w or l_y <= 0 or l_y >= h or
                r_x <= 0 or r_x >= w or r_y <= 0 or r_y >= h):
                self._trigger_violation("Bahu tidak terlihat dengan jelas", "ringan")
            
            # Check head position (cheating indication)
            nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
            nose_x = int(nose.x * w)
            
            margin = int(w * 0.25)
            if nose_x < margin:
                self._trigger_violation("Kepala terlalu sering menengok ke kiri", "ringan")
            elif nose_x > w - margin:
                self._trigger_violation("Kepala terlalu sering menengok ke kanan", "ringan")
    
    def _detect_face_violations(self, rgb, frame):
        """Deteksi pelanggaran wajah"""
        face_results = self.face.process(rgb)
        if face_results.detections:
            if len(face_results.detections) > 1:
                self._trigger_violation("Terdeteksi wajah orang lain", "berat")
        else:
            self._trigger_violation("Wajah tidak terdeteksi", "ringan")
    
    def _detect_object_violations(self, frame):
        """Deteksi objek terlarang"""
        results = self.model.predict(source=frame, conf=0.5, verbose=False)
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                label = self.model.names[cls]
                
                if label in ["cell phone", "book", "laptop"]:
                    screenshot_path = self._save_screenshot(frame, f"objek_{label}")
                    self._trigger_violation(f"Terdeteksi benda terlarang: {label}", "berat", screenshot_path)
    
    def _trigger_violation(self, message, level, screenshot_path=None):
        """Trigger pelanggaran"""
        current_time = time.time()
        if current_time - self.last_warning_time < self.cooldown:
            return
        
        self.last_warning_time = current_time
        self.pelanggaran_count += 1
        
        # Save violation log
        violation_data = {
            'user_id': self.user_id,
            'ujian_id': self.ujian_id,
            'message': message,
            'level': level,
            'screenshot_path': screenshot_path,
            'timestamp': datetime.now().isoformat(),
            'pelanggaran_ke': self.pelanggaran_count
        }
        
        # Call callback function to notify web interface
        if self.callback_function:
            self.callback_function(violation_data)
        
        # Check if max violations reached
        if self.pelanggaran_count >= self.max_pelanggaran:
            self._end_exam_due_to_violations()
    
    def _save_screenshot(self, frame, prefix="violation"):
        """Simpan screenshot pelanggaran"""
        timestamp = int(time.time())
        filename = f"{prefix}_{self.user_id}_{timestamp}.jpg"
        filepath = os.path.join(self.screenshot_dir, filename)
        cv2.imwrite(filepath, frame)
        return filepath
    
    def _end_exam_due_to_violations(self):
        """Akhiri ujian karena terlalu banyak pelanggaran"""
        if self.callback_function:
            self.callback_function({
                'action': 'end_exam',
                'reason': 'Terlalu banyak pelanggaran',
                'pelanggaran_count': self.pelanggaran_count
            })
        self.stop_monitoring()
    
    def get_violation_count(self):
        """Dapatkan jumlah pelanggaran saat ini"""
        return self.pelanggaran_count
    
    def reset_violations(self):
        """Reset counter pelanggaran"""
        self.pelanggaran_count = 0