import React, { useState, useRef, useEffect } from 'react';
import { Icon } from '../components/Icon';
import { ResearchService, ResearchEvent } from '../services/api';
import { extractSourcesFromToolResponse, ResearchSource } from '../utils/sourceUtils';
// Optional: import ReactMarkdown if available, or just use whitespace-pre-wrap

interface ReasoningStep {
  type: 'status' | 'think' | 'tool';
  content: string;
  status: 'pending' | 'active' | 'completed';
  toolName?: string;
  timestamp: number;
}

export const LiveResearchScreen: React.FC = () => {
  const [query, setQuery] = useState("");
  const [isResearching, setIsResearching] = useState(false);
  const [reportContent, setReportContent] = useState("");
  const [steps, setSteps] = useState<ReasoningStep[]>([]);
  const [sources, setSources] = useState<ResearchSource[]>([]);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(-1);

  const reportEndRef = useRef<HTMLDivElement>(null);
  const stepsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logic
  useEffect(() => {
    if (reportEndRef.current) {
      reportEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [reportContent]);

  useEffect(() => {
    if (stepsEndRef.current) {
      stepsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [steps]);

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!query.trim() || isResearching) return;

    setIsResearching(true);
    setReportContent("");
    setSteps([]);
    setSources([]);
    setCurrentStepIndex(-1);

    await ResearchService.streamResearch(query, (event: ResearchEvent) => {
      handleEvent(event);
    });

    setIsResearching(false);
  };

  const handleEvent = (event: ResearchEvent) => {
    // 1. Handle Status / Thinking
    if (event.type === 'status' || event.type === 'think' || event.type === 'tool_start') {
      setSteps(prev => {
        const newSteps = [...prev];
        // Mark previous as completed
        if (newSteps.length > 0) {
          newSteps[newSteps.length - 1].status = 'completed';
        }

        let content = event.content;
        if (event.type === 'tool_start') {
          content = `Using tool: ${event.tool}...`;
        }

        newSteps.push({
          type: event.type === 'tool_start' ? 'tool' : event.type as any,
          content: content,
          status: 'active',
          toolName: event.tool,
          timestamp: Date.now()
        });
        return newSteps;
      });
      setCurrentStepIndex(prev => prev + 1);
    }
    // 2. Handle Tool Response (Extract Sources)
    else if (event.type === 'tool_response') {
      const newSources = extractSourcesFromToolResponse(event.tool || '', event.content);
      if (newSources.length > 0) {
        setSources(prev => {
          // Deduplicate by URL
          const existingUrls = new Set(prev.map(s => s.url));
          const uniqueNew = newSources.filter(s => !existingUrls.has(s.url));
          return [...prev, ...uniqueNew];
        });
      }

      // Update step content to show it finished
      setSteps(prev => {
        const newSteps = [...prev];
        if (newSteps.length > 0) {
          newSteps[newSteps.length - 1].status = 'completed';
          newSteps[newSteps.length - 1].content += ` (Done)`;
        }
        return newSteps;
      });
    }
    // 3. Handle Answer (Stream to Report)
    else if (event.type === 'answer') {
      // Append text
      setReportContent(prev => prev + event.content);
    }
    // 4. Handle Final Answer
    else if (event.type === 'final_answer') {
      setIsResearching(false);
    }
    // 5. Handle Error
    else if (event.type === 'error') {
      setReportContent(prev => prev + `\n\n**Error:** ${event.content}`);
      setIsResearching(false);
    }
  };

  return (
    <div className="flex flex-col h-full relative">
      {/* Header */}
      <header className="h-16 glass-panel border-b border-border-light flex items-center justify-between px-6 z-10 sticky top-0 bg-white/80 backdrop-blur-md">
        <div className="flex-1 max-w-2xl relative">
          <form onSubmit={handleSearch} className="relative w-full">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Icon name="search" className="text-slate-400" />
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-slate-200 rounded-lg leading-5 bg-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary sm:text-sm transition-shadow shadow-sm"
              placeholder="Enter a research topic..."
              disabled={isResearching}
            />
          </form>
        </div>

        <div className="flex items-center gap-6 ml-6">
          <div className="hidden md:flex flex-col items-end">
            <div className={`flex items-center gap-1.5 text-xs font-medium ${isResearching ? 'text-emerald-600' : 'text-slate-500'}`}>
              <span className="relative flex h-2 w-2">
                {isResearching && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
                <span className={`relative inline-flex rounded-full h-2 w-2 ${isResearching ? 'bg-emerald-500' : 'bg-slate-400'}`}></span>
              </span>
              {isResearching ? 'DeepResearch Running' : 'Ready'}
            </div>
          </div>
          {isResearching && (
            <button className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors">
              <Icon name="stop_circle" className="text-sm" />
              Stop
            </button>
          )}
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 p-6 overflow-hidden">
        <div className="grid grid-cols-12 gap-6 h-full">

          {/* Sidebar Area */}
          <div className="col-span-12 lg:col-span-3 flex flex-col gap-6 h-full overflow-hidden">

            {/* Reasoning Chain */}
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col h-1/2 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                  <Icon name="psychology" className="text-sm text-primary" />
                  Reasoning Chain
                </h3>
                {isResearching && <span className="bg-blue-100 text-blue-700 text-[10px] px-2 py-0.5 rounded-full font-medium">Active</span>}
              </div>
              <div className="p-0 overflow-y-auto flex-1 relative scroll-smooth">
                <div className="absolute left-6 top-4 bottom-4 w-0.5 bg-slate-200"></div>
                <ul className="space-y-0 py-4">
                  {steps.map((step, idx) => (
                    <li key={idx} className={`relative pl-12 pr-4 py-2 group ${step.status === 'active' ? 'bg-blue-50/50' : ''}`}>
                      <div className={`absolute left-4 top-3 w-4 h-4 rounded-full flex items-center justify-center z-10 ${step.status === 'completed' ? 'bg-emerald-100 border-2 border-emerald-500' :
                          step.status === 'active' ? 'bg-white border-2 border-primary animate-pulse' :
                            'bg-slate-100 border-2 border-slate-300'
                        }`}>
                        {step.status === 'completed' && <Icon name="check" className="text-[10px] text-emerald-600 font-bold" />}
                        {step.status === 'active' && <div className="w-1.5 h-1.5 bg-primary rounded-full"></div>}
                      </div>
                      <p className={`text-sm font-medium ${step.status === 'active' ? 'text-primary' : 'text-slate-700'}`}>
                        {step.type === 'tool' ? `Tool: ${step.toolName}` :
                          step.type === 'think' ? 'Thinking...' : 'Status Update'}
                      </p>
                      <p className="text-xs text-slate-500 mt-0.5 line-clamp-3">
                        {step.content}
                      </p>
                    </li>
                  ))}
                  <div ref={stepsEndRef} />
                </ul>
                {steps.length === 0 && !isResearching && (
                  <div className="p-6 text-center text-slate-400 text-xs">
                    Ready to start reasoning.
                  </div>
                )}
              </div>
            </div>

            {/* Sources */}
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col h-1/2 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                  <Icon name="link" className="text-sm text-indigo-500" />
                  Sources
                </h3>
                <span className="text-[10px] text-slate-400">{sources.length} Found</span>
              </div>
              <div className="p-3 overflow-y-auto flex-1 space-y-3 bg-slate-50/30">
                {sources.map((source, idx) => (
                  <a key={idx} href={source.url} target="_blank" rel="noreferrer" className="block bg-white p-3 rounded-lg border border-slate-200 shadow-sm hover:shadow-md transition-shadow cursor-pointer group">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
                        <Icon name="public" className="text-[10px]" />
                        <span className="truncate max-w-[150px]">{new URL(source.url).hostname}</span>
                      </div>
                      <Icon name="open_in_new" className="text-xs text-slate-300 group-hover:text-primary" />
                    </div>
                    <h4 className="text-sm font-medium text-slate-800 leading-tight line-clamp-2">{source.title}</h4>
                  </a>
                ))}
                {sources.length === 0 && (
                  <div className="p-6 text-center text-slate-400 text-xs">
                    No sources found yet.
                  </div>
                )}
              </div>
            </div>

          </div>

          {/* Main Report Area */}
          <div className="col-span-12 lg:col-span-9 flex flex-col h-full overflow-hidden">
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm h-full flex flex-col relative overflow-hidden">
              {/* Report Toolbar */}
              <div className="h-12 border-b border-slate-200 px-4 flex items-center justify-between bg-slate-50/80 backdrop-blur-sm z-20">
                <div className="flex items-center gap-4">
                  <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                    <Icon name="auto_awesome" className="text-primary text-base" />
                    Live Research Report
                  </h2>
                </div>
              </div>

              {/* Report Content */}
              <div className="flex-1 overflow-y-auto p-8 lg:px-16 bg-white relative">
                {isResearching && (
                  <div className="absolute top-4 right-4 flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-xs font-medium animate-pulse">
                    <Icon name="refresh" className="text-sm animate-spin" />
                    Generating insights...
                  </div>
                )}

                <article className="prose prose-slate max-w-none prose-headings:font-display prose-headings:font-bold prose-h1:text-3xl prose-p:leading-relaxed prose-a:text-primary whitespace-pre-wrap">
                  {reportContent || (
                    <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                      <Icon name="science" className="text-6xl mb-4 opacity-20" />
                      <p>Enter a topic above to begin research.</p>
                    </div>
                  )}
                  <div ref={reportEndRef} />
                </article>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};