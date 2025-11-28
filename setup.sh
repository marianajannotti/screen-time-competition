#!/bin/bash

# Screen Time Competition - Development Setup Script
# Run this script to set up the entire development environment

echo "🚀 Screen Time Competition - Development Setup"
echo "=============================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if Python is installed
echo -e "\n${BLUE}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check if Node.js is installed (for frontend)
echo -e "\n${BLUE}Checking Node.js installation...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠️  Node.js not found - needed for React frontend${NC}"
    echo "Install Node.js from https://nodejs.org/"
else
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js $NODE_VERSION found${NC}"
fi

# Setup Backend
echo -e "\n${BLUE}Setting up Backend...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit backend/.env with your configuration${NC}"
fi

# Initialize database
echo "Initializing database..."
cd ..
python init_db.py

echo -e "${GREEN}✓ Backend setup complete${NC}"

# Setup Frontend
if command -v node &> /dev/null; then
    echo -e "\n${BLUE}Setting up Frontend...${NC}"
    cd offy-front
    
    # Install npm dependencies
    echo "Installing npm dependencies..."
    npm install
    
    echo -e "${GREEN}✓ Frontend setup complete${NC}"
    cd ..
else
    echo -e "\n${YELLOW}⚠️  Skipping frontend setup - Node.js not available${NC}"
fi

# Make scripts executable
echo -e "\n${BLUE}Making scripts executable...${NC}"
chmod +x test_api.sh
chmod +x init_db.py
if [ -f "backend/run_server.py" ]; then
    chmod +x backend/run_server.py
fi

# Final instructions
echo -e "\n${GREEN}🎉 Setup Complete!${NC}"
echo "==================="
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Start the backend server:"
echo "   cd backend && python run_server.py"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   cd offy-front && npm run dev"
echo ""
echo "3. Open your browser to:"
echo "   Backend API: http://localhost:5000"
echo "   Frontend:    http://localhost:3000"
echo ""
echo "4. Test the API:"
echo "   ./test_api.sh"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "   - API Documentation: backend/API_DOCS.md"
echo "   - Project README: README.md"
echo ""
echo -e "${YELLOW}🔧 Configuration:${NC}"
echo "   - Backend config: backend/.env"
echo "   - Frontend config: offy-front/vite.config.js"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
