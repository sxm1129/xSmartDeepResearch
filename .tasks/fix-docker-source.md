# IMPLEMENTATION CHECKLIST

1. [ ] Modify `deploy/Dockerfile.unified` to replace `FROM node:18-alpine AS frontend-builder` with `FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/node:18-alpine AS frontend-builder`.
2. [ ] Modify `deploy/Dockerfile.unified` to replace `FROM python:3.11-slim AS backend-builder` with `FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/python:3.11-slim AS backend-builder`.
3. [ ] **ACTION REQUIRED BY USER**: The Docker daemon has a proxy configured (`127.0.0.1:10808`) that is currently refusing connections. You must start your proxy client or disable the Docker proxy configuration, otherwise ALL `docker pull` commands will fail regardless of the registry.
