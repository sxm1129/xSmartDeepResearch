---
description: Version bump, changelog, build, push, and deploy — full release pipeline.
---

# Release Workflow

**适用场景：** 版本发布全流程。
**Invoke:** `/global_release [version] [services]`
**Version:** `patch` (x.y.Z), `minor` (x.Y.0), `major` (X.0.0), 或具体版本号

---

## Phase 1: Pre-flight Checks

// turbo
1. 确认工作区干净且在主分支：
```bash
git status --short && git branch --show-current
```

2. 全量编译/测试（使用项目的编译命令）。
3. 编译失败 → 停止发布，先走 `/global_bugfix` 或 `/global_hotfix`。

---

## Phase 2: Version Bump

4. 更新版本号（根据项目的包管理工具调整）：
```bash
# Node.js
npm version <version> --no-git-tag-version
# Python
# 编辑 pyproject.toml / setup.py 中的 version 字段
```

5. 生成 Changelog：
```bash
git log $(git describe --tags --abbrev=0 2>/dev/null || echo HEAD~20)..HEAD --oneline --no-merges
```
// turbo

6. 追加到 `CHANGELOG.md`：
```markdown
## v<version> (<date>)

### Features
- <feat commits>

### Bug Fixes
- <fix commits>

### Improvements
- <refactor/perf commits>
```

7. Commit + Tag:
```bash
git add -A
git commit -m "chore(release): bump version to v<version>"
git tag -a v<version> -m "Release v<version>" --no-sign
git push origin main --tags
```

---

## Phase 3: Build & Push

> 根据项目的构建方式调整以下命令。

**Docker 项目：**
```bash
docker buildx build --platform linux/amd64 \
  -t <registry>/<image>:v<version> \
  -t <registry>/<image>:latest \
  -f <Dockerfile> . --push
```

**非 Docker 项目：**
```bash
# 使用项目的 build 命令
npm run build  # 或 go build / cargo build 等
```

---

## Phase 4: Deploy

> 根据部署方式调整。

**Docker Compose 部署：**
```bash
ssh <user>@<server> << 'EOF'
cd <deploy_dir>
docker-compose pull
docker-compose up -d --remove-orphans
docker-compose ps
EOF
```

**其他部署方式：** 按项目具体脚本执行。

---

## Phase 5: Post-deploy Verification

// turbo
1. Health check:
```bash
curl -sf https://<production_url>/health && echo "healthy"
```

2. 检查启动日志（无 error）。
3. 运行 `/global_e2e-test production` 验证关键流程。
4. 监控日志 5 分钟。

---

## Rollback Protocol

```bash
# 1. 立即回退 — 不在生产 debug
ssh <user>@<server> << 'EOF'
cd <deploy_dir>
docker-compose down
IMAGE_TAG=v<previous-version> docker-compose up -d
EOF

# 2. 创建 bugfix task
# /global_bugfix <issue>

# 3. 修复后重新走 /global_release
```

**原则：** 先回退再 debug，绝对不在生产环境排查。
