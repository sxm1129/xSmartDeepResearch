# Bug Fix: Tool JSON Parsing Failure

## Root Cause
- **Trigger:** An LLM response containing an unclosed `<tool_call>` or extra characters after the JSON arguments.
- **Location:** `src/agent/react_agent.py` in `_extract_tool_calls`
- **Cause:** The fallback parsing logic for unclosed `<tool_call>` tags uses a greedy regex: `re.search(r'(\{.*\})', potential_content, re.DOTALL)`. If the LLM generates trailing braces (e.g., from an accidental closing parenthesis or an unstructured thought output), the greedy `.*` captures them all (resulting in inputs like `...}}}}`), leading to `JSONDecodeError`.
- **Impact:** Valid tool calls are rejected because they appear to be invalid JSON. The agent either thinks it has finished or outputs the raw tool call JSON to the user as text.
- **Parallel paths:** The primary closed `<tool_call>` parsing logic has a robust incremental brace-parsing loop. This loop needs to be refactored into a shared method so the fallback logic can use it instead of relying on a greedy regex.

## FIX CHECKLIST
1. [ ] `src/agent/react_agent.py`: Extract the incremental JSON parsing logic (lines 494-502) into a standalone method `_parse_json_robustly(self, text: str) -> Optional[Dict]`.
2. [ ] Update the standard `<tool_call>` extraction to use `_parse_json_robustly`.
3. [ ] Update the fallback unclosed `<tool_call>` chunk extraction to also use `_parse_json_robustly`, removing the flawed greedy regex `match = re.search(r'(\{.*\})', ...)`.
4. [ ] Compile and verify via `pytest tests/test_agent/test_react_agent.py`.
