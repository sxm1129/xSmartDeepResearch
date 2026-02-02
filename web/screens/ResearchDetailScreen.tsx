import React, { useContext } from 'react';
import { Icon } from '../components/Icon';
import { MarkdownViewer } from '../components/MarkdownViewer';
import { ResearchHistoryItem, ResearchService } from '../services/api';
import { LanguageContext } from '../App';

interface ResearchDetailScreenProps {
    item: ResearchHistoryItem;
    onBack: () => void;
}

export const ResearchDetailScreen: React.FC<ResearchDetailScreenProps> = ({ item: initialItem, onBack }) => {
    const { t } = useContext(LanguageContext);
    const [item, setItem] = React.useState(initialItem);
    const [isBookmarked, setIsBookmarked] = React.useState(initialItem.is_bookmarked || false);

    const [isExportMenuOpen, setIsExportMenuOpen] = React.useState(false);
    const exportMenuRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
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
        if (!item.answer) return;
        const blob = new Blob([item.answer], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = getSanitizedFilename(item.question, 'md');
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        setIsExportMenuOpen(false);
    };

    const handleExportPDF = () => {
        if (!item.answer) return;

        // Dynamically import html2pdf
        import('html2pdf.js').then((html2pdf) => {
            const element = document.getElementById('report-content');
            const opt = {
                margin: 10,
                filename: getSanitizedFilename(item.question, 'pdf'),
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2, useCORS: true },
                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
            };

            // @ts-ignore
            html2pdf.default().set(opt).from(element).save();
            setIsExportMenuOpen(false);
        }).catch(err => console.error("Failed to load html2pdf", err));
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
                            <span>{item.iterations} {t('steps')}</span>
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
                        {isBookmarked ? t('saved') : t('save')}
                    </button>

                    <div className="relative" ref={exportMenuRef}>
                        <button
                            onClick={() => setIsExportMenuOpen(!isExportMenuOpen)}
                            disabled={!item.answer}
                            className="flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-lg text-sm font-medium hover:bg-primary/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <Icon name="download" className="text-lg" />
                            {t('export')}
                            <Icon name="expand_more" className="text-lg" />
                        </button>

                        {isExportMenuOpen && (
                            <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-slate-100 py-1 z-50 animate-in fade-in zoom-in-95 duration-200">
                                <button
                                    onClick={handleExportMarkdown}
                                    className="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                                >
                                    <Icon name="description" className="text-slate-400 text-base" />
                                    {t('exportAsMarkdown')}
                                </button>
                                <button
                                    onClick={handleExportPDF}
                                    className="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                                >
                                    <Icon name="picture_as_pdf" className="text-slate-400 text-base" />
                                    {t('exportAsPDF')}
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 md:p-10">
                <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-sm border border-slate-100 p-8 min-h-[500px]">
                    {item.answer ? (
                        <div className="flex-1 overflow-y-auto" id="report-content">
                            <MarkdownViewer content={item.answer} />
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                            <Icon name="description" className="text-6xl mb-4 opacity-20" />
                            <p className="text-lg font-medium">{t('noReportContent')}</p>
                            <p className="text-sm">{t('researchFailedHint')}</p>
                            {item.termination_reason && (
                                <div className="mt-4 p-4 bg-red-50 text-red-600 rounded-lg text-sm max-w-md text-center">
                                    {t('error')}: {item.termination_reason}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
