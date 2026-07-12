#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# ==========================================
# Terminal Colors
# ==========================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=======================================${NC}"
echo -e "${CYAN}      ROS2 AI Doctor Installer         ${NC}"
echo -e "${CYAN}=======================================${NC}\n"

# ==========================================
# 1. OS Detection (Ubuntu/Debian)
# ==========================================
echo -e "${BLUE}[1/5] Detecting Operating System...${NC}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
        echo -e "${YELLOW}⚠️  Warning: This script is optimized for Ubuntu/Debian. Detected OS: $PRETTY_NAME.${NC}"
        echo -e "${YELLOW}    Proceeding with caution...${NC}"
    else
        echo -e "${GREEN}✅ OS Compatible: $PRETTY_NAME${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Unable to detect OS. Proceeding with caution...${NC}"
fi

# ==========================================
# 2. Python Version Check (3.10+)
# ==========================================
echo -e "\n${BLUE}[2/5] Checking Python environment...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 is not installed. Please install Python 3.10+ first.${NC}"
    exit 1
fi

if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo -e "${GREEN}✅ Python version $PYTHON_VERSION detected (>= 3.10).${NC}"
else
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo -e "${RED}❌ Python version $PYTHON_VERSION detected. Python 3.10+ is required.${NC}"
    exit 1
fi

# ==========================================
# 3. python3-venv Check
# ==========================================
if ! python3 -c "import venv" &> /dev/null; then
    echo -e "${RED}❌ The 'venv' module is missing.${NC}"
    echo -e "${YELLOW}💡 Fix this by running: sudo apt install python3-venv${NC}"
    exit 1
else
    echo -e "${GREEN}✅ python3-venv module is available.${NC}"
fi

# ==========================================
# 4. Virtual Environment Setup
# ==========================================
echo -e "\n${BLUE}[3/5] Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment 'venv'...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created successfully.${NC}"
else
    echo -e "${GREEN}✅ Virtual environment 'venv' already exists. Skipping creation.${NC}"
fi

echo -e "${YELLOW}🔄 Activating virtual environment...${NC}"
source venv/bin/activate

# ==========================================
# 5. Dependency Installation
# ==========================================
echo -e "\n${BLUE}[4/5] Installing dependencies...${NC}"
echo -e "${YELLOW}⬆️  Upgrading pip...${NC}"
pip install --upgrade pip --quiet
echo -e "${GREEN}✅ pip upgraded successfully.${NC}"

if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}📥 Installing packages from requirements.txt...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed successfully.${NC}"
else
    echo -e "${RED}❌ requirements.txt not found! Skipping dependency installation.${NC}"
    echo -e "${YELLOW}⚠️  Please ensure you are in the correct directory.${NC}"
fi

# ==========================================
# 6. Environment Variables Setup
# ==========================================
echo -e "\n${BLUE}[5/5] Configuring environment variables...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}📋 Found .env.example. Copying to .env...${NC}"
        cp .env.example .env
        echo -e "${GREEN}✅ .env file created from template.${NC}"
        echo -e "${YELLOW}⚠️  Please remember to update .env with your actual API keys.${NC}"
    else
        echo -e "${YELLOW}⚠️  No .env or .env.example found. Creating a default template...${NC}"
        cat <<EOF > .env
GROQ_API_KEY=your_groq_api_key_here
EOF
        echo -e "${GREEN}✅ Created a default .env file.${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env to add your Groq API key.${NC}"
    fi
else
    echo -e "${GREEN}✅ .env file already exists. Skipping creation.${NC}"
fi

# ==========================================
# Completion
# ==========================================
echo -e "\n${CYAN}=======================================${NC}"
echo -e "${GREEN}        ✅ Installation Complete!      ${NC}"
echo -e "${CYAN}=======================================${NC}\n"
echo -e "You can now run the ROS2 AI Doctor using the following commands:\n"
echo -e "  ${YELLOW}source venv/bin/activate${NC}"
echo -e "  ${YELLOW}python3 main.py${NC}\n"
