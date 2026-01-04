#!/bin/bash

# Azerbaijani TTS Docker Verification Script
# This script verifies that Docker setup is correct and working

set -e

echo "================================================"
echo "Azerbaijani TTS - Docker Verification Script"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print success
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to print info
info() {
    echo "ℹ $1"
}

# 1. Check Docker installation
echo "1. Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    success "Docker is installed: $DOCKER_VERSION"
else
    error "Docker is not installed"
    echo "   Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# 2. Check Docker Compose installation
echo ""
echo "2. Checking Docker Compose installation..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    success "Docker Compose is installed: $COMPOSE_VERSION"
else
    error "Docker Compose is not installed"
    echo "   Docker Compose comes with Docker Desktop. Please reinstall Docker Desktop."
    exit 1
fi

# 3. Check if Docker daemon is running
echo ""
echo "3. Checking if Docker daemon is running..."
if docker info &> /dev/null; then
    success "Docker daemon is running"
else
    error "Docker daemon is not running"
    echo "   Please start Docker Desktop and wait for it to fully initialize"
    exit 1
fi

# 4. Check required files exist
echo ""
echo "4. Checking required files..."

if [ -f "Dockerfile" ]; then
    success "Dockerfile found"
else
    error "Dockerfile not found"
    exit 1
fi

if [ -f "docker-compose.yml" ]; then
    success "docker-compose.yml found"
else
    error "docker-compose.yml not found"
    exit 1
fi

if [ -f "requirements.txt" ]; then
    success "requirements.txt found"
else
    error "requirements.txt not found"
    exit 1
fi

# 5. Check artifacts directory and model files
echo ""
echo "5. Checking artifacts directory..."

if [ -d "artifacts" ]; then
    success "artifacts directory found"

    if [ -f "artifacts/best_model.pt" ]; then
        MODEL_SIZE=$(du -h "artifacts/best_model.pt" | cut -f1)
        success "best_model.pt found (Size: $MODEL_SIZE)"
    else
        error "best_model.pt not found in artifacts/"
        echo "   You need to train the model first using the Jupyter notebook"
        exit 1
    fi

    if [ -f "artifacts/char_encoder.pkl" ]; then
        success "char_encoder.pkl found"
    else
        error "char_encoder.pkl not found in artifacts/"
        exit 1
    fi
else
    error "artifacts directory not found"
    exit 1
fi

# 6. Check if port 8000 is available
echo ""
echo "6. Checking if port 8000 is available..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    warning "Port 8000 is already in use"
    echo "   You may need to stop the existing service or change the port in docker-compose.yml"
    EXISTING_PROCESS=$(lsof -Pi :8000 -sTCP:LISTEN | tail -n 1)
    echo "   Process using port 8000: $EXISTING_PROCESS"
else
    success "Port 8000 is available"
fi

# 7. Check available disk space
echo ""
echo "7. Checking available disk space..."
AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
info "Available disk space: $AVAILABLE_SPACE"

# 8. Check available memory
echo ""
echo "8. Checking system resources..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    TOTAL_MEM=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024) " GB"}')
    info "Total system memory: $TOTAL_MEM"
else
    TOTAL_MEM=$(free -h | awk '/^Mem:/ {print $2}')
    info "Total system memory: $TOTAL_MEM"
fi
warning "Ensure Docker Desktop has at least 4GB RAM allocated"

# 9. Try to build the image (optional - commented out for speed)
echo ""
echo "9. Docker build test..."
info "Skipping build test for speed. To test build, run:"
echo "   docker build -t azerbaijani-tts:test ."

# 10. Summary
echo ""
echo "================================================"
echo "Verification Summary"
echo "================================================"
success "All basic checks passed!"
echo ""
echo "Next steps:"
echo "  1. Start the application:"
echo "     docker-compose up -d --build"
echo ""
echo "  2. Check logs:"
echo "     docker-compose logs -f"
echo ""
echo "  3. Verify health:"
echo "     curl http://localhost:8000/health"
echo ""
echo "  4. Open web interface:"
echo "     open http://localhost:8000"
echo ""
echo "For detailed instructions, see: docs/QUICKSTART.md"
echo "================================================"
