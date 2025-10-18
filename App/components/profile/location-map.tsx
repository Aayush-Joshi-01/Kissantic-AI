"use client"

import React from "react"
import { Map, Marker } from "pigeon-maps"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

type Props = {
  value?: { lat: number; lng: number; address?: string }
  onChange?: (v: { lat: number; lng: number; address?: string }) => void
}

type LatLng = [number, number]

type SearchResult = {
  display_name: string
  lat: string
  lon: string
}

export default function LocationMap({ value, onChange }: Props) {
  const fallbackCenter: LatLng = value ? [value.lat, value.lng] : [20.5937, 78.9629] // India center fallback
  const [center, setCenter] = React.useState<LatLng>(fallbackCenter)
  const [zoom, setZoom] = React.useState<number>(6)
  const [marker, setMarker] = React.useState<LatLng | null>(value ? [value.lat, value.lng] : null)
  const [address, setAddress] = React.useState<string>(value?.address ?? "")

  const [query, setQuery] = React.useState("")
  const [loading, setLoading] = React.useState(false)

  React.useEffect(() => {
    if (value?.lat != null && value?.lng != null) {
      const next: LatLng = [value.lat, value.lng]
      setCenter(next)
      setMarker(next)
      setAddress(value?.address ?? "")
    }
  }, [value?.lat, value?.lng, value?.address])

  async function geocode(q: string) {
    if (!q || q.trim().length < 2) return null
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
      q.trim(),
    )}&addressdetails=1&limit=5`
    const res = await fetch(url, { headers: { Accept: "application/json" } })
    if (!res.ok) return null
    const data = (await res.json()) as SearchResult[]
    return data?.[0] ?? null
  }

  async function reverse(lat: number, lng: number) {
    const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`
    const res = await fetch(url, { headers: { Accept: "application/json" } })
    if (!res.ok) return undefined
    const data = await res.json()
    return (data?.display_name as string | undefined) ?? undefined
  }

  async function handleSearch() {
    if (!query.trim()) return
    setLoading(true)
    try {
      const first = await geocode(query)
      if (first) {
        const lat = Number.parseFloat(first.lat)
        const lng = Number.parseFloat(first.lon)
        const next: LatLng = [lat, lng]
        setCenter(next)
        setMarker(next)
        setZoom(13)
        setAddress(first.display_name)
        onChange?.({ lat, lng, address: first.display_name })
      }
    } catch (e) {
      console.error("[v0] Geocode error:", e)
    } finally {
      setLoading(false)
    }
  }

  function useMyLocation() {
    if (!("geolocation" in navigator)) return
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude
        const lng = pos.coords.longitude
        const next: LatLng = [lat, lng]
        setCenter(next)
        setMarker(next)
        setZoom(13)
        const addr = await reverse(lat, lng)
        setAddress(addr ?? "")
        onChange?.({ lat, lng, address: addr })
      },
      (err) => {
        console.error("[v0] Geolocation error:", err?.message || err)
      },
      { enableHighAccuracy: true, maximumAge: 10_000, timeout: 15_000 },
    )
  }

  async function handleMapClick({ latLng }: { latLng: LatLng }) {
    const [lat, lng] = latLng
    const next: LatLng = [lat, lng]
    setMarker(next)
    setCenter(next)
    const addr = await reverse(lat, lng)
    setAddress(addr ?? "")
    onChange?.({ lat, lng, address: addr })
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Input
          placeholder="Search location (village, district, state)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault()
              handleSearch()
            }
          }}
        />
        <Button type="button" onClick={handleSearch} disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </Button>
        <Button type="button" variant="secondary" onClick={useMyLocation}>
          Use current
        </Button>
      </div>

      <div className="text-xs text-muted-foreground">{address || "No address selected"}</div>

      <div className="h-72 rounded-md overflow-hidden border">
        <Map
          height={288}
          center={center}
          zoom={zoom}
          onBoundsChanged={({ center: c, zoom: z }) => {
            setCenter(c as LatLng)
            setZoom(z as number)
          }}
          onClick={handleMapClick as any}
        >
          {marker ? <Marker anchor={marker} /> : null}
        </Map>
      </div>

      {marker && (
        <div className="text-xs">
          Selected: {marker[0].toFixed(5)}, {marker[1].toFixed(5)}
        </div>
      )}
    </div>
  )
}
