import React from 'react';
import { View, NavItem } from '../types';
import { Icon } from './Icon';

interface SidebarProps {
  currentView: View;
  onChangeView: (view: View) => void;
  onNewResearch: () => void;
}

const NAV_ITEMS: NavItem[] = [
  { icon: 'grid_view', label: 'Dashboard', view: View.DASHBOARD },
  { icon: 'history', label: 'History', view: View.HISTORY, activeIcon: 'history' },
  { icon: 'description', label: 'Saved Reports', view: View.SAVED_REPORTS },
  { icon: 'settings', label: 'Settings', view: View.SETTINGS },
];

export const Sidebar: React.FC<SidebarProps> = ({ currentView, onChangeView, onNewResearch }) => {
  return (
    <aside className="w-64 bg-surface-light border-r border-border-light flex flex-col h-full shrink-0">
      <div className="p-6 flex flex-col h-full justify-between">
        {/* Logo & Nav */}
        <div className="flex flex-col gap-8">
          {/* Logo */}
          <div className="flex gap-3 items-center cursor-pointer" onClick={() => onChangeView(View.DASHBOARD)}>
            <div className="bg-primary/10 flex items-center justify-center aspect-square rounded-full size-10 text-primary">
              <Icon name="psychology" className="text-[24px]" />
            </div>
            <div className="flex flex-col">
              <h1 className="text-slate-900 text-base font-bold leading-none">xSmart</h1>
              <p className="text-primary text-xs font-semibold uppercase tracking-wider mt-1">DeepResearch</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex flex-col gap-2">
            {NAV_ITEMS.map((item) => {
              const isActive = currentView === item.view;
              return (
                <button
                  key={item.view}
                  onClick={() => onChangeView(item.view)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group w-full text-left
                    ${isActive
                      ? 'bg-primary/10 text-primary'
                      : 'text-slate-600 hover:bg-slate-100'
                    }`}
                >
                  <Icon
                    name={item.icon}
                    className={isActive ? 'text-[22px] font-bold' : 'text-[22px] group-hover:text-primary transition-colors'}
                    fill={isActive}
                  />
                  <span className={`text-sm ${isActive ? 'font-bold' : 'font-medium'}`}>
                    {item.label}
                  </span>
                </button>
              );
            })}

            {/* Extra link for Wizard Demo */}
            <button
              onClick={() => onChangeView(View.WIZARD)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group w-full text-left
                    ${currentView === View.WIZARD
                  ? 'bg-primary/10 text-primary'
                  : 'text-slate-600 hover:bg-slate-100'
                }`}
            >
              <Icon name="auto_fix_high" className={`text-[22px] ${currentView === View.WIZARD ? '' : 'group-hover:text-primary'}`} />
              <span className="text-sm font-medium">Setup Wizard</span>
            </button>
          </nav>
        </div>

        {/* Action Button */}
        <div>
          <button
            onClick={onNewResearch}
            className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-lg h-10 px-4 bg-primary hover:bg-primary-dark text-white text-sm font-bold shadow-lg shadow-primary/30 transition-all active:scale-95"
          >
            <Icon name="add" className="text-[20px]" />
            <span className="truncate">New Research</span>
          </button>

          <div className="mt-6 pt-4 border-t border-slate-200 flex items-center gap-3">
            <img
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuBHhP4ZO5jZAlhN9Qgy_fElOqtFUsxSl7RMktYjKzvAv-3iMJVEypMosS2jfV9Kjl0lqmLZPpABOMAbO0Vr0ITdqs6mwYspObXMHsLOAwx6Pwab1nfXYQnrMwPpQpDEh-nkokwYf4EAaYwS_aPOTAJcVqRiCJZEbFLrHv7C2IdRxZ5Cpr1zlomAqAIeD50-JAWq3O6vKvcrMbYkN1mo9WKtE586DqPthXHTJ5_fz9gHamOUAvARgCK_BB9Pwcuz-cmveSGCiUKKKw"
              alt="User"
              className="w-8 h-8 rounded-full border border-slate-200"
            />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">Dr. Researcher</p>
              <p className="text-xs text-slate-500 truncate">Pro Plan</p>
            </div>
            <Icon name="settings" className="text-slate-400 text-[18px]" />
          </div>
        </div>
      </div>
    </aside>
  );
};