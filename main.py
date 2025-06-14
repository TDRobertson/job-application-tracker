import sys
import requests
import time
import re
from urllib.parse import urlparse
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QLineEdit, QPushButton,
                            QComboBox, QTreeWidget, QTreeWidgetItem, QMessageBox,
                            QCompleter, QHeaderView, QToolBar, QTabWidget)
from PyQt6.QtCore import Qt, QStringListModel, QUrl
from PyQt6.QtGui import QDesktopServices
from database import Database
from cache import CompanyCache

class JobTrackerApp(QMainWindow):
    """
    Main application window for the Job Application Tracker.
    Handles UI setup, user interactions, and communication with the database.
    """
    def __init__(self):
        """
        Initialize the main window, database, and UI components.
        """
        super().__init__()
        self.db = Database()
        self.cache = CompanyCache()
        self.last_api_call = 0
        self.min_api_interval = 1  # Minimum seconds between API calls
        self.init_ui()

    def init_ui(self):
        """
        Set up the user interface, including all widgets, layouts, and signals.
        """
        self.setWindowTitle('Job Application Tracker')
        self.setGeometry(100, 100, 1000, 700)  

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Application counters
        counter_layout = QHBoxLayout()
        self.counter_label = QLabel('Total Applications: 0')
        self.interview_counter_label = QLabel('Interviews: 0')
        self.rejected_counter_label = QLabel('Rejections: 0')
        self.counter_label.setStyleSheet('font-size: 14px; font-weight: bold;')
        self.interview_counter_label.setStyleSheet('font-size: 14px; font-weight: bold; color: #f5a623;')
        self.rejected_counter_label.setStyleSheet('font-size: 14px; font-weight: bold; color: #d0021b;')
        counter_layout.addWidget(self.counter_label)
        counter_layout.addWidget(self.interview_counter_label)
        counter_layout.addWidget(self.rejected_counter_label)
        counter_layout.addStretch()
        layout.addLayout(counter_layout)

        # Input form
        form_layout = QVBoxLayout()  #  vertical layout
        
        # Company name input with enhanced autocomplete
        company_layout = QHBoxLayout()
        company_label = QLabel('Company:')
        self.company_input = QLineEdit()
        self.company_model = QStringListModel()
        self.company_completer = QCompleter()
        self.company_completer.setModel(self.company_model)
        self.company_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.company_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.company_input.setCompleter(self.company_completer)
        self.company_input.textChanged.connect(self.update_company_suggestions)
        self.update_company_completer()  # Initial population
        company_layout.addWidget(company_label)
        company_layout.addWidget(self.company_input)
        form_layout.addLayout(company_layout)

        # Company website and description
        company_details_layout = QHBoxLayout()
        
        # Website URL
        website_label = QLabel('Website:')
        self.website_input = QLineEdit()
        self.website_input.setPlaceholderText('https://www.example.com')
        self.website_input.setToolTip('Enter a valid URL (e.g., https://www.example.com)')
        company_details_layout.addWidget(website_label)
        company_details_layout.addWidget(self.website_input)
        
        form_layout.addLayout(company_details_layout)
        
        # Company description
        description_label = QLabel('Description:')
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText('Optional company description...')
        self.description_input.setToolTip('Enter any additional information about the company')
        form_layout.addWidget(description_label)
        form_layout.addWidget(self.description_input)

        # Position input with enhanced autocomplete
        position_layout = QHBoxLayout()
        position_label = QLabel('Position:')
        self.position_input = QLineEdit()
        self.position_model = QStringListModel()
        self.position_completer = QCompleter()
        self.position_completer.setModel(self.position_model)
        self.position_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.position_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.position_input.setCompleter(self.position_completer)
        self.position_input.textChanged.connect(self.update_position_suggestions)
        self.update_position_completer()  # Initial population
        position_layout.addWidget(position_label)
        position_layout.addWidget(self.position_input)
        form_layout.addLayout(position_layout)

        # Status selection
        status_layout = QHBoxLayout()
        status_label = QLabel('Status:')
        self.status_input = QComboBox()
        self.status_input.addItems(['Applied', 'Interview', 'Rejected', 'Accepted'])
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_input)
        form_layout.addLayout(status_layout)

        # Add button
        add_button = QPushButton('Add Application')
        add_button.clicked.connect(self.add_application)
        form_layout.addWidget(add_button)

        layout.addLayout(form_layout)

        # Search and filter section
        search_layout = QHBoxLayout()
        
        # Search input
        search_label = QLabel('Search:')
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Search companies, positions, or status...')
        self.search_input.textChanged.connect(self.filter_applications)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        
        # Filter by status
        status_label = QLabel('Status:')
        self.status_filter = QComboBox()
        self.status_filter.addItems(['All', 'Applied', 'Interview', 'Rejected', 'Accepted'])
        self.status_filter.currentTextChanged.connect(self.filter_applications)
        search_layout.addWidget(status_label)
        search_layout.addWidget(self.status_filter)
        
        # Clear filters button
        clear_filters_btn = QPushButton('Clear Filters')
        clear_filters_btn.clicked.connect(self.clear_filters)
        search_layout.addWidget(clear_filters_btn)
        
        layout.addLayout(search_layout)

        # Tabs for active/rejected applications
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Active Applications tab
        active_tab = QWidget()
        active_layout = QVBoxLayout(active_tab)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Company/Position', 'Website', 'Application Date', 'Interview Round', 'Last Contact', 'Status'])
        self.tree.setColumnWidth(0, 200)
        self.tree.setColumnWidth(1, 200)
        self.tree.setAlternatingRowColors(True)
        self.tree.itemClicked.connect(self.handle_tree_click)
        active_layout.addWidget(self.tree)
        self.tabs.addTab(active_tab, 'Active Applications')

        # Rejected Applications tab
        rejected_tab = QWidget()
        rejected_layout = QVBoxLayout(rejected_tab)
        self.rejected_tree = QTreeWidget()
        self.rejected_tree.setHeaderLabels(['Company/Position', 'Website', 'Application Date', 'Interview Round', 'Last Contact', 'Status'])
        self.rejected_tree.setColumnWidth(0, 200)
        self.rejected_tree.setColumnWidth(1, 200)
        self.rejected_tree.setAlternatingRowColors(True)
        self.rejected_tree.itemClicked.connect(self.handle_tree_click)
        rejected_layout.addWidget(self.rejected_tree)
        self.tabs.addTab(rejected_tab, 'Rejected Applications')

        # Tree control buttons
        tree_controls = QHBoxLayout()
        
        # Expand/Collapse buttons
        expand_all_btn = QPushButton('Expand All')
        expand_all_btn.clicked.connect(self.tree.expandAll)
        tree_controls.addWidget(expand_all_btn)
        
        collapse_all_btn = QPushButton('Collapse All')
        collapse_all_btn.clicked.connect(self.tree.collapseAll)
        tree_controls.addWidget(collapse_all_btn)
        
        # Sort options
        sort_label = QLabel('Sort by:')
        tree_controls.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['Date (Newest First)', 'Date (Oldest First)', 
                                'Position (A-Z)', 'Position (Z-A)',
                                'Status (A-Z)', 'Status (Z-A)',
                                'Interview Round (High-Low)', 'Interview Round (Low-High)'])
        self.sort_combo.currentIndexChanged.connect(self.sort_applications)
        tree_controls.addWidget(self.sort_combo)
        
        tree_controls.addStretch()  # Push controls to the left
        layout.addLayout(tree_controls)

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

        # Status selection for updates
        self.update_status_combo = QComboBox()
        self.update_status_combo.addItems(['Applied', 'Interview', 'Rejected', 'Accepted'])
        update_layout.addWidget(QLabel('Status:'))
        update_layout.addWidget(self.update_status_combo)

        # Update button
        update_button = QPushButton('Update Status')
        update_button.clicked.connect(self.update_application)
        update_layout.addWidget(update_button)

        layout.addLayout(update_layout)

        # Load initial data
        self.load_applications()

    def update_company_suggestions(self, text):
        """
        Update the company autocomplete suggestions based on user input.
        Only show suggestions if the input is at least 3 characters.
        """
        if len(text) < 3:
            self.company_model.setStringList([])
        else:
            companies = self.db.get_unique_companies()
            # Sort companies by frequency of use (most used first)
            company_counts = {}
            for app in self.db.get_all_applications_grouped():
                company_name = app[1]  # company_name is at index 1
                if app[3] is not None:  # Only count if there's an application
                    company_counts[company_name] = company_counts.get(company_name, 0) + 1
            companies.sort(key=lambda x: (-company_counts.get(x, 0), x.lower()))
            self.company_model.setStringList(companies)

    def update_position_suggestions(self, text):
        """
        Update the position autocomplete suggestions based on user input.
        Only show suggestions if the input is at least 3 characters.
        """
        if len(text) < 3:
            self.position_model.setStringList([])
        else:
            positions = self.db.get_unique_positions()
            # Sort positions by frequency of use (most used first)
            position_counts = {}
            for app in self.db.get_all_applications_grouped():
                position = app[4]  # position is at index 4
                if app[3] is not None:  # Only count if there's an application
                    position_counts[position] = position_counts.get(position, 0) + 1
            positions.sort(key=lambda x: (-position_counts.get(x, 0), x.lower()))
            self.position_model.setStringList(positions)

    def update_company_completer(self):
        """
        Refresh the company autocomplete model with sorted suggestions.
        """
        companies = self.db.get_unique_companies()
        # Sort companies by frequency of use (most used first)
        company_counts = {}
        for app in self.db.get_all_applications_grouped():
            company_name = app[1]  # company_name is at index 1
            if app[3] is not None:  # Only count if there's an application
                company_counts[company_name] = company_counts.get(company_name, 0) + 1
        companies.sort(key=lambda x: (-company_counts.get(x, 0), x.lower()))
        self.company_model.setStringList(companies)

    def update_position_completer(self):
        """
        Refresh the position autocomplete model with sorted suggestions.
        """
        positions = self.db.get_unique_positions()
        # Sort positions by frequency of use (most used first)
        position_counts = {}
        for app in self.db.get_all_applications_grouped():
            position = app[4]  # position is at index 4
            if app[3] is not None:  # Only count if there's an application
                position_counts[position] = position_counts.get(position, 0) + 1
        positions.sort(key=lambda x: (-position_counts.get(x, 0), x.lower()))
        self.position_model.setStringList(positions)

    def validate_url(self, url):
        """
        Validate the format of a URL. Accepts empty strings as valid (optional field).
        Args:
            url (str): The URL to validate.
        Returns:
            bool: True if valid or empty, False otherwise.
        """
        if not url:  # Empty URL is valid (optional field)
            return True
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def add_application(self):
        """
        Add a new application to the database using the form fields.
        Validates required fields and URL format.
        Updates the UI and application counter after adding.
        """
        company = self.company_input.text().strip()
        position = self.position_input.text().strip()
        status = self.status_input.currentText()
        website = self.website_input.text().strip()
        description = self.description_input.text().strip()

        if not company or not position:
            QMessageBox.warning(self, 'Error', 'Please fill in company and position fields')
            return

        if website and not self.validate_url(website):
            QMessageBox.warning(self, 'Error', 'Please enter a valid URL (e.g., https://www.example.com)')
            return

        # Add to database
        self.db.add_application(company, position, description, website)
        
        # Update completers with new values
        self.update_company_completer()
        self.update_position_completer()
        
        # Clear inputs
        self.company_input.clear()
        self.position_input.clear()
        self.website_input.clear()
        self.description_input.clear()
        
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

    def sort_applications(self, tree=None):
        """
        Sort the applications within each company based on the selected sort option.
        If tree is None, sorts the main (active) tree. Otherwise, sorts the given tree.
        """
        if tree is None:
            tree = self.tree
        sort_option = self.sort_combo.currentText()
        expanded_companies = set()
        for i in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            if item.isExpanded():
                expanded_companies.add(item.text(0))
        for i in range(tree.topLevelItemCount()):
            company_item = tree.topLevelItem(i)
            applications = []
            for j in range(company_item.childCount()):
                app_item = company_item.child(j)
                applications.append(app_item)
                company_item.removeChild(app_item)
            if sort_option == 'Date (Newest First)':
                applications.sort(key=lambda x: x.text(2), reverse=True)
            elif sort_option == 'Date (Oldest First)':
                applications.sort(key=lambda x: x.text(2))
            elif sort_option == 'Position (A-Z)':
                applications.sort(key=lambda x: x.text(0))
            elif sort_option == 'Position (Z-A)':
                applications.sort(key=lambda x: x.text(0), reverse=True)
            elif sort_option == 'Status (A-Z)':
                applications.sort(key=lambda x: x.text(5))
            elif sort_option == 'Status (Z-A)':
                applications.sort(key=lambda x: x.text(5), reverse=True)
            elif sort_option == 'Interview Round (High-Low)':
                applications.sort(key=lambda x: int(x.text(3)), reverse=True)
            elif sort_option == 'Interview Round (Low-High)':
                applications.sort(key=lambda x: int(x.text(3)))
            for app in applications:
                company_item.addChild(app)
        for i in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            if item.text(0) in expanded_companies:
                item.setExpanded(True)

    def filter_applications(self):
        """
        Filter the displayed applications based on search text and status filter.
        Only shows companies and applications that match the criteria in the current tab.
        """
        search_text = self.search_input.text().lower()
        status_filter = self.status_filter.currentText()
        # Use the correct tree for the current tab
        current_tree = self.tree if self.tabs.currentIndex() == 0 else self.rejected_tree
        expanded_companies = set()
        for i in range(current_tree.topLevelItemCount()):
            item = current_tree.topLevelItem(i)
            if item.isExpanded():
                expanded_companies.add(item.text(0))
        for i in range(current_tree.topLevelItemCount()):
            company_item = current_tree.topLevelItem(i)
            company_name = company_item.text(0).lower()
            company_visible = False
            if search_text in company_name:
                company_visible = True
            for j in range(company_item.childCount()):
                app_item = company_item.child(j)
                position = app_item.text(0).lower()
                status = app_item.text(5)
                app_visible = True
                if search_text and search_text not in position:
                    app_visible = False
                if status_filter != 'All' and status != status_filter:
                    app_visible = False
                app_item.setHidden(not app_visible)
                if app_visible:
                    company_visible = True
            company_item.setHidden(not company_visible)
            if company_visible and company_item.text(0) in expanded_companies:
                company_item.setExpanded(True)

    def clear_filters(self):
        """
        Clear all search and filter fields and show all applications.
        """
        self.search_input.clear()
        self.status_filter.setCurrentText('All')
        self.filter_applications()

    def handle_tree_click(self, item, column):
        """
        Handle clicks on the tree widget. Opens the company website if the website column is clicked.
        Args:
            item (QTreeWidgetItem): The clicked item.
            column (int): The column index that was clicked.
        """
        # If the website column is clicked and it has a valid URL, open it
        if column == 1:
            url = item.text(1)
            if url and urlparse(url).scheme in ('http', 'https'):
                QDesktopServices.openUrl(QUrl(url))

    def get_status_color(self, status):
        colors = {
            'Applied': '#4a90e2',    # Blue
            'Interview': '#f5a623',  # Orange
            'Rejected': '#d0021b',   # Red
            'Accepted': '#7ed321'    # Green
        }
        return colors.get(status, '#000000')  # Default to black if status not found

    def load_applications(self):
        """
        Load all applications from the database and display them in the appropriate tree views.
        Updates the company combo box and application counters.
        """
        self.tree.clear()
        self.rejected_tree.clear()
        self.company_combo.clear()

        # Get all applications grouped by company
        applications = self.db.get_all_applications_grouped()

        # Dictionaries to store company items for each tree
        company_items = {}
        rejected_company_items = {}

        # Counters
        total_apps = 0
        interview_count = 0
        rejected_count = 0

        for app in applications:
            company_id = app[0]
            company_name = app[1]
            company_description = app[2]
            application_id = app[3]
            if application_id is None:
                continue
            position = app[4]
            application_date = app[5]
            interview_round = app[6]
            last_contact = app[7]
            status = app[8]

            # Count for stats
            total_apps += 1
            if status == 'Interview':
                interview_count += 1
            if status == 'Rejected':
                rejected_count += 1

            # Choose which tree to display in
            if status == 'Rejected':
                # Rejected tab
                if company_id not in rejected_company_items:
                    company_info = self.db.get_company_info(company_id)
                    website = ''
                    if company_info:
                        _, _, website = company_info
                    company_item = QTreeWidgetItem(self.rejected_tree)
                    company_item.setText(0, company_name)
                    company_item.setText(1, website or '')
                    rejected_company_items[company_id] = company_item
                app_item = QTreeWidgetItem(rejected_company_items[company_id])
                app_item.setText(0, position)
                app_item.setText(1, '')
                app_item.setText(2, application_date)
                app_item.setText(3, str(interview_round))
                app_item.setText(4, str(last_contact or ''))
                app_item.setText(5, status)
                app_item.setData(0, Qt.ItemDataRole.UserRole, application_id)
            else:
                # Active tab
                if company_id not in company_items:
                    company_info = self.db.get_company_info(company_id)
                    website = ''
                    if company_info:
                        _, _, website = company_info
                    company_item = QTreeWidgetItem(self.tree)
                    company_item.setText(0, company_name)
                    company_item.setText(1, website or '')
                    company_items[company_id] = company_item
                    self.company_combo.addItem(f"{company_name}", company_id)
                app_item = QTreeWidgetItem(company_items[company_id])
                app_item.setText(0, position)
                app_item.setText(1, '')
                app_item.setText(2, application_date)
                app_item.setText(3, str(interview_round))
                app_item.setText(4, str(last_contact or ''))
                app_item.setText(5, status)
                app_item.setData(0, Qt.ItemDataRole.UserRole, application_id)

        # Apply initial sort (newest first) for both trees
        self.sort_combo.setCurrentText('Date (Newest First)')
        self.sort_applications()
        self.sort_applications(tree=self.rejected_tree)

        # Update counters
        self.counter_label.setText(f'Total Applications: {total_apps}')
        self.interview_counter_label.setText(f'Interviews: {interview_count}')
        self.rejected_counter_label.setText(f'Rejections: {rejected_count}')

    def update_application(self):
        """
        Update the interview round and status for the selected application.
        Validates selection and updates the database and UI.
        """
        if self.company_combo.currentIndex() == -1:
            QMessageBox.warning(self, 'Error', 'Please select a company')
            return

        # Get the selected application ID from the tree
        selected_items = self.tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'Error', 'Please select an application to update')
            return
            
        selected_item = selected_items[0]
        # Only allow updating individual applications, not company groups
        if selected_item.parent() is None:
            QMessageBox.warning(self, 'Error', 'Please select a specific application to update')
            return
            
        application_id = selected_item.data(0, Qt.ItemDataRole.UserRole)
        round_number = int(self.round_combo.currentText())
        status = self.update_status_combo.currentText()
        
        self.db.update_interview_round(application_id, round_number)
        self.db.update_application_status(application_id, status)
        self.load_applications()

    def closeEvent(self, event):
        """
        Handle the window close event. Clears expired cache entries.
        Args:
            event (QCloseEvent): The close event.
        """
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