import { ResearchResult } from '../types';

export type ResearchEventType =
    | 'status'
    | 'think'
    | 'tool_start'
    | 'tool_response'
    | 'answer'
    | 'final_answer'
    | 'error'
    | 'timeout';

export interface ResearchEvent {
    type: ResearchEventType;
    content: string;
    tool?: string;
    arguments?: any;
    messages?: any[];
    iterations?: number;
    termination?: string;
}

export interface Settings {
    model_name: string;
    temperature: number;
    top_p: number;
    max_iterations: number;
    max_context_tokens: number;
    openrouter_api_key?: string;
    serper_api_key?: string;
    openrouter_api_key_masked: string;
    serper_api_key_masked: string;
}

export type SettingsUpdate = Partial<Settings>;

export interface ResearchHistoryItem {
    task_id: string;
    question: string;
    status: string;
    iterations: number;
    execution_time: number;
    created_at: string;
    answer?: string;
    termination_reason?: string;
    is_bookmarked?: boolean;
}

export class ResearchService {
    private static BASE_URL = '/api/v1/research';

    static async streamResearch(
        question: string,
        onEvent: (event: ResearchEvent) => void,
        maxIterations: number = 30
    ): Promise<void> {
        try {
            const response = await fetch(`${this.BASE_URL}/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question,
                    max_iterations: maxIterations
                }),
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
            console.error('Research stream failed', error);
            onEvent({
                type: 'error',
                content: error instanceof Error ? error.message : 'Unknown error occurred'
            });
        }
    }

    static async getHistory(): Promise<ResearchHistoryItem[]> {
        const response = await fetch(`${this.BASE_URL}/history`);
        if (!response.ok) {
            console.warn("Backend history endpoint failed or not found.");
            return [];
        }
        return response.json();
    }

    static async getSettings(): Promise<Settings> {
        const response = await fetch('/api/v1/settings');
        if (!response.ok) {
            throw new Error('Failed to fetch settings');
        }
        return response.json();
    }

    static async updateSettings(update: SettingsUpdate): Promise<Settings> {
        const response = await fetch('/api/v1/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(update),
        });
        if (!response.ok) {
            throw new Error('Failed to update settings');
        }
        return response.json();
    }

    static async toggleBookmark(taskId: string): Promise<{ is_bookmarked: boolean }> {
        const response = await fetch(`${this.BASE_URL}/${taskId}/bookmark`, {
            method: 'POST',
        });
        if (!response.ok) {
            throw new Error('Failed to toggle bookmark');
        }
        return response.json();
    }
}
