import sqlite3
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('job_tracker.db')
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                position TEXT NOT NULL,
                application_date TIMESTAMP NOT NULL,
                company_description TEXT,
                interview_round INTEGER DEFAULT 0,
                last_contact_date TIMESTAMP,
                status TEXT DEFAULT 'Applied'
            )
        ''')
        self.conn.commit()

    def add_application(self, company_name, position, company_description=None):
        cursor = self.conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO applications (company_name, position, application_date, company_description)
            VALUES (?, ?, ?, ?)
        ''', (company_name, position, current_time, company_description))
        self.conn.commit()
        return cursor.lastrowid

    def update_interview_round(self, application_id, round_number):
        cursor = self.conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            UPDATE applications 
            SET interview_round = ?, last_contact_date = ?
            WHERE id = ?
        ''', (round_number, current_time, application_id))
        self.conn.commit()

    def get_all_applications(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM applications ORDER BY application_date DESC')
        return cursor.fetchall()

    def get_application_by_id(self, application_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM applications WHERE id = ?', (application_id,))
        return cursor.fetchone()

    def update_application_status(self, application_id, status):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE applications 
            SET status = ?
            WHERE id = ?
        ''', (status, application_id))
        self.conn.commit()

    def __del__(self):
        self.conn.close() 