import sqlite3
from datetime import datetime

class Database:
    """
    Handles all database operations for the job application tracker.
    Manages tables for companies and applications, and provides methods to add, update, and retrieve data.
    """
    def __init__(self):
        """
        Initialize the database connection and create tables if they do not exist.
        """
        self.conn = sqlite3.connect('job_tracker.db')
        self.create_tables()

    def create_tables(self):
        """
        Create the companies and applications tables if they do not already exist.
        The companies table stores unique company information.
        The applications table stores job application details and references companies.
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                website_url TEXT
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

    def add_application(self, company_name, position, company_description=None, company_website=None):
        """
        Add a new job application to the database. If the company does not exist, it is created.
        Args:
            company_name (str): Name of the company.
            position (str): Position applied for.
            company_description (str, optional): Description of the company.
            company_website (str, optional): Website URL of the company.
        Returns:
            int: The ID of the newly created application.
        """
        cursor = self.conn.cursor()
        # Ensure the company exists in the companies table
        cursor.execute('''
            INSERT OR IGNORE INTO companies (name, description, website_url)
            VALUES (?, ?, ?)
        ''', (company_name, company_description, company_website))
        # Retrieve the company ID
        cursor.execute('SELECT id FROM companies WHERE name = ?', (company_name,))
        company_id = cursor.fetchone()[0]
        # Insert the application
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO applications (company_id, position, application_date, status)
            VALUES (?, ?, ?, ?)
        ''', (company_id, position, current_time, 'Applied'))
        self.conn.commit()
        return cursor.lastrowid

    def get_all_applications_grouped(self):
        """
        Retrieve all applications, grouped by company, with company and application details.
        Returns:
            list: List of tuples containing company and application data.
        """
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
        """
        Retrieve all applications for a specific company.
        Args:
            company_id (int): The ID of the company.
        Returns:
            list: List of tuples containing application data for the company.
        """
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
        """
        Update the interview round and last contact date for a specific application.
        Args:
            application_id (int): The ID of the application.
            round_number (int): The new interview round number.
        """
        cursor = self.conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            UPDATE applications 
            SET interview_round = ?, last_contact_date = ?
            WHERE id = ?
        ''', (round_number, current_time, application_id))
        self.conn.commit()

    def update_application_status(self, application_id, status):
        """
        Update the status and last contact date for a specific application.
        Args:
            application_id (int): The ID of the application.
            status (str): The new status (e.g., 'Applied', 'Interview', 'Rejected', 'Accepted').
        """
        cursor = self.conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            UPDATE applications 
            SET status = ?, last_contact_date = ?
            WHERE id = ?
        ''', (status, current_time, application_id))
        self.conn.commit()

    def get_unique_companies(self):
        """
        Retrieve a list of all unique company names in the database.
        Returns:
            list: List of company names (str).
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM companies ORDER BY name')
        return [row[0] for row in cursor.fetchall()]

    def get_unique_positions(self):
        """
        Retrieve a list of all unique positions in the database.
        Returns:
            list: List of position names (str).
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT DISTINCT position FROM applications ORDER BY position')
        return [row[0] for row in cursor.fetchall()]

    def get_total_applications(self):
        """
        Get the total number of applications in the database.
        Returns:
            int: Total number of applications.
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM applications')
        return cursor.fetchone()[0]

    def get_company_info(self, company_id):
        """
        Retrieve the name, description, and website URL for a specific company.
        Args:
            company_id (int): The ID of the company.
        Returns:
            tuple: (name, description, website_url) for the company.
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT name, description, website_url
            FROM companies
            WHERE id = ?
        ''', (company_id,))
        return cursor.fetchone()

    def __del__(self):
        """
        Close the database connection when the Database object is deleted.
        """
        self.conn.close() 