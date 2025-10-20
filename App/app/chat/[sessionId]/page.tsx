"use client"

import { useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import ChatUI from "@/components/chat/chat-ui"

export default function ChatSessionPage() {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()
  const params = useParams()
  const sessionId = params?.sessionId as string | undefined

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login")
    }
  }, [isAuthenticated, isLoading, router])

  if (isLoading) {
    return (
      <div className="h-[calc(100svh-64px)] flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="h-[calc(100svh-64px)] overflow-hidden">
      <ChatUI initialSessionId={sessionId} />
    </div>
  )
}
