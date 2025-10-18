"use client"

import React from "react"
import { Map, Marker } from "pigeon-maps"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

type LatLng = [number, number]

export type LocationValue = {
  lat: number
  lng: number
  label?: string
}

type Props = {
  value?: LocationValue
  onChange?: (val: LocationValue) => void
  className?: string
}

type SearchResult = {
  display_name: string
  lat: string
  lon: string
}

export default function LocationMap({ value, onChange, className }: Props) {
  const defaultCenter: LatLng = value ? [value.lat, value.lng] : [20.5937, 78.9629] // India center fallback
  const [center, setCenter] = React.useState<LatLng>(defaultCenter)
  const [zoom, setZoom] = React.useState<number>(6)
  const [marker, setMarker] = React.useState<LatLng | null>(value ? [value.lat, value.lng] : null)

  const [query, setQuery] = React.useState("")
  const [results, setResults] = React.useState<SearchResult[]>([])
  const [loading, setLoading] = React.useState(false)
  const [openList, setOpenList] = React.useState(false)

  React.useEffect(() => {
    if (value) {
      const next: LatLng = [value.lat, value.lng]
      setCenter(next)
      setMarker(next)
    }
  }, [value])

  async function searchPlaces(q: string) {
    if (!q || q.trim().length < 2) {
      setResults([])
      return
    }
    try {
      setLoading(true)
      // Nominatim search (public OSM geocoding)
      const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
        q,
      )}&addressdetails=1&limit=5`
      const res = await fetch(url, {
        headers: {
          // Set a friendly referer via browser; UA header cannot be set by fetch in browser
          Accept: "application/json",
        },
      })
      if (!res.ok) throw new Error("Failed to search locations")
      const data = (await res.json()) as SearchResult[]
      setResults(data)
      setOpenList(true)
    } catch (e) {
      console.error("[v0] Nominatim search error:", e)
      setResults([])
      setOpenList(false)
    } finally {
      setLoading(false)
    }
  }

  function handlePickFromSearch(item: SearchResult) {
    const lat = Number.parseFloat(item.lat)
    const lng = Number.parseFloat(item.lon)
    const pos: LatLng = [lat, lng]
    setCenter(pos)
    setMarker(pos)
    setZoom(13)
    setQuery(item.display_name)
    setOpenList(false)
    onChange?.({ lat, lng, label: item.display_name })
  }

  function handleMapClick({ latLng }: any) {
    const [lat, lng] = latLng as LatLng
    const pos: LatLng = [lat, lng]
    setMarker(pos)
    setCenter(pos)
    onChange?.({ lat, lng })
  }

  function useMyLocation() {
    if (!("geolocation" in navigator)) return
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude
        const lng = pos.coords.longitude
        const next: LatLng = [lat, lng]
        setCenter(next)
        setMarker(next)
        setZoom(13)
        onChange?.({ lat, lng })
      },
      (err) => {
        console.error("[v0] Geolocation error:", err?.message || err)
      },
      { enableHighAccuracy: true, maximumAge: 10_000, timeout: 15_000 },
    )
  }

  return (
    <Card className={className}>
      <CardContent className="p-4 grid gap-3">
        <div className="flex items-center gap-2">
          <label htmlFor="location-search" className="sr-only">
            Search for a location
          </label>
          <Input
            id="location-search"
            placeholder="Search for a location (city, village, district)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => query.length >= 2 && setOpenList(true)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault()
                searchPlaces(query)
              }
            }}
            aria-autocomplete="list"
          />
          <Button variant="default" onClick={() => searchPlaces(query)} disabled={loading}>
            {loading ? "Searching..." : "Search"}
          </Button>
          <Button variant="secondary" onClick={useMyLocation}>
            Use my location
          </Button>
        </div>

        {openList && results.length > 0 ? (
          <ul
            role="listbox"
            aria-label="Search results"
            className="max-h-56 overflow-auto rounded-md border border-border bg-card text-card-foreground"
          >
            {results.map((r, i) => (
              <li
                key={`${r.lat}-${r.lon}-${i}`}
                role="option"
                className="cursor-pointer px-3 py-2 hover:bg-muted"
                onClick={() => handlePickFromSearch(r)}
              >
                {r.display_name}
              </li>
            ))}
          </ul>
        ) : null}

        <div className="rounded-md overflow-hidden border">
          <Map
            height={360}
            center={center}
            zoom={zoom}
            onBoundsChanged={({ center: c, zoom: z }: any) => {
              setCenter(c)
              setZoom(z)
            }}
            onClick={handleMapClick}
          >
            {marker ? <Marker anchor={marker} /> : null}
          </Map>
        </div>

        <div className="text-sm text-muted-foreground">
          {marker ? (
            <span>
              Selected: {marker[0].toFixed(6)}, {marker[1].toFixed(6)}
            </span>
          ) : (
            <span>Click on the map to pick a location.</span>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
