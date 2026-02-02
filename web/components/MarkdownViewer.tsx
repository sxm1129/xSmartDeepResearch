import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { Copy, Check } from 'lucide-react';

interface MarkdownViewerProps {
    content: string;
    className?: string;
}

export const MarkdownViewer: React.FC<MarkdownViewerProps> = ({ content, className = '' }) => {
    const [copied, setCopied] = React.useState<string | null>(null);

    const handleCopy = (code: string) => {
        navigator.clipboard.writeText(code);
        setCopied(code);
        setTimeout(() => setCopied(null), 2000);
    };

    return (
        <div className={`markdown-viewer prose prose-slate max-w-none 
      prose-headings:font-display prose-headings:font-bold prose-headings:tracking-tight prose-headings:text-slate-900
      prose-h1:text-3xl prose-h1:mb-6 prose-h1:pb-4 prose-h1:border-b prose-h1:border-slate-100
      prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-4
      prose-h3:text-xl prose-h3:mt-8 prose-h3:mb-3
      prose-p:text-slate-600 prose-p:leading-relaxed prose-p:mb-5
      prose-strong:text-slate-900 prose-strong:font-bold
      prose-ul:my-6 prose-li:my-2 prose-li:text-slate-600
      prose-blockquote:border-l-4 prose-blockquote:border-primary/30 prose-blockquote:bg-primary/5 prose-blockquote:py-2 prose-blockquote:px-5 prose-blockquote:rounded-r-lg prose-blockquote:italic prose-blockquote:text-slate-700
      prose-code:text-primary prose-code:bg-primary/5 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:before:content-none prose-code:after:content-none
      prose-pre:bg-slate-900 prose-pre:rounded-xl prose-pre:p-0 prose-pre:shadow-xl prose-pre:my-8
      prose-table:w-full prose-table:border-collapse prose-table:my-8
      prose-th:bg-slate-50 prose-th:px-4 prose-th:py-3 prose-th:text-left prose-th:text-slate-900 prose-th:font-bold prose-th:border prose-th:border-slate-200
      prose-td:px-4 prose-td:py-3 prose-td:border prose-td:border-slate-100 prose-td:text-slate-600
      ${className}`}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
                components={{
                    pre: ({ node, ...props }) => (
                        <div className="relative group">
                            <pre {...props} className="!mb-0" />
                            <button
                                onClick={() => {
                                    const code = (props.children as any)?.props?.children;
                                    if (code) handleCopy(code);
                                }}
                                className="absolute top-3 right-3 p-2 bg-white/10 hover:bg-white/20 text-white/50 hover:text-white rounded-lg transition-all opacity-0 group-hover:opacity-100 backdrop-blur-sm border border-white/10"
                                title="Copy code"
                            >
                                {copied ? <Check size={16} className="text-green-400" /> : <Copy size={16} />}
                            </button>
                        </div>
                    ),
                    h1: ({ node, ...props }) => <h1 {...props} id={props.children?.toString().toLowerCase().replace(/\s+/g, '-')} />,
                    h2: ({ node, ...props }) => <h2 {...props} id={props.children?.toString().toLowerCase().replace(/\s+/g, '-')} />,
                }}
            >
                {content}
            </ReactMarkdown>

            {/* Add highlight.js theme via external stylesheet if needed, 
          but usually rehype-highlight needs a theme. 
          We'll add a simple one in index.css later or use an existing one. */}
            <style>{`
        .hljs { display: block; overflow-x: auto; padding: 1.25rem; color: #e2e8f0; background: #0f172a; font-family: 'JetBrains Mono', monospace; font-size: 0.875rem; line-height: 1.7142857; }
        .hljs-comment, .hljs-quote { color: #64748b; font-style: italic; }
        .hljs-keyword, .hljs-selector-tag, .hljs-literal { color: #818cf8; }
        .hljs-string, .hljs-title, .hljs-section, .hljs-type, .hljs-attribute, .hljs-symbol, .hljs-bullet, .hljs-addition { color: #34d399; }
        .hljs-subst, .hljs-string { color: #34d399; }
        .hljs-number, .hljs-variable, .hljs-template-variable, .hljs-tag, .hljs-name, .hljs-attr, .hljs-built_in, .hljs-regexp, .hljs-link, .hljs-deletion { color: #f472b6; }
        .hljs-function .hljs-title { color: #60a5fa; }
        .hljs-params { color: #e2e8f0; }
        .hljs-class .hljs-title { color: #fbbf24; }
      `}</style>
        </div>
    );
};
