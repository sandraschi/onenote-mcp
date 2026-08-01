export const API_BASE = import.meta.env.VITE_API_BASE || "/api";

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
