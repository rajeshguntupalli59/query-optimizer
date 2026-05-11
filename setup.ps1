# QueryOptimizer — Windows Setup Script
# Run with: powershell -ExecutionPolicy Bypass -File setup.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  QueryOptimizer — Installation" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker
try {
    $v = docker --version 2>&1
    Write-Host "[OK] Docker found: $v" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not installed or not in PATH." -ForegroundColor Red
    Write-Host "        Download from https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check docker compose
try {
    docker compose version | Out-Null
    Write-Host "[OK] Docker Compose found" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker Compose not found. Update Docker Desktop." -ForegroundColor Red
    exit 1
}

# Create .env if it doesn't exist
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] Created .env from .env.example" -ForegroundColor Green
    Write-Host "     Edit .env to configure AI integration (optional)" -ForegroundColor Yellow
} else {
    Write-Host "[OK] .env already exists — skipping" -ForegroundColor Green
}

# Create data directory
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory "data" | Out-Null
    Write-Host "[OK] Created data/ directory" -ForegroundColor Green
}

# Build and start
Write-Host ""
Write-Host "Building containers (this may take a few minutes on first run)..." -ForegroundColor Cyan
docker compose build

Write-Host ""
Write-Host "Starting QueryOptimizer..." -ForegroundColor Cyan
docker compose up -d

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  QueryOptimizer is running!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  App:  http://localhost:3000" -ForegroundColor White
Write-Host "  API:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "To stop:   docker compose down" -ForegroundColor Gray
Write-Host "To update: git pull && docker compose build && docker compose up -d" -ForegroundColor Gray
Write-Host ""
