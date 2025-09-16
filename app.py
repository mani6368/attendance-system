from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os
from models import db, Person, Attendance

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

ATTENDANCE_DIR = 'attendance_logs'
FACE_SAVE_DIR = 'detected_faces'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_attendance')
def get_attendance():
    try:
        # Get today's date
        today = datetime.now().date()
        
        # Query the database
        attendances = Attendance.query.filter_by(date=today).all()
        attendance_data = [attendance.to_dict() for attendance in attendances]
        
        attendance_data = []
        if os.path.exists(attendance_file):
            with open(attendance_file, 'r') as f:
                for line in f:
                    parts = line.strip().split(', ')
                    entry = {}
                    for part in parts:
                        key, value = part.split(': ')
                        entry[key.lower()] = value
                    attendance_data.append(entry)
        
        # Get list of detected face images
        face_images = []
        if os.path.exists(FACE_SAVE_DIR):
            face_images = [f for f in os.listdir(FACE_SAVE_DIR) if f.endswith('.jpg')]
        
        # Get current status
        current_status = "ABSENT"
        if attendance_data:
            current_status = attendance_data[-1]['status']
        
        return jsonify({
            'attendance': attendance_data,
            'face_images': face_images,
            'current_status': current_status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)