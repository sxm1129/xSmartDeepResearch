/**
 * Advanced Research Context
 * 
 * Independent state machine for advanced research with intent clarification.
 * States: IDLE → CLARIFYING → RESEARCHING → DONE
 */

import React, { createContext, useState, useContext, useCallback, useRef } from 'react';
import { AdvancedResearchService, ClarificationDirection, ClarifyResponse } from '../services/advancedResearchApi';
import { ResearchEvent } from '../services/api';
import { extractSourcesFromToolResponse, ResearchSource } from '../utils/sourceUtils';
import { LanguageContext } from '../App';

export type AdvancedResearchPhase = 'idle' | 'clarifying' | 'researching' | 'done';

export interface ReasoningStep {
    type: 'status' | 'think' | 'tool';
    content: string;
    status: 'pending' | 'active' | 'completed';
    toolName?: string;
    timestamp: number;
}

interface AdvancedResearchContextType {
    // State
    phase: AdvancedResearchPhase;
    query: string;
    setQuery: (q: string) => void;
    clarificationRound: number;
    directions: ClarificationDirection[];
    selectedDirection: ClarificationDirection | null;
    refinedQuery: string;
    isLoading: boolean;
    reportContent: string;
    steps: ReasoningStep[];
    sources: ResearchSource[];
    error: string | null;

    // Actions
    startClarification: (query: string) => Promise<void>;
    selectDirection: (direction: ClarificationDirection) => Promise<void>;
    submitCustomDirection: (customInput: string) => Promise<void>;
    startResearch: () => Promise<void>;
    resetAll: () => void;
}

const AdvancedResearchContext = createContext<AdvancedResearchContextType | undefined>(undefined);

