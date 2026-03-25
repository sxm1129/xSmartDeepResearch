---
description: Version bump, changelog, Docker build, push to ACR, and remote deploy — full release pipeline.
---

# Release Workflow

**适用场景：** 版本发布，覆盖 版本号 → Changelog → 构建 → 推送 → 部署 → 验证 全流程。
**Invoke:** `/release [version] [services]`
**Version:** `patch` (x.y.Z), `minor` (x.Y.0), `major` (X.0.0), 或具体版本号如 `1.3.0`
**Services:** `all`, `backend`, `frontend`, `sandbox`

---

## Phase 1: Pre-flight Checks

// turbo
1. 确认工作区干净且在 main 分支：
```bash
cd /Users/hs/workspace/github/LeapClaw
git status --short && git branch --show-current
```

// turbo
2. 全量编译：
```bash
pytest tests/ && echo \"backend OK\"
cd ../web && npm run build && echo \"web OK\"
```

3. 如果编译失败 → 停止发布，先走 `/bugfix` 或 `/hotfix`。

---

## Phase 2: Version Bump

4. 更新所有 `package.json` 版本号：
```bash
# Root
npm version <version> --no-git-tag-version
# Services
cd src && npm version <version> --no-git-tag-version
cd ../frontend-web && npm version <version> --no-git-tag-version
cd ../sandbox-agent && npm version <version> --no-git-tag-version
```

5. 生成 Changelog（基于 git log）：
```bash
# 获取上次 tag 到现在的 commit
git log $(git describe --tags --abbrev=0 2>/dev/null || echo HEAD~20)..HEAD --oneline --no-merges
```
// turbo

6. 将 Changelog 追加到 `CHANGELOG.md`（如不存在就创建）：
```markdown
## v<version> (<date>)

### Features
- <feat commits>

### Bug Fixes
- <fix commits>

### Improvements
- <refactor/perf commits>
```

7. Commit version bump:
```bash
git add -A
git commit -m "chore(release): bump version to v<version>"
git tag -a v<version> -m "Release v<version>" --no-sign
git push origin main --tags
```

---

## Phase 3: Build & Push

**Registry:** `crpi-feit7ei40cgu7xjt.cn-shenzhen.personal.cr.aliyuncs.com/sxm1129`

8. 使用 build-and-push 脚本（如果可用）：
```bash
cd /Users/hs/workspace/github/LeapClaw
./scripts/build-and-push.sh
```

9. 如需手动构建单个服务：
```bash
# Backend
docker buildx build --platform linux/amd64 \
  -t crpi-feit7ei40cgu7xjt.cn-shenzhen.personal.cr.aliyuncs.com/sxm1129/leapclaw-backend:v<version> \
  -t crpi-feit7ei40cgu7xjt.cn-shenzhen.personal.cr.aliyuncs.com/sxm1129/leapclaw-backend:latest \
  -f Dockerfile . --push

# Frontend
docker buildx build --platform linux/amd64 \
  -t crpi-feit7ei40cgu7xjt.cn-shenzhen.personal.cr.aliyuncs.com/sxm1129/leapclaw-frontend:v<version> \
  -t crpi-feit7ei40cgu7xjt.cn-shenzhen.personal.cr.aliyuncs.com/sxm1129/leapclaw-frontend:latest \
  -f web/Dockerfile . --push

# Sandbox
docker buildx build --platform linux/amd64 \
  -t crpi-feit7ei40cgu7xjt.cn-shenzhen.personal.cr.aliyuncs.com/sxm1129/leapclaw-sandbox:v<version> \
  -t crpi-feit7ei40cgu7xjt.cn-shenzhen.personal.cr.aliyuncs.com/sxm1129/leapclaw-sandbox:latest \
  -f infra/sandbox/Dockerfile . --push
```

**NOTE:** 3 个 Docker secrets-in-ENV 警告是 dev 默认值，生产用 env override，可忽略。

---

## Phase 4: Deploy

10. SSH 到生产服务器部署：
```bash
ssh root@bigdata-ambari-31 << 'EOF'
cd /opt/leapclaw
./deploy.sh
EOF
```

11. 如 deploy.sh 不可用，手动部署：
```bash
ssh root@bigdata-ambari-31 << 'EOF'
cd /opt/leapclaw
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --remove-orphans
docker-compose -f docker-compose.prod.yml ps
EOF
```

---

## Phase 5: Post-deploy Verification

// turbo
12. Health check:
```bash
curl -sf https://openclaw.fusionxlink.com/health && echo "API healthy"
```

13. 检查启动日志（无 error）：
```bash
ssh root@bigdata-ambari-31 "docker-compose -f /opt/leapclaw/docker-compose.prod.yml logs --tail=20 backend-api 2>&1 | tail -15"
```
// turbo

14. 运行 `/e2e-test` 验证关键用户流程。

15. 监控日志 5 分钟：
```bash
ssh root@bigdata-ambari-31 "docker-compose -f /opt/leapclaw/docker-compose.prod.yml logs -f --tail=0 backend-api 2>&1 | head -100"
```

---

## Rollback Protocol

如果部署后发现问题：

```bash
# 1. 立即回退 — 不在生产 debug
ssh root@bigdata-ambari-31 << 'EOF'
cd /opt/leapclaw
docker-compose -f docker-compose.prod.yml down
# 使用上一个版本重新部署
IMAGE_TAG=v<previous-version> docker-compose -f docker-compose.prod.yml up -d
EOF

# 2. 创建 bugfix task
# /bugfix <issue-description>

# 3. 修复后重新走 /release 流程
```

**原则：** 先回退再 debug，绝对不在生产环境排查。
