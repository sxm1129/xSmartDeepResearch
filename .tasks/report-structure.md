# Bug Fix: Optimize Deep Research Report Structure

## Root Cause
- **Trigger:** Generating a final deep research report using the `react_agent` LLM.
- **Location:** `config/prompts.py` (`SYSTEM_PROMPT_TEMPLATE` and `FORCE_SUMMARIZE_PROMPT`)
- **Cause:** While the previous fix enforced *length*, the *structural template* provided to the LLM (Executive Summary, Key Findings, Deep Analysis, Conclusion, References) was still too generic. It resulted in a long but functionally basic "essay-like" output rather than a professional Tech/Product Deep Research report containing distinct multi-dimensional benchmarks, market assessments, and strategic recommendations.
- **Impact:** The user, as a technical and product expert, finds the report structure lacking professional depth, categorical teardowns, and analytical rigor.
- **Parallel paths:** Both `SYSTEM_PROMPT_TEMPLATE` and `FORCE_SUMMARIZE_PROMPT` need their structural templates profoundly upgraded.

## FIX CHECKLIST
1. [ ] `config/prompts.py`: Update the output structure in `SYSTEM_PROMPT_TEMPLATE` to an industry-standard 6-part tech/product deep dive format (Executive Summary, Key Insights, Multi-Dimensional Deep-Dive, Product/Market Assessment, Strategic Recommendations, References).
2. [ ] `config/prompts.py`: Demand rich Markdown formatting (Tables, Blockquotes, Bold metrics) to increase scannability and professional feel.
3. [ ] `config/prompts.py`: Apply the identical rigorous structure to `FORCE_SUMMARIZE_PROMPT`.
4. [ ] Build and Commit.
