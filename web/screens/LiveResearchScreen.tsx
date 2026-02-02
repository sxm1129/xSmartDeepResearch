import React, { useState, useRef, useEffect, useContext } from 'react';
import { Icon } from '../components/Icon';
import { MarkdownViewer } from '../components/MarkdownViewer';
import { ResearchService, ResearchEvent } from '../services/api';
import { extractSourcesFromToolResponse, ResearchSource } from '../utils/sourceUtils';
import { LanguageContext } from '../App';
import { useResearch } from '../contexts/ResearchContext';

export const LiveResearchScreen: React.FC = () => {
  const { t } = useContext(LanguageContext);
  const {
    query,
    setQuery,
    isResearching,
    reportContent,
    steps,
    sources,
    startResearch
  } = useResearch();

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
    await startResearch(query, t);
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
              placeholder={t('enterTopic')}
              disabled={isResearching}
            />
          </form>
        </div>

        <div className="flex items-center gap-6 ml-6">
          <div className="hidden md:flex flex-col items-end">
            <div className={`flex items - center gap - 1.5 text - xs font - medium ${isResearching ? 'text-emerald-600' : 'text-slate-500'} `}>
              <span className="relative flex h-2 w-2">
                {isResearching && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
                <span className={`relative inline - flex rounded - full h - 2 w - 2 ${isResearching ? 'bg-emerald-500' : 'bg-slate-400'} `}></span>
              </span>
              {isResearching ? t('deepResearchRunning') : t('ready')}
            </div>
          </div>
          {isResearching && (
            <button className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors">
              <Icon name="stop_circle" className="text-sm" />
              {t('stop')}
            </button>
          )}
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 p-6 overflow-hidden">
        <div className="grid grid-cols-12 gap-6 h-full">

          {/* Sidebar Area */}
          <div className="col-span-12 lg:col-span-3 flex flex-col gap-6 h-full overflow-hidden">

            {/* Reasoning Chain - Enhanced */}
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col h-1/2 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/80 backdrop-blur-sm flex items-center justify-between sticky top-0 z-10">
                <h3 className="text-xs font-bold text-slate-600 uppercase tracking-widest flex items-center gap-2 font-display">
                  <div className="p-1.5 bg-indigo-50 rounded-md">
                    <Icon name="psychology" className="text-sm text-indigo-600" />
                  </div>
                  {t('reasoningChain')}
                </h3>
                <div className="flex items-center gap-2">
                  {isResearching && (
                    <span className="flex h-2 w-2 relative">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                  )}
                  <span className="text-[10px] font-medium text-slate-400 font-mono tracking-tight bg-slate-100 px-2 py-0.5 rounded-full shadow-sm">
                    {steps.length} STEPS
                  </span>
                </div>
              </div>
              <div className="overflow-y-auto flex-1 p-0 scroll-smooth bg-slate-50/30">
                <div className="space-y-0 relative pb-10">
                  {/* Vertical Line Connector */}
                  <div className="absolute left-6 top-0 bottom-0 w-px bg-slate-200/60 z-0"></div>
                  <ul className="relative z-10 w-full">
                    {steps.map((step, idx) => (
                      <li key={idx} className={`relative pl-14 pr-4 py-3 group border-b border-slate-100/50 last:border-0 transition-colors duration-200 ${step.status === 'active' ? 'bg-indigo-50/40' : 'hover:bg-slate-50'}`}>
                        {/* Timeline Dot */}
                        <div className={`absolute left-4 top-3.5 w-4 h-4 rounded-full flex items-center justify-center z-10 ring-4 ring-white transition-all duration-300 ${step.status === 'completed' ? 'bg-emerald-500 shadow-sm' :
                          step.status === 'active' ? 'bg-white border-2 border-indigo-500 shadow-indigo-100' :
                            'bg-slate-200'
                          } `}>
                          {step.status === 'completed' && <Icon name="check" className="text-[10px] text-white font-bold" />}
                          {step.status === 'active' && <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse"></div>}
                        </div>

                        {/* Header */}
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded leading-none ${step.type === 'tool' ? 'bg-purple-50 text-purple-600 border border-purple-100' :
                            step.type === 'think' ? 'bg-amber-50 text-amber-600 border border-amber-100' :
                              'bg-slate-100 text-slate-600 border border-slate-200'
                            }`}>
                            {step.type === 'tool' ? 'TOOL' : step.type === 'think' ? 'THOUGHT' : 'SYSTEM'}
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono opacity-60">
                            {new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                          </span>
                        </div>

                        {/* Title */}
                        <p className={`text-xs font-semibold mb-1 truncate ${step.status === 'active' ? 'text-indigo-700' : 'text-slate-700'}`}>
                          {step.type === 'tool' ? (
                            <span className="font-mono text-[11px]">{step.toolName}<span className="opacity-50 text-slate-400 ml-1">()</span></span>
                          ) : step.type === 'think' ? t('thinking') : t('statusUpdate')}
                        </p>

                        {/* Content */}
                        <div className={`text-xs leading-relaxed font-mono ${step.status === 'active' ? 'text-slate-600' : 'text-slate-500'}`}>
                          {step.type === 'tool' ? (
                            <code className="bg-slate-100 px-1 py-0.5 rounded text-[10px] text-slate-600 break-all border border-slate-200">
                              {step.content.length > 100 ? step.content.substring(0, 100) + '...' : step.content}
                            </code>
                          ) : (
                            <span className="opacity-90">{step.content}</span>
                          )}
                        </div>
                      </li>
                    ))}
                    <div ref={stepsEndRef} />
                  </ul>
                  {steps.length === 0 && !isResearching && (
                    <div className="p-6 text-center text-slate-400 text-xs">
                      {t('readyToStartReasoning')}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Sources */}
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col h-1/2 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                  <Icon name="link" className="text-sm text-indigo-500" />
                  {t('sources')}
                </h3>
                <span className="text-[10px] text-slate-400">{sources.length} {t('found')}</span>
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
                    {t('noSourcesFound')}
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
                    {t('liveResearchReport')}
                  </h2>
                </div>
              </div>

              {/* Report Content */}
              <div className="flex-1 overflow-y-auto p-8 lg:px-16 bg-white relative">
                {isResearching && (
                  <div className="absolute top-4 right-4 flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-xs font-medium animate-pulse">
                    <Icon name="refresh" className="text-sm animate-spin" />
                    {t('generatingInsights')}
                  </div>
                )}

                <article className="prose prose-slate max-w-none prose-headings:font-display prose-headings:font-bold prose-h1:text-3xl prose-p:leading-relaxed prose-a:text-primary whitespace-pre-wrap">
                  {reportContent || (
                    <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                      <Icon name="science" className="text-6xl mb-4 opacity-20" />
                      <p>{t('startTopicAbove')}</p>
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