import { create } from "zustand";

export type ChurnDriverDirection = "risk" | "protective";
export type LiftDecileTier = "high" | "mid" | "low";

export interface ChurnDriver {
  label: string;
  n: number;
  effectPp: number;
  direction: ChurnDriverDirection;
}

export interface QiniPoint {
  pctTreated: number;
  model: number;
  baseline: number;
  random: number;
}

export interface CalibrationPoint {
  predicted: number;
  observed: number;
}

export interface UpliftBucket {
  bucket: string;
  control: number;
  treated: number;
}

export interface ShapFeature {
  feature: string;
  value: number;
}

export interface HeatmapCell {
  segment: string;
  treatment: string;
  lift: number;
}

export interface AuucWeek {
  week: string;
  auuc: number;
}

export interface PolicyBar {
  policy: string;
  value: number;
  colorKey: "primary" | "warning" | "info" | "ai" | "muted";
}

export interface ConfusionMatrix {
  tp: number;
  fp: number;
  fn: number;
  tn: number;
  precision: number;
  recall: number;
  f1: number;
}

export interface LiftDecile {
  decile: string;
  lift: number;
  tier: LiftDecileTier;
}

export interface DagNode {
  id: string;
  label: string;
  x: number;
  y: number;
}

export interface DagEdge {
  from: string;
  to: string;
  dashed?: boolean;
  danger?: boolean;
}

export interface HoldoutOutcome {
  label: string;
  value: string;
  trend: "up" | "down" | "flat";
  sparkline: number[];
}

export interface CausalModelSummary {
  modelVersion: string;
  auuc: number;
  auucDelta: number;
  calibration: number;
  coverage: number;
  coverageDelta: number;
  driftPsi: number;
  lastRetrain: string;
  outcomes: number;
}

export interface CausalModelState {
  summary: CausalModelSummary;
  churnDrivers: ChurnDriver[];
  qiniCurve: QiniPoint[];
  calibration: CalibrationPoint[];
  upliftDistribution: UpliftBucket[];
  featureImportance: ShapFeature[];
  treatmentHeatmap: HeatmapCell[];
  heatmapSegments: string[];
  heatmapTreatments: string[];
  auucOverTime: AuucWeek[];
  auucTarget: number;
  policyValue: PolicyBar[];
  confusion: ConfusionMatrix;
  liftDeciles: LiftDecile[];
  dagNodes: DagNode[];
  dagEdges: DagEdge[];
  holdoutOutcomes: HoldoutOutcome[];
  retrainInProgress: boolean;
  setSnapshot: (partial: Partial<Omit<CausalModelState, "setSnapshot" | "setRetrainInProgress">>) => void;
  setRetrainInProgress: (v: boolean) => void;
}

