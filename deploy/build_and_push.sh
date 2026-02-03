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
VERSION="${1:-1.0.0}"

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
# Step 1: Build Docker Image
# ============================================
echo -e "${GREEN}[1/3] Building Docker image...${NC}"

docker build \
    -t ${IMAGE_NAME}:${VERSION} \
    -t ${IMAGE_NAME}:latest \
    -f deploy/Dockerfile.unified \
    .

echo -e "${GREEN}✓ Build completed${NC}"
echo ""

# ============================================
# Step 2: Tag for Registry
# ============================================
echo -e "${GREEN}[2/3] Tagging image for registry...${NC}"

docker tag ${IMAGE_NAME}:${VERSION} ${FULL_IMAGE_NAME}:${VERSION}
docker tag ${IMAGE_NAME}:latest ${FULL_IMAGE_NAME}:latest

echo -e "${GREEN}✓ Tagged: ${FULL_IMAGE_NAME}:${VERSION}${NC}"
echo -e "${GREEN}✓ Tagged: ${FULL_IMAGE_NAME}:latest${NC}"
echo ""

# ============================================
# Step 3: Push to Registry
# ============================================
echo -e "${GREEN}[3/3] Pushing to Alibaba Cloud Registry...${NC}"
echo -e "${YELLOW}Note: Make sure you are logged in with:${NC}"
echo -e "${YELLOW}  docker login --username=sxm1129@126.com ${REGISTRY}${NC}"
echo ""

docker push ${FULL_IMAGE_NAME}:${VERSION}
docker push ${FULL_IMAGE_NAME}:latest

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
