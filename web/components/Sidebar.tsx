import React, { useContext } from 'react';
import { View, NavItem } from '../types';
import { Icon } from './Icon';
import { LanguageContext } from '../App';

// Injected by Vite at build time from VERSION file
declare const __APP_VERSION__: string;
const APP_VERSION = typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : 'dev';

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
          <div className="flex gap-3 items-center cursor-pointer overflow-hidden group" onClick={() => onChangeView(View.DASHBOARD)}>
            <div className="flex items-center justify-center size-8 rounded-lg bg-zinc-900 text-white shrink-0 shadow-sm border border-zinc-700">
              <Icon name="psychology" className="text-[18px]" />
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
                  className={`flex items-center rounded-md transition-all group w-full text-left
                    ${isCollapsed ? 'justify-center p-2' : 'gap-2.5 px-2.5 py-1.5'}
                    ${isActive
                      ? 'bg-zinc-100 text-zinc-900 font-medium'
                      : 'text-zinc-500 hover:bg-zinc-50 hover:text-zinc-900'
                    }`}
                  title={isCollapsed ? item.label : ''}
                >
                  <Icon
                    name={item.icon}
                    className={isActive ? 'text-[18px]' : 'text-[18px] group-hover:text-zinc-900 transition-colors'}
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
          </nav>
        </div>

        {/* Action Button & User */}
        <div className="flex flex-col gap-4">
          <button
            onClick={onNewResearch}
            className={`flex w-full cursor-pointer items-center justify-center rounded-md h-8 bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-medium shadow-sm transition-all active:scale-95 border border-transparent
              ${isCollapsed ? 'px-0' : 'gap-2 px-3'}`}
            title={isCollapsed ? t('newResearch') : ""}
          >
            <Icon name="add" className="text-[16px] shrink-0" />
            {!isCollapsed && <span className="truncate whitespace-nowrap animate-in fade-in duration-500">{t('newResearch')}</span>}
          </button>

          {/* Language Toggle */}
          <div className={`flex items-center border border-zinc-200 rounded-md p-0.5 bg-zinc-50 ${isCollapsed ? 'flex-col gap-1' : 'flex-row'}`}>
            <button
              onClick={() => setLanguage('en')}
              className={`flex-1 text-[10px] font-semibold py-0.5 px-1 rounded-sm transition-colors ${language === 'en' ? 'bg-white shadow-sm text-zinc-900 border border-zinc-200' : 'text-zinc-400 hover:text-zinc-600'}`}
            >
              EN
            </button>
            <button
              onClick={() => setLanguage('zh')}
              className={`flex-1 text-[10px] font-semibold py-0.5 px-1 rounded-sm transition-colors ${language === 'zh' ? 'bg-white shadow-sm text-zinc-900 border border-zinc-200' : 'text-zinc-400 hover:text-zinc-600'}`}
            >
              CN
            </button>
          </div>

          <div className={`mt-2 pt-3 border-t border-zinc-100 flex items-center overflow-hidden ${isCollapsed ? 'justify-center' : 'gap-2.5'}`}>
            <img
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuBHhP4ZO5jZAlhN9Qgy_fElOqtFUsxSl7RMktYjKzvAv-3iMJVEypMosS2jfV9Kjl0lqmLZPpABOMAbO0Vr0ITdqs6mwYspObXMHsLOAwx6Pwab1nfXYQnrMwPpQpDEh-nkokwYf4EAaYwS_aPOTAJcVqRiCJZEbFLrHv7C2IdRxZ5Cpr1zlomAqAIeD50-JAWq3O6vKvcrMbYkN1mo9WKtE586DqPthXHTJ5_fz9gHamOUAvARgCK_BB9Pwcuz-cmveSGCiUKKKw"
              alt="User"
              className="size-6 rounded-full border border-zinc-200 shrink-0 grayscale hover:grayscale-0 transition-all opacity-80 hover:opacity-100"
            />
            {!isCollapsed && (
              <div className="flex-1 min-w-0 animate-in fade-in duration-500">
                <p className="text-xs font-medium text-zinc-700 truncate">Dr. Researcher</p>
              </div>
            )}
          </div>

          {/* Version Display */}
          <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-1.5'}`} title={`Version ${APP_VERSION}`}>
            <Icon name="info" className="text-[14px] text-zinc-300" />
            {!isCollapsed && (
              <span className="text-[10px] text-zinc-400 font-mono tracking-wide animate-in fade-in duration-500">
                v{APP_VERSION}
              </span>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
};