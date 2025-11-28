# Screen Time Competition - API Documentation

## Authentication Endpoints (`/api/auth`)

### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "alice",
  "email": "alice@example.com", 
  "password": "securepass123"
}
```

### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "alice",
  "password": "securepass123"
}
```

### Logout
```http
POST /api/auth/logout
# Requires authentication
```

### Check Auth Status
```http
GET /api/auth/status
```

### Get Current User
```http
GET /api/auth/me
# Requires authentication
```

---

## Screen Time Endpoints (`/api/screentime`)

### Log Screen Time
```http
POST /api/screentime/log
Content-Type: application/json
# Requires authentication

{
  "date": "2024-01-15",  # optional, defaults to today
  "screen_time_minutes": 180,
  "top_apps": [  # optional
    {"name": "Instagram", "minutes": 60},
    {"name": "TikTok", "minutes": 45}
  ]
}
```

### Get Today's Screen Time
```http
GET /api/screentime/today
# Requires authentication
```

### Get Screen Time History
```http
GET /api/screentime/history?days=7
GET /api/screentime/history?start_date=2024-01-01&end_date=2024-01-15
# Requires authentication
```

### Get Screen Time Statistics
```http
GET /api/screentime/stats?period=7d
# period options: 7d, 30d, 90d
# Requires authentication
```

### Delete Screen Time Entry
```http
DELETE /api/screentime/delete/2024-01-15
# Requires authentication
```

---

## Goals Endpoints (`/api/goals`)

### Get All Goals
```http
GET /api/goals/
# Requires authentication
```

### Create/Update Goal
```http
POST /api/goals/
Content-Type: application/json
# Requires authentication

{
  "goal_type": "daily",  # or "weekly"
  "target_minutes": 120
}
```

### Get Specific Goal
```http
GET /api/goals/daily
GET /api/goals/weekly
# Requires authentication
```

### Delete Goal
```http
DELETE /api/goals/1
# Requires authentication
```

### Get Goal Progress
```http
GET /api/goals/progress
```

Get progress on all user goals.

**Response:**
```json
{
  "data": {
    "daily": {
      "goal_exists": true,
      "target_minutes": 120,
      "current_minutes": 85,
      "progress_percent": 70.8,
      "goal_met": true
    },
    "weekly": {
      "goal_exists": true,
      "target_minutes": 840,
      "current_minutes": 450,
      "progress_percent": 53.6,
      "goal_met": true,
      "days_remaining": 3
    }
  }
}
```

### Get Specific Goal Progress
```http
GET /api/goals/progress/{goal_type}
```

Get progress on specific goal type (daily/weekly).

---

## Friends Endpoints (`/api/friends`)

### Get Friends List
```http
GET /api/friends/
# Requires authentication
```

### Get Friend Requests
```http
GET /api/friends/requests
# Requires authentication
```

### Send Friend Request
```http
POST /api/friends/add
Content-Type: application/json
# Requires authentication

{
  "username": "bob"
}
```

### Accept Friend Request
```http
POST /api/friends/accept/1
# Requires authentication
```

### Reject Friend Request
```http
POST /api/friends/reject/1
# Requires authentication
```

### Remove Friend
```http
DELETE /api/friends/remove/2
# Requires authentication
```

### Get Leaderboard
```http
GET /api/friends/leaderboard?period=weekly
# period options: daily, weekly
# Requires authentication
```

---

## Profile Endpoints (`/api/profile`)

### Get Profile
```http
GET /api/profile/
# Requires authentication
```

### Update Profile
```http
PUT /api/profile/
Content-Type: application/json
# Requires authentication

{
  "username": "new_username",  # optional
  "email": "new@example.com"   # optional
}
```

### Change Password
```http
PUT /api/profile/password
Content-Type: application/json
# Requires authentication

{
  "current_password": "oldpass",
  "new_password": "newpass123"
}
```

### Get Profile Stats
```http
GET /api/profile/stats
# Requires authentication
```

### Delete Account
```http
DELETE /api/profile/delete
Content-Type: application/json
# Requires authentication

{
  "password": "user_password",
  "confirm": "DELETE"
}
```

---

## Response Format

All endpoints return JSON responses with consistent formatting:

### Success Response
```json
{
  "message": "Operation successful",
  "data": { /* response data */ }
}
```

### Error Response
```json
{
  "error": "Error description"
}
```

---

## Authentication

Most endpoints require authentication using Flask-Login sessions. After logging in successfully, your session will be maintained automatically by the browser.

## CORS

The API supports CORS for `http://localhost:3000` to work with React frontend.

## Rate Limiting

The API includes built-in rate limiting:
- **Per IP**: 1000 requests per hour
- **Per authenticated user**: 60 requests per minute
- **Authentication endpoints**: Special limits apply

When rate limit is exceeded, you'll receive a `429 Too Many Requests` response.

## Error Responses

All error responses follow this format:
```json
{
  "success": false,
  "error": "Error message",
  "timestamp": 1640995200.0,
  "details": {} // Optional additional details
}
```

## Success Responses

All success responses follow this format:
```json
{
  "success": true,
  "message": "Success message",
  "data": {}, // Response data
  "timestamp": 1640995200.0
}
```

## Enhanced Profile Features

The `GET /api/profile/` endpoint now returns additional data:

```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "streak_count": 15,
    "total_points": 1250,
    "friend_count": 8,
    "goals": {
      "daily": {
        "goal_exists": true,
        "target_minutes": 120,
        "current_minutes": 85,
        "progress_percent": 70.8,
        "goal_met": true
      },
      "weekly": {
        "goal_exists": false
      }
    }
  }
}
```

## Business Logic Integration

The API now automatically:
- ✅ **Updates streaks** when screen time is logged
- ✅ **Calculates points** based on activity and goals
- ✅ **Validates goal progress** in real-time
- ✅ **Maintains gamification stats** automatically

## Development

To start the development server:
```bash
cd backend
python run_server.py
```

The API will be available at `http://localhost:5000`