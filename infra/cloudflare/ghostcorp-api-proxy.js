/**
 * GhostCorp same-origin API reverse proxy for Cloudflare Workers.
 *
 * Bind routes only for:
 *   ghostcorpnet.com/auth/*
 *   ghostcorpnet.com/api/*
 *   ghostcorpnet.com/webhooks/*
 *   ghostcorpnet.com/health
 *   ghostcorpnet.com/ready
 *
 * Set BACKEND_ORIGIN as a Worker environment variable (HTTPS origin only),
 * e.g. https://your-backend-host.example. Never include a path or credentials.
 * Static website routes remain served by GitHub Pages.
 */
const ALLOWED_PREFIXES = ["/auth/", "/api/", "/webhooks/"];
const ALLOWED_EXACT = new Set(["/health", "/ready"]);
const HOP_BY_HOP = new Set([
  "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
  "te", "trailers", "transfer-encoding", "upgrade", "host"
]);

function jsonError(status, message) {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff"
    }
  });
}

function validBackendOrigin(value) {
  try {
    const parsed = new URL(value);
    return parsed.protocol === "https:" &&
      parsed.username === "" && parsed.password === "" &&
      parsed.pathname === "/" && parsed.search === "" && parsed.hash === "";
  } catch {
    return false;
  }
}

export default {
  async fetch(request, env) {
    const incoming = new URL(request.url);
    const allowed = ALLOWED_EXACT.has(incoming.pathname) ||
      ALLOWED_PREFIXES.some(prefix => incoming.pathname.startsWith(prefix));
    if (!allowed) return jsonError(404, "not_found");

    if (!env.BACKEND_ORIGIN || !validBackendOrigin(env.BACKEND_ORIGIN)) {
      return jsonError(503, "backend_origin_not_configured");
    }

    const backend = new URL(env.BACKEND_ORIGIN);
    const target = new URL(incoming.pathname + incoming.search, backend.origin);
    const headers = new Headers(request.headers);
    for (const header of HOP_BY_HOP) headers.delete(header);
    headers.set("x-forwarded-host", incoming.host);
    headers.set("x-forwarded-proto", "https");

    const init = {
      method: request.method,
      headers,
      redirect: "manual"
    };
    if (request.method !== "GET" && request.method !== "HEAD") {
      init.body = request.body;
    }

    try {
      const upstream = await fetch(target, init);
      const responseHeaders = new Headers(upstream.headers);
      responseHeaders.set("cache-control", "no-store");
      responseHeaders.set("x-content-type-options", "nosniff");
      responseHeaders.delete("server");
      return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers: responseHeaders
      });
    } catch {
      return jsonError(502, "backend_unavailable");
    }
  }
};
