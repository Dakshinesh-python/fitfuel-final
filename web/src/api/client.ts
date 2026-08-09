import axios, { AxiosError } from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:4000';

export const apiClient = axios.create({
  baseURL,
});

const TOKEN_KEY = 'fitfuel_token';

export function saveToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

interface ZodFieldErrors {
  [field: string]: string[] | undefined;
}

interface BackendZodError {
  formErrors?: string[];
  fieldErrors?: ZodFieldErrors;
}

interface BackendErrorBody {
  error?: string | BackendZodError;
}

function isBackendErrorBody(value: unknown): value is BackendErrorBody {
  return typeof value === 'object' && value !== null && 'error' in value;
}

export function extractErrorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const axiosErr = err as AxiosError<unknown>;
    const data = axiosErr.response?.data;

    if (isBackendErrorBody(data) && data.error !== undefined) {
      const { error } = data;

      if (typeof error === 'string') {
        return error;
      }

      const messages: string[] = [];

      if (error.formErrors && error.formErrors.length > 0) {
        messages.push(...error.formErrors);
      }

      if (error.fieldErrors) {
        for (const [field, fieldMessages] of Object.entries(error.fieldErrors)) {
          if (fieldMessages && fieldMessages.length > 0) {
            messages.push(`${field}: ${fieldMessages.join(', ')}`);
          }
        }
      }

      if (messages.length > 0) {
        return messages.join(' | ');
      }
    }

    if (axiosErr.message) {
      return axiosErr.message;
    }
  }

  if (err instanceof Error) {
    return err.message;
  }

  return fallback;
}
