#!/bin/bash
# xSmartDeepResearch Docker Build and Push Script
# Builds unified image and pushes to Alibaba Cloud Container Registry

set -e

# ============================================
# Configuration
# ============================================
REGISTRY="crpi-feit7ei40cgu7xjt.cn-shenzhen.personal.cr.aliyuncs.com"
NAMESPACE="sxm1129"
IMAGE_NAME="xsmart-deepresearch"

# Read version: CLI arg > VERSION file > default
DEFAULT_VERSION=$(cat "$(dirname "$0")/../VERSION" 2>/dev/null | tr -d '[:space:]' || echo "1.0.0")
VERSION="${1:-$DEFAULT_VERSION}"

FULL_IMAGE_NAME="${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN} xSmartDeepResearch Docker Build & Push${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "Registry:  ${YELLOW}${REGISTRY}${NC}"
echo -e "Image:     ${YELLOW}${IMAGE_NAME}:${VERSION}${NC}"
echo ""

# ============================================
# Step 1: Build & Push Multi-Platform Image
# ============================================
echo -e "${GREEN}[1/2] Building and Pushing for linux/amd64...${NC}"

# Check if buildx builder exists, if not create one
if ! docker buildx inspect xsmart-builder > /dev/null 2>&1; then
    echo -e "${YELLOW}Creating new buildx builder...${NC}"
    docker buildx create --name xsmart-builder --use
fi

docker buildx build \
    --platform linux/amd64 \
    --build-arg APP_VERSION=${VERSION} \
    -t ${FULL_IMAGE_NAME}:${VERSION} \
    -t ${FULL_IMAGE_NAME}:latest \
    -f deploy/Dockerfile.unified \
    --push \
    .

echo -e "${GREEN}✓ Build and Push completed for linux/amd64${NC}"
echo ""

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✓ Successfully pushed to registry!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "Pull command:"
echo -e "  ${YELLOW}docker pull ${FULL_IMAGE_NAME}:${VERSION}${NC}"
echo ""
echo -e "Run command:"
echo -e "  ${YELLOW}docker run -d -p 80:80 -p 8000:8000 --env-file .env ${FULL_IMAGE_NAME}:${VERSION}${NC}"
