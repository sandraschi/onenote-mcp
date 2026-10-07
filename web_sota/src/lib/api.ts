const isTauri =
  typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

// In dev the Vite proxy maps /api -> 127.0.0.1:10907. The built dist served by
// the Tauri WebView has no proxy, so the API base must be absolute there, on the
// installed app's own port (11250, onenote-mcp-native) - never the dev backend port.
export const API_BASE =
  import.meta.env.VITE_API_BASE ||
  (isTauri ? "http://127.0.0.1:11250/api" : "/api");

/** Origin the API is actually reached at (for display; never a hardcoded port). */
export const API_ORIGIN =
  typeof window === "undefined"
    ? ""
    : new URL(API_BASE, window.location.href).origin;

export async function fetchJson<T = unknown>(
  path: string,
  init?: RequestInit,
  timeoutMs = 30_000,
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
      signal: controller.signal,
    });
    if (!res.ok) {
      const body = await res.text();
      let detail = body.slice(0, 300);
      try {
        const parsed = JSON.parse(body);
        if (typeof parsed?.error === "string") detail = parsed.error;
      } catch {
        /* non-JSON error body */
      }
      throw new Error(detail);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}
