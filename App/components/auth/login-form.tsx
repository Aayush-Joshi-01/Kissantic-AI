"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { setTokens } from "@/lib/auth"
import { apiBase } from "@/lib/api"
import { useAuth } from "@/contexts/auth-context"

export default function LoginForm() {
  const router = useRouter()
  const { login } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    
    try {
      const res = await fetch(`${apiBase()}/api/auth/login`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify({ email, password }),
      })

      const contentType = res.headers.get("content-type")
      if (!contentType || !contentType.includes("application/json")) {
        throw new Error(`Server returned non-JSON response: ${contentType}`)
      }

      const responseText = await res.clone().text()

      if (!res.ok) {
        let errorMessage = "Login failed"
        try {
          const data = JSON.parse(responseText)
          errorMessage = data?.message || errorMessage
        } catch {
          errorMessage = `Login failed with status ${res.status}`
        }
        throw new Error(errorMessage)
      }

      const data = JSON.parse(responseText)
      
      if (!data.access_token || !data.refresh_token) {
        throw new Error("Invalid response: missing tokens")
      }

      setTokens(data.access_token, data.refresh_token, Date.now() + (data.expires_in || 900) * 1000)
      login()
      router.push("/chat")
    } catch (err: any) {
      console.error("Login error:", err)
      
      if (err.message.includes("Failed to fetch")) {
        setError("Network error - Cannot connect to server. Please check if the API is running.")
      } else if (err.message.includes("non-JSON")) {
        setError("Server error - Received invalid response format")
      } else {
        setError(err.message || "Login failed")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="transition-shadow duration-200 hover:shadow-lg">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-primary animate-pulse" />
          Welcome back
        </CardTitle>
        <CardDescription>Log in to access your agent and sessions</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600" role="alert">
                {error}
              </p>
            </div>
          )}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Logging in..." : "Log in"}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
