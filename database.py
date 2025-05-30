import sqlite3
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('job_tracker.db')
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                position TEXT NOT NULL,
                application_date TIMESTAMP NOT NULL,
                interview_round INTEGER DEFAULT 0,
                last_contact_date TIMESTAMP,
                status TEXT DEFAULT 'Applied',
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        ''')
        self.conn.commit()

    def add_application(self, company_name, position, company_description=None):
        cursor = self.conn.cursor()
        
        # First, ensure company exists
        cursor.execute('''
            INSERT OR IGNORE INTO companies (name, description)
            VALUES (?, ?)
        ''', (company_name, company_description))
        
        # Get company ID
        cursor.execute('SELECT id FROM companies WHERE name = ?', (company_name,))
        company_id = cursor.fetchone()[0]
        
        # Add application
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO applications (company_id, position, application_date)
            VALUES (?, ?, ?)
        ''', (company_id, position, current_time))
        self.conn.commit()
        return cursor.lastrowid

    def get_all_applications_grouped(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                c.id as company_id,
                c.name as company_name,
                c.description as company_description,
                a.id as application_id,
                a.position,
                a.application_date,
                a.interview_round,
                a.last_contact_date,
                a.status
            FROM companies c
            LEFT JOIN applications a ON c.id = a.company_id
            ORDER BY c.name, a.application_date DESC
        ''')
        return cursor.fetchall()

    def get_company_applications(self, company_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                a.id,
                a.position,
                a.application_date,
                a.interview_round,
                a.last_contact_date,
                a.status
            FROM applications a
            WHERE a.company_id = ?
            ORDER BY a.application_date DESC
        ''', (company_id,))
        return cursor.fetchall()

    def update_interview_round(self, application_id, round_number):
        cursor = self.conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            UPDATE applications 
            SET interview_round = ?, last_contact_date = ?
            WHERE id = ?
        ''', (round_number, current_time, application_id))
        self.conn.commit()

    def update_application_status(self, application_id, status):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE applications 
            SET status = ?
            WHERE id = ?
        ''', (status, application_id))
        self.conn.commit()

    def get_unique_companies(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM companies ORDER BY name')
        return [row[0] for row in cursor.fetchall()]

    def get_unique_positions(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT DISTINCT position FROM applications ORDER BY position')
        return [row[0] for row in cursor.fetchall()]

    def __del__(self):
        self.conn.close() 