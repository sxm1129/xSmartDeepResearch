export enum View {
  DASHBOARD = 'DASHBOARD',
  HISTORY = 'HISTORY',
  AGENTS = 'AGENTS',
  SETTINGS = 'SETTINGS',
  SAVED_REPORTS = 'SAVED_REPORTS',
  WIZARD = 'WIZARD',
  DETAIL = 'DETAIL'
}

export interface ResearchItem {
  id: string;
  title: string;
  description: string;
  status: 'Completed' | 'Processing' | 'Failed';
  timeAgo: string;
  meta: string;
}

export interface NavItem {
  icon: string;
  label: string;
  view: View;
  activeIcon?: string;
}

export interface ResearchResult {
  question: string;
  answer: string;
  messages: any[];
  iterations: number;
  execution_time: number;
  termination: string;
}