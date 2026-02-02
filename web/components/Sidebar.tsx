import React, { useContext } from 'react';
import { View, NavItem } from '../types';
import { Icon } from './Icon';
import { LanguageContext } from '../App';

interface SidebarProps {
  currentView: View;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onChangeView: (view: View) => void;
  onNewResearch: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentView, isCollapsed, onToggleCollapse, onChangeView, onNewResearch }) => {
  const { language, setLanguage, t } = useContext(LanguageContext);

  const navItems: NavItem[] = [
    { icon: 'grid_view', label: t('dashboard'), view: View.DASHBOARD },
    { icon: 'history', label: t('history'), view: View.HISTORY, activeIcon: 'history' },
    { icon: 'description', label: t('savedReports'), view: View.SAVED_REPORTS },
    { icon: 'settings', label: t('settings'), view: View.SETTINGS },
  ];

  return (
    <aside className={`${isCollapsed ? 'w-20' : 'w-64'} bg-surface-light border-r border-border-light flex flex-col h-full shrink-0 transition-all duration-300 ease-in-out relative group/sidebar`}>
      {/* Collapse Toggle Button */}
      <button
        onClick={onToggleCollapse}
        className="absolute -right-3 top-20 bg-white border border-slate-200 rounded-full p-1 shadow-sm hover:shadow-md hover:text-primary transition-all z-20"
        title={isCollapsed ? t('expandSidebar') : t('collapseSidebar')}
      >
        <span className={`material-symbols-outlined text-sm transform transition-transform duration-300 ${isCollapsed ? 'rotate-180' : ''}`}>
          chevron_left
        </span>
      </button>

      <div className={`flex flex-col h-full justify-between ${isCollapsed ? 'p-3' : 'p-6'}`}>
        {/* Logo & Nav */}
        <div className="flex flex-col gap-8">
          {/* Logo */}
          <div className="flex gap-3 items-center cursor-pointer overflow-hidden" onClick={() => onChangeView(View.DASHBOARD)}>
            <div className="bg-primary/10 flex items-center justify-center aspect-square rounded-full size-10 text-primary shrink-0">
              <Icon name="psychology" className="text-[24px]" />
            </div>
            {!isCollapsed && (
              <div className="flex flex-col whitespace-nowrap animate-in fade-in duration-500">
                <h1 className="text-slate-900 text-base font-bold leading-none">xSmart</h1>
                <p className="text-primary text-xs font-semibold uppercase tracking-wider mt-1">DeepResearch</p>
              </div>
            )}
          </div>

          {/* Navigation */}
          <nav className="flex flex-col gap-2">
            {navItems.map((item) => {
              const isActive = currentView === item.view;
              return (
                <button
                  key={item.view}
                  onClick={() => onChangeView(item.view)}
                  className={`flex items-center rounded-lg transition-colors group w-full text-left
                    ${isCollapsed ? 'justify-center p-2.5' : 'gap-3 px-3 py-2.5'}
                    ${isActive
                      ? 'bg-primary/10 text-primary'
                      : 'text-slate-600 hover:bg-slate-100'
                    }`}
                  title={isCollapsed ? item.label : ''}
                >
                  <Icon
                    name={item.icon}
                    className={isActive ? 'text-[22px] font-bold' : 'text-[22px] group-hover:text-primary transition-colors'}
                    fill={isActive}
                  />
                  {!isCollapsed && (
                    <span className={`text-sm whitespace-nowrap animate-in slide-in-from-left-1 duration-300 ${isActive ? 'font-bold' : 'font-medium'}`}>
                      {item.label}
                    </span>
                  )}
                </button>
              );
            })}

            {/* Extra link for Wizard Demo */}
            <button
              onClick={() => onChangeView(View.WIZARD)}
              className={`flex items-center rounded-lg transition-colors group w-full text-left
                    ${isCollapsed ? 'justify-center p-2.5' : 'gap-3 px-3 py-2.5'}
                    ${currentView === View.WIZARD
                  ? 'bg-primary/10 text-primary'
                  : 'text-slate-600 hover:bg-slate-100'
                }`}
              title={isCollapsed ? t('setupWizard') : ""}
            >
              <Icon name="auto_fix_high" className={`text-[22px] ${currentView === View.WIZARD ? '' : 'group-hover:text-primary'}`} />
              {!isCollapsed && (
                <span className="text-sm font-medium whitespace-nowrap animate-in slide-in-from-left-1 duration-300">{t('setupWizard')}</span>
              )}
            </button>
          </nav>
        </div>

        {/* Action Button & Language Toggle */}
        <div className="flex flex-col gap-4">
          <button
            onClick={onNewResearch}
            className={`flex w-full cursor-pointer items-center justify-center rounded-lg h-10 bg-primary hover:bg-primary-dark text-white text-sm font-bold shadow-lg shadow-primary/30 transition-all active:scale-95
              ${isCollapsed ? 'px-0' : 'gap-2 px-4'}`}
            title={isCollapsed ? t('newResearch') : ""}
          >
            <Icon name="add" className="text-[20px] shrink-0" />
            {!isCollapsed && <span className="truncate whitespace-nowrap animate-in fade-in duration-500">{t('newResearch')}</span>}
          </button>

          {/* Language Toggle */}
          <div className={`flex items-center border border-slate-200 rounded-lg p-1 bg-slate-50 ${isCollapsed ? 'flex-col gap-1' : 'flex-row'}`}>
            <button
              onClick={() => setLanguage('en')}
              className={`flex-1 text-[10px] font-bold py-1 px-1 rounded transition-colors ${language === 'en' ? 'bg-white shadow-sm text-primary border border-slate-100' : 'text-slate-400 hover:text-slate-600'}`}
            >
              EN
            </button>
            <button
              onClick={() => setLanguage('zh')}
              className={`flex-1 text-[10px] font-bold py-1 px-1 rounded transition-colors ${language === 'zh' ? 'bg-white shadow-sm text-primary border border-slate-100' : 'text-slate-400 hover:text-slate-600'}`}
            >
              中文
            </button>
          </div>

          <div className={`mt-2 pt-4 border-t border-slate-200 flex items-center overflow-hidden ${isCollapsed ? 'justify-center' : 'gap-3'}`}>
            <img
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuBHhP4ZO5jZAlhN9Qgy_fElOqtFUsxSl7RMktYjKzvAv-3iMJVEypMosS2jfV9Kjl0lqmLZPpABOMAbO0Vr0ITdqs6mwYspObXMHsLOAwx6Pwab1nfXYQnrMwPpQpDEh-nkokwYf4EAaYwS_aPOTAJcVqRiCJZEbFLrHv7C2IdRxZ5Cpr1zlomAqAIeD50-JAWq3O6vKvcrMbYkN1mo9WKtE586DqPthXHTJ5_fz9gHamOUAvARgCK_BB9Pwcuz-cmveSGCiUKKKw"
              alt="User"
              className="w-8 h-8 rounded-full border border-slate-200 shrink-0"
            />
            {!isCollapsed && (
              <div className="flex-1 min-w-0 animate-in fade-in duration-500">
                <p className="text-sm font-medium text-slate-900 truncate">Dr. Researcher</p>
                <p className="text-xs text-slate-500 truncate">{t('proPlan')}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
};