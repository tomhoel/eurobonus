const USER_AGENTS = [
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
];

function randomUA(): string {
  return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export interface SASClientOptions {
  market?: string;
  pos?: string;
  cookies?: string;
  sessionId?: string;
  bearerToken?: string;
}

export async function sasRequest<T = unknown>(
  url: string,
  params: Record<string, string | number | boolean>,
  options: SASClientOptions = {},
): Promise<T | null> {
  const { cookies, sessionId, bearerToken } = options;
  const maxRetries = 3;

  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  }
  const fullUrl = `${url}?${qs.toString()}`;

  const headers: Record<string, string> = {
    Accept: "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": randomUA(),
  };
  if (cookies) headers["Cookie"] = cookies;
  if (sessionId) headers["sas-user-session-id"] = sessionId;
  if (bearerToken) headers["Authorization"] = `Bearer ${bearerToken}`;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const res = await fetch(fullUrl, { headers, signal: AbortSignal.timeout(30_000) });

      if (res.status === 429) {
        const wait = Math.pow(2, attempt + 1) * 1000;
        console.warn(`[SAS] Rate limited, waiting ${wait}ms`);
        await sleep(wait);
        continue;
      }

      if (!res.ok) {
        console.error(`[SAS] ${url} returned ${res.status}`);
        return null;
      }

      return (await res.json()) as T;
    } catch (err) {
      if (attempt < maxRetries - 1) {
        const wait = Math.pow(2, attempt) * 1000;
        console.warn(`[SAS] Request failed, retrying in ${wait}ms`, err);
        await sleep(wait);
      } else {
        console.error(`[SAS] Request failed after ${maxRetries} retries`, err);
        return null;
      }
    }
  }
  return null;
}
