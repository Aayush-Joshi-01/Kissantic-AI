"use client"

import useSWR from "swr"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import LocationMap from "./location-map"
import { PWAInstallButton } from "./pwa-install-button"
import { fetchWithAuth } from "@/lib/api"

type User = {
  user_id: string
  email: string
  name?: string
  phone?: string
  farm_size?: string
  crop_type?: string
  latitude?: number
  longitude?: number
  address?: string
}

export default function ProfileForm() {
  const { data, mutate, isLoading } = useSWR<User>("/api/auth/me", (url) => fetchWithAuth(url).then((r) => r.json()))
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState<Partial<User>>({})

  const update = (key: keyof User, val: any) => setForm((prev) => ({ ...prev, [key]: val }))

  const onSave = async () => {
    setSaving(true)
    try {
      const body: any = {}
      for (const [k, v] of Object.entries(form)) {
        if (v !== undefined) body[k] = v
      }
      const res = await fetchWithAuth("/api/auth/me", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
      if (res.ok) {
        await mutate()
        setForm({})
      }
    } finally {
      setSaving(false)
    }
  }

  const initialLocation =
    data?.latitude && data?.longitude ? { lat: data.latitude, lng: data.longitude, address: data?.address } : undefined

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Your Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="name">Full name</Label>
              <Input id="name" defaultValue={data?.name ?? ""} onChange={(e) => update("name", e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" defaultValue={data?.email ?? ""} disabled />
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
              <Input id="phone" defaultValue={data?.phone ?? ""} onChange={(e) => update("phone", e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="farm_size">Farm size (acres)</Label>
              <Input
                id="farm_size"
                defaultValue={data?.farm_size ?? ""}
                onChange={(e) => update("farm_size", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="crop_type">Primary crop</Label>
              <Input
                id="crop_type"
                defaultValue={data?.crop_type ?? ""}
                onChange={(e) => update("crop_type", e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Location</Label>
            <LocationMap
              value={initialLocation}
              onChange={(v) => {
                update("latitude", v.lat)
                update("longitude", v.lng)
                update("address", v.address)
              }}
            />
          </div>

          <div className="flex justify-end">
            <Button onClick={onSave} disabled={saving}>
              {saving ? "Saving..." : "Save changes"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <PWAInstallButton />
    </div>
  )
}
