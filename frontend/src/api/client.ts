/**
 * API Client for Smart Financial Coach Backend
 * 
 * Provides typed fetch wrappers for all backend endpoints.
 * Handles errors consistently and returns typed responses.
 */

import type {
  UploadResponse,
  AnalyzeResponse,
  DashboardResponse,
  GoalResponse,
  Transaction,
  Category,
  ChatResponse,
  SuggestedPromptsResponse,
  ConversationHistory,
} from '../types';

// Base URL for API requests
const API_BASE = 'http://localhost:8000';

// =============================================================================
// Error Handling
// =============================================================================

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorBody = await response.text();
    let details: string | undefined;
    
    try {
      const parsed = JSON.parse(errorBody);
      details = parsed.detail || parsed.message;
    } catch {
      details = errorBody;
    }
    
    throw new ApiError(
      `API Error: ${response.status}`,
      response.status,
      details
    );
  }
  
  return response.json();
}

// =============================================================================
// Health Check
// =============================================================================

export interface HealthStatus {
  status: string;
  database: string;
  openai: string;
}

export async function checkHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE}/health`);
  return handleResponse<HealthStatus>(response);
}

// =============================================================================
// Upload Endpoints
// =============================================================================

/**
 * Upload a CSV file for processing.
 */
export async function uploadCSV(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });
  
  return handleResponse<UploadResponse>(response);
}

/**
 * Load sample transaction data for demo.
 */
export async function useSampleData(): Promise<UploadResponse> {
  const response = await fetch(`${API_BASE}/sample`, {
    method: 'POST',
  });
  
  return handleResponse<UploadResponse>(response);
}

// =============================================================================
// Analysis Endpoint
// =============================================================================

/**
 * Run full analysis on uploaded transactions.
 * This triggers categorization, anomaly detection, recurring detection, and insight generation.
 */
export async function analyzeSession(sessionId: string): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE}/analyze/${sessionId}`, {
    method: 'POST',
  });
  
  return handleResponse<AnalyzeResponse>(response);
}

// =============================================================================
// Dashboard Endpoint
// =============================================================================

/**
 * Get consolidated dashboard data for a session.
 */
export async function getDashboard(sessionId: string): Promise<DashboardResponse> {
  const response = await fetch(`${API_BASE}/dashboard/${sessionId}`);
  return handleResponse<DashboardResponse>(response);
}

// =============================================================================
// Goal Endpoint
// =============================================================================

/**
 * Get AI-powered savings goal recommendations.
 */
export async function getGoalRecommendations(
  sessionId: string,
  targetAmount: number
): Promise<GoalResponse> {
  const response = await fetch(`${API_BASE}/goal/${sessionId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ target_amount: targetAmount }),
  });
  
  return handleResponse<GoalResponse>(response);
}

// =============================================================================
// Transaction Endpoints
// =============================================================================

/**
 * Get paginated transactions for a session.
 */
export async function getTransactions(
  sessionId: string,
  limit: number = 100,
  offset: number = 0
): Promise<Transaction[]> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });
  
  const response = await fetch(
    `${API_BASE}/transactions/${sessionId}?${params}`
  );
  
  return handleResponse<Transaction[]>(response);
}

// =============================================================================
// Category Endpoints
// =============================================================================

/**
 * Get all available categories.
 */
export async function getCategories(): Promise<Category[]> {
  const response = await fetch(`${API_BASE}/categories`);
  return handleResponse<Category[]>(response);
}

// =============================================================================
// Convenience: Full Flow
// =============================================================================

/**
 * Upload, analyze, and get dashboard in one flow.
 * Returns the dashboard data after full processing.
 */
export async function uploadAndAnalyze(
  file: File,
  onProgress?: (step: string) => void
): Promise<DashboardResponse> {
  // Step 1: Upload
  onProgress?.('Uploading file...');
  const uploadResult = await uploadCSV(file);
  
  // Step 2: Analyze
  onProgress?.('Analyzing transactions...');
  await analyzeSession(uploadResult.session_id);
  
  // Step 3: Get dashboard
  onProgress?.('Loading dashboard...');
  return getDashboard(uploadResult.session_id);
}

/**
 * Use sample data, analyze, and get dashboard.
 */
export async function loadSampleAndAnalyze(
  onProgress?: (step: string) => void
): Promise<DashboardResponse> {
  // Step 1: Load sample data
  onProgress?.('Loading sample data...');
  const uploadResult = await useSampleData();
  
  // Step 2: Analyze
  onProgress?.('Analyzing transactions...');
  await analyzeSession(uploadResult.session_id);
  
  // Step 3: Get dashboard
  onProgress?.('Loading dashboard...');
  return getDashboard(uploadResult.session_id);
}

// =============================================================================
// Chat Endpoints
// =============================================================================

/**
 * Send a chat message (non-streaming).
 * Use this when you don't need streaming responses.
 */
export async function sendChatMessage(
  sessionId: string,
  message: string,
  conversationId?: string | null
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat/${sessionId}/sync`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
  });

  return handleResponse<ChatResponse>(response);
}

/**
 * Send a chat message with streaming response.
 * Returns a ReadableStream for real-time responses.
 */
export async function sendChatMessageStream(
  sessionId: string,
  message: string,
  conversationId?: string | null
): Promise<Response> {
  return fetch(`${API_BASE}/chat/${sessionId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
  });
}

/**
 * Get suggested prompts based on the user's financial data.
 */
export async function getSuggestedPrompts(
  sessionId: string
): Promise<SuggestedPromptsResponse> {
  const response = await fetch(`${API_BASE}/chat/${sessionId}/prompts`);
  return handleResponse<SuggestedPromptsResponse>(response);
}

/**
 * Get conversation history.
 */
export async function getConversationHistory(
  sessionId: string,
  conversationId: string
): Promise<ConversationHistory> {
  const response = await fetch(
    `${API_BASE}/chat/${sessionId}/history/${conversationId}`
  );
  return handleResponse<ConversationHistory>(response);
}
