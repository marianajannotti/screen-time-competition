#!/bin/bash
# Test script for Screen Time API endpoints
# Make sure the Flask server is running first: python run.py

BASE_URL="http://127.0.0.1:5000"

echo "=== Screen Time API Testing ==="
echo

# 1. Register a test user
echo "1. Registering test user..."
curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "screentime_user", "email": "screentime@test.com", "password": "password123"}' \
  | python -m json.tool
echo

# 2. Login to get session
echo "2. Logging in..."
curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"username": "screentime_user", "password": "password123"}' \
  | python -m json.tool
echo

# 3. Log screen time for today
echo "3. Logging today's screen time..."
curl -s -X POST "$BASE_URL/api/screentime/log" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "screen_time_minutes": 240,
    "top_apps": [
      {"name": "Instagram", "minutes": 80},
      {"name": "TikTok", "minutes": 60},
      {"name": "YouTube", "minutes": 50},
      {"name": "Safari", "minutes": 30},
      {"name": "Messages", "minutes": 20}
    ]
  }' \
  | python -m json.tool
echo

# 4. Log screen time for yesterday
echo "4. Logging yesterday's screen time..."
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d)
curl -s -X POST "$BASE_URL/api/screentime/log" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d "{
    \"date\": \"$YESTERDAY\",
    \"screen_time_minutes\": 180,
    \"top_apps\": [
      {\"name\": \"Instagram\", \"minutes\": 70},
      {\"name\": \"TikTok\", \"minutes\": 40},
      {\"name\": \"YouTube\", \"minutes\": 35},
      {\"name\": \"Safari\", \"minutes\": 25},
      {\"name\": \"WhatsApp\", \"minutes\": 10}
    ]
  }" \
  | python -m json.tool
echo

# 5. Get today's screen time
echo "5. Getting today's screen time..."
curl -s "$BASE_URL/api/screentime/today" -b cookies.txt | python -m json.tool
echo

# 6. Get screen time history (last 7 days)
echo "6. Getting screen time history..."
curl -s "$BASE_URL/api/screentime/history?days=7" -b cookies.txt | python -m json.tool
echo

# 7. Get screen time statistics
echo "7. Getting screen time statistics..."
curl -s "$BASE_URL/api/screentime/stats?period=7d" -b cookies.txt | python -m json.tool
echo

# 8. Update today's screen time
echo "8. Updating today's screen time..."
curl -s -X POST "$BASE_URL/api/screentime/log" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "screen_time_minutes": 300,
    "top_apps": [
      {"name": "Instagram", "minutes": 100},
      {"name": "TikTok", "minutes": 80},
      {"name": "YouTube", "minutes": 60},
      {"name": "Safari", "minutes": 40},
      {"name": "Messages", "minutes": 20}
    ]
  }' \
  | python -m json.tool
echo

echo "=== Testing Complete ==="
echo "Cleanup: rm cookies.txt"
rm -f cookies.txt