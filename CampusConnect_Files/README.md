# CampusConnect+ - Unified College Communication Platform

## Project Overview
**CampusConnect+** is a single digital platform for college communication, events, notices, clubs, and student participation management.

## Technology Stack
- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Template Engine**: Jinja2

## Features

### Core Features (Phase 1)
1. **Notices** - Centralized academic and event notices
2. **Events** - Event listings and registration
3. **Clubs** - Club information and management

### Advanced Features (Phase 2)
4. **Polls & Feedback** - Student polls and feedback collection
5. **Attendance** - Event attendance tracking
6. **Issue Reporting** - Report campus issues (water, cleanliness, hostel)

## User Roles
- **Student** - View notices, events, clubs; participate in polls
- **Faculty** - Post notices, manage events
- **Admin** - Full system management

## Project Structure
```
CampusConnect+/
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── database.db         # SQLite database (auto-created)
├── requirements.txt    # Python dependencies
├── static/
│   ├── css/           # Stylesheets
│   ├── js/            # JavaScript files
│   └── images/        # Image assets
└── templates/
    ├── base.html       # Base template
    ├── index.html      # Home page
    ├── notices.html    # Notices page
    ├── events.html     # Events page
    ├── clubs.html      # Clubs page
    ├── login.html      # Login page
    └── register.html   # Registration page
```

## Setup Instructions
1. Install dependencies: `pip install -r requirements.txt`
2. Run the application: `python app.py`
3. Open browser: `http://localhost:5000`

## Database Schema
- **users** - id, username, email, password, role, created_at
- **notices** - id, title, content, category, posted_by, created_at
- **events** - id, title, description, date, location, organized_by, created_at
- **clubs** - id, name, description, created_at
- **issues** - id, title, description, category, status, reported_by, created_at
