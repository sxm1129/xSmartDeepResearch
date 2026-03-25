# Bug Fix: Markdown Renderer Dark Blocks

## Root Cause
- **Trigger:** Rendering LLM research output containing many technical terms in backticks or blockquotes.
- **Location:** `web/components/MarkdownViewer.tsx`
- **Cause:** The `prose-code` and `prose-blockquote` Tailwind typography classes use `bg-primary/5`. Since the global `primary` color is `slate-900` (almost black), a 5% opacity translates to a gray/dark block. When the LLM outputs many technical terms like `OPC`, `PLC`, etc., the screen becomes cluttered with these dark gray blocks.
- **Impact:** Visually distracting and poor readability for technical research reports.
- **Parallel paths:** None identified. Only one `MarkdownViewer` component is used across the frontend.

## FIX CHECKLIST
1. [ ] `web/components/MarkdownViewer.tsx`: Change `prose-code:bg-primary/5 prose-code:text-primary` to `prose-code:bg-slate-100 prose-code:text-slate-800`.
2. [ ] `web/components/MarkdownViewer.tsx`: Change `prose-blockquote:bg-primary/5` to `prose-blockquote:bg-slate-50`.
3. [ ] Check if ````markdown` block wrappers need stripping (optional, as a safety measure).
4. [ ] Build `web/` frontend and run tests to compile the React components successfully.
