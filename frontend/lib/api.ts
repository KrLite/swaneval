import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
});

// Auto-set Content-Type: let Axios handle multipart/form-data when body is FormData
api.interceptors.request.use((config) => {
  if (!(config.data instanceof FormData)) {
    config.headers["Content-Type"] = "application/json";
  }
  return config;
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    const tenantId = localStorage.getItem("active_tenant_id");
    if (tenantId) {
      config.headers["X-Tenant-ID"] = tenantId;
    }
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      const url = err.config?.url || "";
      // Don't redirect on auth endpoints — let the login page handle its own errors
      if (!url.includes("/auth/")) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        localStorage.removeItem("active_tenant_id");
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

export default api;
