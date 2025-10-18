"use client"

type Tokens = {
  accessToken: string | null
  refreshToken: string | null
  accessExpiry: number | null
}

const ACCESS_KEY = "access_token"
const REFRESH_KEY = "refresh_token"
const EXP_KEY = "access_expiry"

export function setTokens(access: string, refresh: string, accessExpiryMs: number) {
  if (typeof window === "undefined") return
  localStorage.setItem(ACCESS_KEY, access)
  localStorage.setItem(REFRESH_KEY, refresh)
  localStorage.setItem(EXP_KEY, String(accessExpiryMs))
}

export function getTokens(): Tokens {
  if (typeof window === "undefined") return { accessToken: null, refreshToken: null, accessExpiry: null }
  return {
    accessToken: localStorage.getItem(ACCESS_KEY),
    refreshToken: localStorage.getItem(REFRESH_KEY),
    accessExpiry: Number.parseInt(localStorage.getItem(EXP_KEY) || "0", 10) || null,
  }
}

export function hasTokens() {
  const t = getTokens()
  return Boolean(t.accessToken && t.refreshToken)
}

export function clearTokens() {
  if (typeof window === "undefined") return
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(EXP_KEY)
}

export function isAccessExpired() {
  const { accessExpiry } = getTokens()
  if (!accessExpiry) return true
  return Date.now() > accessExpiry - 10_000
}

export function isRefreshTokenValid(): boolean {
  const { refreshToken } = getTokens()
  if (!refreshToken) return false
  
  try {
    const payload = JSON.parse(atob(refreshToken.split('.')[1]))
    const expiry = payload.exp * 1000
    return Date.now() < expiry - 5000
  } catch {
    return true
  }
}

export function handleAuthError(error?: any) {
  if (typeof window === "undefined") return
  
  console.error("Auth error:", error)
  clearTokens()
  
  const currentPath = window.location.pathname
  if (currentPath !== "/login" && currentPath !== "/signup" && currentPath !== "/") {
    window.location.href = "/login"
  }
}
