# Bug Fix: Content Length Insufficient

## Root Cause
- **Trigger:** Generating a final deep research report using the `react_agent` LLM.
- **Location:** `config/prompts.py` (`SYSTEM_PROMPT_TEMPLATE` and `FORCE_SUMMARIZE_PROMPT`)
- **Cause:** Although the context and generation token limits are extremely high (10,000 tokens for final answer), the prompt instructions allowed the LLM to output "brief overviews" instead of deep, exhaustive analysis. The instruction "1000+ words" was treated loosely by the model, especially if it felt lazy or gathered less data.
- **Impact:** The user receives a brief summary that lacks the "Deep" in Deep Research, rendering the output insufficient.
- **Parallel paths:** Both `SYSTEM_PROMPT_TEMPLATE` for regular answers and `FORCE_SUMMARIZE_PROMPT` for token-limit forced answers suffered from weak length enforcement.

## FIX CHECKLIST
1. [ ] `config/prompts.py`: Update `# Output Depth Requirements` in `SYSTEM_PROMPT_TEMPLATE` to be capital `MANDATORY`, strictly prohibiting short summaries and demanding sub-headings, side-by-side data, and a 2000+ words minimum limit.
2. [ ] `config/prompts.py`: Update `FORCE_SUMMARIZE_PROMPT` to include similar "WARNING: Short summaries will be deemed as task failures" and mandate exhaustive documentation of technical details.
3. [ ] Commit the changes.