export const AdvancedResearchProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { language } = useContext(LanguageContext);
    // Core state
    const [phase, setPhase] = useState<AdvancedResearchPhase>('idle');
    const [query, setQuery] = useState("");
    const [clarificationRound, setClarificationRound] = useState(0);
    const [directions, setDirections] = useState<ClarificationDirection[]>([]);
    const [selectedDirection, setSelectedDirection] = useState<ClarificationDirection | null>(null);
    const [refinedQuery, setRefinedQuery] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Research state (mirrors ResearchContext)
    const [reportContent, setReportContent] = useState("");
    const [steps, setSteps] = useState<ReasoningStep[]>([]);
    const [sources, setSources] = useState<ResearchSource[]>([]);

    // Use ref to track if research completed via SSE event (avoids race with manual setPhase)
    const researchCompletedRef = useRef(false);

    const resetAll = useCallback(() => {
        setPhase('idle');
        setQuery("");
        setClarificationRound(0);
        setDirections([]);
        setSelectedDirection(null);
        setRefinedQuery("");
        setIsLoading(false);
        setReportContent("");
        setSteps([]);
        setSources([]);
        setError(null);
        researchCompletedRef.current = false;
    }, []);

    /**
     * Handle individual research SSE events (useCallback to avoid recreating on every render)
     */
    const handleResearchEvent = useCallback((event: ResearchEvent) => {
        if (event.type === 'status' || event.type === 'think' || event.type === 'tool_start') {
            setSteps(prev => {
                const newSteps = [...prev];
                if (newSteps.length > 0) {
                    newSteps[newSteps.length - 1].status = 'completed';
                }

                let content = event.content;
                if (event.type === 'tool_start') {
                    content = `Using tool: ${event.tool}...`;
                }

                newSteps.push({
                    type: event.type === 'tool_start' ? 'tool' : event.type as any,
                    content,
                    status: 'active',
                    toolName: event.tool,
                    timestamp: Date.now()
                });
                return newSteps;
            });
        } else if (event.type === 'tool_response') {
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
                    newSteps[newSteps.length - 1].content += ' (Done)';
                }
                return newSteps;
            });
        } else if (event.type === 'answer') {
            setReportContent(prev => prev + event.content);
        } else if (event.type === 'final_answer') {
            researchCompletedRef.current = true;
            setPhase('done');
            setIsLoading(false);
        } else if (event.type === 'error') {
            researchCompletedRef.current = true;
            setError(event.content);
            setPhase('done');
            setIsLoading(false);
        }
    }, []);

    /**
     * Shared helper: execute research with a refined query (fixes SMELL-1 & BUG-4)
     * Extracts the duplicated stream logic from selectDirection/submitCustomDirection/startResearch.
     */
    const executeResearch = useCallback(async (researchQuery: string, originalQuestion: string) => {
        setRefinedQuery(researchQuery);
        setPhase('researching');
        setIsLoading(true);
        setReportContent("");
        setSteps([]);
        setSources([]);
        setError(null);
        researchCompletedRef.current = false;

        try {
            await AdvancedResearchService.streamResearch(
                {
                    refined_query: researchQuery,
                    original_question: originalQuestion,
                },
                (event: ResearchEvent) => handleResearchEvent(event)
            );
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Research failed');
        } finally {
            setIsLoading(false);
            // Only set 'done' if SSE events didn't already handle it (fixes BUG-4 race)
            if (!researchCompletedRef.current) {
                setPhase('done');
            }
        }
    }, [handleResearchEvent]);

    /**
     * Round 1: Analyze question, generate direction options
     */
    const startClarification = useCallback(async (inputQuery: string) => {
        if (!inputQuery.trim() || isLoading) return;

        setQuery(inputQuery);
        setPhase('clarifying');
        setIsLoading(true);
        setError(null);
        setDirections([]);
        setClarificationRound(1);

        try {
            const response: ClarifyResponse = await AdvancedResearchService.clarify({
                question: inputQuery,
                round: 1,
                language,
            });

            setDirections(response.directions);
            setClarificationRound(response.round);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Clarification failed');
            setPhase('idle');
        } finally {
            setIsLoading(false);
        }
    }, [isLoading, language]);

    /**
     * Round 2: User selects a direction, generate refined query and auto-start research
     */
    const selectDirection = useCallback(async (direction: ClarificationDirection) => {
        if (isLoading) return;

        setSelectedDirection(direction);
        setIsLoading(true);
        setError(null);

        try {
            const response = await AdvancedResearchService.clarify({
                question: query,
                round: 2,
                selected_direction_id: direction.id,
                selected_direction: direction,
                language,
            });

            setClarificationRound(2);

            if (response.ready_to_research && response.refined_query) {
                // Auto-start research with refined query
                await executeResearch(response.refined_query, query);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to process selection');
            setIsLoading(false);
        }
    }, [isLoading, query, language, executeResearch]);

    /**
     * User provides custom direction input
     */
    const submitCustomDirection = useCallback(async (customInput: string) => {
        if (isLoading || !customInput.trim()) return;

        setIsLoading(true);
        setError(null);

        try {
            const response = await AdvancedResearchService.clarify({
                question: query,
                round: 2,
                custom_input: customInput,
                language,
            });

            setClarificationRound(2);

            if (response.ready_to_research && response.refined_query) {
                await executeResearch(response.refined_query, query);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to process custom direction');
            setIsLoading(false);
        }
    }, [isLoading, query, language, executeResearch]);

    /**
     * Start research directly (if refinedQuery is already set)
     */
    const startResearch = useCallback(async () => {
        if (!refinedQuery || isLoading) return;
        await executeResearch(refinedQuery, query);
    }, [refinedQuery, query, isLoading, executeResearch]);

    return (
        <AdvancedResearchContext.Provider value={{
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
            startResearch,
            resetAll,
        }}>
            {children}
        </AdvancedResearchContext.Provider>
    );
};

export const useAdvancedResearch = () => {
    const context = useContext(AdvancedResearchContext);
    if (context === undefined) {
        throw new Error('useAdvancedResearch must be used within an AdvancedResearchProvider');
    }
    return context;
};
