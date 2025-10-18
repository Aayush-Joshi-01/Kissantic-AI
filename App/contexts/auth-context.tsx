"use client"

import React, { createContext, useContext, useEffect, useState, useCallback } from "react"
import { useRouter, usePathname } from "next/navigation"
import { hasTokens, clearTokens } from "@/lib/auth"

type AuthContextType = {
  isAuthenticated: boolean
  isLoading: boolean
  login: () => void
  logout: () => void
  checkAuth: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  const checkAuth = useCallback(() => {
    const authed = hasTokens()
    setIsAuthenticated(authed)
    return authed
  }, [])

  const login = useCallback(() => {
    setIsAuthenticated(true)
  }, [])

  const logout = useCallback(() => {
    clearTokens()
    setIsAuthenticated(false)
    router.push("/login")
  }, [router])

  useEffect(() => {
    checkAuth()
    setIsLoading(false)
  }, [checkAuth])

  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "access_token" || e.key === "refresh_token") {
        checkAuth()
      }
    }

    window.addEventListener("storage", handleStorageChange)
    return () => window.removeEventListener("storage", handleStorageChange)
  }, [checkAuth])

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, login, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within AuthProvider")
  }
  return context
}
