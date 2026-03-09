/**
 * AdvancedResearchScreen
 * 
 * Independent screen for advanced deep research with intent clarification.
 * 3 visual phases: Input → Clarification (rich cards) → Research (reasoning chain + report)
 */

import React, { useState, useRef, useEffect, useContext } from 'react';
import { Icon } from '../components/Icon';
import { MarkdownViewer } from '../components/MarkdownViewer';
import { LanguageContext } from '../App';
import { useAdvancedResearch } from '../contexts/AdvancedResearchContext';
import { ClarificationDirection } from '../services/advancedResearchApi';

export const AdvancedResearchScreen: React.FC = () => {
    const { t } = useContext(LanguageContext);
    const {
        phase,
        query,
        setQuery,
        clarificationRound,
        directions,
        selectedDirection,
        refinedQuery,
        isLoading,
        reportContent,
        steps,
        sources,
        error,
        startClarification,
        selectDirection,
        submitCustomDirection,
        resetAll,
    } = useAdvancedResearch();

    const [customInput, setCustomInput] = useState("");
    const [isExportMenuOpen, setIsExportMenuOpen] = useState(false);
    const reportEndRef = useRef<HTMLDivElement>(null);
    const stepsEndRef = useRef<HTMLDivElement>(null);
    const exportMenuRef = useRef<HTMLDivElement>(null);

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

    // Click-outside handler for export menu
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (exportMenuRef.current && !exportMenuRef.current.contains(event.target as Node)) {
                setIsExportMenuOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const getSanitizedFilename = (title: string, ext: string) => {
        return `${title.replace(/[^a-z0-9\u4e00-\u9fa5]/gi, '_').slice(0, 50)}.${ext}`;
    };

    const handleExportMarkdown = () => {
        if (!reportContent) return;
        const blob = new Blob([reportContent], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = getSanitizedFilename(query || 'advanced_research', 'md');
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        setIsExportMenuOpen(false);
    };

    const handleExportPDF = () => {
        if (!reportContent) return;
        import('html2pdf.js').then((html2pdf) => {
            const element = document.getElementById('advanced-report-content');
            const opt = {
                margin: 10,
                filename: getSanitizedFilename(query || 'advanced_research', 'pdf'),
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2, useCORS: true },
                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' as const }
            };
            // @ts-ignore
            html2pdf.default().set(opt).from(element).save();
            setIsExportMenuOpen(false);
        }).catch(err => console.error('Failed to load html2pdf', err));
    };

    const handleSearch = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!query.trim() || isLoading) return;
        await startClarification(query);
    };

    const handleCustomSubmit = async () => {
        if (!customInput.trim() || isLoading) return;
        await submitCustomDirection(customInput);
    };

    const handleNewResearch = () => {
        resetAll();
        setCustomInput("");
    };

    // ==========================================
    // Render: Input Phase (Idle)
    // ==========================================
    const renderInputPhase = () => (
        <div className="flex flex-col items-center justify-center h-full px-6">
            <div className="w-full max-w-2xl">
                {/* Hero Section */}
                <div className="text-center mb-10">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-600 text-white shadow-lg shadow-violet-200 mb-6">
                        <Icon name="neurology" className="text-3xl" />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-900 mb-2">{t('advancedResearch')}</h1>
                    <p className="text-sm text-slate-500 leading-relaxed max-w-md mx-auto">
                        {t('advancedResearchDesc')}
                    </p>
                </div>

                {/* Search Input */}
                <form onSubmit={handleSearch} className="relative group">
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                            <Icon name="search" className="text-slate-400 group-focus-within:text-violet-500 transition-colors" />
                        </div>
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            className="block w-full pl-11 pr-28 py-4 border border-slate-200 rounded-xl bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-400 text-base shadow-sm hover:border-slate-300 transition-all"
                            placeholder={t('advancedResearchPlaceholder')}
                            disabled={isLoading}
                        />
                        <button
                            type="submit"
                            disabled={isLoading || !query.trim()}
                            className="absolute right-2 top-1/2 -translate-y-1/2 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 disabled:from-slate-300 disabled:to-slate-300 text-white px-5 py-2 rounded-lg text-sm font-medium transition-all shadow-sm disabled:shadow-none"
                        >
                            {isLoading ? (
                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                t('analyze')
                            )}
                        </button>
                    </div>
                </form>

                {/* Example Questions */}
                <div className="mt-6 flex flex-wrap gap-2 justify-center">
                    {[
                        "AI对程序员的影响",
                        "2025年新能源汽车市场分析",
                        "Remote work productivity research"
                    ].map((example, i) => (
                        <button
                            key={i}
                            onClick={() => { setQuery(example); }}
                            className="text-xs px-3 py-1.5 rounded-full border border-slate-200 text-slate-500 hover:text-violet-600 hover:border-violet-300 hover:bg-violet-50 transition-all"
                        >
                            {example}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );

    // ==========================================
    // Render: Clarification Phase
    // ==========================================
    const renderClarificationPhase = () => (
        <div className="flex flex-col h-full overflow-auto">
            {/* Header */}
            <div className="sticky top-0 z-10 bg-white border-b border-slate-100 px-6 py-4">
                <div className="flex items-center justify-between max-w-4xl mx-auto">
                    <div className="flex items-center gap-3">
                        <button onClick={handleNewResearch} className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors">
                            <Icon name="arrow_back" className="text-slate-500 text-lg" />
                        </button>
                        <div>
                            <h2 className="text-sm font-semibold text-slate-800">{t('clarifyingIntent')}</h2>
                            <p className="text-xs text-slate-400 mt-0.5">{t('round')} {clarificationRound}/2</p>
                        </div>
                    </div>
                    {isLoading && (
                        <div className="flex items-center gap-2 text-xs text-violet-600">
                            <div className="w-3 h-3 border-2 border-violet-200 border-t-violet-600 rounded-full animate-spin" />
                            {t('analyzing')}
                        </div>
                    )}
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 px-6 py-8">
                <div className="max-w-4xl mx-auto">
                    {/* User Question Display */}
                    <div className="mb-8">
                        <div className="flex items-start gap-3 bg-slate-50 rounded-xl p-4 border border-slate-100">
                            <div className="p-1.5 bg-slate-200 rounded-lg shrink-0">
                                <Icon name="person" className="text-slate-600 text-sm" />
                            </div>
                            <div>
                                <p className="text-xs font-medium text-slate-400 mb-1">{t('yourQuestion')}</p>
                                <p className="text-sm text-slate-800 font-medium">{query}</p>
                            </div>
                        </div>
                    </div>

                    {/* Clarification Message */}
                    {directions.length > 0 && (
                        <div className="mb-6">
                            <div className="flex items-start gap-3 mb-6">
                                <div className="p-1.5 bg-gradient-to-br from-violet-500 to-indigo-500 rounded-lg shrink-0">
                                    <Icon name="neurology" className="text-white text-sm" />
                                </div>
                                <div>
                                    <p className="text-xs font-medium text-slate-400 mb-1">xSmart DeepResearch</p>
                                    <p className="text-sm text-slate-700">{t('selectDirectionDesc')}</p>
                                </div>
                            </div>

                            {/* Direction Cards */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                                {directions.map((direction) => (
                                    <DirectionCard
                                        key={direction.id}
                                        direction={direction}
                                        isSelected={selectedDirection?.id === direction.id}
                                        isLoading={isLoading && selectedDirection?.id === direction.id}
                                        onClick={() => selectDirection(direction)}
                                        disabled={isLoading}
                                    />
                                ))}
                            </div>

                            {/* Custom Input */}
                            <div className="border border-dashed border-slate-200 rounded-xl p-4 hover:border-violet-300 transition-colors">
                                <p className="text-xs font-medium text-slate-500 mb-3 flex items-center gap-1.5">
                                    <Icon name="edit" className="text-sm" />
                                    {t('customDirection')}
                                </p>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={customInput}
                                        onChange={(e) => setCustomInput(e.target.value)}
                                        className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-400 placeholder-slate-400"
                                        placeholder={t('customDirectionPlaceholder')}
                                        disabled={isLoading}
                                        onKeyDown={(e) => { if (e.key === 'Enter') handleCustomSubmit(); }}
                                    />
                                    <button
                                        onClick={handleCustomSubmit}
                                        disabled={isLoading || !customInput.trim()}
                                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:bg-slate-200 text-white disabled:text-slate-400 rounded-lg text-sm font-medium transition-colors"
                                    >
                                        {t('startResearch')}
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Loading Skeleton */}
                    {isLoading && directions.length === 0 && (
                        <div className="space-y-4">
                            {[1, 2, 3, 4].map(i => (
                                <div key={i} className="bg-slate-50 rounded-xl p-5 border border-slate-100 animate-pulse">
                                    <div className="h-4 bg-slate-200 rounded w-1/3 mb-3" />
                                    <div className="h-3 bg-slate-100 rounded w-2/3 mb-2" />
                                    <div className="h-3 bg-slate-100 rounded w-1/2" />
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Error */}
                    {error && (
                        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700 flex items-start gap-2">
                            <Icon name="error" className="text-red-500 text-lg shrink-0" />
                            <p>{error}</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );

    // ==========================================
    // Render: Research Phase
    // ==========================================
    const renderResearchPhase = () => (
        <div className="flex flex-col h-full relative bg-white">
            {/* Header */}
            <header className="h-14 border-b border-slate-100 flex items-center justify-between px-6 z-10 sticky top-0 bg-white">
                <div className="flex items-center gap-3">
                    <button onClick={handleNewResearch} className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors">
                        <Icon name="arrow_back" className="text-slate-500 text-lg" />
                    </button>
                    <div>
                        <h2 className="text-xs font-semibold text-slate-700 flex items-center gap-2">
                            <div className="p-1 bg-gradient-to-br from-violet-500 to-indigo-500 rounded">
                                <Icon name="neurology" className="text-white text-[10px]" />
                            </div>
                            {t('advancedResearch')}
                        </h2>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    {phase === 'researching' && (
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                            <span className="text-xs font-medium text-slate-600">{t('deepResearchRunning')}</span>
                        </div>
                    )}
                    {phase === 'done' && (
                        <button
                            onClick={handleNewResearch}
                            className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5"
                        >
                            <Icon name="add" className="text-sm" />
                            {t('newAdvancedResearch')}
                        </button>
                    )}
                </div>
            </header>

            {/* Main Content - mirrors LiveResearchScreen layout */}
            <div className="flex-1 p-6 overflow-hidden">
                <div className="grid grid-cols-12 gap-6 h-full">

                    {/* Sidebar: Reasoning Chain + Sources */}
                    <div className="col-span-12 lg:col-span-3 flex flex-col gap-6 h-full overflow-hidden">

                        {/* Refined Query Banner */}
                        <div className="bg-gradient-to-br from-violet-50 to-indigo-50 border border-violet-200/50 rounded-xl p-3">
                            <p className="text-[10px] font-bold text-violet-500 uppercase tracking-wider mb-1">{t('refinedQuery')}</p>
                            <p className="text-xs text-slate-700 leading-relaxed line-clamp-3">{refinedQuery}</p>
                        </div>

                        {/* Reasoning Chain */}
                        <div className="bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col flex-1 overflow-hidden">
                            <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/80 flex items-center justify-between sticky top-0 z-10">
                                <h3 className="text-xs font-bold text-slate-600 uppercase tracking-widest flex items-center gap-2">
                                    <div className="p-1.5 bg-indigo-50 rounded-md">
                                        <Icon name="psychology" className="text-sm text-indigo-600" />
                                    </div>
                                    {t('reasoningChain')}
                                </h3>
                                <span className="text-[10px] font-medium text-slate-400 font-mono bg-slate-100 px-2 py-0.5 rounded-full">
                                    {steps.length} STEPS
                                </span>
                            </div>
                            <div className="overflow-y-auto flex-1 p-0 scroll-smooth bg-slate-50/30">
                                <div className="space-y-0 relative pb-10">
                                    <div className="absolute left-6 top-0 bottom-0 w-px bg-slate-200/60 z-0" />
                                    <ul className="relative z-10 w-full">
                                        {steps.map((step, idx) => (
                                            <li key={idx} className={`relative pl-14 pr-4 py-3 border-b border-slate-100/50 last:border-0 transition-colors duration-200 ${step.status === 'active' ? 'bg-indigo-50/40' : 'hover:bg-slate-50'}`}>
                                                <div className={`absolute left-4 top-3.5 w-4 h-4 rounded-full flex items-center justify-center z-10 ring-4 ring-white transition-all duration-300 ${step.status === 'completed' ? 'bg-emerald-500 shadow-sm' :
                                                    step.status === 'active' ? 'bg-white border-2 border-indigo-500 shadow-indigo-100' : 'bg-slate-200'}`}>
                                                    {step.status === 'completed' && <Icon name="check" className="text-[10px] text-white font-bold" />}
                                                    {step.status === 'active' && <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse" />}
                                                </div>
                                                <div className="flex items-center gap-2 mb-1">
                                                    <span className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded leading-none ${step.type === 'tool' ? 'bg-purple-50 text-purple-600 border border-purple-100' :
                                                        step.type === 'think' ? 'bg-amber-50 text-amber-600 border border-amber-100' : 'bg-slate-100 text-slate-600 border border-slate-200'}`}>
                                                        {step.type === 'tool' ? 'TOOL' : step.type === 'think' ? 'THOUGHT' : 'SYSTEM'}
                                                    </span>
                                                </div>
                                                <p className={`text-xs font-semibold mb-1 truncate ${step.status === 'active' ? 'text-indigo-700' : 'text-slate-700'}`}>
                                                    {step.type === 'tool' ? (
                                                        <span className="font-mono text-[11px]">{step.toolName}<span className="opacity-50 text-slate-400 ml-1">()</span></span>
                                                    ) : step.type === 'think' ? t('thinking') : t('statusUpdate')}
                                                </p>
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
                                    {steps.length === 0 && !isLoading && (
                                        <div className="p-6 text-center text-slate-400 text-xs">{t('readyToStartReasoning')}</div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Main Report Area */}
                    <div className="col-span-12 lg:col-span-9 flex flex-col h-full overflow-hidden">
                        <div className="bg-white border border-slate-200 rounded-xl shadow-sm h-full flex flex-col relative overflow-hidden">
                            <div className="h-10 border-b border-slate-100 px-4 flex items-center justify-between bg-white z-20">
                                <h2 className="text-xs font-semibold text-slate-700 flex items-center gap-2 uppercase tracking-wide">
                                    <Icon name="auto_awesome" className="text-violet-500 text-sm" />
                                    {t('advancedResearchReport')}
                                </h2>
                                <div className="flex items-center gap-3">
                                    {sources.length > 0 && (
                                        <span className="text-[10px] text-slate-400">{sources.length} {t('sources')}</span>
                                    )}
                                    {phase === 'done' && reportContent && (
                                        <div className="relative" ref={exportMenuRef}>
                                            <button
                                                onClick={() => setIsExportMenuOpen(!isExportMenuOpen)}
                                                className="flex items-center gap-1.5 px-2.5 py-1 bg-zinc-900 text-white rounded-md text-[11px] font-medium hover:bg-zinc-800 transition-colors shadow-sm"
                                            >
                                                <Icon name="download" className="text-xs" />
                                                {t('export')}
                                                <Icon name="expand_more" className="text-xs" />
                                            </button>
                                            {isExportMenuOpen && (
                                                <div className="absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 py-0.5 z-50">
                                                    <button
                                                        onClick={handleExportMarkdown}
                                                        className="w-full text-left px-4 py-2 text-xs text-zinc-700 hover:bg-zinc-50 flex items-center gap-2"
                                                    >
                                                        <Icon name="description" className="text-zinc-400 text-sm" />
                                                        {t('exportAsMarkdown')}
                                                    </button>
                                                    <button
                                                        onClick={handleExportPDF}
                                                        className="w-full text-left px-4 py-2 text-xs text-zinc-700 hover:bg-zinc-50 flex items-center gap-2"
                                                    >
                                                        <Icon name="picture_as_pdf" className="text-zinc-400 text-sm" />
                                                        {t('exportAsPDF')}
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                            <div className="flex-1 overflow-y-auto p-12 lg:px-20 bg-white relative">
                                {isLoading && !reportContent && (
                                    <div className="absolute top-4 right-4 flex items-center gap-2">
                                        <div className="loader border-t-violet-400 border-slate-200 size-4 border-2 rounded-full animate-spin" />
                                    </div>
                                )}
                                <div className="flex-1" id="advanced-report-content">
                                    {reportContent ? (
                                        <MarkdownViewer content={reportContent} />
                                    ) : (
                                        <div className="flex flex-col items-center justify-center h-64 text-slate-300">
                                            <Icon name="neurology" className="text-4xl mb-4 opacity-50" />
                                            <p className="text-sm">{t('researchInProgress')}</p>
                                        </div>
                                    )}
                                    <div ref={reportEndRef} />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

    // ==========================================
    // Main Render
    // ==========================================
    return (
        <div className="flex flex-col h-full bg-white">
            {phase === 'idle' && renderInputPhase()}
            {phase === 'clarifying' && renderClarificationPhase()}
            {(phase === 'researching' || phase === 'done') && renderResearchPhase()}
        </div>
    );
};


// ==========================================
// Sub-components
// ==========================================

interface DirectionCardProps {
    direction: ClarificationDirection;
    isSelected: boolean;
    isLoading: boolean;
    onClick: () => void;
    disabled: boolean;
}

const DirectionCard: React.FC<DirectionCardProps> = ({ direction, isSelected, isLoading, onClick, disabled }) => {
    const ICON_MAP: Record<string, string> = {
        dir_1: 'visibility',
        dir_2: 'trending_up',
        dir_3: 'rocket_launch',
        dir_4: 'build',
    };

    const GRADIENT_MAP: Record<string, string> = {
        dir_1: 'from-blue-500 to-cyan-500',
        dir_2: 'from-violet-500 to-purple-500',
        dir_3: 'from-amber-500 to-orange-500',
        dir_4: 'from-emerald-500 to-teal-500',
    };

    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={`w-full text-left rounded-xl border p-5 transition-all duration-200 group relative overflow-hidden ${isSelected
                ? 'border-violet-400 bg-violet-50 ring-2 ring-violet-500/20 shadow-md'
                : 'border-slate-200 bg-white hover:border-violet-300 hover:shadow-md hover:bg-slate-50/50'
                } ${disabled && !isSelected ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
        >
            {/* Loading overlay */}
            {isLoading && (
                <div className="absolute inset-0 bg-white/80 flex items-center justify-center z-10 rounded-xl">
                    <div className="w-5 h-5 border-2 border-violet-200 border-t-violet-600 rounded-full animate-spin" />
                </div>
            )}

            <div className="flex items-start gap-3">
                <div className={`p-2 rounded-lg bg-gradient-to-br ${GRADIENT_MAP[direction.id] || 'from-slate-500 to-slate-600'} text-white shrink-0 shadow-sm`}>
                    <Icon name={ICON_MAP[direction.id] || 'lightbulb'} className="text-base" />
                </div>
                <div className="flex-1 min-w-0">
                    <h3 className={`text-sm font-semibold mb-1 ${isSelected ? 'text-violet-800' : 'text-slate-800 group-hover:text-violet-700'} transition-colors`}>
                        {direction.title}
                    </h3>
                    <p className="text-xs text-slate-500 leading-relaxed mb-2">
                        {direction.description}
                    </p>
                    <p className="text-[10px] text-slate-400 italic truncate">
                        {direction.example_query}
                    </p>
                </div>
                <Icon
                    name="arrow_forward"
                    className={`text-sm shrink-0 mt-1 transition-transform ${isSelected ? 'text-violet-500' : 'text-slate-300 group-hover:text-violet-400 group-hover:translate-x-0.5'}`}
                />
            </div>
        </button>
    );
};
