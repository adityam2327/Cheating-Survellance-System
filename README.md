# Cheating Surveillance System

## Overview
The **Cheating Surveillance System** is a comprehensive solution designed to detect cheating during Online Interviews/Exams. It combines real-time computer vision analysis with a Django web application and blockchain-based logging for secure, tamper-proof record keeping. The system monitors head and pupil movements, identifies unauthorized mobile phone usage, analyzes facial emotions for stress indicators, and provides a complete web-based dashboard for monitoring and analytics.

## Features

### Core Surveillance Features
- **Head and Pupil Movement Detection**: Uses **dlib's Shape Predictor 68** to track facial landmarks and detect suspicious gaze patterns
- **Mobile Phone Detection**: Utilizes **YOLOv8 model** trained on the [Roboflow Cellphone Detection Dataset](https://universe.roboflow.com/d1156414/cellphone-0aodn) to detect mobile phones in real-time
- **Lip Movement Detection**: Analyzes lip movements to detect whispering or silent communication
- **Emotion Detection**: Detects stress, fear, and overconfidence through facial emotion recognition using machine learning models
- **Real-Time Monitoring**: Processes live video feeds for instant analysis and detection
- **Alert System**: Detects and flags potential cheating behavior with configurable thresholds

### Web Application Features
- **Django Web Dashboard**: Complete web interface for monitoring sessions and violations
- **User Authentication**: Secure login system with JWT token authentication
- **Session Management**: Create and manage surveillance sessions
- **Violation Tracking**: Comprehensive logging of all detected violations
- **Analytics Dashboard**: Real-time statistics and historical data visualization
- **Blockchain Integration**: Tamper-proof logging of all surveillance events

### Blockchain Security Features
- **Immutable Logging**: All surveillance events are logged to a blockchain database
- **Audit Trail**: Complete history of all detected violations and system activities
- **Data Integrity**: Cryptographic verification of logged data
- **Export Capabilities**: Export blockchain logs for external analysis

## Technologies Used

### Core Technologies
- **Python 3.10+**
- **OpenCV 4.11.0** (for video processing)
- **dlib 20.0.0** (for facial landmark detection)
- **YOLOv8** (for object detection)
- **MediaPipe 0.10.21** (for face detection and landmarks)
- **Librosa 0.11.0** (for audio analysis)
- **Scikit-learn 1.7.0** (for machine learning models)
- **NumPy 1.26.4** (for numerical computations)

### Web Framework
- **Django 5.0.2** (web framework)
- **Django REST Framework 3.15.0** (API development)
- **Django Channels 4.0.0** (WebSocket support)
- **Celery 5.3.4** (background task processing)
- **Redis 5.0.1** (message broker and caching)

### Authentication & Security
- **Django Allauth 0.60.1** (authentication)
- **JWT Authentication** (token-based auth)
- **Cryptography 45.0.4** (encryption)

### Database & Storage
- **SQLite/PostgreSQL** (primary database)
- **Blockchain Database** (immutable logging)

## Project Structure
```
Cheating-Surveillance-System/
├── surveillance_system/          # Django project settings
│   ├── settings.py              # Main Django configuration
│   ├── urls.py                  # Main URL routing
│   ├── celery.py                # Celery configuration
│   └── asgi.py                  # ASGI configuration
├── users/                       # User authentication app
├── sessions/                    # Session management app
├── violations/                  # Violation tracking app
├── blockchain/                  # Blockchain integration app
├── monitoring/                  # Real-time monitoring app
├── analytics/                   # Analytics and reporting app
├── dashboard/                   # Web dashboard app
├── templates/                   # HTML templates
├── model/                       # ML models and weights
│   ├── shape_predictor_68_face_landmarks.dat
│   ├── best_yolov8.pt
│   └── best.pt
├── demo_vdo/                    # Demo videos
│   ├── gaze-detection.mp4
│   ├── headpose-detection.mp4
│   └── Mobile-detection.mp4
├── log/                         # Screenshots and recordings
├── main.py                      # Entry point for real-time detection
├── eye_movement.py              # Gaze detection module
├── head_pose.py                 # Head movement detection
├── mobile_detection.py          # Mobile phone detection
├── lip_movement.py              # Lip movement analysis
├── emotion_detection.py         # Emotion detection
├── blockchain_integration.py    # Blockchain logging
├── blockchain_logger.py         # Blockchain utilities
├── blockchain_dashboard.py      # Blockchain dashboard
├── test_blockchain.py           # Blockchain testing
├── test_emotion_detection.py    # Emotion detection testing
├── requirements.txt             # Python dependencies
├── manage.py                    # Django management
└── README.md                    # Project documentation
```

## Installation

### Prerequisites
- Python 3.10 or higher
- Virtual environment (recommended)
- Webcam or video input device
- Sufficient disk space for models (~100MB)

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Sania-hasann/Cheating-Surveillance-System.git
   cd Cheating-Surveillance-System
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Django database:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

6. **Verify installation:**
   ```bash
   python manage.py check
   ```

## Usage

### Running the Web Application
1. **Start the Django development server:**
   ```bash
   python manage.py runserver
   ```
2. **Access the web interface:**
   - Main dashboard: http://localhost:8000/
   - Admin panel: http://localhost:8000/admin/
   - API endpoints: http://localhost:8000/api/

### Running Real-Time Surveillance
1. **Start the surveillance system:**
   ```bash
   python main.py
   ```
2. **The system will:**
   - Initialize video capture
   - Start real-time monitoring
   - Log violations to blockchain
   - Display live analysis results

### Testing Individual Components
- **Test emotion detection:**
  ```bash
  python test_emotion_detection.py
  ```
- **Test blockchain integration:**
  ```bash
  python test_blockchain.py
  ```

## API Endpoints

### Authentication
- `POST /api/token/` - Obtain JWT token
- `POST /api/token/refresh/` - Refresh JWT token
- `POST /api/token/verify/` - Verify JWT token

### Sessions
- `GET /api/sessions/` - List all sessions
- `POST /api/sessions/` - Create new session
- `GET /api/sessions/{id}/` - Get session details

### Violations
- `GET /api/violations/` - List all violations
- `GET /api/violations/{id}/` - Get violation details

### Blockchain
- `GET /api/blockchain/` - Get blockchain logs
- `POST /api/blockchain/export/` - Export blockchain data

## Configuration

### Environment Variables
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Surveillance Settings
The system can be configured through the web interface or by modifying the detection thresholds in the respective Python modules.

## Demo Videos
- **[Gaze Detection](demo_vdo/gaze-detection.mp4)** - Eye movement tracking demonstration
- **[Head Movement Detection](demo_vdo/headpose-detection.mp4)** - Head pose analysis
- **[Mobile Phone Detection](demo_vdo/Mobile-detection.mp4)** - Mobile device detection

## Testing
Run the test suite:
```bash
pytest
```

**Note:** Some tests require user interaction and may need to be run with the `-s` flag to allow input.

## Contributing
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Commit your changes: `git commit -m "Add feature description"`
5. Push to the branch: `git push origin feature-name`
6. Open a Pull Request

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- [dlib](http://dlib.net/) for facial landmark detection
- [OpenCV](https://opencv.org/) for computer vision
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) for object detection
- [Django](https://djangoproject.com/) for the web framework
- [Roboflow](https://roboflow.com/) for the mobile detection dataset
- [MediaPipe](https://mediapipe.dev/) for face detection and landmarks

## Support
For issues and questions:
1. Check the [Issues](https://github.com/Sania-hasann/Cheating-Surveillance-System/issues) page
2. Create a new issue with detailed description
3. Include system information and error logs
