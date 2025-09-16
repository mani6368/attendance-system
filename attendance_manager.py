import sqlite3
import cv2
import numpy as np
import requests
import time
import os
from datetime import datetime

class AttendanceManager:
    def __init__(self):
        self.db_file = 'attendance.db'
        self.setup_database()

    def setup_database(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS person (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER,
                date DATE,
                time_in TIMESTAMP,
                time_out TIMESTAMP,
                status TEXT,
                image_path TEXT,
                FOREIGN KEY (person_id) REFERENCES person (id)
            );
        ''')
        conn.commit()
        conn.close()

    def mark_attendance(self, person_name, face_image_path, status='PRESENT'):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        now = datetime.now()
        today = now.date()

        # Get or create person
        cursor.execute('SELECT id FROM person WHERE name = ?', (person_name,))
        result = cursor.fetchone()
        
        if result is None:
            cursor.execute('INSERT INTO person (name) VALUES (?)', (person_name,))
            person_id = cursor.lastrowid
        else:
            person_id = result[0]

        # Check for existing attendance today
        cursor.execute('''
            SELECT id FROM attendance 
            WHERE person_id = ? AND date = ?
        ''', (person_id, today))
        
        existing = cursor.fetchone()
        
        if existing is None:
            # Create new attendance record
            cursor.execute('''
                INSERT INTO attendance (person_id, date, time_in, status, image_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (person_id, today, now, status, face_image_path))
        else:
            # Update existing record
            cursor.execute('''
                UPDATE attendance 
                SET time_out = ?, status = ?
                WHERE person_id = ? AND date = ?
            ''', (now, status, person_id, today))

        conn.commit()
        conn.close()
        return True