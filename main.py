import sys
import requests
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QLineEdit, QPushButton,
                            QComboBox, QTableWidget, QTableWidgetItem, QMessageBox)
from PyQt6.QtCore import Qt
from database import Database
from cache import CompanyCache

class JobTrackerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.cache = CompanyCache()
        self.last_api_call = 0
        self.min_api_interval = 1  # Minimum seconds between API calls
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Job Application Tracker')
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Input form
        form_layout = QHBoxLayout()
        
        # Company name input
        company_label = QLabel('Company:')
        self.company_input = QLineEdit()
        form_layout.addWidget(company_label)
        form_layout.addWidget(self.company_input)

        # Position input
        position_label = QLabel('Position:')
        self.position_input = QLineEdit()
        form_layout.addWidget(position_label)
        form_layout.addWidget(self.position_input)

        # Add button
        add_button = QPushButton('Add Application')
        add_button.clicked.connect(self.add_application)
        form_layout.addWidget(add_button)

        layout.addLayout(form_layout)

        # Applications table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Company', 'Position', 'Application Date',
            'Interview Round', 'Last Contact', 'Status'
        ])
        layout.addWidget(self.table)

        # Update section
        update_layout = QHBoxLayout()
        
        # Company selection for updates
        self.company_combo = QComboBox()
        update_layout.addWidget(QLabel('Select Company:'))
        update_layout.addWidget(self.company_combo)

        # Interview round selection
        self.round_combo = QComboBox()
        self.round_combo.addItems(['0', '1', '2', '3', '4', '5'])
        update_layout.addWidget(QLabel('Interview Round:'))
        update_layout.addWidget(self.round_combo)

        # Update button
        update_button = QPushButton('Update Status')
        update_button.clicked.connect(self.update_application)
        update_layout.addWidget(update_button)

        layout.addLayout(update_layout)

        # Load initial data
        self.load_applications()

    def add_application(self):
        company = self.company_input.text().strip()
        position = self.position_input.text().strip()

        if not company or not position:
            QMessageBox.warning(self, 'Error', 'Please fill in all fields')
            return

        # Get company description (simplified for now)
        company_description = self.get_company_description(company)
        
        # Add to database
        self.db.add_application(company, position, company_description)
        
        # Clear inputs
        self.company_input.clear()
        self.position_input.clear()
        
        # Reload data
        self.load_applications()

    def get_company_description(self, company_name):
        # Check cache first
        cached_data = self.cache.get(company_name)
        if cached_data:
            return cached_data

        try:
            # Rate limiting
            current_time = time.time()
            time_since_last_call = current_time - self.last_api_call
            if time_since_last_call < self.min_api_interval:
                time.sleep(self.min_api_interval - time_since_last_call)
            
            # OpenCorporates API endpoint
            url = f"https://api.opencorporates.com/v0.4/companies/search"
            params = {
                'q': company_name,
                'api_token': 'YOUR_API_TOKEN'  # You'll need to sign up for a free API token
            }
            
            response = requests.get(url, params=params)
            self.last_api_call = time.time()

            # Handle rate limiting response
            if response.status_code == 429:  # Too Many Requests
                retry_after = int(response.headers.get('Retry-After', 60))
                QMessageBox.warning(
                    self,
                    'Rate Limit Reached',
                    f'API rate limit reached. Please wait {retry_after} seconds before trying again.'
                )
                return f"Description for {company_name} (Rate limited)"
            
            # Handle other error responses
            response.raise_for_status()
            
            data = response.json()
            
            if data['results']['companies']:
                company = data['results']['companies'][0]['company']
                description = f"{company.get('name', '')} - "
                description += f"Founded: {company.get('incorporation_date', 'Unknown')}, "
                description += f"Status: {company.get('current_status', 'Unknown')}, "
                description += f"Jurisdiction: {company.get('jurisdiction_code', 'Unknown')}"
                
                # Cache the result
                self.cache.set(company_name, description)
                return description
            else:
                return f"No detailed information found for {company_name}"
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching company data: {e}")
            return f"Description for {company_name} (API error)"

    def load_applications(self):
        applications = self.db.get_all_applications()
        self.table.setRowCount(len(applications))
        self.company_combo.clear()

        for row, app in enumerate(applications):
            self.table.setItem(row, 0, QTableWidgetItem(str(app[0])))
            self.table.setItem(row, 1, QTableWidgetItem(app[1]))
            self.table.setItem(row, 2, QTableWidgetItem(app[2]))
            self.table.setItem(row, 3, QTableWidgetItem(app[3]))
            self.table.setItem(row, 4, QTableWidgetItem(str(app[5])))
            self.table.setItem(row, 5, QTableWidgetItem(str(app[6] or '')))
            self.table.setItem(row, 6, QTableWidgetItem(app[7]))

            self.company_combo.addItem(f"{app[1]} - {app[2]}", app[0])

    def update_application(self):
        if self.company_combo.currentIndex() == -1:
            QMessageBox.warning(self, 'Error', 'Please select a company')
            return

        application_id = self.company_combo.currentData()
        round_number = int(self.round_combo.currentText())
        
        self.db.update_interview_round(application_id, round_number)
        self.load_applications()

    def closeEvent(self, event):
        # Clear expired cache entries when closing the application
        self.cache.clear_expired()
        super().closeEvent(event)

def main():
    app = QApplication(sys.argv)
    window = JobTrackerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 