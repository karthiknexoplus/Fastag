# Fastag Management System

A modern, scalable Flask application for managing FASTag parking locations, lanes, and RFID readers with a beautiful, responsive UI.

## 🚀 Features

### Authentication
- Secure login/signup system with session management
- Glassmorphism design with modern UI elements
- Activity logging for all user actions

### Location Management
- Create and manage parking locations
- Auto-generated unique site IDs
- Full CRUD operations with modern interface

### Lane Management
- Add lanes to locations
- Track reader count per lane
- Integrated with location system

### Reader Management
- Configure RFID readers per lane
- Support for entry/exit readers (max 2 per lane)
- MAC address and IP configuration
- Type validation (entry/exit only)

### Technical Features
- Modular blueprint architecture
- SQLite database with proper relationships
- Comprehensive logging system
- Production-ready configuration
- Responsive Bootstrap UI with FontAwesome icons

## 🏗️ Project Structure

```
Fastag/
├── fastag/                    # Main application package
│   ├── __init__.py           # Flask app factory
│   ├── routes/               # Blueprint routes
│   │   ├── auth.py          # Authentication routes
│   │   ├── locations.py     # Location management
│   │   ├── lanes.py         # Lane management
│   │   └── readers.py       # Reader management
│   ├── templates/           # Jinja2 templates
│   │   ├── base.html        # Base template
│   │   ├── login.html       # Login page
│   │   ├── signup.html      # Signup page
│   │   ├── home.html        # Dashboard
│   │   ├── locations.html   # Location management
│   │   ├── lanes.html       # Lane management
│   │   ├── edit_lane.html   # Edit lane form
│   │   ├── readers.html     # Reader management
│   │   └── edit_reader.html # Edit reader form
│   └── utils/               # Utility modules
│       ├── db.py           # Database utilities
│       └── logging.py      # Logging configuration
├── instance/                # Instance-specific files
│   └── fastag.db           # SQLite database
├── logs/                    # Application logs
├── config.py               # Configuration settings
├── wsgi.py                 # WSGI entry point
├── test_app.py             # Test script
└── README.md               # This file
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.7+
- pip

### Installation Steps

1. **Clone or download the project**
   ```bash
   cd /path/to/Fastag
   ```

2. **Install dependencies**
   ```bash
   pip install flask
   ```

3. **Run the test script to verify setup**
   ```bash
   python test_app.py
   ```

4. **Start the application**
   ```bash
   python wsgi.py
   ```

5. **Access the application**
   - Open your browser and go to `http://localhost:5000`
   - Create an account and start managing your FASTag system

## 📊 Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `password`: Hashed password
- `created_at`: Timestamp

### Activity Log Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `action`: Action description
- `details`: Additional details
- `timestamp`: When action occurred

### Locations Table
- `id`: Primary key
- `name`: Location name
- `address`: Physical address
- `site_id`: Auto-generated unique ID
- `created_at`: Timestamp

### Lanes Table
- `id`: Primary key
- `location_id`: Foreign key to locations
- `lane_name`: Lane identifier
- `created_at`: Timestamp

### Readers Table
- `id`: Primary key
- `lane_id`: Foreign key to lanes
- `mac_address`: Reader MAC address
- `type`: 'entry' or 'exit'
- `reader_ip`: Reader IP address
- `created_at`: Timestamp

## 🔧 Configuration

The application uses a `config.py` file for configuration:

```python
import os

class Config:
    SECRET_KEY = 'your-secret-key-here'
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'fastag.db')
    LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
```

## 🎨 UI Features

### Modern Design
- Glassmorphism effects
- Responsive Bootstrap 5 layout
- FontAwesome icons throughout
- Consistent color scheme
- Professional typography

### User Experience
- Intuitive navigation
- Confirmation dialogs for deletions
- Real-time form validation
- Clear visual feedback
- Mobile-friendly interface

## 🔒 Security Features

- Session-based authentication
- Password hashing
- SQL injection protection
- CSRF protection
- Input validation
- Activity logging

## 📝 Usage Guide

### 1. Authentication
- Register a new account or login
- All actions are logged for audit purposes

### 2. Location Management
- Add new locations with name and address
- Site IDs are automatically generated
- Edit or delete existing locations

### 3. Lane Management
- Select a location to manage its lanes
- Add lanes to locations
- Each lane can have up to 2 readers

### 4. Reader Configuration
- Configure RFID readers for each lane
- Set MAC address and IP address
- Specify reader type (entry/exit)
- Maximum 2 readers per lane (1 entry, 1 exit)

## 🚀 Production Deployment

### Using WSGI Server
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

### Using Docker (example)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install flask gunicorn
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "wsgi:app"]
```

## 🐛 Troubleshooting

### Common Issues

1. **Database errors**: Ensure the `instance/` directory exists and is writable
2. **Import errors**: Verify all dependencies are installed
3. **Port conflicts**: Change the port in `wsgi.py` if 5000 is in use

### Logs
- Check the `logs/` directory for application logs
- Database is stored in `instance/fastag.db`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support or questions, please check the logs or create an issue in the repository.

---

**Powered by Nexoplus Innovations Pvt Ltd** 