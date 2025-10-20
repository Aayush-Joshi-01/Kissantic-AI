"use client"

import type React from "react"

import useSWR from "swr"
import { useCallback, useEffect, useRef, useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Tooltip } from "@/components/ui/tooltip"
import { fetchWithAuth } from "@/lib/api"
import { cn } from "@/lib/utils"
import { motion, AnimatePresence } from "framer-motion"
import { useAuth } from "@/contexts/auth-context"
import { LoadingIndicator } from "./loading-indicator"
import { MarkdownRenderer } from "./markdown-renderer"
import { BookingOrderSuggestion } from "./booking-order-suggestion"
import { BookingSuggestion, OrderSuggestion } from "@/lib/types"

type SessionItem = {
  session_id: string
  title: string
  updated_at: string
  message_count: number
}

type Message = {
  message_id: string
  sender: "user" | "ai"
  text: string
  created_at: string
  metadata?: {
    booking_suggestion?: BookingSuggestion
    order_suggestion?: OrderSuggestion
    [key: string]: any
  }
}

type WeatherData = {
  temp_c?: number
  condition?: string
  humidity?: number
  wind_kph?: number
  feelslike_c?: number
  uv?: number
}

type ForecastDay = {
  date: string
  day: {
    maxtemp_c: number
    mintemp_c: number
    avgtemp_c: number
    condition: {
      text: string
      icon: string
    }
    daily_chance_of_rain: number
  }
}

function useSessions() {
  const { data, error, mutate, isLoading } = useSWR<{ items: SessionItem[] }>(
    "/api/sessions",
    (url) => fetchWithAuth(url).then((r) => r.json()),
    { 
      revalidateOnFocus: false,
      shouldRetryOnError: false,
    },
  )
  return { sessions: data?.items ?? [], error, mutate, isLoading }
}

