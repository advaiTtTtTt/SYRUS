/**
 * HTTP client wrapper for backend API.
 */

import axios from "axios";

const client = axios.create({
  baseURL: "/api",
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

export default client;
