import { Approval } from "@/store/approvals-store";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchApprovals(): Promise<Approval[]> {
  const response = await fetch(`${API_URL}/api/approvals`);
  if (!response.ok) {
    throw new Error("Failed to fetch approvals");
  }
  return response.json();
}

export async function patchApprovalMessage(id: string, subject: string, body: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/approvals/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ subject, body }),
  });
  if (!response.ok) {
    throw new Error("Failed to patch approval message");
  }
}

export async function postApprovalStatus(id: string, status: "approved" | "dismissed"): Promise<void> {
  const response = await fetch(`${API_URL}/api/approvals/${id}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!response.ok) {
    throw new Error("Failed to post approval status");
  }
}

export async function startIntervention(payload: any): Promise<void> {
  const response = await fetch(`${API_URL}/api/interventions/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to start intervention");
  }
}

export async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.statusText}`);
  }
  return response.json();
}
