/**
 * Shared TypeScript type definitions for Signal Clone frontend.
 */

export interface User {
  id: string;
  phone_number: string;
  display_name: string;
  avatar_url?: string | null;
  about?: string;
  is_verified?: number;
  created_at?: string;
  last_seen_at?: string | null;
}

export interface AuthResponse {
  user: User;
  token: string;
}
