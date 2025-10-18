"use client"

import { getTokens, isAccessExpired, setTokens, clearTokens, handleAuthError, isRefreshTokenValid } from "./auth"

export function apiBase() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL
  if (!base) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured. Please set it in your environment variables.")
  }
  return base.trim()
}

// Default timeout for most API calls (30 seconds)
const DEFAULT_TIMEOUT = 30000

// No timeout for chat API (which can take longer due to AI processing)
const CHAT_TIMEOUT = 0 // 0 means no timeout

function fetchWithTimeout(url: string, init?: RequestInit, timeout = DEFAULT_TIMEOUT): Promise<Response> {
  // If timeout is 0, don't use timeout at all
  if (timeout === 0) {
    return fetch(url, init)
  }

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  return fetch(url, {
    ...init,
    signal: controller.signal,
  })
    .then((response) => {
      clearTimeout(timeoutId)
      return response
    })
    .catch((error) => {
      clearTimeout(timeoutId)
      if (error.name === "AbortError") {
        throw new Error("Request timeout - API took too long to respond")
      }
      throw error
    })
}

let refreshPromise: Promise<string | null> | null = null

async function refreshTokens(): Promise<string | null> {
  if (refreshPromise) {
    return refreshPromise
  }

  refreshPromise = (async () => {
    const { refreshToken } = getTokens()
    
    if (!refreshToken) {
      handleAuthError("No refresh token")
      return null
    }

    if (!isRefreshTokenValid()) {
      handleAuthError("Refresh token expired")
      return null
    }

    try {
      const res = await fetchWithTimeout(`${apiBase()}/api/auth/refresh`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
        mode: 'cors',
        credentials: 'omit',
      }, DEFAULT_TIMEOUT)
      
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: "Refresh failed" }))
        throw new Error(data?.message || "Refresh failed")
      }

      const data = await res.json()
      const expiry = Date.now() + (data?.expires_in ?? 900) * 1000
      setTokens(data.access_token, data.refresh_token ?? refreshToken, expiry)
      return data.access_token
    } catch (err: any) {
      console.error("Token refresh error:", err)
      handleAuthError(err)
      return null
    } finally {
      refreshPromise = null
    }
  })()

  return refreshPromise
}

async function getValidToken(): Promise<string | null> {
  const { accessToken } = getTokens()
  
  if (!accessToken) {
    return await refreshTokens()
  }
  
  if (isAccessExpired()) {
    return await refreshTokens()
  }
  
  return accessToken
}

// Determine timeout based on endpoint
function getTimeoutForEndpoint(pathOrUrl: string): number {
  // No timeout for chat API
  if (pathOrUrl.includes('/api/chat')) {
    return CHAT_TIMEOUT
  }
  // Default timeout for other endpoints
  return DEFAULT_TIMEOUT
}

export async function fetchWithAuth(pathOrUrl: string, init?: RequestInit, retryCount = 0): Promise<Response> {
  const fullUrl = pathOrUrl.startsWith("http") ? pathOrUrl : `${apiBase()}${pathOrUrl}`
  
  const token = await getValidToken()
  if (!token && retryCount === 0) {
    handleAuthError("No valid token available")
    throw new Error("Authentication required")
  }

  const headers = new Headers(init?.headers ?? {})
  headers.set("Accept", "application/json")
  if (token) headers.set("Authorization", `Bearer ${token}`)

  // Use appropriate timeout based on endpoint
  const timeout = getTimeoutForEndpoint(pathOrUrl)

  try {
    const res = await fetchWithTimeout(fullUrl, { 
      ...init, 
      headers,
      mode: 'cors',
      credentials: 'omit',
    }, timeout)

    if (res.status === 401 && retryCount === 0) {
      const newToken = await refreshTokens()
      if (!newToken) {
        handleAuthError("Token refresh failed")
        throw new Error("Authentication failed")
      }
      
      return fetchWithAuth(pathOrUrl, init, retryCount + 1)
    }

    if (res.status === 401 || res.status === 403) {
      handleAuthError(`Auth error: ${res.status}`)
    }

    return res
  } catch (err: any) {
    if (err.message.includes("Authentication")) {
      throw err
    }
    
    console.error("API request error:", err)
    throw err
  }
}
