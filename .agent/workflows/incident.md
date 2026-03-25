---
description: Production incident response — triage, hotfix, verify, postmortem.
---

# Incident Response Workflow

**适用场景：** 线上出现用户可感知的故障。
**Invoke:** `/incident [description]`
**原则：** 先恢复服务，再排查根因。

---

## Phase 1: TRIAGE（5 分钟内）

1. **确认影响范围：**
   - 全站不可用？部分功能？单个用户？
   - 从什么时候开始？前一次部署后？

2. **快速日志扫描：**
```bash
# 后端日志（最近 50 行）
ssh root@bigdata-ambari-31 "docker-compose -f /opt/leapclaw/docker-compose.prod.yml logs --tail=50 backend-api 2>&1"
# Redis 状态
ssh root@bigdata-ambari-31 "docker exec leapclaw-redis redis-cli ping"
# 前端构建状态
ssh root@bigdata-ambari-31 "docker-compose -f /opt/leapclaw/docker-compose.prod.yml ps"
```
// turbo

3. **分类决策：**

| 严重度 | 标准 | 响应 |
|--------|------|------|
| **P0 全站不可用** | Health check 返回 5xx / 服务 crash loop | 立即回退到上一版本 |
| **P1 核心功能故障** | 对话、workspace 管理无法使用 | 尝试热修复，30 分钟内无果则回退 |
| **P2 非核心功能** | 导出、通知等辅助功能异常 | 记录 issue，不紧急回退 |

---

## Phase 2: STABILIZE

### P0/P1: 立即回退

```bash
ssh root@bigdata-ambari-31 << 'EOF'
cd /opt/leapclaw
docker-compose -f docker-compose.prod.yml down
IMAGE_TAG=v<previous-version> docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml ps
EOF
```

### P2: 热修复路径

4. 在 main 分支上定位问题代码
5. 走压缩版 `/bugfix` 流程：
   - Root cause analysis（限时 30 分钟）
   - Minimal fix + 编译验证
   - Commit → Build → Deploy

---

## Phase 3: VERIFY

6. 确认服务恢复：
```bash
curl -sf https://openclaw.fusionxlink.com/health && echo "API healthy"
```
// turbo

7. 检查关键流程（手动或 `/e2e-test`）：
   - 登录
   - 创建 workspace
   - 发送消息 + 收到回复
   - 切换 workspace

8. 监控 10 分钟无新异常。

---

## Phase 4: POSTMORTEM

9. 在 `Docs/` 目录创建事故报告：

```markdown
# Incident Report: <title>
Date: <date>
Duration: <start> — <end> (<total>)
Severity: P<0/1/2>

## Timeline
- HH:MM 发现问题 / 用户报告
- HH:MM 开始排查
- HH:MM 执行回退 / 修复
- HH:MM 服务恢复

## Root Cause
<technical explanation>

## Impact
- 影响用户数: <N>
- 影响功能: <list>
- 数据丢失: <yes/no>

## Fix
- Commit: <hash>
- 修改文件: <list>

## Prevention
- [ ] <action item 1>
- [ ] <action item 2>
```

10. 将 Prevention 的 action items 转为 `.tasks/` 跟踪项。

---

## Anti-Patterns

1. **不要在生产环境 debug** — 先回退，拿日志回本地分析
2. **不要跳过 postmortem** — 每次事故都是改进 workflow 的机会
3. **不要手动改生产配置** — 所有变更通过代码仓库，走正常发布流程
4. **不要只修症状** — postmortem 必须找到根因并提出预防措施
