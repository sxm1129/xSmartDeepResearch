
import React, { useEffect, useState, useContext } from 'react';
import { Icon } from '../components/Icon';
import { ResearchService, ResearchHistoryItem } from '../services/api';
import { HistoryScreen } from './HistoryScreen';
import { LanguageContext } from '../App';

// Reusing HistoryScreen logic but wrapping it to filter for bookmarked items
// However, HistoryScreen currently fetches its own data.
// Ideally, we should refactor HistoryScreen to accept data as prop or use a common customized hook.
// For speed, let's copy the structure or create a wrapper if possible.
// HistoryScreen is implemented as a self-fetching component.
// Let's create a stand-alone SavedReportsScreen that works similarly but filters locally (since we don't have a backend filter endpoint yet, or we can fetch all and filter client side).

export const SavedReportsScreen: React.FC<{ onSelect: (item: ResearchHistoryItem) => void }> = ({ onSelect }) => {
    const { t } = useContext(LanguageContext);
    const [history, setHistory] = useState<ResearchHistoryItem[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchHistory = async () => {
        try {
            const data = await ResearchService.getHistory();
            // Filter for bookmarked items
            setHistory(data.filter(item => item.is_bookmarked));
        } catch (error) {
            console.error("Failed to load saved reports", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, []);

    const formatTimeAgo = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

        if (diffInSeconds < 60) return t('justNow');
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}${t('minutes')} ${t('ago')}`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}${t('hours')} ${t('ago')}`;
        return `${Math.floor(diffInSeconds / 86400)}${t('days')} ${t('ago')}`;
    };

    const getStatusColor = (status: string) => {
        switch (status?.toLowerCase()) {
            case 'completed': return 'bg-green-100 text-green-700';
            case 'processing': return 'bg-blue-100 text-blue-700';
            case 'failed': return 'bg-red-100 text-red-700';
            default: return 'bg-slate-100 text-slate-700';
        }
    };

    const handleToggleBookmark = async (e: React.MouseEvent, item: ResearchHistoryItem) => {
        e.stopPropagation();
        try {
            // Optimistic update - remove from list immediately
            setHistory(prev => prev.filter(i => i.task_id !== item.task_id));
            await ResearchService.toggleBookmark(item.task_id);
        } catch (error) {
            console.error("Failed to toggle bookmark", error);
            fetchHistory(); // Reload on error
        }
    };

    return (
        <div className="flex flex-col h-full bg-background-light">
            {/* Header */}
            <header className="w-full px-6 py-5 md:px-10 border-b border-border-light bg-surface-light/80 backdrop-blur-md sticky top-0 z-10">
                <div className="flex justify-between items-center max-w-7xl mx-auto">
                    <div className="flex flex-col gap-1">
                        <h2 className="text-2xl font-black tracking-tight text-slate-900">{t('savedReportsConfig')}</h2>
                        <p className="text-slate-500 text-sm">{t('savedReportsDesc')}</p>
                    </div>
                    <button onClick={fetchHistory} className="p-2 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
                        <Icon name="refresh" className={`text-slate-500 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </header>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 md:p-10">
                <div className="max-w-7xl mx-auto flex flex-col gap-6">

                    {/* Grid */}
                    {loading ? (
                        <div className="flex items-center justify-center h-64 text-slate-400">{t('loading')}</div>
                    ) : history.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                            <Icon name="star_border" className="text-6xl mb-4 opacity-20" />
                            <p>{t('noSavedReports')}</p>
                            <p className="text-sm">{t('starItemsHint')}</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">

                            {history.map((item) => (
                                <div
                                    key={item.task_id}
                                    onClick={() => onSelect(item)}
                                    className="group relative flex flex-col justify-between p-5 bg-white rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.04)] border border-slate-100 hover:shadow-lg hover:border-primary/30 transition-all duration-300 h-64 cursor-pointer"
                                >
                                    <div className="flex justify-between items-start mb-3">
                                        <div className={`p-2.5 rounded-lg ${item.status === 'completed' ? 'bg-blue-50 text-primary' :
                                            item.status === 'processing' ? 'bg-purple-50 text-purple-600' :
                                                'bg-red-50 text-red-600'
                                            }`}>
                                            <Icon name={
                                                item.status === 'completed' ? 'memory' :
                                                    item.status === 'processing' ? 'query_stats' :
                                                        'biotech'
                                            } />
                                        </div>

                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={(e) => handleToggleBookmark(e, item)}
                                                className="p-1 rounded-full hover:bg-slate-100 transition-colors text-yellow-400"
                                                title={t('removeFromSaved')}
                                            >
                                                <Icon name="star" className="text-[20px]" fill={true} />
                                            </button>
                                            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${getStatusColor(item.status)}`}>
                                                {item.status === 'completed' && <span className="size-1.5 rounded-full bg-green-500"></span>}
                                                {item.status === 'processing' && <Icon name="progress_activity" className="text-[14px] animate-spin" />}
                                                {item.status}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="flex-1 overflow-hidden">
                                        <h3 className="font-bold text-lg text-slate-900 mb-2 leading-tight line-clamp-2">{item.question}</h3>
                                        <div className="text-sm text-slate-500 line-clamp-3">
                                            {item.answer ? item.answer : (item.termination_reason || 'No description available')}
                                        </div>
                                    </div>

                                    <div className="mt-4 pt-4 border-t border-slate-100 flex justify-between items-center text-xs text-slate-400">
                                        <div className="flex items-center gap-1">
                                            <Icon name="schedule" className="text-[14px]" />
                                            {formatTimeAgo(item.created_at)}
                                        </div>
                                        <span className="font-mono">{item.iterations} {t('steps')}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
