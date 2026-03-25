---
description: Browser-based E2E testing — full-stack flow verification with screenshots.
---

# E2E Testing Workflow

**适用场景：** 端到端浏览器验证，覆盖 UI + API + WS 全链路。
**Invoke:** `/e2e-test [environment]`
**Environment:** `local` (默认), `production`

---

## Phase 1: Environment Check

1. 确认目标环境可用：

**Local:**
```bash
# Backend (port 9001)
curl -sf http://localhost:9001/health && echo "backend OK"
# Frontend (port 3000)
curl -sf http://localhost:3000 > /dev/null && echo "frontend OK"
```
// turbo

**Production:**
```bash
curl -sf https://openclaw.fusionxlink.com/health && echo "API OK"
```
// turbo

---

## Phase 2: Define Test Scenarios

2. 根据当前测试目标列出场景：

| Flow | Steps | 验证条件 |
|------|-------|---------|
| **登录** | 打开首页 → 登录 | 看到 dashboard |
| **创建 Workspace** | 点击新建 → 输入名称 → 确认 | workspace 出现在侧边栏 |
| **发送消息** | 输入 prompt → 发送 | thinking 状态 → agent 回复 |
| **切换 Workspace** | 点击另一个 workspace | 对话内容切换，无残留 |
| **WS 事件** | 发送消息后观察实时更新 | 无闪跳、无重复消息 |
| **消息中切换** | 发消息 → 立刻切 ws | 旧 ws 的回复不污染新 ws |

---

## Phase 3: Execute Tests

3. 使用 `browser_subagent` 执行每个场景：
   - 指定 URL
   - 描述期望的元素和交互
   - 定义成功/失败条件
   - 关键节点截图

4. 浏览器测试之间，验证后端状态：
```bash
# Local
curl -s http://localhost:9001/v1/workspaces | head -20
# Production
curl -s https://openclaw.fusionxlink.com/v1/workspaces -H "Authorization: Bearer <token>" | head -20
```

---

## Phase 4: Report

5. 汇总结果：

| Flow | Status | Screenshot | Notes |
|------|--------|------------|-------|
| 登录 | PASS | [screenshot](file:///..) | — |
| 发送消息 | FAIL | [screenshot](file:///..) | WS timeout |

6. 失败项处理：
   - 截图 + 后端日志
   - 确认是 bug → 走 `/bugfix`
   - 确认是环境问题 → 记录，不开 task

---

## Best Practices

- 异步操作（WS、polling）必须等待完成后再断言
- 用 `waitForPreviousTools: true` 串联依赖步骤
- 关键状态转换时截图留档
- 测试完清理测试数据（如适用）
- 重点测试**状态切换场景**（切 workspace、F5 刷新、并发消息）
