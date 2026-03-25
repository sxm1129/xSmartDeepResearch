---
description: Browser-based E2E testing — full-stack flow verification with screenshots.
---

# E2E Testing Workflow

**适用场景：** 端到端浏览器验证，覆盖 UI + API + WS 全链路。
**Invoke:** `/global_e2e-test [environment]`
**Environment:** `local` (默认), `production`

---

## Phase 1: Environment Check

1. 确认目标环境可用：

**Local:**
```bash
curl -sf http://localhost:<backend_port>/health && echo "backend OK"
curl -sf http://localhost:<frontend_port> > /dev/null && echo "frontend OK"
```
// turbo

**Production:**
```bash
curl -sf https://<production_url>/health && echo "API OK"
```
// turbo

---

## Phase 2: Define Test Scenarios

2. 根据测试目标列出场景：

| Flow | Steps | 验证条件 |
|------|-------|---------|
| **核心功能 1** | ... | ... |
| **核心功能 2** | ... | ... |
| **状态切换** | 操作中切换上下文 | 无数据残留/泄漏 |
| **异步操作** | 触发异步 → 等待完成 | 实时更新、无闪跳 |
| **错误恢复** | 模拟失败 → 重试 | 错误提示正确、可恢复 |

---

## Phase 3: Execute Tests

3. 使用 `browser_subagent` 执行每个场景：
   - 指定 URL + 期望元素 + 成功/失败条件
   - 关键节点截图

4. 浏览器测试之间，验证后端状态（API 调用检查）。

---

## Phase 4: Report

| Flow | Status | Screenshot | Notes |
|------|--------|------------|-------|
| ... | PASS/FAIL | [...] | ... |

失败项：截图 + 后端日志 → 走 `/global_bugfix`。

---

## Best Practices

- 异步操作必须等待完成后再断言
- 用 `waitForPreviousTools: true` 串联依赖步骤
- 重点测试**状态切换场景**（切上下文、刷新、并发）
- 关键状态转换时截图留档
