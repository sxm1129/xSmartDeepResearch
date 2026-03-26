# Bug: Report Symbol Artifacts

## Root Cause
- **Trigger:** LLM (kimi-k2.5) generates long-form Markdown reports via `<answer>` tags
- **Location:** `src/agent/react_agent.py:_extract_answer()` — no post-processing after extraction
- **Cause:** kimi-k2.5 produces "echo" artifacts — it duplicates the last character/token of a line onto the next line. This is a known behavior with certain LLMs when generating long structured output, especially with parentheses, bold markers, and Chinese punctuation.
- **Impact:** ~100+ stray symbols across a typical 600-line report, severely degrading readability.
- **Parallel paths:** Both the normal answer extraction (L259) and the token-limit forced answer path (L594) call `_extract_answer()` — fix applies to both.

## Pattern Catalog (8 categories)

| # | Pattern | Example | Regex |
|:--|:--------|:--------|:------|
| 1 | Standalone `)` on its own line | `)\n` after `## 1. 研究概要 (Executive Summary)` | `^\s*\)\s*$` |
| 2 | Standalone `.`/`。` on its own line | `。\n` after a paragraph | `^\s*[.。]\s*$` |
| 3 | Standalone `**` on its own line | `**\n` after `### 🔬 **Insight 1: ...` | `^\s*\*{2,}\s*$` |
| 4 | Duplicated Chinese punctuation `：：` | `关键设计决策：：` | `：{2,}` → `：` |
| 5 | Duplicated `))` at end of line | `(val_bpb))` | `\){2,}` → `)` |
| 6 | Duplicated `**` bold closing | `$96****` | `\*{3,}` → `**` |
| 7 | Extra `|` in table last column (trailing pipe echo) | `| 开源 |\n |\n` | `^\s*\|\s*$` |
| 8 | Trailing `：` on standalone line | `：\n` after section body | `^\s*[：:]\s*$` |

## FIX CHECKLIST
1. [x] `src/agent/react_agent.py` — Add `_sanitize_markdown()` method that strips all 8 echo patterns
2. [x] `src/agent/react_agent.py:_extract_answer()` — Call `_sanitize_markdown()` on extracted content
3. [x] Compilation check
