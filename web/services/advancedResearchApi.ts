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
     * Start streaming advanced research with a refined query
     */
    static async streamResearch(
        request: AdvancedResearchRequest,
        onEvent: (event: ResearchEvent) => void,
    ): Promise<void> {
        try {
            const response = await fetch(`${this.BASE_URL}/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(request),
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.statusText}`);
            }

            if (!response.body) {
                throw new Error('Response body is null');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;

                const lines = buffer.split('\n\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const jsonStr = line.substring(6);
                            const event: ResearchEvent = JSON.parse(jsonStr);
                            onEvent(event);
                        } catch (e) {
                            console.error('Failed to parse SSE event', e);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Advanced research stream failed', error);
            onEvent({
                type: 'error',
                content: error instanceof Error ? error.message : 'Unknown error occurred'
            });
        }
    }
}
