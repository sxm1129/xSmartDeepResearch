# Bug Fix: Enforce Chinese Output

## Root Cause
- **Trigger:** Executing any deep research task in the application.
- **Location:** `config/prompts.py` (`SYSTEM_PROMPT_TEMPLATE`, `FORCE_SUMMARIZE_PROMPT`, `EXTRACTOR_PROMPT`)
- **Cause:** The system prompts are primarily written in English with strict English formatting guidelines ("Executive Summary", etc.). There are no explicit instructions forcing the LLM to output its thought process and final answer in Chinese.
- **Impact:** The LLM defaults to responding in English, resulting in English research reports.
- **Parallel paths:** The intent clarifier (`intent_classifier.py`) conditionally passes `language_instruction` based on user input, but `react_agent.py` uses statically defined English-heavy prompts from `config.py` without language constraints.

## FIX CHECKLIST
1. [ ] `config/prompts.py:56` Expand `SYSTEM_PROMPT_TEMPLATE` to explicitly require Chinese output for all sections and `<think>` tags.
2. [ ] `config/prompts.py:165` Add Chinese language instruction to `EXTRACTOR_PROMPT`.
3. [ ] `config/prompts.py:198` Add Chinese language instruction to `FORCE_SUMMARIZE_PROMPT`.
4. [ ] Compilation/Syntax check using `pytest tests/`.
