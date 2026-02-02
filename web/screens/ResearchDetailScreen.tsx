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
        <div className="flex flex-col h-full bg-white">
            {/* Header */}
            <header className="w-full px-6 py-3 border-b border-zinc-200 bg-white sticky top-0 z-10 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <button
                        onClick={onBack}
                        className="p-1.5 rounded-md hover:bg-zinc-100 text-zinc-500 hover:text-zinc-900 transition-colors"
                    >
                        <Icon name="arrow_back" className="text-lg" />
                    </button>
                    <div>
                        <h2 className="text-lg font-bold text-zinc-900 line-clamp-1 tracking-tight">{item.question}</h2>
                        <div className="flex items-center gap-2 text-[10px] text-zinc-400 font-mono mt-0.5">
                            <span className="uppercase font-semibold tracking-wider text-zinc-500">{item.status}</span>
                            <span>/</span>
                            <span>{new Date(item.created_at).toLocaleString()}</span>
                            <span>/</span>
                            <span>{item.iterations} {t('steps')}</span>
                        </div>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={handleToggleBookmark}
                        className={`p-1.5 px-3 rounded-md border transition-colors flex items-center gap-2 text-xs font-semibold ${isBookmarked
                            ? 'bg-amber-50 border-amber-200 text-amber-600'
                            : 'bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50 hover:border-zinc-300'}`}
                    >
                        <Icon name={isBookmarked ? "star" : "star_border"} className={isBookmarked ? "fill-current" : "text-sm"} />
                        {isBookmarked ? t('saved') : t('save')}
                    </button>

                    <div className="relative" ref={exportMenuRef}>
                        <button
                            onClick={() => setIsExportMenuOpen(!isExportMenuOpen)}
                            disabled={!item.answer}
                            className="flex items-center gap-2 px-3 py-1.5 bg-zinc-900 text-white rounded-md text-xs font-medium hover:bg-zinc-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                        >
                            <Icon name="download" className="text-sm" />
                            {t('export')}
                            <Icon name="expand_more" className="text-sm" />
                        </button>

                        {isExportMenuOpen && (
                            <div className="absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 py-0.5 z-50 animate-in fade-in zoom-in-95 duration-100">
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
                </div>
            </header>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-0">
                <div className="max-w-4xl mx-auto bg-white min-h-full py-12 px-8">
                    {item.answer ? (
                        <div className="flex-1" id="report-content">
                            <article className="prose prose-zinc max-w-none prose-headings:font-display prose-headings:font-semibold prose-headings:tracking-tight prose-h1:text-2xl prose-p:text-sm prose-p:leading-7 prose-a:text-zinc-800">
                                <MarkdownViewer content={item.answer} />
                            </article>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center py-20 text-zinc-300">
                            <Icon name="description" className="text-5xl mb-4 opacity-30" />
                            <p className="text-sm font-medium text-zinc-500">{t('noReportContent')}</p>
                            <p className="text-xs">{t('researchFailedHint')}</p>
                            {item.termination_reason && (
                                <div className="mt-4 p-3 bg-red-50 text-red-600 rounded-md text-xs border border-red-100 max-w-md text-center">
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
