import { create } from "zustand";

export type ApprovalRisk = "High" | "Medium" | "Low";
export type ApprovalStatus = "pending" | "approved" | "dismissed";

export interface Approval {
  id: string;
  company: string;
  contact: string;
  type: string;
  amount?: string;
  confidence: number;
  risk: ApprovalRisk;
  summary: string;
  status: ApprovalStatus;
  createdAt: string; // ISO string

  // Detailed view fields
  agentAction: {
    action: string;
    amount: string;
    channel: string;
    template: string;
    send_at: string;
    expected_lift: string;
    expected_roi: string;
  };
  messagePreview: {
    subject: string;
    body: string;
  };
  reasoning: {
    text: string;
    bullets: string[];
  };
  alternatives: {
    label: string;
    amount: string;
    roi: string;
    selected: boolean;
  }[];
}

interface ApprovalsState {
  items: Approval[];
  addApproval: (a: Approval) => void;
  setStatus: (id: string, status: Exclude<ApprovalStatus, "pending">) => void;
  updateMessagePreview: (id: string, preview: { subject: string; body: string }) => void;
  hydrateFromAPI: (approvals: Approval[]) => void;
}

const mockApprovals: Approval[] = [
  {
    id: "1",
    company: "Northwind Analytics",
    contact: "Sarah Chen",
    type: "Offer 25% renewal credit",
    amount: "$ 540",
    confidence: 81,
    risk: "Medium",
    summary: "Reason: Exceeds $500 autonomous ceiling",
    status: "pending",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 4).toISOString(),
    agentAction: {
      action: '"offer_credit"',
      amount: "$540",
      channel: '["email", "csm_followup"]',
      template: '"renewal_save_v3"',
      send_at: "auto · within 4h",
      expected_lift: "+18.0%",
      expected_roi: "2.7x",
    },
    messagePreview: {
      subject: "A 25% credit on your renewal — and a thank-you",
      body: "Hi Sara, — I noticed your team's been heads-down lately, and your renewal is coming up. To make the transition easier, I'd like to offer a one-time 25% credit on the next billing cycle...",
    },
    reasoning: {
      text: 'Among 6 candidate interventions, "25% renewal credit" maximized expected ROI given:',
      bullets: [
        "Past discounts on this segment have +18% retention lift",
        "Procurement signals indicate price sensitivity",
        "Renewal window opens in 41d — timing is favorable",
      ],
    },
    alternatives: [
      { label: "15% renewal credit", amount: "$324", roi: "4.2x", selected: false },
      { label: "25% renewal credit", amount: "$540", roi: "6.8x", selected: true },
      { label: "Free month + CSM call", amount: "$660", roi: "5.1x", selected: false },
      { label: "Product education only", amount: "$0", roi: "1.8x", selected: false },
      { label: "Do nothing", amount: "$0", roi: "0.0x", selected: false },
    ],
  },
  {
    id: "2",
    company: "Tessera Health",
    contact: "Mark Torres",
    type: "Schedule exec sponsor call (CEO)",
    amount: "$ 650",
    confidence: 74,
    risk: "High",
    summary: "Reason: High value account at risk of churn",
    status: "pending",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    agentAction: {
      action: '"schedule_exec_call"',
      amount: "$650",
      channel: '["email"]',
      template: '"exec_checkin_v1"',
      send_at: "auto · within 24h",
      expected_lift: "+22.0%",
      expected_roi: "3.1x",
    },
    messagePreview: {
      subject: "Checking in on your experience with RetentionOS",
      body: "Hi Mark, — As the CEO of RetentionOS, I like to personally check in with our most valued partners. I noticed a recent drop in engagement and wanted to schedule a brief call to see how we can better support Tessera Health...",
    },
    reasoning: {
      text: 'Among 4 candidate interventions, "Schedule exec sponsor call" maximized expected ROI given:',
      bullets: [
        "High ACV account with recent drop in core metric usage",
        "Previous exec touchpoints resulted in +30% expansion",
        "Key champion left the company 2 weeks ago",
      ],
    },
    alternatives: [
      { label: "Schedule exec sponsor call (CEO)", amount: "$650", roi: "3.1x", selected: true },
      { label: "Offer 15% discount", amount: "$450", roi: "2.1x", selected: false },
      { label: "Assign dedicated CSM", amount: "$0", roi: "1.5x", selected: false },
      { label: "Do nothing", amount: "$0", roi: "0.0x", selected: false },
    ],
  },
  {
    id: "3",
    company: "Helios Robotics",
    contact: "Priya Mehta",
    type: "Custom pricing proposal",
    amount: "$ 0",
    confidence: 89,
    risk: "Low",
    summary: "Reason: Expansion opportunity detected",
    status: "pending",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(),
    agentAction: {
      action: '"custom_pricing"',
      amount: "$0",
      channel: '["csm_outreach"]',
      template: '"expansion_proposal"',
      send_at: "manual review required",
      expected_lift: "+45.0%",
      expected_roi: "8.5x",
    },
    messagePreview: {
      subject: "Action required: Review custom pricing for Helios",
      body: "CSM Task: Draft a custom pricing proposal for Helios Robotics covering the new enterprise tier features they have been evaluating...",
    },
    reasoning: {
      text: 'Among 3 candidate interventions, "Custom pricing proposal" maximized expected ROI given:',
      bullets: [
        "Heavy usage of premium feature trial over last 14 days",
        "Company size grew 200% in last quarter",
        "Current plan limits reached, causing friction",
      ],
    },
    alternatives: [
      { label: "Custom pricing proposal", amount: "$0", roi: "8.5x", selected: true },
      { label: "Standard enterprise upgrade", amount: "$0", roi: "4.2x", selected: false },
      { label: "Do nothing", amount: "$0", roi: "0.0x", selected: false },
    ],
  },
];

export const useApprovalsStore = create<ApprovalsState>((set) => ({
  items: mockApprovals,
  addApproval: (approval) =>
    set((state) => ({
      items: [approval, ...state.items],
    })),
  setStatus: (id, status) =>
    set((state) => ({
      items: state.items.map((item) =>
        item.id === id ? { ...item, status } : item
      ),
    })),
  updateMessagePreview: (id, preview) =>
    set((state) => ({
      items: state.items.map((item) =>
        item.id === id ? { ...item, messagePreview: preview } : item
      ),
    })),
  hydrateFromAPI: (approvals) => set({ items: approvals }),
}));
