#!/usr/bin/env bash
set -e

CYAN='\033[0;36m' GREEN='\033[0;32m' YELLOW='\033[1;33m' RED='\033[0;31m' NC='\033[0m'

echo ""
echo -e "${CYAN}===========================================${NC}"
echo -e "${CYAN}  QueryOptimizer — Installation${NC}"
echo -e "${CYAN}===========================================${NC}"
echo ""

# Check Docker
if ! command -v docker &>/dev/null; then
  echo -e "${RED}[ERROR] Docker is not installed.${NC}"
  echo -e "${YELLOW}        https://docs.docker.com/get-docker/${NC}"
  exit 1
fi
echo -e "${GREEN}[OK] Docker: $(docker --version)${NC}"

# Check docker compose
if ! docker compose version &>/dev/null 2>&1; then
  echo -e "${RED}[ERROR] Docker Compose v2 not found. Update Docker.${NC}"
  exit 1
fi
echo -e "${GREEN}[OK] Docker Compose found${NC}"

# Create .env
if [ ! -f .env ]; then
  cp .env.example .env
  echo -e "${GREEN}[OK] Created .env from .env.example${NC}"
  echo -e "${YELLOW}     Edit .env to configure AI integration (optional)${NC}"
else
  echo -e "${GREEN}[OK] .env already exists — skipping${NC}"
fi

# Create data dir
mkdir -p data
echo -e "${GREEN}[OK] data/ directory ready${NC}"

# Build and start
echo ""
echo -e "${CYAN}Building containers...${NC}"
docker compose build

echo ""
echo -e "${CYAN}Starting QueryOptimizer...${NC}"
docker compose up -d

echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}  QueryOptimizer is running!${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo "  App:  http://localhost:3000"
echo "  API:  http://localhost:8000/docs"
echo ""
echo "To stop:   docker compose down"
echo "To update: git pull && docker compose build && docker compose up -d"
echo ""
