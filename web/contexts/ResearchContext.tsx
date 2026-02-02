
import React, { createContext, useState, useContext, useCallback, useRef } from 'react';
import { ResearchService, ResearchEvent } from '../services/api';
import { extractSourcesFromToolResponse, ResearchSource } from '../utils/sourceUtils';

export interface ReasoningStep {
    type: 'status' | 'think' | 'tool';
    content: string;
    status: 'pending' | 'active' | 'completed';
    toolName?: string;
    timestamp: number;
}

interface ResearchContextType {
    query: string;
    setQuery: (q: string) => void;
    isResearching: boolean;
    reportContent: string;
    steps: ReasoningStep[];
    sources: ResearchSource[];
    startResearch: (query: string, t: (key: string) => string) => Promise<void>;
    resetResearch: () => void;
}

const ResearchContext = createContext<ResearchContextType | undefined>(undefined);

export const ResearchProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [query, setQuery] = useState("");
    const [isResearching, setIsResearching] = useState(false);
    const [reportContent, setReportContent] = useState("");
    const [steps, setSteps] = useState<ReasoningStep[]>([]);
    const [sources, setSources] = useState<ResearchSource[]>([]);

    const resetResearch = useCallback(() => {
        setReportContent("");
        setSteps([]);
        setSources([]);
        setIsResearching(false);
    }, []);

    const handleEvent = useCallback((event: ResearchEvent, t: (key: string) => string) => {
        if (event.type === 'status' || event.type === 'think' || event.type === 'tool_start') {
            setSteps(prev => {
                const newSteps = [...prev];
                if (newSteps.length > 0) {
                    newSteps[newSteps.length - 1].status = 'completed';
                }

                let content = event.content;
                if (event.type === 'tool_start') {
                    content = `${t('usingTool')}: ${event.tool}...`;
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
        }
        else if (event.type === 'tool_response') {
            const newSources = extractSourcesFromToolResponse(event.tool || '', event.content);
            if (newSources.length > 0) {
                setSources(prev => {
                    const existingUrls = new Set(prev.map(s => s.url));
                    const uniqueNew = newSources.filter(s => !existingUrls.has(s.url));
                    return [...prev, ...uniqueNew];
                });
            }

            setSteps(prev => {
                const newSteps = [...prev];
                if (newSteps.length > 0) {
                    newSteps[newSteps.length - 1].status = 'completed';
                    newSteps[newSteps.length - 1].content += ` (Done)`;
                }
                return newSteps;
            });
        }
        else if (event.type === 'answer') {
            setReportContent(prev => prev + event.content);
        }
        else if (event.type === 'final_answer') {
            setIsResearching(false);
        }
        else if (event.type === 'error') {
            setReportContent(prev => prev + `\n\n ** ${t('error') || 'Error'}:** ${event.content} `);
            setIsResearching(false);
        }
    }, []);

    const startResearch = useCallback(async (searchQuery: string, t: (key: string) => string) => {
        if (!searchQuery.trim() || isResearching) return;

        setQuery(searchQuery);
        setIsResearching(true);
        setReportContent("");
        setSteps([]);
        setSources([]);

        await ResearchService.streamResearch(searchQuery, (event: ResearchEvent) => {
            handleEvent(event, t);
        });

        setIsResearching(false);
    }, [isResearching, handleEvent]);

    return (
        <ResearchContext.Provider value={{
            query,
            setQuery,
            isResearching,
            reportContent,
            steps,
            sources,
            startResearch,
            resetResearch
        }}>
            {children}
        </ResearchContext.Provider>
    );
};

export const useResearch = () => {
    const context = useContext(ResearchContext);
    if (context === undefined) {
        throw new Error('useResearch must be used within a ResearchProvider');
    }
    return context;
};
