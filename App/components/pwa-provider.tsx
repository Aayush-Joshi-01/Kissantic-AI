"use client"

import { useEffect } from "react"

export default function PWAProvider() {
  useEffect(() => {
    if ("serviceWorker" in navigator) {
      const register = async () => {
        try {
          await navigator.serviceWorker.register("/sw.js")
        } catch (e) {
          // swallow registration errors
        }
      }
      register()
    }
  }, [])
  return null
}
