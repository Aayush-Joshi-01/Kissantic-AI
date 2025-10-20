export interface BookingSuggestion {
  booking_id: string
  vendor: string
  service: string
  message: string
  estimated_cost: string
}

export interface OrderSuggestion {
  order_id: string
  vendor: string
  product: string
  message: string
  suggested_quantity: string
  estimated_cost: string
}

export interface BookingOrder {
  PK: string
  SK: string
  BookingOrderId: string
  UserId: string
  SessionId: string
  MessageId: string
  Type: "booking" | "order"
  VendorName: string
  ServiceProduct: string
  SuggestedQuantity?: string
  EstimatedCost: string
  Message: string
  Status: "pending" | "approved" | "rejected" | "cancelled"
  AdditionalInfo: Record<string, any>
  CreatedAt: number
  UpdatedAt: number
  CreatedAtISO: string
  UpdatedAtISO: string
  EntityType: string
  GSI2PK?: string
}

export interface BookingsOrdersResponse {
  success: boolean
  bookings: BookingOrder[]
  orders: BookingOrder[]
  total_count: number
  bookings_count: number
  orders_count: number
}
