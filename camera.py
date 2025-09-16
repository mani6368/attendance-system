import cv2
import numpy as np
import requests
import time
import os
from datetime import datetime
from attendance_manager import AttendanceManager

# Face detection configuration
HAAR_CASCADE_FILE = 'haarcascade_frontalface_default.xml'
FACE_SAVE_DIR = 'detected_faces'
ATTENDANCE_DIR = 'attendance_logs'
DATABASE_FILE = 'attendance.db'

def update_attendance(person_id, status='present'):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    now = datetime.now()
    today = now.date()
    
    # Check if attendance exists
    cursor.execute('''
        SELECT id FROM attendance 
        WHERE person_id = ? AND date = ?
    ''', (person_id, today))
    
    existing = cursor.fetchone()
    
    if existing:
        if status == 'absent':
            cursor.execute('''
                UPDATE attendance 
                SET time_out = ?, status = ? 
                WHERE person_id = ? AND date = ?
            ''', (now, status, person_id, today))
    else:
        cursor.execute('''
            INSERT INTO attendance (person_id, date, time_in, status)
            VALUES (?, ?, ?, ?)
        ''', (person_id, today, now, status))
    
    conn.commit()
    conn.close()

class ESP32Camera:
    def __init__(self):
        self.face_count = 0
        self.last_save_time = time.time()
        self.last_detection_time = time.time()
        self.SAVE_INTERVAL = 2.0
        self.ABSENCE_THRESHOLD = 5.0
        self.attendance_marked = False
        self.person_present = False
        self.last_presence_status = False
        self.attendance_manager = AttendanceManager()
        
        # Ensure directories exist
        os.makedirs(FACE_SAVE_DIR, exist_ok=True)
        os.makedirs(ATTENDANCE_DIR, exist_ok=True)
        
        # Load face cascade
        self.face_cascade = cv2.CascadeClassifier(HAAR_CASCADE_FILE)
        if self.face_cascade.empty():
            raise ValueError("Error: Haar cascade file is empty or invalid")

    def connect_to_camera(self):
        while True:
            try:
                esp32_ip = input("\nEnter ESP32-CAM IP address from Serial Monitor: ").strip()
                if esp32_ip.startswith("http://"):
                    esp32_ip = esp32_ip.replace("http://", "")
                
                print(f"\nTesting connection to ESP32-CAM at http://{esp32_ip}")
                response = requests.get(f"http://{esp32_ip}", timeout=5)
                if response.status_code == 200:
                    print("Successfully connected to ESP32-CAM!")
                    return f"http://{esp32_ip}:81/stream"
            except requests.exceptions.RequestException as e:
                print(f"\nError connecting to ESP32-CAM: {str(e)}")
                retry = input("\nWould you like to try again? (yes/no): ").strip().lower()
                if retry != 'yes':
                    raise ConnectionError("Failed to connect to ESP32-CAM")

    def run(self):
        stream_url = self.connect_to_camera()
        
        try:
            stream = requests.get(stream_url, stream=True, timeout=5)
            if stream.status_code != 200:
                raise ConnectionError(f"Could not access stream (status code: {stream.status_code})")
            
            print("Successfully connected to video stream!")
            print("\nStarting face detection...")
            print("Press 'q' to quit the program")
            
            cv2.namedWindow("ESP32-CAM Stream", cv2.WINDOW_NORMAL)
            
            bytes_buffer = bytes()
            while True:
                chunk = stream.raw.read(1024)
                if not chunk:
                    break
                
                bytes_buffer += chunk
                a = bytes_buffer.find(b'\xff\xd8')
                b = bytes_buffer.find(b'\xff\xd9')
                
                if a != -1 and b != -1:
                    jpg = bytes_buffer[a:b+2]
                    bytes_buffer = bytes_buffer[b+2:]
                    
                    if len(jpg) > 1000:
                        frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if frame is not None and frame.size > 0:
                            self.process_frame(frame)
                            
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                break
                
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            cv2.destroyAllWindows()

    def process_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=4,
            minSize=(50, 50),
            maxSize=(300, 300)
        )
        
        current_time = time.time()
        
        # Update presence status
        if len(faces) > 0:
            self.last_detection_time = current_time
            self.person_present = True
        elif current_time - self.last_detection_time > self.ABSENCE_THRESHOLD:
            self.person_present = False
        
        # Log status changes
        if self.person_present != self.last_presence_status:
            self.log_attendance(self.person_present)
            self.last_presence_status = self.person_present
        
        # Draw rectangles and status
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            if not self.attendance_marked:
                self.save_face(frame[y:y+h, x:x+w])
                self.attendance_marked = True
        
        # Add status text
        status_text = "Person 1: PRESENT" if self.person_present else "Person 1: ABSENT"
        status_color = (0, 255, 0) if self.person_present else (0, 0, 255)
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
        
        cv2.imshow('ESP32-CAM Stream', frame)

    def save_face(self, face_img):
        if face_img.size > 0:
            # Save the face image
            face_path = os.path.join(FACE_SAVE_DIR, f"person1_{self.face_count}.jpg")
            cv2.imwrite(face_path, face_img)
            print(f"\nSaved face as {face_path}")
            
            # Mark attendance in database
            self.attendance_manager.mark_attendance(
                person_name="Person 1",
                face_image_path=face_path,
                status="PRESENT"
            )
            
            self.face_count += 1
            print("Attendance marked in database")

    def log_attendance(self, is_present):
        current_date = time.strftime("%Y-%m-%d")
        current_time = time.strftime("%H:%M:%S")
        status = "PRESENT" if is_present else "ABSENT"
        
        attendance_file = os.path.join(ATTENDANCE_DIR, f"attendance_{current_date}.txt")
        with open(attendance_file, 'a') as f:
            f.write(f"Person 1 - Date: {current_date}, Time: {current_time}, Status: {status}\n")
        
        print(f"\nPerson 1 is now {status} at {current_time}")

if __name__ == '__main__':
    camera = ESP32Camera()
    camera.run()