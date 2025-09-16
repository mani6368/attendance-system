# ESP32-CAM Attendance System with Web Interface

This project implements a face detection-based attendance system using ESP32-CAM and provides a web interface to view attendance records.

## Features
- Real-time face detection using ESP32-CAM
- Automatic attendance marking
- Web interface to view attendance records
- Status tracking (Present/Absent)
- Face image storage
- Daily attendance logs

## Setup Instructions

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Configure ESP32-CAM:
- Upload the ESP32-CAM code to your device
- Connect to the WiFi network
- Note down the IP address from Serial Monitor

3. Run the application:
```bash
python app.py
```

4. Access the web interface:
- Open browser and go to `http://localhost:5000`

## Project Structure
```
attendance_system/
├── static/
│   ├── css/
│   └── js/
├── templates/
├── detected_faces/
├── attendance_logs/
├── app.py
├── camera.py
└── requirements.txt
```

## Usage
1. Start the camera system: `python camera.py`
2. Start the web server: `python app.py`
3. Open web browser and navigate to `http://localhost:5000`

## Notes
- Ensure ESP32-CAM is properly configured and connected to the network
- Keep the camera stable for better face detection
- Check attendance logs in `attendance_logs` directory