import React, { useState, useEffect } from 'react';
import { Icon } from '../components/Icon';
import { ResearchService, Settings } from '../services/api';

export const SettingsScreen: React.FC<{ onShowError: () => void }> = ({ onShowError }) => {
    const [settings, setSettings] = useState<Settings>({
        model_name: 'gpt-4o',
        temperature: 0.7,
        top_p: 0.9,
        max_iterations: 10,
        max_context_tokens: 32000,
        openrouter_api_key_masked: '',
        serper_api_key_masked: ''
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    // Local state for inputs to allow editing
    const [openrouterKey, setOpenrouterKey] = useState('');
    const [serperKey, setSerperKey] = useState('');

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            const data = await ResearchService.getSettings();
            setSettings(data);
        } catch (e) {
            console.error("Failed to load settings", e);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const update: any = {
                model_name: settings.model_name,
                temperature: settings.temperature,
                top_p: settings.top_p,
                max_iterations: settings.max_iterations,
                max_context_tokens: settings.max_context_tokens
            };

            if (openrouterKey) update.openrouter_api_key = openrouterKey;
            if (serperKey) update.serper_api_key = serperKey;

            const newSettings = await ResearchService.updateSettings(update);
            setSettings(newSettings);
            setOpenrouterKey(''); // Clear after save
            setSerperKey('');
            alert('Settings saved successfully!');
        } catch (e) {
            console.error("Failed to save settings", e);
            alert('Failed to save settings.');
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="p-10 text-center text-slate-500">Loading settings...</div>;

    return (
        <div className="flex flex-col h-full bg-background-light overflow-y-auto">
            {/* Header */}
            <header className="flex items-center justify-between px-10 py-3 bg-white border-b border-slate-200 sticky top-0 z-20">
                <div className="flex flex-col gap-2">
                    <h1 className="text-3xl font-black text-slate-900 tracking-tight">Agent Configuration</h1>
                    <p className="text-slate-500 text-base font-normal">Configure your AI agent's model parameters, search capabilities, and API credentials.</p>
                </div>
                <div className="flex gap-3">
                    <button onClick={() => loadSettings()} className="flex items-center justify-center rounded-lg h-10 px-6 border border-slate-300 bg-white text-sm font-medium hover:bg-slate-50 transition-colors">
                        Reset
                    </button>
                    <button onClick={handleSave} disabled={saving} className="flex items-center justify-center rounded-lg h-10 px-6 bg-primary text-white text-sm font-bold shadow-lg shadow-primary/30 hover:bg-primary-dark transition-colors disabled:opacity-50">
                        {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                </div>
            </header>

            <div className="flex-1 p-10 max-w-[1200px] mx-auto w-full">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

                    {/* Left Column */}
                    <div className="lg:col-span-8 flex flex-col gap-6">

                        {/* Model Selection */}
                        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
                                <h3 className="text-lg font-bold flex items-center gap-2">
                                    <Icon name="psychology" className="text-primary" />
                                    Model Selection
                                </h3>
                            </div>
                            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="col-span-2">
                                    <label className="block text-sm font-medium mb-2 text-slate-700">Primary Model</label>
                                    <div className="relative">
                                        <select
                                            value={settings.model_name}
                                            onChange={(e) => setSettings({ ...settings, model_name: e.target.value })}
                                            className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-primary focus:border-primary block p-3 pr-10 appearance-none">
                                            <option value="gpt-4o">GPT-4o (OpenRouter)</option>
                                            <option value="openai/gpt-4o-mini">GPT-4o Mini (OpenRouter)</option>
                                            <option value="z-ai/glm-4.7-flash">GLM-4.7 Flash (OpenRouter)</option>
                                            <option value="deepseek/deepseek-chat">DeepSeek Chat (OpenRouter)</option>
                                        </select>
                                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-500">
                                            <Icon name="expand_more" className="text-sm" />
                                        </div>
                                    </div>
                                </div>
                                {/* Sliders */}
                                <div className="space-y-4">
                                    <div className="flex justify-between items-center mb-1">
                                        <label className="text-sm font-medium text-slate-700 flex items-center gap-1">
                                            Temperature
                                            <Icon name="info" className="text-slate-400 text-[16px] cursor-help" />
                                        </label>
                                        <span className="text-xs font-mono bg-slate-100 px-2 py-0.5 rounded text-slate-600">{settings.temperature}</span>
                                    </div>
                                    <input
                                        type="range" min="0" max="2" step="0.1"
                                        value={settings.temperature} onChange={(e) => setSettings({ ...settings, temperature: parseFloat(e.target.value) })}
                                        className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-primary"
                                    />
                                    <div className="flex justify-between text-xs text-slate-400">
                                        <span>Precise</span>
                                        <span>Creative</span>
                                    </div>
                                </div>
                                <div className="space-y-4">
                                    <div className="flex justify-between items-center mb-1">
                                        <label className="text-sm font-medium text-slate-700 flex items-center gap-1">
                                            Top P
                                            <Icon name="info" className="text-slate-400 text-[16px] cursor-help" />
                                        </label>
                                        <span className="text-xs font-mono bg-slate-100 px-2 py-0.5 rounded text-slate-600">{settings.top_p}</span>
                                    </div>
                                    <input
                                        type="range" min="0" max="1" step="0.05"
                                        value={settings.top_p} onChange={(e) => setSettings({ ...settings, top_p: parseFloat(e.target.value) })}
                                        className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-primary"
                                    />
                                    <div className="flex justify-between text-xs text-slate-400">
                                        <span>Focused</span>
                                        <span>Diverse</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Advanced Parameters */}
                        <div className="bg-white rounded-xl shadow-sm border border-slate-200">
                            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
                                <h3 className="text-lg font-bold flex items-center gap-2">
                                    <Icon name="tune" className="text-primary" />
                                    Advanced Parameters
                                </h3>
                            </div>
                            <div className="p-6 flex flex-col gap-5">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-xs font-medium text-slate-500 mb-1">Max Iterations</label>
                                        <input
                                            type="number"
                                            value={settings.max_iterations}
                                            onChange={(e) => setSettings({ ...settings, max_iterations: parseInt(e.target.value) })}
                                            className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-sm focus:ring-primary focus:border-primary"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-slate-500 mb-1">Context Limit</label>
                                        <select
                                            value={settings.max_context_tokens}
                                            onChange={(e) => setSettings({ ...settings, max_context_tokens: parseInt(e.target.value) })}
                                            className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-sm focus:ring-primary focus:border-primary">
                                            <option value="4000">4k</option>
                                            <option value="16000">16k</option>
                                            <option value="32000">32k</option>
                                            <option value="128000">128k</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Right Column */}
                    <div className="lg:col-span-4 flex flex-col gap-6">

                        {/* API Keys */}
                        <div className="bg-white rounded-xl shadow-sm border border-slate-200">
                            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
                                <h3 className="text-lg font-bold flex items-center gap-2">
                                    <Icon name="key" className="text-primary" />
                                    API Keys
                                </h3>
                            </div>
                            <div className="p-6 flex flex-col gap-6">
                                {/* OpenRouter */}
                                <div>
                                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">OpenRouter API Key</label>
                                    <div className="relative">
                                        <input
                                            type="password"
                                            placeholder={settings.openrouter_api_key_masked || "No key set"}
                                            value={openrouterKey}
                                            onChange={(e) => setOpenrouterKey(e.target.value)}
                                            className="w-full bg-emerald-50 border border-emerald-500/50 text-slate-900 text-sm rounded-lg focus:ring-emerald-500 focus:border-emerald-500 block p-2.5"
                                        />
                                    </div>
                                    <p className="text-[10px] text-slate-400 mt-1">Leave empty to keep current key</p>
                                </div>

                                {/* Serper */}
                                <div>
                                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Serper API Key</label>
                                    <div className="relative">
                                        <input
                                            type="password"
                                            placeholder={settings.serper_api_key_masked || "No key set"}
                                            value={serperKey}
                                            onChange={(e) => setSerperKey(e.target.value)}
                                            className="w-full bg-blue-50 border border-blue-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    );
};