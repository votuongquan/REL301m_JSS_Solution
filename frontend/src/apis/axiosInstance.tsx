import axios from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://localhost:8000/api/v1";


const axiosInstance = axios.create({
  baseURL: `${API_BASE_URL}`,
});

export default axiosInstance;
