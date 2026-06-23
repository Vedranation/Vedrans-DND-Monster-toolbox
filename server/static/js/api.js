// Thin fetch wrapper around the REST API. Every call is one request→response.

async function req(method, url, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(url, opts);
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const msg = (data && data.message) || res.statusText || "Request failed";
    throw new Error(msg);
  }
  return data;
}

export const api = {
  get: (url) => req("GET", url),
  post: (url, body) => req("POST", url, body),
  put: (url, body) => req("PUT", url, body),
  patch: (url, body) => req("PATCH", url, body),
  del: (url) => req("DELETE", url),
};
