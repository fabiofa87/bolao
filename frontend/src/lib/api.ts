declare global {
  interface Window {
    __APP_CONFIG__?: {
      apiBaseUrl?: string;
      backendScheme?: string;
      backendUrl?: string;
      adminUrl?: string;
    };
  }
}

let csrfToken = "";
let activeApiBaseUrl = "";
let csrfPromise: Promise<string> | null = null;

const getCookie = (name: string) => {
  const value = document.cookie
    .split("; ")
    .find((item) => item.startsWith(`${name}=`))
    ?.split("=")[1];
  return value ? decodeURIComponent(value) : "";
};

const trimQuotes = (value: string) => value.replace(/^["']|["']$/g, "");

const getApiBaseUrl = () => {
  const config = window.__APP_CONFIG__;
  const explicit = trimQuotes(config?.apiBaseUrl?.trim() ?? "");
  if (explicit) return explicit.replace(/\/$/, "");
  return "/api";
};

const getFallbackApiBaseUrl = () => {
  const config = window.__APP_CONFIG__;
  const backendUrl = trimQuotes(config?.backendUrl?.trim() ?? "");
  if (!backendUrl || backendUrl === "backend:8000") return "";
  const scheme = trimQuotes(config?.backendScheme?.trim() || "https");
  return `${scheme}://${backendUrl.replace(/\/$/, "")}/api`;
};

const getApiBaseUrls = () => {
  const primary = activeApiBaseUrl || getApiBaseUrl();
  const fallback = getFallbackApiBaseUrl();
  return [primary, fallback].filter(
    (base, index, bases): base is string => Boolean(base) && bases.indexOf(base) === index
  );
};

const buildApiUrl = (base: string, path: string) => `${base}${path}`;

const withTimeout = (options: RequestInit, timeoutMs = 12000) => {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  const clear = () => window.clearTimeout(timeout);

  if (options.signal) {
    options.signal.addEventListener("abort", () => controller.abort(), { once: true });
  }

  return {
    options: { ...options, signal: controller.signal },
    clear
  };
};

const fetchWithApiFallback = async (path: string, options: RequestInit = {}) => {
  const bases = getApiBaseUrls();
  let networkError: unknown = null;

  for (const base of bases) {
    const timed = withTimeout(options);
    try {
      const response = await fetch(buildApiUrl(base, path), timed.options);
      activeApiBaseUrl = base;
      return response;
    } catch (error) {
      networkError = error;
    } finally {
      timed.clear();
    }
  }

  throw networkError;
};

const getSignedCsrfToken = async () => {
  if (csrfToken) return csrfToken;
  csrfPromise ??= fetchWithApiFallback("/auth/session/", {
    credentials: "include",
    cache: "no-store"
  })
    .then((session) => session.json().catch(() => null))
    .then((data) => {
      csrfToken = data?.csrf_token ?? "";
      return csrfToken;
    })
    .finally(() => {
      csrfPromise = null;
    });
  return csrfPromise;
};

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, data: unknown) {
    super(
      typeof data === "object" && data && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : "Não foi possível concluir a operação."
    );
    this.status = status;
    this.data = data;
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = options.method?.toUpperCase() ?? "GET";
  const signedToken = method !== "GET" ? await getSignedCsrfToken() : "";
  const response = await fetchWithApiFallback(path, {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(method !== "GET" ? { "X-CSRFToken": signedToken || getCookie("csrftoken") } : {}),
      ...options.headers
    }
  });
  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => null);
  if (data && typeof data === "object" && "csrf_token" in data) {
    csrfToken = String((data as { csrf_token: unknown }).csrf_token ?? "");
  }
  if (!response.ok) throw new ApiError(response.status, data);
  return data as T;
}
