"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { fetchWithAuth } from "@/lib/api"
import { BookingOrder, BookingsOrdersResponse } from "@/lib/types"
import { motion, AnimatePresence } from "framer-motion"
import { Calendar, ShoppingCart, Loader2, CheckCircle2, XCircle, Clock, Ban } from "lucide-react"

export default function BookingsOrdersPage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [data, setData] = useState<BookingsOrdersResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<"all" | "pending" | "approved" | "rejected" | "cancelled">("all")
  const [typeFilter, setTypeFilter] = useState<"all" | "booking" | "order">("all")
  const [updating, setUpdating] = useState<string | null>(null)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/login")
    }
  }, [isAuthenticated, authLoading, router])

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (filter !== "all") params.append("status", filter)
      if (typeFilter !== "all") params.append("type", typeFilter)
      
      const res = await fetchWithAuth(`/api/bookings-orders?${params.toString()}`)
      if (res.ok) {
        const result = await res.json()
        setData(result)
      } else {
        throw new Error("Failed to fetch bookings/orders")
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isAuthenticated) {
      fetchData()
    }
  }, [isAuthenticated, filter, typeFilter])

  const updateStatus = async (id: string, type: "booking" | "order", newStatus: "approved" | "rejected" | "cancelled") => {
    setUpdating(id)
    try {
      const res = await fetchWithAuth("/api/bookings-orders/update", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          booking_order_id: id,
          type,
          status: newStatus,
        }),
      })

      if (res.ok) {
        await fetchData()
      } else {
        throw new Error("Failed to update status")
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setUpdating(null)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "pending":
        return <Badge variant="secondary" className="flex items-center gap-1"><Clock className="h-3 w-3" /> Pending</Badge>
      case "approved":
        return <Badge variant="success" className="flex items-center gap-1"><CheckCircle2 className="h-3 w-3" /> Approved</Badge>
      case "rejected":
        return <Badge variant="destructive" className="flex items-center gap-1"><XCircle className="h-3 w-3" /> Rejected</Badge>
      case "cancelled":
        return <Badge variant="outline" className="flex items-center gap-1"><Ban className="h-3 w-3" /> Cancelled</Badge>
      default:
        return <Badge>{status}</Badge>
    }
  }

  if (authLoading || !isAuthenticated) {
    return (
      <div className="h-[calc(100svh-64px)] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  const allItems = [...(data?.bookings || []), ...(data?.orders || [])]
    .sort((a, b) => b.CreatedAt - a.CreatedAt)

  return (
    <div className="min-h-[calc(100svh-64px)] bg-background">
      <div className="container mx-auto p-4 sm:p-6 lg:p-8 max-w-7xl">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <h1 className="text-3xl font-bold mb-2">My Bookings & Orders</h1>
          <p className="text-muted-foreground">Manage your service bookings and product orders</p>
        </motion.div>

        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-6 flex flex-col sm:flex-row gap-4"
        >
          <div className="flex flex-wrap gap-2">
            <span className="text-sm font-medium self-center">Status:</span>
            {["all", "pending", "approved", "rejected", "cancelled"].map((f) => (
              <Button
                key={f}
                size="sm"
                variant={filter === f ? "default" : "outline"}
                onClick={() => setFilter(f as any)}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </Button>
            ))}
          </div>
          
          <div className="flex flex-wrap gap-2">
            <span className="text-sm font-medium self-center">Type:</span>
            {["all", "booking", "order"].map((f) => (
              <Button
                key={f}
                size="sm"
                variant={typeFilter === f ? "default" : "outline"}
                onClick={() => setTypeFilter(f as any)}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </Button>
            ))}
          </div>
        </motion.div>

        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-4 p-4 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300"
          >
            {error}
          </motion.div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : allItems.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center py-12"
          >
            <Card className="max-w-md mx-auto">
              <CardContent className="pt-6">
                <div className="text-6xl mb-4">📋</div>
                <h3 className="text-xl font-semibold mb-2">No items found</h3>
                <p className="text-muted-foreground">
                  {filter !== "all" || typeFilter !== "all"
                    ? "Try changing your filters"
                    : "Start a chat to get booking and order suggestions"}
                </p>
              </CardContent>
            </Card>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="grid gap-4 sm:grid-cols-1 lg:grid-cols-2"
          >
            <AnimatePresence mode="popLayout">
              {allItems.map((item, index) => (
                <motion.div
                  key={item.BookingOrderId}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className={`h-full transition-shadow hover:shadow-lg ${
                    item.Type === "booking" 
                      ? "border-green-200 dark:border-green-800" 
                      : "border-blue-200 dark:border-blue-800"
                  }`}>
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          {item.Type === "booking" ? (
                            <Calendar className="h-5 w-5 text-green-600 dark:text-green-400" />
                          ) : (
                            <ShoppingCart className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                          )}
                          <CardTitle className="text-lg">
                            {item.Type === "booking" ? "Service Booking" : "Product Order"}
                          </CardTitle>
                        </div>
                        {getStatusBadge(item.Status)}
                      </div>
                      <CardDescription className="text-sm font-medium">
                        {item.VendorName}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div>
                        <p className="font-semibold text-sm">{item.ServiceProduct}</p>
                        <p className="text-sm text-muted-foreground mt-1">{item.Message}</p>
                      </div>
                      
                      {item.SuggestedQuantity && (
                        <div className="text-sm">
                          <span className="text-muted-foreground">Quantity: </span>
                          <span className="font-medium">{item.SuggestedQuantity}</span>
                        </div>
                      )}
                      
                      <div className="text-sm">
                        <span className="text-muted-foreground">Cost: </span>
                        <span className="font-semibold text-primary">{item.EstimatedCost}</span>
                      </div>

                      <div className="text-xs text-muted-foreground pt-2 border-t">
                        <div>Created: {new Date(item.CreatedAtISO).toLocaleString()}</div>
                        {item.UpdatedAt !== item.CreatedAt && (
                          <div>Updated: {new Date(item.UpdatedAtISO).toLocaleString()}</div>
                        )}
                      </div>

                      {item.Status === "pending" && (
                        <div className="flex gap-2 pt-2">
                          <Button
                            size="sm"
                            className="flex-1 bg-green-600 hover:bg-green-700"
                            onClick={() => updateStatus(item.BookingOrderId, item.Type, "approved")}
                            disabled={updating === item.BookingOrderId}
                          >
                            {updating === item.BookingOrderId ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <>
                                <CheckCircle2 className="h-4 w-4 mr-1" />
                                Approve
                              </>
                            )}
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            className="flex-1"
                            onClick={() => updateStatus(item.BookingOrderId, item.Type, "rejected")}
                            disabled={updating === item.BookingOrderId}
                          >
                            {updating === item.BookingOrderId ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <>
                                <XCircle className="h-4 w-4 mr-1" />
                                Reject
                              </>
                            )}
                          </Button>
                        </div>
                      )}

                      {item.Status === "approved" && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="w-full"
                          onClick={() => updateStatus(item.BookingOrderId, item.Type, "cancelled")}
                          disabled={updating === item.BookingOrderId}
                        >
                          {updating === item.BookingOrderId ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <>
                              <Ban className="h-4 w-4 mr-1" />
                              Cancel
                            </>
                          )}
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-6 text-center text-sm text-muted-foreground"
        >
          Total: {data?.total_count || 0} items
          {data && data.bookings_count > 0 && ` • ${data.bookings_count} booking${data.bookings_count !== 1 ? 's' : ''}`}
          {data && data.orders_count > 0 && ` • ${data.orders_count} order${data.orders_count !== 1 ? 's' : ''}`}
        </motion.div>
      </div>
    </div>
  )
}
