/**
 * Advanced Research API Service
 * 
 * Handles communication with the /api/v1/advanced-research endpoints.
 * Fully independent from the existing ResearchService.
 */

import { ResearchEvent } from './api';

// Types
export interface ClarificationDirection {
    id: string;
    title: string;
    description: string;
    example_query: string;
}

export interface ClarifyRequest {
    question: string;
    selected_direction_id?: string;
    selected_direction?: ClarificationDirection;
    custom_input?: string;
    round: number;
    user_context?: string;
    language?: string;
}

export interface ClarifyResponse {
    directions: ClarificationDirection[];
    round: number;
    ready_to_research: boolean;
    refined_query?: string;
    original_question: string;
}

export interface AdvancedResearchRequest {
    refined_query: string;
    original_question: string;
    max_iterations?: number;
}


export class AdvancedResearchService {
    private static BASE_URL = '/api/v1/advanced-research';

    /**
     * Request intent clarification (round 1 or round 2)
     */
    static async clarify(request: ClarifyRequest): Promise<ClarifyResponse> {
        const response = await fetch(`${this.BASE_URL}/clarify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`Clarification failed: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Start advanced research with a refined query (Submits task to background queue)
     */
    static async submitResearch(
        request: AdvancedResearchRequest
    ): Promise<{ task_id: string }> {
        const response = await fetch(`${this.BASE_URL}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }

        return response.json();
    }
}
