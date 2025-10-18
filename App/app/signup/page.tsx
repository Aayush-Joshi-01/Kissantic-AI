"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import SignupForm from "@/components/auth/signup-form"

export default function SignupPage() {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/chat")
    }
  }, [isAuthenticated, isLoading, router])

  if (isLoading) {
    return (
      <div className="relative vh-header overflow-hidden no-scrollbar flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (isAuthenticated) {
    return null
  }

  return (
    <div className="relative vh-header overflow-hidden no-scrollbar flex items-center justify-center">
      <div
        className="absolute inset-0 bg-center bg-cover"
        style={{ backgroundImage: "url('/images/farmers-sowing.jpg')" }}
        aria-hidden="true"
      />
      <div className="absolute inset-0 bg-gradient-to-b from-background/40 to-background/80" aria-hidden="true" />
      <div className="relative mx-auto px-4 py-6 w-full max-w-md">
        <div className="rounded-2xl border bg-background/50 backdrop-blur-xl shadow-xl">
          <div className="p-6">
            <SignupForm />
          </div>
        </div>
      </div>
    </div>
  )
}