export default function ChatUI({ initialSessionId }: { initialSessionId?: string }) {
  const { logout } = useAuth()
  const router = useRouter()
  const { sessions, mutate: refreshSessions } = useSessions()
  const [selectedId, setSelectedId] = useState<string | null>(initialSessionId || null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null)
  const [address, setAddress] = useState<string | null>(null)
  const [currentWeather, setCurrentWeather] = useState<WeatherData | null>(null)
  const [forecast, setForecast] = useState<ForecastDay | null>(null)
  const [history, setHistory] = useState<ForecastDay | null>(null)
  const [weatherExpanded, setWeatherExpanded] = useState(false)

  // Update URL when session changes
  useEffect(() => {
    if (selectedId) {
      router.replace(`/chat/${selectedId}`, { scroll: false })
    } else {
      router.replace('/chat', { scroll: false })
    }
  }, [selectedId, router])

  useEffect(() => {
    navigator.geolocation?.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude
        const lng = pos.coords.longitude
        setCoords({ lat, lng })
      },
      () => setCoords(null),
      { enableHighAccuracy: true, timeout: 10000 },
    )
  }, [])

  useEffect(() => {
    const fetchWeatherData = async () => {
      if (!coords) return
      
      try {
        const [currentRes, forecastRes, historyRes] = await Promise.all([
          fetchWithAuth(`/api/weather/current?lat=${coords.lat}&lng=${coords.lng}`),
          fetchWithAuth(`/api/weather/forecast?lat=${coords.lat}&lng=${coords.lng}&days=1`),
          fetchWithAuth(`/api/weather/history?lat=${coords.lat}&lng=${coords.lng}&dt=${getYesterdayDate()}`)
        ])

        if (currentRes.ok) {
          const data = await currentRes.json()
          setCurrentWeather({
            temp_c: data?.current?.temp_c,
            condition: data?.current?.condition?.text,
            humidity: data?.current?.humidity,
            wind_kph: data?.current?.wind_kph,
            feelslike_c: data?.current?.feelslike_c,
            uv: data?.current?.uv,
          })
        }

        if (forecastRes.ok) {
          const data = await forecastRes.json()
          setForecast(data?.forecast?.forecastday?.[0] || null)
        }

        if (historyRes.ok) {
          const data = await historyRes.json()
          setHistory(data?.forecast?.forecastday?.[0] || null)
        }
      } catch (err) {
        console.error("Weather fetch error:", err)
      }
    }

    fetchWeatherData()
    const interval = setInterval(fetchWeatherData, 900000)
    return () => clearInterval(interval)
  }, [coords])

  const getYesterdayDate = () => {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    return yesterday.toISOString().split('T')[0]
  }

  useEffect(() => {
    const fetchAddress = async () => {
      if (!coords) return
      try {
        const res = await fetch(
          `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${coords.lat}&lon=${coords.lng}`,
          { headers: { Accept: "application/json" } },
        )
        const data = await res.json()
        const label: string =
          data?.display_name ||
          [data?.address?.hamlet, data?.address?.village, data?.address?.town, data?.address?.state]
            .filter(Boolean)
            .join(", ")
        setAddress(label || "Your location")
      } catch {
        setAddress(null)
      }
    }
    fetchAddress()
  }, [coords])

  useEffect(() => {
    if (!selectedId) return
    ;(async () => {
      try {
        const res = await fetchWithAuth(`/api/sessions/${selectedId}`)
        if (res.ok) {
          const data = await res.json()
          setMessages(data?.messages ?? [])
          setError(null)
        } else {
          setError("Failed to load session")
          setMessages([])
        }
      } catch (err) {
        setError("Error loading session")
        setMessages([])
      }
    })()
  }, [selectedId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, sending])

  const onNewChat = async () => {
    try {
      setError(null)
      const title = "New Chat"
      const res = await fetchWithAuth("/api/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      })

      if (res.ok) {
        const data = await res.json()
        setSelectedId(data.session_id)
        setMessages([])
        refreshSessions()
        setSidebarOpen(false)
      } else {
        setError("Failed to create session")
      }
    } catch (err: any) {
      setError(err.message || "Error creating session")
    }
  }

  const deleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm("Delete this session?")) return
    
    const previousSessions = sessions
    const wasCurrent = selectedId === sessionId
    
    try {
      await refreshSessions(
        { items: sessions.filter(s => s.session_id !== sessionId) },
        false
      )
      
      const res = await fetchWithAuth(`/api/sessions/${sessionId}`, { method: "DELETE" })
      
      if (res.ok) {
        if (wasCurrent) {
          // Create new session if we deleted the current one
          await onNewChat()
        } else {
          await refreshSessions()
        }
      } else {
        await refreshSessions({ items: previousSessions }, false)
        setError("Failed to delete session")
      }
    } catch (err) {
      console.error("Delete error:", err)
      await refreshSessions({ items: previousSessions }, false)
      setError("Error deleting session")
    }
  }

  const handleLogout = async () => {
    try {
      await fetchWithAuth("/api/auth/logout", { method: "POST" })
    } catch (err) {
      console.error("Logout API error:", err)
    } finally {
      logout()
    }
  }

  const sendMessage = useCallback(async () => {
    if (!input.trim()) return
    setSending(true)
    setError(null)
    try {
      const payload: any = { message: input.trim() }
      if (selectedId) payload.session_id = selectedId
      if (coords) {
        payload.latitude = coords.lat
        payload.longitude = coords.lng
      }
      if (address) payload.address = address
      if (currentWeather) {
        if (typeof currentWeather.temp_c === "number") payload.weather_temp = currentWeather.temp_c
        if (currentWeather.condition) payload.weather_condition = currentWeather.condition
        if (typeof currentWeather.humidity === "number") payload.weather_humidity = currentWeather.humidity
      }

      const res = await fetchWithAuth("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      if (res.ok) {
        const data = await res.json()
        const newSessionId = data.session_id
        selectSession(newSessionId)
        const newMessages = [data.user_message, data.ai_message];
        setMessages((prev) => [...prev, ...newMessages])
        setInput("")
        refreshSessions()
      } else {
        const errData = await res.json()
        setError(errData?.message || "Failed to send message")
      }
    } catch (err: any) {
      setError(err.message || "Error sending message")
    } finally {
      setSending(false)
    }
  }, [coords, address, input, selectedId, currentWeather, refreshSessions])

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      if (!sending && input.trim()) {
        void sendMessage()
      }
    }
  }

  return (
    <div className="flex h-full bg-background relative">
      {/* Mobile Overlay - Behind sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar - Above overlay */}
      <AnimatePresence>
        {(sidebarOpen || typeof window === 'undefined') && (
          <motion.aside 
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className={cn(
              "w-72 border-r flex flex-col bg-background shrink-0 z-50",
              "fixed lg:relative inset-y-0 left-0 h-full",
              "lg:translate-x-0"
            )}
          >
            <div className="p-4 border-b flex items-center justify-between shrink-0 bg-background">
              <h2 className="font-semibold text-lg">Kisaantic AI</h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSidebarOpen(false)}
                className="h-8 w-8 p-0 lg:hidden hover:bg-muted transition-colors"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </Button>
            </div>

            <div className="p-3 shrink-0 bg-background">
              <Button onClick={onNewChat} className="w-full transition-all hover:scale-[1.02]" size="sm">
                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Chat
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto px-2 space-y-1 min-h-0 bg-background">
              <div className="text-xs font-semibold text-muted-foreground px-2 mb-2">
                Chat Sessions
              </div>
              {sessions.length === 0 ? (
                <div className="text-center text-sm text-muted-foreground p-4">
                  No sessions yet
                </div>
              ) : (
                sessions.map((s) => (
                  <motion.div 
                    key={s.session_id} 
                    className="relative group"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <button
                      onClick={() => {
                        setSelectedId(s.session_id)
                        setSidebarOpen(false)
                      }}
                      className={cn(
                        "w-full text-left px-3 py-2 rounded-md transition-all hover:bg-muted text-sm",
                        selectedId === s.session_id && "bg-muted font-medium"
                      )}
                    >
                      <div className="truncate">{s.title || "Untitled"}</div>
                      <div className="text-xs text-muted-foreground truncate">
                        {new Date(s.updated_at).toLocaleDateString()}
                      </div>
                    </button>
                    <button
                      onClick={(e) => deleteSession(s.session_id, e)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 transition-all hover:scale-110"
                      title="Delete session"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </motion.div>
                ))
              )}
            </div>

            <div className="p-3 border-t shrink-0 bg-background">
              <Card className="bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-950 dark:to-cyan-950 border-blue-200 dark:border-blue-800 transition-all hover:shadow-md">
                <CardHeader className="p-3 pb-2">
                  <div className="flex items-center justify-between">
                    <div className="text-xs font-semibold text-blue-900 dark:text-blue-100">Weather</div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setWeatherExpanded(!weatherExpanded)}
                      className="h-6 text-xs hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors"
                    >
                      {weatherExpanded ? "Less" : "More"}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="p-3 pt-0 space-y-2">
                  {currentWeather?.temp_c != null ? (
                    <>
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-3xl font-bold text-blue-900 dark:text-blue-100">{currentWeather.temp_c}°C</div>
                          <div className="text-xs text-blue-700 dark:text-blue-300">{currentWeather.condition || "Clear"}</div>
                        </div>
                        <span className="text-4xl">☀️</span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <Tooltip content="Current humidity level - percentage of water vapor in the air">
                          <div className="flex items-center gap-1 cursor-help p-1 rounded hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors">
                            <span>💧</span>
                            <span>{currentWeather.humidity}%</span>
                          </div>
                        </Tooltip>
                        <Tooltip content="Feels like temperature - what the temperature actually feels like on your skin">
                          <div className="flex items-center gap-1 cursor-help p-1 rounded hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors">
                            <span>🌡️</span>
                            <span>{currentWeather.feelslike_c}°C</span>
                          </div>
                        </Tooltip>
                        <Tooltip content="Wind speed - current speed of wind in kilometers per hour">
                          <div className="flex items-center gap-1 cursor-help p-1 rounded hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors">
                            <span>🌬️</span>
                            <span>{currentWeather.wind_kph} km/h</span>
                          </div>
                        </Tooltip>
                        <Tooltip content="UV Index - measure of ultraviolet radiation intensity (0-2: Low, 3-5: Moderate, 6-7: High, 8-10: Very High, 11+: Extreme)">
                          <div className="flex items-center gap-1 cursor-help p-1 rounded hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors">
                            <span>☀️</span>
                            <span>UV {currentWeather.uv}</span>
                          </div>
                        </Tooltip>
                      </div>

                      {weatherExpanded && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          className="space-y-2 pt-2 border-t border-blue-200 dark:border-blue-800"
                        >
                          {history && (
                            <div className="bg-white/50 dark:bg-white/10 rounded p-2 hover:bg-white/70 dark:hover:bg-white/20 transition-colors">
                              <div className="text-xs font-semibold text-blue-900 dark:text-blue-100 mb-1">Yesterday</div>
                              <div className="flex items-center justify-between text-xs">
                                <span>{history.day.condition.text}</span>
                                <span className="font-semibold">
                                  {history.day.mintemp_c}° - {history.day.maxtemp_c}°C
                                </span>
                              </div>
                              <div className="text-xs text-blue-700 dark:text-blue-300">
                                Rain: {history.day.daily_chance_of_rain}%
                              </div>
                            </div>
                          )}
                          
                          {forecast && (
                            <div className="bg-white/50 dark:bg-white/10 rounded p-2 hover:bg-white/70 dark:hover:bg-white/20 transition-colors">
                              <div className="text-xs font-semibold text-blue-900 dark:text-blue-100 mb-1">Tomorrow</div>
                              <div className="flex items-center justify-between text-xs">
                                <span>{forecast.day.condition.text}</span>
                                <span className="font-semibold">
                                  {forecast.day.mintemp_c}° - {forecast.day.maxtemp_c}°C
                                </span>
                              </div>
                              <div className="text-xs text-blue-700 dark:text-blue-300">
                                Rain: {forecast.day.daily_chance_of_rain}%
                              </div>
                            </div>
                          )}
                        </motion.div>
                      )}
                    </>
                  ) : (
                    <div className="text-xs text-muted-foreground">Loading...</div>
                  )}
                </CardContent>
              </Card>
            </div>

            <div className="p-3 border-t space-y-2 shrink-0 bg-background">
              <Button
                variant="outline"
                className="w-full justify-start transition-all hover:bg-muted"
                size="sm"
                onClick={() => window.location.href = "/profile"}
              >
                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Profile
              </Button>
              <Button
                variant="ghost"
                className="w-full transition-all hover:bg-muted"
                size="sm"
                onClick={handleLogout}
              >
                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Logout
              </Button>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Always show sidebar on desktop */}
      <aside className={cn(
        "hidden lg:flex w-72 border-r flex-col bg-muted/30 shrink-0"
      )}>
        <div className="p-4 border-b flex items-center justify-between shrink-0">
          <h2 className="font-semibold text-lg">Kisaantic AI</h2>
        </div>

        <div className="p-3 shrink-0">
          <Button onClick={onNewChat} className="w-full transition-all hover:scale-[1.02]" size="sm">
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Chat
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 space-y-1 min-h-0">
          <div className="text-xs font-semibold text-muted-foreground px-2 mb-2">
            Chat Sessions
          </div>
          {sessions.length === 0 ? (
            <div className="text-center text-sm text-muted-foreground p-4">
              No sessions yet
            </div>
          ) : (
            sessions.map((s) => (
              <motion.div 
                key={s.session_id} 
                className="relative group"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2 }}
              >
                <button
                  onClick={() => setSelectedId(s.session_id)}
                  className={cn(
                    "w-full text-left px-3 py-2 rounded-md transition-all hover:bg-muted text-sm",
                    selectedId === s.session_id && "bg-muted font-medium"
                  )}
                >
                  <div className="truncate">{s.title || "Untitled"}</div>
                  <div className="text-xs text-muted-foreground truncate">
                    {new Date(s.updated_at).toLocaleDateString()}
                  </div>
                </button>
                <button
                  onClick={(e) => deleteSession(s.session_id, e)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 transition-all hover:scale-110"
                  title="Delete session"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </motion.div>
            ))
          )}
        </div>

        <div className="p-3 border-t shrink-0">
          <Card className="bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-950 dark:to-cyan-950 border-blue-200 dark:border-blue-800 transition-all hover:shadow-md">
            <CardHeader className="p-3 pb-2">
              <div className="flex items-center justify-between">
                <div className="text-xs font-semibold text-blue-900 dark:text-blue-100">Weather</div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setWeatherExpanded(!weatherExpanded)}
                  className="h-6 text-xs hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors"
                >
                  {weatherExpanded ? "Less" : "More"}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-3 pt-0 space-y-2">
              {currentWeather?.temp_c != null ? (
                <>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-3xl font-bold text-blue-900 dark:text-blue-100">{currentWeather.temp_c}°C</div>
                      <div className="text-xs text-blue-700 dark:text-blue-300">{currentWeather.condition || "Clear"}</div>
                    </div>
                    <span className="text-4xl">☀️</span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <Tooltip content="Current humidity level - percentage of water vapor in the air">
                      <div className="flex items-center gap-1 cursor-help p-1 rounded hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors">
                        <span>💧</span>
                        <span>{currentWeather.humidity}%</span>
                      </div>
                    </Tooltip>
                    <Tooltip content="Feels like temperature - what the temperature actually feels like on your skin">
                      <div className="flex items-center gap-1 cursor-help p-1 rounded hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors">
                        <span>🌡️</span>
                        <span>{currentWeather.feelslike_c}°C</span>
                      </div>
                    </Tooltip>
                    <Tooltip content="Wind speed - current speed of wind in kilometers per hour">
                      <div className="flex items-center gap-1 cursor-help p-1 rounded hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors">
                        <span>🌬️</span>
                        <span>{currentWeather.wind_kph} km/h</span>
                      </div>
                    </Tooltip>
                    <Tooltip content="UV Index - measure of ultraviolet radiation intensity (0-2: Low, 3-5: Moderate, 6-7: High, 8-10: Very High, 11+: Extreme)">
                      <div className="flex items-center gap-1 cursor-help p-1 rounded hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors">
                        <span>☀️</span>
                        <span>UV {currentWeather.uv}</span>
                      </div>
                    </Tooltip>
                  </div>

                  {weatherExpanded && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="space-y-2 pt-2 border-t border-blue-200 dark:border-blue-800"
                    >
                      {history && (
                        <div className="bg-white/50 dark:bg-white/10 rounded p-2 hover:bg-white/70 dark:hover:bg-white/20 transition-colors">
                          <div className="text-xs font-semibold text-blue-900 dark:text-blue-100 mb-1">Yesterday</div>
                          <div className="flex items-center justify-between text-xs">
                            <span>{history.day.condition.text}</span>
                            <span className="font-semibold">
                              {history.day.mintemp_c}° - {history.day.maxtemp_c}°C
                            </span>
                          </div>
                          <div className="text-xs text-blue-700 dark:text-blue-300">
                            Rain: {history.day.daily_chance_of_rain}%
                          </div>
                        </div>
                      )}
                      
                      {forecast && (
                        <div className="bg-white/50 dark:bg-white/10 rounded p-2 hover:bg-white/70 dark:hover:bg-white/20 transition-colors">
                          <div className="text-xs font-semibold text-blue-900 dark:text-blue-100 mb-1">Tomorrow</div>
                          <div className="flex items-center justify-between text-xs">
                            <span>{forecast.day.condition.text}</span>
                            <span className="font-semibold">
                              {forecast.day.mintemp_c}° - {forecast.day.maxtemp_c}°C
                            </span>
                          </div>
                          <div className="text-xs text-blue-700 dark:text-blue-300">
                            Rain: {forecast.day.daily_chance_of_rain}%
                          </div>
                        </div>
                      )}
                    </motion.div>
                  )}
                </>
              ) : (
                <div className="text-xs text-muted-foreground">Loading...</div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="p-3 border-t space-y-2 shrink-0">
          <Button
            variant="outline"
            className="w-full justify-start transition-all hover:bg-muted"
            size="sm"
            onClick={() => window.location.href = "/profile"}
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            Profile
          </Button>
          <Button
            variant="ghost"
            className="w-full transition-all hover:bg-muted"
            size="sm"
            onClick={handleLogout}
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Logout
          </Button>
        </div>
      </aside>

      <main className="flex-1 flex flex-col min-w-0 w-full">
        <div className="border-b p-2 flex items-center gap-2 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden hover:bg-muted transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </Button>
          <span className="text-sm font-medium">Kisaantic AI</span>
        </div>

        <div className="flex-1 overflow-y-auto p-2 sm:p-4 min-h-0">
          {error && (
            <motion.div 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700 w-full max-w-7xl mx-auto"
            >
              {error}
            </motion.div>
          )}
          
          {messages.length === 0 && !sending ? (
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
              className="w-full max-w-5xl mx-auto px-2 sm:px-4"
            >
              <Card className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="text-2xl">🌾</span>
                    Welcome to Kisaantic AI
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground space-y-2">
                  <p>
                    Get personalized agricultural advice based on your location, weather conditions, and farming needs.
                  </p>
                  {(address || currentWeather?.temp_c != null) && (
                    <div className="flex items-center gap-2 text-xs pt-2 border-t">
                      {address && (
                        <span className="flex items-center gap-1">
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          {address}
                        </span>
                      )}
                      {currentWeather?.temp_c != null && (
                        <span className="flex items-center gap-1">
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                          </svg>
                          {currentWeather.temp_c}°C {currentWeather?.condition ?? ""}
                        </span>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          ) : (
            <div className="w-full max-w-7xl mx-auto px-1 sm:px-2 md:px-4 space-y-4">
              <AnimatePresence initial={false}>
                {messages.map((m) => (
                  <motion.div
                    key={m.message_id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.2 }}
                    className={cn(
                      "rounded-lg transition-shadow hover:shadow-md",
                      m.sender === "user" 
                        ? "bg-primary text-primary-foreground ml-auto w-full sm:max-w-[85%] lg:max-w-[75%] p-3 sm:p-4" 
                        : "bg-muted w-full p-3 sm:p-4"
                    )}
                  >
                    <div className={cn(
                      "text-xs mb-2 opacity-70 flex items-center gap-1",
                      m.sender === "user" && "text-primary-foreground"
                    )}>
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        {m.sender === "user" ? (
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        ) : (
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        )}
                      </svg>
                      {m.sender === "user" ? "You" : "Kisaantic AI"} • {new Date(m.created_at).toLocaleTimeString()}
                    </div>
                    {m.sender === "ai" ? (
                      <>
                        <div className="overflow-x-auto">
                          <MarkdownRenderer content={m.text} />
                        </div>
                        {(m.metadata?.booking_suggestion || m.metadata?.order_suggestion) && (
                          <BookingOrderSuggestion
                            bookingSuggestion={m.metadata.booking_suggestion}
                            orderSuggestion={m.metadata.order_suggestion}
                            messageId={m.message_id}
                            sessionId={selectedId || ""}
                          />
                        )}
                      </>
                    ) : (
                      <p className="whitespace-pre-wrap text-sm">{m.text}</p>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
              
              {sending && <LoadingIndicator />}
              
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <div className="border-t bg-background p-2 sm:p-4 shrink-0">
          <div className="mx-auto w-full max-w-7xl px-1 sm:px-2 md:px-4">
            <div className="flex gap-2 items-end">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Ask about crops, weather, fertilizers, equipment..."
                rows={3}
                className="resize-none text-sm transition-all focus:shadow-md"
              />
              <Button
                onClick={sendMessage}
                disabled={sending || !input.trim()}
                size="lg"
                className="px-4 sm:px-6 transition-all hover:scale-[1.02] disabled:opacity-50"
              >
                {sending ? (
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                )}
              </Button>
            </div>
            {(address || currentWeather?.temp_c != null) && (
              <div className="mt-2 text-xs text-muted-foreground flex items-center gap-2">
                {address && (
                  <span className="flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    {address}
                  </span>
                )}
                {currentWeather?.temp_c != null && (
                  <span className="flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                    </svg>
                    {currentWeather.temp_c}°C {currentWeather?.condition ?? ""}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
