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
  const backendUrl = trimQuotes(config?.backendUrl?.trim() ?? "");
  if (!backendUrl || backendUrl === "backend:8000") return "/api";
  const scheme = trimQuotes(config?.backendScheme?.trim() || "https");
  return `${scheme}://${backendUrl.replace(/\/$/, "")}/api`;
};

const buildApiUrl = (path: string) => {
  const base = getApiBaseUrl();
  return `${base}${path}`;
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
  if (method !== "GET" && !csrfToken && !getCookie("csrftoken")) {
    const session = await fetch(buildApiUrl("/auth/session/"), {
      credentials: "include"
    });
    const data = await session.json().catch(() => null);
    csrfToken = data?.csrf_token ?? "";
  }
  const response = await fetch(buildApiUrl(path), {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(method !== "GET" ? { "X-CSRFToken": csrfToken || getCookie("csrftoken") } : {}),
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
