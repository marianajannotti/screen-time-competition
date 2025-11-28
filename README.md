# Screen Time Competition

A web application for friendly screen time competition - track daily usage, set goals, and compete with friends to reduce screen time.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- git

### Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/marianajannotti/screen-time-competition.git
   cd screen-time-competition
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Create `.env` file in project root:**
   ```bash
   SECRET_KEY=your-team-secret-key-2024
   FLASK_ENV=development
   DATABASE_URL=sqlite:///screen_time_app.db
   ```

5. **Run the backend:**
   ```bash
   python run.py
   ```
   API available at: `http://127.0.0.1:5000`

## Frontend (React + Vite)

The frontend lives in the `offy-front` directory. To run the development server:

1. Change into the frontend folder and install dependencies:
```bash
cd offy-front
npm install
```

2. Start the dev server:
```bash
npm run dev
```

The Vite dev server typically runs at `http://localhost:5173` (or `5174` if the port is occupied).

Environment note: the frontend reads `VITE_API_BASE` to point at the backend API (default `http://localhost:5001`). If your backend runs on a different host/port, set it in `offy-front/.env`:

```
VITE_API_BASE=http://localhost:5001
```

## 🔧 Backend API

### Features
- **Authentication System** - User registration, login, session management
- **Database Models** - Users, screen time logs, goals, friendships
- **Flask + SQLAlchemy** - Clean API structure with SQLite database
- **CORS Support** - Ready for React frontend

### API Endpoints
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Login user
- `GET /api/auth/status` - Check auth status
- `GET /api/auth/me` - Get user info
- `POST /api/auth/logout` - Logout

## 🧪 Testing the Backend

### 1. Check Status
```bash
curl -s "http://127.0.0.1:5000/api/auth/status"
```

### 2. Register User
```bash
curl -X POST "http://127.0.0.1:5000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'
```

### 3. Login
```bash
curl -X POST "http://127.0.0.1:5000/api/auth/login" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"username": "testuser", "password": "password123"}'
```

### 4. Get User Info (requires login)
```bash
curl -s "http://127.0.0.1:5000/api/auth/me" -b cookies.txt
```

---

**CS162 Final Project**