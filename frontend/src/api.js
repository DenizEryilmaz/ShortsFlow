const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export function getApiUrl(path) {
  if (path.startsWith('http')) return path;
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalized}`;
}

export class ApiError extends Error {
  constructor(status, detail, raw) {
    super(`${status}: ${raw}`);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export async function apiFetch(path, options = {}) {
  return fetch(getApiUrl(path), options);
}

export async function apiJson(path, options = {}) {
  const res = await apiFetch(path, options);
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    let detail = '';
    try {
      const parsed = JSON.parse(text).detail;
      if (typeof parsed === 'string') detail = parsed;
    } catch (_) {
      // Ignore non-JSON bodies
    }
    throw new ApiError(res.status, detail, text);
  }
  return res.json();
}
