export interface ResearchSource {
    title: string;
    url: string;
    snippet?: string;
    relevance?: string;
}

export function extractSourcesFromToolResponse(toolName: string, response: string): ResearchSource[] {
    const sources: ResearchSource[] = [];

    if (!response) return sources;

    const lowerToolName = toolName.toLowerCase();

    try {
        // 1. Generic Markdown Link Extraction (works for 'search' and others returning formatted text)
        const markdownRegex = /\[(.*?)\]\((https?:\/\/[^\s)]+)\)/g;
        let match;
        while ((match = markdownRegex.exec(response)) !== null) {
            sources.push({
                title: match[1],
                url: match[2],
                relevance: 'Information'
            });
        }

        // 2. Specific tool logic if needed
        if (lowerToolName === 'visit') {
            // Visit often starts with "The useful information in URL..."
            const visitUrlRegex = /information in (https?:\/\/[^\s]+) for/i;
            const visitMatch = visitUrlRegex.exec(response);
            if (visitMatch && !sources.some(s => s.url === visitMatch[1])) {
                sources.push({
                    title: "Visited Page",
                    url: visitMatch[1],
                    relevance: 'Direct Visit'
                });
            }
        }
    } catch (error) {
        console.warn('Failed to parse sources', error);
    }

    return sources;
}
