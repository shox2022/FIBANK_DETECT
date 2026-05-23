import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8010";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 12000
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("aegis_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("aegis_token");
      localStorage.removeItem("aegis_user");
    }
    return Promise.reject(error);
  }
);

export function apiErrorMessage(error) {
  if (error.code === "ECONNABORTED" || !error.response) {
    return `Backend unavailable at ${API_BASE_URL}. Start FastAPI and try again.`;
  }
  const detail = error.response?.data?.detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(", ");
  return detail || error.message || "Request failed";
}

export default api;

