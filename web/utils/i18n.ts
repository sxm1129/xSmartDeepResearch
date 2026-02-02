export type Language = 'en' | 'zh';

export const translations = {
    en: {
        // Sidebar
        dashboard: 'Dashboard',
        history: 'History',
        savedReports: 'Saved Reports',
        settings: 'Settings',
        setupWizard: 'Setup Wizard',
        newResearch: 'New Research',
        proPlan: 'Pro Plan',
        collapseSidebar: 'Collapse Sidebar',
        expandSidebar: 'Expand Sidebar',

        // Live Research
        enterTopic: 'Enter a research topic...',
        deepResearchRunning: 'DeepResearch Running',
        ready: 'Ready',
        stop: 'Stop',
        reasoningChain: 'Reasoning Chain',
        active: 'Active',
        readyToStartReasoning: 'Ready to start reasoning.',
        sources: 'Sources',
        found: 'Found',
        noSourcesFound: 'No sources found yet.',
        liveResearchReport: 'Live Research Report',
        generatingInsights: 'Generating insights...',
        startTopicAbove: 'Enter a topic above to begin research.',

        // Status Updates
        intent: 'Intent',
        thinking: 'Thinking...',
        statusUpdate: 'Status Update',
        contextPruned: 'Context pruned to save tokens.',
        tokenLimitReached: 'Token limit reached, forcing final summary...',
        error: 'Error',

        // Tools
        usingTool: 'Using tool',

        // Common
        language: 'Language',
        chinese: 'Chinese',
        english: 'English',
    },
    zh: {
        // Sidebar
        dashboard: '仪表盘',
        history: '历史记录',
        savedReports: '已存报告',
        settings: '设置',
        setupWizard: '启动向导',
        newResearch: '开始研究',
        proPlan: '专业版',
        collapseSidebar: '收起侧边栏',
        expandSidebar: '展开侧边栏',

        // Live Research
        enterTopic: '输入研究课题...',
        deepResearchRunning: '深度研究运行中',
        ready: '就绪',
        stop: '停止',
        reasoningChain: '推理链',
        active: '活动中',
        readyToStartReasoning: '准备开始推理。',
        sources: '参考资料',
        found: '已找到',
        noSourcesFound: '尚未找到参考资料。',
        liveResearchReport: '实时研究报告',
        generatingInsights: '正在生成洞察...',
        startTopicAbove: '在上方输入课题以开始研究。',

        // Status Updates
        intent: '意图',
        thinking: '思考中...',
        statusUpdate: '状态更新',
        contextPruned: '上下文已修剪以节省 Token。',
        tokenLimitReached: 'Token 达到限制，强制生成最终总结...',
        error: '错误',

        // Tools
        usingTool: '正在使用工具',

        // Common
        language: '语言',
        chinese: '中文',
        english: 'English',
    }
};

export type TranslationKeys = keyof typeof translations.en;
