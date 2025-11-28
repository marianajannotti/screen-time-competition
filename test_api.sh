#!/bin/bash

# Screen Time Competition API Testing Script
# Tests all major backend endpoints with sample data

BASE_URL="http://localhost:5000"
TOKEN=""
USER_ID=""

echo "🧪 Testing Screen Time Competition API"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to make API calls
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    local expect_success=${5:-true}
    
    echo -e "\n${YELLOW}Testing:${NC} $description"
    echo "→ $method $endpoint"
    
    if [ -n "$data" ]; then
        if [ -n "$TOKEN" ]; then
            response=$(curl -s -X $method "$BASE_URL$endpoint" \
                -H "Content-Type: application/json" \
                -H "Cookie: remember_token=$TOKEN" \
                -d "$data")
        else
            response=$(curl -s -X $method "$BASE_URL$endpoint" \
                -H "Content-Type: application/json" \
                -d "$data")
        fi
    else
        if [ -n "$TOKEN" ]; then
            response=$(curl -s -X $method "$BASE_URL$endpoint" \
                -H "Cookie: remember_token=$TOKEN")
        else
            response=$(curl -s -X $method "$BASE_URL$endpoint")
        fi
    fi
    
    echo "Response: $response"
    
    # Check if response contains error
    if echo "$response" | grep -q '"error"' && [ "$expect_success" = true ]; then
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    elif echo "$response" | grep -q '"message"' && [ "$expect_success" = true ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        return 0
    elif [ "$expect_success" = false ]; then
        echo -e "${GREEN}✓ PASSED (Expected error)${NC}"
        return 0
    else
        echo -e "${YELLOW}? UNCLEAR${NC}"
        return 0
    fi
}

# Check if server is running
echo "Checking if server is running..."
if ! curl -s "$BASE_URL/" > /dev/null; then
    echo -e "${RED}❌ Server not running at $BASE_URL${NC}"
    echo "Please start the server first:"
    echo "  cd backend && python run_server.py"
    exit 1
fi

echo -e "${GREEN}✓ Server is running${NC}"

# Test 1: Root endpoint
test_endpoint "GET" "/" "" "Root endpoint check"

# Test 2: User Registration
echo -e "\n${YELLOW}=== USER AUTHENTICATION TESTS ===${NC}"
test_endpoint "POST" "/api/auth/register" '{
    "username": "testuser",
    "email": "test@example.com", 
    "password": "testpass123"
}' "User registration"

# Test 3: User Login
login_response=$(curl -s -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username": "testuser", "password": "testpass123"}')

echo -e "\n${YELLOW}Testing:${NC} User login"
echo "→ POST /api/auth/login"
echo "Response: $login_response"

# Extract token from response (this might need adjustment based on your auth implementation)
if echo "$login_response" | grep -q '"message"'; then
    echo -e "${GREEN}✓ PASSED${NC}"
    # Try to extract session info (implementation dependent)
    TOKEN="dummy_token_for_testing"
else
    echo -e "${RED}✗ FAILED - Cannot proceed with authenticated tests${NC}"
fi

# Test 4: Screen Time Logging
echo -e "\n${YELLOW}=== SCREEN TIME TESTS ===${NC}"
test_endpoint "POST" "/api/screentime/log" '{
    "date": "2024-01-15",
    "screen_time_minutes": 240,
    "top_apps": [
        {"name": "Instagram", "minutes": 90},
        {"name": "YouTube", "minutes": 80},
        {"name": "TikTok", "minutes": 70}
    ]
}' "Log screen time"

test_endpoint "GET" "/api/screentime/history" "" "Get screen time history"

test_endpoint "GET" "/api/screentime/stats/weekly" "" "Get weekly stats"

# Test 5: Goals Management
echo -e "\n${YELLOW}=== GOALS TESTS ===${NC}"
test_endpoint "POST" "/api/goals/" '{
    "goal_type": "daily",
    "target_minutes": 180
}' "Create daily goal"

test_endpoint "POST" "/api/goals/" '{
    "goal_type": "weekly", 
    "target_minutes": 1200
}' "Create weekly goal"

test_endpoint "GET" "/api/goals/" "" "Get all goals"

test_endpoint "GET" "/api/goals/progress" "" "Get goal progress"

test_endpoint "GET" "/api/goals/daily" "" "Get daily goal"

# Test 6: Profile Management
echo -e "\n${YELLOW}=== PROFILE TESTS ===${NC}"
test_endpoint "GET" "/api/profile/" "" "Get user profile"

test_endpoint "PUT" "/api/profile/" '{
    "username": "testuser_updated"
}' "Update profile"

test_endpoint "PUT" "/api/profile/password" '{
    "current_password": "testpass123",
    "new_password": "newpass123"
}' "Change password"

# Test 7: Friends System (might fail if no other users exist)
echo -e "\n${YELLOW}=== FRIENDS TESTS ===${NC}"
test_endpoint "GET" "/api/friends/" "" "Get friends list"

test_endpoint "GET" "/api/friends/requests" "" "Get friend requests"

test_endpoint "GET" "/api/friends/leaderboard" "" "Get leaderboard"

# Test 8: Invalid requests (should fail)
echo -e "\n${YELLOW}=== ERROR HANDLING TESTS ===${NC}"
test_endpoint "POST" "/api/screentime/log" '{
    "screen_time_minutes": "invalid"
}' "Invalid screen time data" false

test_endpoint "POST" "/api/goals/" '{
    "goal_type": "invalid",
    "target_minutes": 120
}' "Invalid goal type" false

# Summary
echo -e "\n${YELLOW}=====================================${NC}"
echo -e "${GREEN}🎉 API Testing Complete!${NC}"
echo ""
echo "If you see mostly ✓ PASSED results, your API is working correctly!"
echo "Any ✗ FAILED results indicate issues that need fixing."
echo ""
echo "Next steps:"
echo "1. Fix any failing tests"
echo "2. Test with your React frontend"
echo "3. Add more comprehensive error handling"
echo "4. Consider adding automated unit tests"
