// Small helper around fetch() for talking to the Python backend.
const BASE = import.meta.env.VITE_API_URL || "";

async function request(path, options) {
  let res;
  try {
    res = await fetch(BASE + path, options);
  } catch {
    throw new Error("Cannot reach the NUMERIQ backend. Start it with:  python app.py  (in the backend folder).");
  }
  let data = null;
  try {
    data = await res.json();
  } catch {
    throw new Error("The server sent an unexpected reply.");
  }
  if (!res.ok || data.ok === false) throw new Error(data?.error || "Something went wrong.");
  return data;
}

const post = (path, body) =>
  request(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

export const api = {
  catalog: () => request("/api/catalog"),
  solve: (method, params) => post("/api/solve", { method, params }),
  learn: (id) => request(`/api/learn/${id}`),
  challenges: () => request("/api/challenges"),
  runChallenge: (id, methods, knobs) => post(`/api/challenge/${id}`, { methods, knobs }),
};
