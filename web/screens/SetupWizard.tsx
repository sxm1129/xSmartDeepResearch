import React, { useState } from 'react';
import { Icon } from '../components/Icon';
import { ResearchService } from '../services/api';

const STEPS = [
    { id: 1, label: 'Welcome', sub: 'Project initialization' },
    { id: 2, label: 'Credentials', sub: 'API Key configuration' },
    { id: 3, label: 'Finish', sub: 'Review & Deploy' },
];

export const SetupWizard: React.FC<{ onComplete?: () => void }> = ({ onComplete }) => {
    const [currentStep, setCurrentStep] = useState(1);
    const [openaiKey, setOpenaiKey] = useState('');
    const [serperKey, setSerperKey] = useState('');
    const [saving, setSaving] = useState(false);

    const handleSaveKeys = async () => {
        if (!openaiKey && !serperKey) {
            setCurrentStep(3);
            return;
        }
        setSaving(true);
        try {
            await ResearchService.updateSettings({
                openai_api_key: openaiKey || undefined,
                serper_api_key: serperKey || undefined
            });
            setCurrentStep(3);
        } catch (e) {
            console.error("Failed to save keys", e);
            alert("Failed to save API keys. Please check console.");
        } finally {
            setSaving(false);
        }
    };

    const renderStepContent = () => {
        switch (currentStep) {
            case 1:
                return (
                    <div className="flex flex-col items-center justify-center text-center p-10 h-full">
                        <div className="size-20 bg-primary/10 rounded-full flex items-center justify-center mb-6 text-primary">
                            <Icon name="rocket_launch" className="text-4xl" />
                        </div>
                        <h2 className="text-3xl font-black text-slate-900 mb-4">Welcome to xSmartDeepResearch</h2>
                        <p className="text-slate-500 max-w-lg mb-8 text-lg">
                            Your autonomous research agent is ready to help you uncover deep insights.
                            Let's configure the essential API keys to get started.
                        </p>
                        <button onClick={() => setCurrentStep(2)} className="bg-primary text-white text-lg font-bold px-8 py-3 rounded-xl shadow-lg shadow-primary/30 hover:bg-primary-dark transition-all transform hover:scale-105">
                            Get Started
                        </button>
                    </div>
                );
            case 2:
                return (
                    <div className="p-8 space-y-8 flex-1">
                        <div className="mb-6">
                            <h2 className="text-2xl font-bold text-slate-900 mb-2">Configure API Credentials</h2>
                            <p className="text-slate-500">Enter your API keys to enable the agent's capabilities.</p>
                        </div>

                        {/* OpenAI Field */}
                        <div className="group">
                            <label className="block text-sm font-medium text-slate-900 mb-2">OpenAI API Key</label>
                            <input
                                type="password"
                                value={openaiKey}
                                onChange={(e) => setOpenaiKey(e.target.value)}
                                placeholder="sk-proj-..."
                                className="w-full pl-4 pr-4 py-3 bg-slate-50 border border-slate-300 rounded-lg text-sm font-mono text-slate-900 focus:ring-2 focus:ring-primary/50 focus:border-primary block"
                            />
                            <p className="mt-1.5 text-xs text-slate-400">Required for the reasoning engine (GPT-4o).</p>
                        </div>

                        {/* Serper Field */}
                        <div className="group">
                            <label className="block text-sm font-medium text-slate-900 mb-2">Serper (Google Search) API Key</label>
                            <input
                                type="password"
                                value={serperKey}
                                onChange={(e) => setSerperKey(e.target.value)}
                                placeholder="api_key..."
                                className="w-full pl-4 pr-4 py-3 bg-slate-50 border border-slate-300 rounded-lg text-sm font-mono text-slate-900 focus:ring-2 focus:ring-primary/50 focus:border-primary block"
                            />
                            <p className="mt-1.5 text-xs text-slate-400">Required for real-time web search capabilities.</p>
                        </div>

                        <div className="pt-4 flex justify-end">
                            <button
                                onClick={handleSaveKeys}
                                disabled={saving}
                                className="flex items-center gap-2 bg-primary text-white font-bold px-6 py-3 rounded-lg hover:bg-primary-dark transition-colors disabled:opacity-50"
                            >
                                {saving ? 'Saving...' : 'Save & Continue'}
                                <Icon name="arrow_forward" />
                            </button>
                        </div>
                    </div>
                );
            case 3:
                return (
                    <div className="flex flex-col items-center justify-center text-center p-10 h-full">
                        <div className="size-20 bg-green-100 rounded-full flex items-center justify-center mb-6 text-green-600">
                            <Icon name="check_circle" className="text-4xl" />
                        </div>
                        <h2 className="text-3xl font-black text-slate-900 mb-4">You're All Set!</h2>
                        <p className="text-slate-500 max-w-lg mb-8 text-lg">
                            System configuration is complete. You can now start creating autonomous research agents.
                        </p>
                        <button onClick={onComplete} className="bg-slate-900 text-white text-lg font-bold px-8 py-3 rounded-xl shadow-lg hover:bg-slate-800 transition-all">
                            Go to Dashboard
                        </button>
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <div className="min-h-screen bg-background-light flex flex-col">
            {/* Simple Header */}
            <header className="w-full bg-surface-light border-b border-border-light sticky top-0 z-50">
                <div className="px-6 md:px-10 py-4 flex items-center justify-between max-w-7xl mx-auto">
                    <div className="flex items-center gap-3">
                        <div className="size-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                            <Icon name="dataset" />
                        </div>
                        <h1 className="text-slate-900 text-lg font-bold tracking-tight">xSmartDeepResearch</h1>
                    </div>
                </div>
            </header>

            <div className="flex-1 flex justify-center py-8 px-4 md:px-8 overflow-y-auto">
                <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-12 gap-8">

                    {/* Sidebar Stepper */}
                    <aside className="lg:col-span-3 lg:block hidden">
                        <nav aria-label="Progress" className="sticky top-24 space-y-1">
                            {STEPS.map((step) => (
                                <div key={step.id} className="relative pb-8 last:pb-0">
                                    <div className={`absolute left-[15px] top-8 bottom-0 w-0.5 ${currentStep > step.id ? 'bg-primary' : 'bg-slate-200'}`}></div>
                                    <div className="relative flex items-center group">
                                        <span className={`h-8 w-8 rounded-full flex items-center justify-center ring-4 ring-white z-10 ${currentStep >= step.id ? 'bg-primary text-white' :
                                                'border-2 border-slate-300 bg-white text-slate-500'
                                            }`}>
                                            {currentStep > step.id ? <Icon name="check" className="text-sm" /> :
                                                <span className="text-xs font-bold">{step.id}</span>
                                            }
                                        </span>
                                        <span className="ml-4 min-w-0 flex flex-col">
                                            <span className={`text-sm font-semibold tracking-wide ${currentStep === step.id ? 'text-slate-900' : 'text-slate-500'}`}>{step.label}</span>
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </nav>
                    </aside>

                    {/* Main Content */}
                    <main className="lg:col-span-9 flex flex-col">
                        <div className="bg-surface-light rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-[500px]">
                            {renderStepContent()}
                        </div>
                    </main>
                </div>
            </div>
        </div>
    );
};