import { create } from "zustand";

export interface Alert {
  id: string;
  company: string;
  summary: string;
  risk: "High" | "Medium" | "Low";
  actions: string[];
}

export interface Strategy {
  id: string;
  title: string;
  successRate: number;
  impact: string;
}

interface DashboardState {
  savedRevenue: { value: string; trend: string };
  netChurnRate: { value: string; trend: string };
  aiPrecision: { value: string; context: string };
  alerts: Alert[];
  strategies: Strategy[];
  updateMetrics: (metrics: Partial<DashboardState>) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  savedRevenue: { value: "$4.2M", trend: "+12.4% vs last quarter" },
  netChurnRate: { value: "1.8%", trend: "-0.4% vs last quarter" },
  aiPrecision: { value: "94.2%", context: "High Confidence in latest cohort" },
  alerts: [
    {
      id: "1",
      company: "Acme Corp",
      risk: "High",
      summary: "Renewal in 14 days. AI suggests immediate executive outreach.",
      actions: ["Ignore", "Approve Outreach"],
    },
    {
      id: "2",
      company: "Globex Inc",
      risk: "Medium",
      summary: "Usage dropped 30%. Discount approval requested.",
      actions: ["Ignore", "Approve 10%"],
    },
    {
      id: "3",
      company: "Hooli AI",
      risk: "High",
      summary: "Champion left org. Auto-escalated to relationship manager.",
      actions: ["Ignore", "Approve CSM"],
    },
    {
      id: "4",
      company: "Initech",
      risk: "Low",
      summary: "Usage stable. No action required.",
      actions: ["Dismiss"],
    },
  ],
  strategies: [
    {
      id: "1",
      title: "Executive Check-in",
      successRate: 68,
      impact: "+$1.2M",
    },
    {
      id: "2",
      title: "Targeted Discount",
      successRate: 52,
      impact: "+$800k",
    },
    {
      id: "3",
      title: "Training Webinar",
      successRate: 45,
      impact: "+$450k",
    },
    {
      id: "4",
      title: "In-app Education",
      successRate: 38,
      impact: "+$210k",
    },
  ],
  updateMetrics: (metrics) => set((state) => ({ ...state, ...metrics })),
}));
