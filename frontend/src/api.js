const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });
  } catch {
    throw new Error("Could not connect to the backend. Make sure Django is running on port 8000.");
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message =
      data.error ||
      data.detail ||
      (typeof data === "object" ? Object.values(data).flat().join(" ") : "") ||
      `Request failed (${response.status})`;
    throw new Error(message);
  }

  return data;
}

export function checkApi() {
  return request("/health/");
}

export function processVideo(url) {
  return request("/videos/process/", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export function askVideoQuestion(videoId, question, language = "Arabic") {
  return request(`/videos/${encodeURIComponent(videoId)}/ask/`, {
    method: "POST",
    body: JSON.stringify({ question, language }),
  });
}

export function generateVideoSummary(
  videoId,
  language = "Arabic"
) {
  return request(
    `/videos/${encodeURIComponent(videoId)}/summary/`,
    {
      method: "POST",
      body: JSON.stringify({ language }),
    }
  );
}

