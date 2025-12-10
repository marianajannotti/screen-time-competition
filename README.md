# Screen Time Competition

A web application for friendly screen time competition - track daily usage, set goals, and compete with friends to reduce screen time.

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Git** - [Download](https://git-scm.com/)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/marianajannotti/screen-time-competition.git
   cd screen-time-competition
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   # Backend
   pip install -r requirements.txt
   
   # Frontend
   cd offy-front && npm install && cd ..
   ```

4. **Create `.env` file in project root:**
   ```bash
   SECRET_KEY=your-secret-key-here
   FLASK_ENV=development
   DATABASE_URL=sqlite:///screen_time_app.db
   
   # Optional - for password reset feature
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   ```

### Running the App

#### Option 1: Use Start Script (Easiest) ⭐

**macOS/Linux:**
```bash
chmod +x start.sh  # First time only
./start.sh
```

**Windows:**
```bash
start.bat
```

This automatically starts both servers:
- **Backend**: http://localhost:5001
- **Frontend**: http://localhost:5173 (default, or next available port)

#### Option 2: Manual Start (Two Terminals)

**Terminal 1 - Backend:**
```bash
source venv/bin/activate  # Activate venv if created
python run.py
```

**Terminal 2 - Frontend:**
```bash
cd offy-front
npm run dev
```

## �️ Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'flask'"**
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

**"command not found: npm"**
- Install Node.js from https://nodejs.org/

**Port already in use**
- Backend (5001): `lsof -ti:5001 | xargs kill -9`
- Frontend (5173): `lsof -ti:5173 | xargs kill -9`
- Or just use `./start.sh` which handles this automatically
- Note: Vite auto-increments to 5174, 5175... if 5173 is busy

**Frontend can't connect to backend**
- Ensure backend is running on port 5001
- Check that `DATABASE_URL` is set in `.env`

**Database errors**
- Reset database: `rm instance/screen_time_app.db`
- Restart backend - tables recreate automatically

## �🔧 Backend API

### Features
- **Authentication System** - User registration, login, session management
- **Database Models** - Users, screen time logs, goals, friendships
- **Flask + SQLAlchemy** - Clean API structure with SQLite database
- **CORS Support** - Ready for React frontend
- **Screen Time Logging** - Capture daily app usage entries with validation helpers
- **Canonical App Dropdown** - Backend enforces a curated list to avoid typos

### API Endpoints
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Login user
- `GET /api/auth/status` - Check auth status
- `GET /api/auth/me` - Get user info
- `POST /api/auth/logout` - Logout
- `POST /api/screen-time/` - Save a screen time entry
- `GET /api/screen-time/` - List recent entries for the signed-in user
- `GET /api/screen-time/apps` - Fetch the canonical list of app names for dropdowns

#### Allowed App Names
To keep UX simple and typo-free, `app_name` must be one of the curated values returned by `GET /api/screen-time/apps`. If `app_name` is omitted or blank, the backend automatically records the entry against `"Total"`.

### Screen Time API Usage

#### 1. Log Screen Time (authenticated)
```bash
curl -X POST "http://localhost:5001/api/screen-time/" \
   -H "Content-Type: application/json" \
   -b cookies.txt \
   -d '{
      "app_name": "YouTube",
      "hours": 1,
      "minutes": 30,
      "date": "2025-01-01"
   }'
```

To log total screen time without specifying an app, omit `app_name`:

```bash
curl -X POST "http://localhost:5001/api/screen-time/" \
   -H "Content-Type: application/json" \
   -b cookies.txt \
   -d '{
      "hours": 2,
      "minutes": 10
   }'
```

#### 2. Fetch Recent Entries (authenticated)
```bash
curl -s "http://localhost:5001/api/screen-time/?limit=10" -b cookies.txt
```

#### 3. Fetch Allowed Apps (public)
```bash
curl -s "http://localhost:5001/api/screen-time/apps"
```

## 🧪 Testing the Backend

### 1. Check Status
```bash
curl -s "http://localhost:5001/api/auth/status"
```

### 2. Register User
```bash
curl -X POST "http://localhost:5001/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'
```

### 3. Login
```bash
curl -X POST "http://localhost:5001/api/auth/login" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"username": "testuser", "password": "password123"}'
```

### 4. Get User Info (requires login)
```bash
curl -s "http://localhost:5001/api/auth/me" -b cookies.txt
```

---

**CS162 Final Project**