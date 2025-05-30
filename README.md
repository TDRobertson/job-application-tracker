# Job Application Tracker

A modern desktop application for tracking your job applications, built with Python and PyQt6.

## Features

- **Add Applications:** Add new job applications with company name, position, status, company website, and description.
- **Autocomplete:** Company and position fields feature smart autocomplete based on your previous entries.
- **Status Tracking:** Track the status of each application (Applied, Interview, Rejected, Accepted) and update it at any time.
- **Interview Rounds:** Track and update the interview round for each application.
- **Company Grouping:** Applications are grouped by company in an expandable/collapsible tree view.
- **Website Links:** Company website URLs are displayed and clickable directly in the table.
- **Search & Filter:** Instantly search and filter applications by company, position, or status.
- **Sorting:** Sort applications by date, position, status, or interview round.
- **Total Applications Counter:** See a running tally of all applications submitted.
- **Modern UI:** Clean, user-friendly interface with dark mode support.

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd job-application-tracker
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   (You need Python 3.8+ and PyQt6)

## Running the Application

From the project directory, run:

```bash
python main.py
```

## Usage Guide

### Adding a New Application

1. Fill in the **Company** name (autocomplete is available).
2. Optionally enter the **Website** and **Description** for the company.
3. Enter the **Position** (autocomplete is available).
4. Select the **Status** (Applied, Interview, Rejected, Accepted).
5. Click **Add Application**.

### Viewing and Managing Applications

- All applications are grouped by company in the main table.
- The **Website** column shows the company website (clickable for parent/company rows).
- Use the **Search** bar and **Status** filter to quickly find applications.
- Use the **Sort by** dropdown to sort applications by date, position, status, or interview round.
- The **Total Applications** counter at the top shows your running tally.

### Updating an Application

1. Select a company from the **Select Company** dropdown at the bottom.
2. Click on the specific application row you want to update in the table.
3. Choose the new **Interview Round** and/or **Status**.
4. Click **Update Status**.

### Expand/Collapse

- Use the **Expand All** and **Collapse All** buttons to quickly expand or collapse all company groups.

## Database

- The application uses a local SQLite database (`job_tracker.db`) in the project directory.
- All data is saved automatically.

## Support

For issues or feature requests, please open an issue on the repository.
