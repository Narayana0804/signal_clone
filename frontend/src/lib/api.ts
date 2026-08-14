/**
 * REST API client helper for Signal Clone frontend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public code?: string,
    public field?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}/api/v1${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const config: RequestInit = {
    ...options,
    headers,
    credentials: "include", // Send HTTP-only session cookies
  };

  let response: Response;
  try {
    response = await fetch(url, config);
  } catch {
    throw new ApiError(
      0,
      "Network error — Unable to connect to Signal server. Please verify your connection."
    );
  }

  if (response.status === 204) {
    return {} as T;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new ApiError(
      response.status,
      data.detail || "An unexpected error occurred",
      data.code,
      data.field
    );
  }

  return data as T;
}
