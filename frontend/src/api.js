export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

function messageFrom(body, status) {
  const d = body?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d) && d[0]?.msg) return d[0].msg.replace(/^Value error, /, "");
  if (status === 429) return "Too many requests. Please wait a moment and try again.";
  return "Something went wrong. Please try again.";
}

async function request(method, path, body) {
  let res;
  try {
    res = await fetch(`/api${path}`, {
      method,
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        // Required by the backend on state-changing requests (CSRF defence).
        "X-Requested-With": "sarcasense",
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("Cannot reach the server.", 0);
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(messageFrom(data, res.status), res.status);
  return data;
}

export const api = {
  me: () => request("GET", "/auth/me"),
  login: (email, password) => request("POST", "/auth/login", { email, password }),
  register: (email, password) => request("POST", "/auth/register", { email, password }),
  logout: () => request("POST", "/auth/logout"),
  deleteAccount: (password) => request("POST", "/auth/delete-account", { password }),
  predict: (text, save = true) => request("POST", "/predict", { text, save }),
  history: (limit, offset) => request("GET", `/history?limit=${limit}&offset=${offset}`),
  stats: () => request("GET", "/history/stats"),
  deleteOne: (id) => request("DELETE", `/history/${id}`),
  deleteAll: () => request("DELETE", "/history"),
};