const initialState: Omit<CausalModelState, "setSnapshot" | "setRetrainInProgress"> = {
  summary: {
    modelVersion: "v2.3",
    auuc: 0.71,
    auucDelta: 0.04,
    calibration: 0.94,
    coverage: 98.2,
    coverageDelta: 1.4,
    driftPsi: 0.04,
    lastRetrain: "2h ago",
    outcomes: 12847,
  },
  churnDrivers: [
    { label: "Champion departure", n: 412, effectPp: 18, direction: "risk" },
    { label: "Activation incomplete (30d)", n: 1820, effectPp: 12, direction: "risk" },
    { label: "Support ticket: pricing", n: 284, effectPp: 16, direction: "risk" },
    { label: "API errors > 10/week", n: 156, effectPp: 9, direction: "risk" },
    { label: "Seat count decline", n: 312, effectPp: 14, direction: "risk" },
    { label: "NPS drop > 3pts", n: 412, effectPp: 7, direction: "risk" },
    { label: "Recent integration added", n: 612, effectPp: 11, direction: "protective" },
    { label: "Multi-team adoption", n: 412, effectPp: 8, direction: "protective" },
  ],
  qiniCurve: [
    { pctTreated: 0, model: 0, baseline: 0, random: 0 },
    { pctTreated: 10, model: 0.12, baseline: 0.08, random: 0.05 },
    { pctTreated: 20, model: 0.24, baseline: 0.16, random: 0.1 },
    { pctTreated: 30, model: 0.36, baseline: 0.24, random: 0.15 },
    { pctTreated: 40, model: 0.48, baseline: 0.32, random: 0.2 },
    { pctTreated: 50, model: 0.58, baseline: 0.4, random: 0.25 },
    { pctTreated: 60, model: 0.66, baseline: 0.48, random: 0.3 },
    { pctTreated: 70, model: 0.72, baseline: 0.56, random: 0.35 },
    { pctTreated: 80, model: 0.76, baseline: 0.64, random: 0.4 },
    { pctTreated: 90, model: 0.78, baseline: 0.72, random: 0.45 },
    { pctTreated: 100, model: 0.8, baseline: 0.8, random: 0.5 },
  ],
  calibration: [
    { predicted: 0.1, observed: 0.09 },
    { predicted: 0.2, observed: 0.19 },
    { predicted: 0.3, observed: 0.31 },
    { predicted: 0.4, observed: 0.38 },
    { predicted: 0.5, observed: 0.52 },
    { predicted: 0.6, observed: 0.58 },
    { predicted: 0.7, observed: 0.71 },
    { predicted: 0.8, observed: 0.79 },
    { predicted: 0.9, observed: 0.88 },
  ],
  upliftDistribution: [
    { bucket: "-0.2", control: 0.08, treated: 0.04 },
    { bucket: "-0.1", control: 0.12, treated: 0.07 },
    { bucket: "0", control: 0.18, treated: 0.14 },
    { bucket: "0.1", control: 0.16, treated: 0.22 },
    { bucket: "0.2", control: 0.14, treated: 0.28 },
    { bucket: "0.3", control: 0.1, treated: 0.32 },
    { bucket: "0.4", control: 0.08, treated: 0.36 },
    { bucket: "0.5", control: 0.06, treated: 0.38 },
  ],
  featureImportance: [
    { feature: "Login frequency Δ", value: 0.34 },
    { feature: "Champion departed", value: 0.31 },
    { feature: "Support ticket vol.", value: 0.27 },
    { feature: "Seat utilization", value: 0.24 },
    { feature: "Plan tier", value: 0.22 },
    { feature: "NPS score", value: 0.18 },
    { feature: "Integration count", value: 0.16 },
    { feature: "Tenure (months)", value: 0.14 },
    { feature: "Last release adopted", value: 0.11 },
    { feature: "Pricing page visits", value: 0.09 },
  ],
  heatmapSegments: ["Enterprise", "Mid-mkt", "SMB", "Trial"],
  heatmapTreatments: ["Email", "In-app", "Discount", "CSM", "Exec"],
  treatmentHeatmap: [
    { segment: "Enterprise", treatment: "Email", lift: 12 },
    { segment: "Enterprise", treatment: "In-app", lift: 18 },
    { segment: "Enterprise", treatment: "Discount", lift: 24 },
    { segment: "Enterprise", treatment: "CSM", lift: 22 },
    { segment: "Enterprise", treatment: "Exec", lift: 20 },
    { segment: "Mid-mkt", treatment: "Email", lift: 10 },
    { segment: "Mid-mkt", treatment: "In-app", lift: 14 },
    { segment: "Mid-mkt", treatment: "Discount", lift: 18 },
    { segment: "Mid-mkt", treatment: "CSM", lift: 16 },
    { segment: "Mid-mkt", treatment: "Exec", lift: 12 },
    { segment: "SMB", treatment: "Email", lift: 8 },
    { segment: "SMB", treatment: "In-app", lift: 10 },
    { segment: "SMB", treatment: "Discount", lift: 14 },
    { segment: "SMB", treatment: "CSM", lift: 8 },
    { segment: "SMB", treatment: "Exec", lift: 6 },
    { segment: "Trial", treatment: "Email", lift: 4 },
    { segment: "Trial", treatment: "In-app", lift: 6 },
    { segment: "Trial", treatment: "Discount", lift: 8 },
    { segment: "Trial", treatment: "CSM", lift: 4 },
    { segment: "Trial", treatment: "Exec", lift: 2 },
  ],
  auucOverTime: [
    { week: "W1", auuc: 0.58 },
    { week: "W2", auuc: 0.6 },
    { week: "W3", auuc: 0.61 },
    { week: "W4", auuc: 0.63 },
    { week: "W5", auuc: 0.64 },
    { week: "W6", auuc: 0.65 },
    { week: "W7", auuc: 0.66 },
    { week: "W8", auuc: 0.67 },
    { week: "W9", auuc: 0.68 },
    { week: "W10", auuc: 0.69 },
    { week: "W11", auuc: 0.7 },
    { week: "W12", auuc: 0.71 },
  ],
  auucTarget: 0.73,
  policyValue: [
    { policy: "RetentionOS", value: 1.0, colorKey: "primary" },
    { policy: "Risk-only", value: 0.62, colorKey: "warning" },
    { policy: "Send-to-all", value: 0.31, colorKey: "info" },
    { policy: "Human playbook", value: 0.74, colorKey: "ai" },
    { policy: "Do nothing", value: 0.0, colorKey: "muted" },
  ],
  confusion: {
    tp: 412,
    fp: 84,
    fn: 67,
    tn: 1721,
    precision: 0.83,
    recall: 0.86,
    f1: 0.84,
  },
  liftDeciles: [
    { decile: "01", lift: 3.8, tier: "high" },
    { decile: "02", lift: 2.9, tier: "high" },
    { decile: "03", lift: 2.1, tier: "mid" },
    { decile: "04", lift: 1.6, tier: "mid" },
    { decile: "05", lift: 1.2, tier: "low" },
    { decile: "06", lift: 1.0, tier: "low" },
    { decile: "07", lift: 0.9, tier: "low" },
    { decile: "08", lift: 0.85, tier: "low" },
    { decile: "09", lift: 0.82, tier: "low" },
    { decile: "10", lift: 0.8, tier: "low" },
  ],
  dagNodes: [
    { id: "activity", label: "Activity", x: 40, y: 30 },
    { id: "champion", label: "Champion", x: 40, y: 100 },
    { id: "nps", label: "NPS", x: 160, y: 65 },
    { id: "churn", label: "Churn risk", x: 280, y: 65 },
    { id: "intervention", label: "Intervention", x: 400, y: 30 },
    { id: "retained", label: "Retained", x: 400, y: 110 },
  ],
  dagEdges: [
    { from: "activity", to: "nps" },
    { from: "champion", to: "nps" },
    { from: "nps", to: "churn" },
    { from: "churn", to: "intervention" },
    { from: "intervention", to: "retained" },
    { from: "churn", to: "retained", dashed: true, danger: true },
  ],
  holdoutOutcomes: [
    { label: "RETAINED", value: "+42/day", trend: "up", sparkline: [20, 24, 28, 32, 36, 40, 42] },
    { label: "CONVERSION", value: "62%", trend: "up", sparkline: [48, 52, 54, 56, 58, 60, 62] },
    { label: "COST / SAVE", value: "$12", trend: "down", sparkline: [18, 16, 15, 14, 13, 12, 12] },
    { label: "LATENCY", value: "1.2s", trend: "flat", sparkline: [1.4, 1.3, 1.2, 1.3, 1.2, 1.2, 1.2] },
  ],
  retrainInProgress: false,
};

export const useCausalModelStore = create<CausalModelState>((set) => ({
  ...initialState,
  setSnapshot: (partial) => set((state) => ({ ...state, ...partial })),
  setRetrainInProgress: (retrainInProgress) => set({ retrainInProgress }),
}));
