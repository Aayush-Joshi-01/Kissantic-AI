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

export default function SignupForm() {
  const router = useRouter()
  const { login } = useAuth()
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${apiBase()}/api/auth/signup`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify({ email, password, name }),
        mode: 'cors',
        credentials: 'omit',
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: "Signup failed" }))
        throw new Error(data?.message || `Signup failed with status ${res.status}`)
      }

      const data = await res.json()
      setTokens(data.access_token, data.refresh_token, Date.now() + (data.expires_in || 900) * 1000)
      login()
      router.push("/chat")
    } catch (err: any) {
      console.error("Signup error:", err)
      if (err.message.includes("Failed to fetch") || err.name === "TypeError") {
        setError("Network error - please check your connection and try again.")
      } else {
        setError(err.message || "Signup failed")
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
          Create an account
        </CardTitle>
        <CardDescription>Join Kisaantic AI and start your first session</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
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
            {loading ? "Creating account..." : "Sign up"}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
