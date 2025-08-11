#!/bin/bash
# ACP Polymarket Trading Agent Deployment Script

# Color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}"
echo "==========================================="
echo "  ACP Polymarket Trading Agent Deployment  "
echo "==========================================="
echo -e "${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found.${NC}"
    echo -e "${YELLOW}Please create a .env file with required configuration values.${NC}"
    echo -e "${YELLOW}You can copy .env.example and fill in your specific values.${NC}"
    exit 1
fi

# Source environment variables
echo -e "${BLUE}Loading environment variables...${NC}"
set -a
source .env
set +a

# Check for Docker and Docker Compose
echo -e "${BLUE}Checking dependencies...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker not found. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose not found. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check environment variables
echo -e "${BLUE}Validating environment variables...${NC}"
REQUIRED_VARS=(
    "WALLET_PRIVATE_KEY"
    "ACP_AGENT_ID"
    "ACP_AGENT_NAME"
    "ACP_SERVICE_REGISTRY"
    "POLYMARKET_API_URL"
    "POLYMARKET_API_KEY"
    "VIRTUAL_TOKEN_ADDRESS"
)

for VAR in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!VAR}" ]; then
        echo -e "${RED}Error: Required environment variable $VAR is not set in .env file${NC}"
        exit 1
    fi
done

# Pull latest changes if in a git repository
if [ -d .git ]; then
    echo -e "${BLUE}Pulling latest changes...${NC}"
    git pull
fi

# Build and start containers
echo -e "${BLUE}Building and starting containers...${NC}"
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check if containers are running
echo -e "${BLUE}Checking container status...${NC}"
sleep 10
if [ "$(docker inspect -f {{.State.Running}} acp-polymarket-agent)" = "true" ]; then
    echo -e "${GREEN}ACP Polymarket Trading Agent is up and running!${NC}"
    echo -e "${GREEN}Dashboard available at: http://localhost:8000/dashboard${NC}"
    echo -e "${GREEN}API docs available at: http://localhost:8000/docs${NC}"
    echo -e "${GREEN}PgAdmin available at: http://localhost:5050${NC}"
else
    echo -e "${RED}Error: ACP Polymarket Trading Agent failed to start.${NC}"
    echo -e "${YELLOW}Check logs with: docker-compose logs${NC}"
    exit 1
fi

echo -e "${BLUE}Deployment completed.${NC}"
