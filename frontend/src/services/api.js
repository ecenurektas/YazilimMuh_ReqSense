const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message, status = 0, errorCode = "api_error") {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.errorCode = errorCode;
  }
}

function buildUrl(path) {
  return `${API_BASE}${path}`;
}

async function requestJson(path, options = {}) {
  let response;
  try {
    response = await fetch(buildUrl(path), {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });
  } catch {
    throw new ApiError(
      "Sunucuya ulaşılamadı. Backend servisinin (port 8000) çalıştığından emin olun.",
      0,
      "network_error"
    );
  }

  let data = null;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    try {
      data = await response.json();
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    const message =
      (data && typeof data.detail === "string" && data.detail) ||
      `Sunucu isteği işleyemedi (HTTP ${response.status}).`;
    const errorCode =
      (data && typeof data.error_code === "string" && data.error_code) ||
      "http_error";
    throw new ApiError(message, response.status, errorCode);
  }

  return data;
}

export function checkHealth() {
  return requestJson("/api/health", { method: "GET" });
}

export function analyzeRequirements({ title, rawInput, useDemo = false }) {
  return requestJson("/api/analyze", {
    method: "POST",
    body: JSON.stringify({
      title: title && title.trim() ? title.trim() : null,
      raw_input: rawInput,
      use_demo: Boolean(useDemo),
    }),
  });
}

export function listSessions() {
  return requestJson("/api/sessions", { method: "GET" });
}

export function getSession(sessionId) {
  return requestJson(`/api/sessions/${sessionId}`, { method: "GET" });
}

export function updateSession(sessionId, payload) {
  return requestJson(`/api/sessions/${sessionId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteSession(sessionId) {
  return requestJson(`/api/sessions/${sessionId}`, { method: "DELETE" });
}

function parseFilenameFromHeader(headerValue, fallbackFilename) {
  if (!headerValue) {
    return fallbackFilename;
  }
  const utfMatch = /filename\*=UTF-8''([^;]+)/i.exec(headerValue);
  if (utfMatch && utfMatch[1]) {
    try {
      return decodeURIComponent(utfMatch[1].replace(/["']/g, ""));
    } catch {
      return utfMatch[1].replace(/["']/g, "");
    }
  }
  const simpleMatch = /filename="?([^";]+)"?/i.exec(headerValue);
  if (simpleMatch && simpleMatch[1]) {
    return simpleMatch[1].trim();
  }
  return fallbackFilename;
}

export async function exportSessionFile(sessionId, format) {
  let response;
  try {
    response = await fetch(
      buildUrl(`/api/sessions/${sessionId}/export?format=${encodeURIComponent(format)}`),
      { method: "GET" }
    );
  } catch {
    throw new ApiError(
      "Dışa aktarma sırasında sunucuya ulaşılamadı.",
      0,
      "network_error"
    );
  }

  if (!response.ok) {
    let message = `Dosya dışa aktarılamadı (HTTP ${response.status}).`;
    let errorCode = "export_error";
    try {
      const errData = await response.json();
      if (errData?.detail) message = errData.detail;
      if (errData?.error_code) errorCode = errData.error_code;
    } catch {
      // JSON olmayan hata gövdesi yoksayılır
    }
    throw new ApiError(message, response.status, errorCode);
  }

  const blob = await response.blob();
  const fallbackName = `reqsense-${sessionId}.${format}`;
  const filename = parseFilenameFromHeader(
    response.headers.get("Content-Disposition"),
    fallbackName
  );

  const objectUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(objectUrl);

  return filename;
}
