---
description: Production incident response — triage, hotfix, verify, postmortem.
---

# Incident Response Workflow

**适用场景：** 线上出现用户可感知的故障。
**Invoke:** `/global_incident [description]`
**原则：** 先恢复服务，再排查根因。

---

## Phase 1: TRIAGE（5 分钟内）

1. **确认影响范围：**
   - 全站不可用？部分功能？单个用户？
   - 从什么时候开始？前一次部署后？

2. **快速日志扫描：**
```bash
# 使用项目的日志获取方式
# Docker: docker-compose logs --tail=50 <service>
# 非 Docker: tail -50 <log_file>
```

3. **分类决策：**

| 严重度 | 标准 | 响应 |
|--------|------|------|
| **P0 全站不可用** | Health check 5xx / 服务 crash | 立即回退上一版本 |
| **P1 核心功能故障** | 主要业务流程不可用 | 30 分钟内热修复，无果则回退 |
| **P2 非核心功能** | 辅助功能异常 | 记录 issue，不紧急回退 |

---

## Phase 2: STABILIZE

### P0/P1: 立即回退
```bash
# Docker Compose 回退
ssh <user>@<server> << 'EOF'
cd <deploy_dir>
docker-compose down
IMAGE_TAG=v<previous-version> docker-compose up -d
EOF
```

### P2: 热修复
- 在主分支定位 → 走压缩版 `/global_bugfix`（限时 30 分钟）
- Fix → Build → Deploy

---

## Phase 3: VERIFY

1. Health check 确认恢复。
2. 关键流程验证（手动或 `/global_e2e-test`）。
3. 监控 10 分钟无新异常。

---

## Phase 4: POSTMORTEM

在 `Docs/` 目录创建事故报告：

```markdown
# Incident Report: <title>
Date: <date>
Duration: <total>
Severity: P<0/1/2>

## Timeline
- HH:MM 发现/报告
- HH:MM 开始排查
- HH:MM 回退/修复
- HH:MM 恢复

## Root Cause
<technical explanation>

## Impact
- 影响范围、用户数、数据丢失

## Fix
- Commit hash + 修改文件

## Prevention
- [ ] <action item 1>
- [ ] <action item 2>
```

---

## Anti-Patterns

1. **不在生产 debug** — 先回退，拿日志回本地分析
2. **不跳过 postmortem** — 每次事故都是改进机会
3. **不手动改生产配置** — 所有变更通过代码仓库
4. **不只修症状** — postmortem 必须找根因 + 预防措施
