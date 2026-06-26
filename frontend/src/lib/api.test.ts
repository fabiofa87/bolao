import { beforeEach, describe, expect, it, vi } from "vitest";

describe("api client", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.restoreAllMocks();
    window.__APP_CONFIG__ = {
      apiBaseUrl: "/broken-api",
      backendScheme: "https",
      backendUrl: "backend.example.com"
    };
  });

  it("falls back to the configured backend URL after a network error", async () => {
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ authenticated: false, user: null }), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        })
      );
    vi.stubGlobal("fetch", fetchMock);

    const { api } = await import("./api");
    const data = await api("/auth/session/");

    expect(data).toEqual({ authenticated: false, user: null });
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "/broken-api/auth/session/",
      expect.objectContaining({ credentials: "include" })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "https://backend.example.com/api/auth/session/",
      expect.objectContaining({ credentials: "include" })
    );
  });
});
