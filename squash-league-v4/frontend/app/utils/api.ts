/**
 * API client utilities for the Squash League application
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

/**
 * Generic fetch wrapper with error handling
 */
export async function apiCall<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      return {
        error: data?.detail || `HTTP ${response.status}`,
        status: response.status,
      };
    }

    return {
      data: data as T,
      status: response.status,
    };
  } catch (error) {
    return {
      error: error instanceof Error ? error.message : 'Network error',
      status: 0,
    };
  }
}

/**
 * Authenticated fetch wrapper
 */
export async function apiCallWithAuth<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  const token = typeof window !== 'undefined' 
    ? localStorage.getItem('squash_token') 
    : null;

  return apiCall<T>(endpoint, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      ...options?.headers,
    },
  });
}

export const API_ENDPOINTS = {
  HEALTH: '/health',
  LOGIN: '/auth/login',
  ME: '/me',
  PLAYERS: '/players',
  SEASONS: '/seasons',
  ROUNDS: '/rounds',
  MATCHES: '/matches',
  STANDINGS: '/standings',
  H2H: '/h2h',
  MY_MATCHES: '/me/matches',
  NOTIFICATIONS: '/notifications',
  ADMIN_OVERVIEW: '/admin/overview',
} as const;
