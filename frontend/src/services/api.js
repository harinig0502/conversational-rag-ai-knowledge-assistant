
import axios from "axios";

// Central configuration for backend API requests
const api = axios.create({
  baseURL: "http://localhost:5000/api",
  timeout: 120000,
});

export default api;
