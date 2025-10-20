"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { BookingSuggestion, OrderSuggestion } from "@/lib/types"
import { fetchWithAuth } from "@/lib/api"
import { motion } from "framer-motion"
import { CheckCircle2, XCircle, Loader2, ShoppingCart, Calendar } from "lucide-react"

interface Props {
  bookingSuggestion?: BookingSuggestion
  orderSuggestion?: OrderSuggestion
  messageId: string
  sessionId: string
  onConfirm?: () => void
}

export function BookingOrderSuggestion({ 
  bookingSuggestion, 
  orderSuggestion, 
  messageId,
  sessionId,
  onConfirm 
}: Props) {
  const [bookingStatus, setBookingStatus] = useState<"idle" | "confirming" | "confirmed" | "error">("idle")
  const [orderStatus, setOrderStatus] = useState<"idle" | "confirming" | "confirmed" | "error">("idle")
  const [error, setError] = useState<string | null>(null)

  const confirmBooking = async () => {
    if (!bookingSuggestion) return
    setBookingStatus("confirming")
    setError(null)
    
    try {
      const res = await fetchWithAuth("/api/bookings-orders/update", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          booking_order_id: bookingSuggestion.booking_id,
          type: "booking",
          status: "approved",
        }),
      })

      if (res.ok) {
        setBookingStatus("confirmed")
        onConfirm?.()
      } else {
        const data = await res.json()
        throw new Error(data?.message || "Failed to confirm booking")
      }
    } catch (err: any) {
      setError(err.message)
      setBookingStatus("error")
    }
  }

  const confirmOrder = async () => {
    if (!orderSuggestion) return
    setOrderStatus("confirming")
    setError(null)
    
    try {
      const res = await fetchWithAuth("/api/bookings-orders/update", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          booking_order_id: orderSuggestion.order_id,
          type: "order",
          status: "approved",
        }),
      })

      if (res.ok) {
        setOrderStatus("confirmed")
        onConfirm?.()
      } else {
        const data = await res.json()
        throw new Error(data?.message || "Failed to confirm order")
      }
    } catch (err: any) {
      setError(err.message)
      setOrderStatus("error")
    }
  }

  if (!bookingSuggestion && !orderSuggestion) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="mt-3"
    >
      <Accordion type="single" collapsible className="w-full">
        <AccordionItem value="suggestions" className="border rounded-lg overflow-hidden">
          <AccordionTrigger className="px-4 hover:no-underline bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-950 dark:to-blue-950">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1">
                {bookingSuggestion && <Calendar className="h-4 w-4 text-green-600 dark:text-green-400" />}
                {orderSuggestion && <ShoppingCart className="h-4 w-4 text-blue-600 dark:text-blue-400" />}
              </div>
              <span className="font-semibold">
                {bookingSuggestion && orderSuggestion
                  ? "Booking & Order Available"
                  : bookingSuggestion
                  ? "Booking Available"
                  : "Order Available"}
              </span>
            </div>
          </AccordionTrigger>
          <AccordionContent className="px-4 pb-4">
            <div className="space-y-3">
              {error && (
                <div className="p-2 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300">
                  {error}
                </div>
              )}

              {bookingSuggestion && (
                <Card className="border-green-200 dark:border-green-800">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-5 w-5 text-green-600 dark:text-green-400" />
                        <CardTitle className="text-base">Service Booking</CardTitle>
                      </div>
                      {bookingStatus === "confirmed" && (
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                      )}
                    </div>
                    <CardDescription className="text-xs">{bookingSuggestion.vendor}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="text-sm">
                      <p className="font-medium">{bookingSuggestion.service}</p>
                      <p className="text-muted-foreground text-xs mt-1">{bookingSuggestion.message}</p>
                    </div>
                    <div className="flex items-center justify-between pt-2">
                      <span className="text-sm font-semibold text-green-600 dark:text-green-400">
                        {bookingSuggestion.estimated_cost}
                      </span>
                      {bookingStatus === "idle" && (
                        <Button size="sm" onClick={confirmBooking} className="bg-green-600 hover:bg-green-700">
                          Confirm Booking
                        </Button>
                      )}
                      {bookingStatus === "confirming" && (
                        <Button size="sm" disabled>
                          <Loader2 className="h-4 w-4 animate-spin mr-2" />
                          Confirming...
                        </Button>
                      )}
                      {bookingStatus === "confirmed" && (
                        <span className="text-sm text-green-600 dark:text-green-400 flex items-center gap-1">
                          <CheckCircle2 className="h-4 w-4" />
                          Confirmed
                        </span>
                      )}
                      {bookingStatus === "error" && (
                        <Button size="sm" variant="destructive" onClick={confirmBooking}>
                          <XCircle className="h-4 w-4 mr-2" />
                          Retry
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {orderSuggestion && (
                <Card className="border-blue-200 dark:border-blue-800">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <ShoppingCart className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                        <CardTitle className="text-base">Product Order</CardTitle>
                      </div>
                      {orderStatus === "confirmed" && (
                        <CheckCircle2 className="h-5 w-5 text-blue-600" />
                      )}
                    </div>
                    <CardDescription className="text-xs">{orderSuggestion.vendor}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="text-sm">
                      <p className="font-medium">{orderSuggestion.product}</p>
                      <p className="text-muted-foreground text-xs mt-1">{orderSuggestion.message}</p>
                      {orderSuggestion.suggested_quantity && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Quantity: {orderSuggestion.suggested_quantity}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center justify-between pt-2">
                      <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                        {orderSuggestion.estimated_cost}
                      </span>
                      {orderStatus === "idle" && (
                        <Button size="sm" onClick={confirmOrder} className="bg-blue-600 hover:bg-blue-700">
                          Confirm Order
                        </Button>
                      )}
                      {orderStatus === "confirming" && (
                        <Button size="sm" disabled>
                          <Loader2 className="h-4 w-4 animate-spin mr-2" />
                          Confirming...
                        </Button>
                      )}
                      {orderStatus === "confirmed" && (
                        <span className="text-sm text-blue-600 dark:text-blue-400 flex items-center gap-1">
                          <CheckCircle2 className="h-4 w-4" />
                          Confirmed
                        </span>
                      )}
                      {orderStatus === "error" && (
                        <Button size="sm" variant="destructive" onClick={confirmOrder}>
                          <XCircle className="h-4 w-4 mr-2" />
                          Retry
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </motion.div>
  )
}
