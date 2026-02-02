import React, { useState } from 'react';
import { View } from './types';
import { Sidebar } from './components/Sidebar';
import { HistoryScreen } from './screens/HistoryScreen';
import { LiveResearchScreen } from './screens/LiveResearchScreen';
import { SettingsScreen } from './screens/SettingsScreen';
import { ResearchDetailScreen } from './screens/ResearchDetailScreen';
import { SavedReportsScreen } from './screens/SavedReportsScreen';
import { SetupWizard } from './screens/SetupWizard';
import { ErrorModal } from './components/ErrorModal';
import { ResearchHistoryItem } from './services/api';
import { Language, translations, TranslationKeys } from './utils/i18n';
import { ResearchProvider } from './contexts/ResearchContext';
import { ToastProvider } from './contexts/ToastContext';

// Language Context
interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: TranslationKeys) => string;
}

export const LanguageContext = React.createContext<LanguageContextType>({
  language: 'en',
  setLanguage: () => { },
  t: (key) => translations.en[key] as string,
});

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>(View.HISTORY);
  const [isErrorModalOpen, setIsErrorModalOpen] = useState(false);
  const [selectedResearch, setSelectedResearch] = useState<ResearchHistoryItem | null>(null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [language, setLanguage] = useState<Language>('en');

  const t = (key: TranslationKeys): string => {
    return (translations[language] as any)[key] || (translations.en as any)[key] || key;
  };

  const handleHistorySelect = (item: ResearchHistoryItem) => {
    setSelectedResearch(item);
    setCurrentView(View.DETAIL);
  };

  const handleBackToHistory = () => {
    setSelectedResearch(null);
    setCurrentView(View.HISTORY);
  };

  // Simple Router
  const renderContent = () => {
    switch (currentView) {
      case View.HISTORY:
        return <HistoryScreen onSelect={handleHistorySelect} />;
      case View.DETAIL:
        return selectedResearch ? (
          <ResearchDetailScreen item={selectedResearch} onBack={handleBackToHistory} />
        ) : (
          <div className="flex items-center justify-center h-full">Error: No item selected</div>
        );
      case View.SAVED_REPORTS:
        return <SavedReportsScreen onSelect={handleHistorySelect} />;
      case View.DASHBOARD:
        return <LiveResearchScreen />;
      case View.SETTINGS:
        return <SettingsScreen onShowError={() => setIsErrorModalOpen(true)} />;
      case View.WIZARD:
        return <SetupWizard onComplete={() => setCurrentView(View.DASHBOARD)} />;
      default:
        // Fallback for screens not implemented in this demo
        return (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <span className="material-symbols-outlined text-6xl mb-4 text-slate-300">construction</span>
            <p>This view ({currentView}) is under construction.</p>
          </div>
        );
    }
  };

  // Setup Wizard takes over the full screen
  if (currentView === View.WIZARD) {
    return (
      <>
        <SetupWizard />
        {/* Floating button to exit wizard for demo purposes */}
        <button
          onClick={() => setCurrentView(View.HISTORY)}
          className="fixed bottom-4 left-4 z-50 bg-slate-800 text-white px-4 py-2 rounded-full text-xs opacity-50 hover:opacity-100 transition-opacity"
        >
          Exit Wizard Demo
        </button>
      </>
    );
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      <ToastProvider>
        <ResearchProvider>
          <div className="flex h-screen w-full bg-background-light">
            <Sidebar
              currentView={currentView}
              isCollapsed={isSidebarCollapsed}
              onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
              onChangeView={setCurrentView}
              onNewResearch={() => setCurrentView(View.DASHBOARD)}
            />
            <main className="flex-1 min-w-0 h-full overflow-hidden relative">
              {renderContent()}
            </main>

            {isErrorModalOpen && (
              <ErrorModal onClose={() => setIsErrorModalOpen(false)} />
            )}
          </div>
        </ResearchProvider>
      </ToastProvider>
    </LanguageContext.Provider>
  );
};

export default App;