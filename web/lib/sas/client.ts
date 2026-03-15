import { execSync } from "child_process";

const USER_AGENTS = [
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
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

/**
 * Make a request to SAS APIs using curl to bypass Cloudflare TLS fingerprinting.
 * Node.js fetch gets blocked by Cloudflare even with correct headers,
 * but curl with browser headers passes through.
 */
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
    Accept: "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,no;q=0.8",
    "User-Agent": randomUA(),
    Referer: "https://www.sas.no/book/flights/",
    Origin: "https://www.sas.no",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
  };
  if (cookies) headers["Cookie"] = cookies;
  if (sessionId) headers["sas-user-session-id"] = sessionId;
  if (bearerToken) headers["Authorization"] = `Bearer ${bearerToken}`;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const result = curlRequest(fullUrl, headers);

      if (result === null) {
        if (attempt < maxRetries - 1) {
          const wait = Math.pow(2, attempt) * 1000;
          console.warn(`[SAS] Request failed, retrying in ${wait}ms`);
          await sleep(wait);
          continue;
        }
        return null;
      }

      return result as T;
    } catch (err) {
      if (attempt < maxRetries - 1) {
        const wait = Math.pow(2, attempt) * 1000;
        console.warn(`[SAS] Error, retrying in ${wait}ms`, err);
        await sleep(wait);
      } else {
        console.error(`[SAS] Request failed after ${maxRetries} retries`, err);
        return null;
      }
    }
  }
  return null;
}

/**
 * Execute an HTTP GET via curl to bypass Cloudflare TLS fingerprinting.
 */
function curlRequest(url: string, headers: Record<string, string>): unknown | null {
  const headerArgs = Object.entries(headers)
    .map(([k, v]) => `-H "${k}: ${v.replace(/"/g, '\\"')}"`)
    .join(" ");

  const cmd = `curl -s -m 30 ${headerArgs} "${url}"`;

  try {
    const stdout = execSync(cmd, {
      encoding: "utf-8",
      timeout: 35_000,
      maxBuffer: 10 * 1024 * 1024,
      // Use shell to handle the command properly
      shell: process.platform === "win32" ? "cmd.exe" : "/bin/bash",
    });

    if (!stdout || stdout.trim().startsWith("<!DOCTYPE") || stdout.trim().startsWith("<html")) {
      console.error(`[SAS] Cloudflare challenge detected for ${url}`);
      return null;
    }

    return JSON.parse(stdout);
  } catch (err) {
    console.error(`[SAS] curl failed for ${url}:`, (err as Error).message?.slice(0, 200));
    return null;
  }
}
