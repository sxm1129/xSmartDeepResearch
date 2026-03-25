## v1.1.1 (2026-03-25)

### Bug Fixes
- **Production Stability**: Guarded `nest_asyncio.apply()` to prevent `ValueError` when running with `uvloop` in production Uvicorn environments.

## v1.1.0 (2026-03-25)

### Features
- **Deep Research Structure**: Implemented a professional 6-part tech/product research template (McKinsey/DeepMind style) with multi-dimensional analysis, tables, and product impact assessment.
- **Language Control**: Enforced Simplified Chinese as the default output language for agent reasoning and report generation.

### Bug Fixes
- **Markdown Rendering**: Fixed "dark color blocks" issue in reports by optimizing Tailwind CSS for inline code and blockquotes. Fixed LLM "markdown" block hallucinations.
- **Tool Parsing**: Implemented `_parse_json_robustly` with bracket matching to handle trailing characters (e.g., `}}}}`) and unclosed tags in LLM tool calling.
- **Content Depth**: Hardened prompt constraints to mandate 2000+ words for deep research outputs, prohibiting superficial summaries.

### Improvements
- **Terminology Preservation**: Added explicit exemptions to retain English technical terms and proper nouns in Chinese reports.
