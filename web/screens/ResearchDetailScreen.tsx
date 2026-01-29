import React from 'react';
import { Icon } from '../components/Icon';
import { ResearchHistoryItem } from '../services/api';
import ReactMarkdown from 'react-markdown';

interface ResearchDetailScreenProps {
    item: ResearchHistoryItem;
    onBack: () => void;
}

export const ResearchDetailScreen: React.FC<ResearchDetailScreenProps> = ({ item: initialItem, onBack }) => {
    const [item, setItem] = React.useState(initialItem);
    const [isBookmarked, setIsBookmarked] = React.useState(initialItem.is_bookmarked || false);

    const handleExport = () => {
        if (!item.answer) return;
        const blob = new Blob([item.answer], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `research-report-${item.task_id}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const handleToggleBookmark = async () => {
        try {
            const newItem = { ...item, is_bookmarked: !isBookmarked };
            setIsBookmarked(!isBookmarked); // Optimistic UI
            await ResearchService.toggleBookmark(item.task_id);
            setItem(newItem); // Sync internal state
        } catch (error) {
            console.error("Failed to toggle bookmark", error);
            setIsBookmarked(!isBookmarked); // Revert
        }
    };

    return (
        <div className="flex flex-col h-full bg-background-light">
            {/* Header */}
            <header className="w-full px-6 py-4 border-b border-border-light bg-surface-light/80 backdrop-blur-md sticky top-0 z-10 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <button
                        onClick={onBack}
                        className="p-2 rounded-full hover:bg-slate-100 text-slate-500 transition-colors"
                    >
                        <Icon name="arrow_back" className="text-xl" />
                    </button>
                    <div>
                        <h2 className="text-xl font-bold text-slate-900 line-clamp-1">{item.question}</h2>
                        <div className="flex items-center gap-2 text-xs text-slate-500">
                            <span className="uppercase font-semibold tracking-wider">{item.status}</span>
                            <span>•</span>
                            <span>{new Date(item.created_at).toLocaleString()}</span>
                            <span>•</span>
                            <span>{item.iterations} steps</span>
                        </div>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={handleToggleBookmark}
                        className={`p-2 rounded-lg border transition-colors flex items-center gap-2 text-sm font-medium ${isBookmarked
                            ? 'bg-yellow-50 border-yellow-200 text-yellow-600'
                            : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'}`}
                    >
                        <Icon name={isBookmarked ? "star" : "star_border"} className={isBookmarked ? "fill-current" : ""} />
                        {isBookmarked ? 'Saved' : 'Save'}
                    </button>

                    <button
                        onClick={handleExport}
                        disabled={!item.answer}
                        className="flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-lg text-sm font-medium hover:bg-primary/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Icon name="download" className="text-lg" />
                        Export
                    </button>
                </div>
            </header>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 md:p-10">
                <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-sm border border-slate-100 p-8 min-h-[500px]">
                    {item.answer ? (
                        <div className="prose prose-slate max-w-none">
                            <ReactMarkdown>{item.answer}</ReactMarkdown>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                            <Icon name="description" className="text-6xl mb-4 opacity-20" />
                            <p className="text-lg font-medium">No report content available.</p>
                            <p className="text-sm">This research might have failed or was terminated early.</p>
                            {item.termination_reason && (
                                <div className="mt-4 p-4 bg-red-50 text-red-600 rounded-lg text-sm max-w-md text-center">
                                    Error: {item.termination_reason}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
