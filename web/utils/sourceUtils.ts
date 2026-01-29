export interface ResearchSource {
    title: string;
    url: string;
    snippet?: string;
    relevance?: string;
}

export function extractSourcesFromToolResponse(toolName: string, response: string): ResearchSource[] {
    const sources: ResearchSource[] = [];

    if (!response) return sources;

    try {
        if (toolName === 'Search') {
            // Handle Serper format
            // Usually Serper returns a stringified JSON or text. 
            // If it's pure text, we might not get structured data easily.
            // But let's assume standard Serper JSON structure if possible, 
            // or try to regex find http links if it's text.

            // Attempt to parse if it looks like JSON
            if (response.trim().startsWith('{') || response.trim().startsWith('[')) {
                try {
                    // Serper usually has 'organic' or 'knowledgeGraph'
                    // We might need to handle cleaner strings in the backend first, 
                    // but let's try a generic JSON parse.
                    // CAUTION: The backend might return a stringified "summary" instead of raw JSON.
                    // In xSmartDeepResearch, SearchTool.run usually returns formatted text.
                    // If it returns text, we regex for markdown links: [Title](URL)

                    const regex = /\[(.*?)\]\((https?:\/\/[^\s)]+)\)/g;
                    let match;
                    while ((match = regex.exec(response)) !== null) {
                        sources.push({
                            title: match[1],
                            url: match[2],
                            relevance: 'High'
                        });
                    }
                } catch (e) {
                    // ignore
                }
            }
        } else if (toolName === 'Visit') {
            // Visit usually returns content of a page.
            // We can treat the visited page as a source if we have the URL in arguments (but we only have response here).
            // The response might contain "Source: URL" at the top.
            // For now, let's just leave Visit sources to be handled by the 'Search' step mostly.
        }
    } catch (error) {
        console.warn('Failed to parse sources', error);
    }

    return sources;
}
