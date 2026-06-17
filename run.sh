#!/bin/bash

# Define colors for beautiful logs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo -e "${BLUE}${BOLD}====================================================${NC}"
echo -e "${BLUE}${BOLD}      STARTING VIETNAM STOCK PREDICTION SYSTEM      ${NC}"
echo -e "${BLUE}${BOLD}====================================================${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] python3 is not installed or not in PATH.${NC}"
    echo -e "${YELLOW}Please install Python 3.9+ and try again.${NC}"
    exit 1
fi

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}[WARNING] .env file not found!${NC}"
    if [ -f .env.example ]; then
        echo -e "${BLUE}[INFO] Creating .env from .env.example...${NC}"
        cp .env.example .env
    else
        echo -e "${YELLOW}[INFO] Creating an empty .env file. Please edit it with your API keys.${NC}"
        touch .env
    fi
fi

# Check if venv exists, if not create it
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[INFO] Virtual environment 'venv' not found. Creating one...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to create virtual environment.${NC}"
        exit 1
    fi
    echo -e "${GREEN}[SUCCESS] Virtual environment created successfully.${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}[INFO] Activating virtual environment...${NC}"
source venv/bin/activate

# Check if requirements should be installed
echo -e "${BLUE}[INFO] Checking and installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to install dependencies.${NC}"
    exit 1
fi
echo -e "${GREEN}[SUCCESS] Dependencies are up to date.${NC}"

# Run the project
echo -e "${GREEN}${BOLD}[START] Running main.py...${NC}"
python main.py

# Deactivate venv on exit
deactivate
