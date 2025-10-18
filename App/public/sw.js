const CACHE_VERSION = "kisaantic-v2"
const STATIC_CACHE = `${CACHE_VERSION}-static`
const API_BASE = "https://d8o991ajjl.execute-api.ap-south-1.amazonaws.com"

// Only cache these static assets
const STATIC_ASSETS = [
  "/manifest.webmanifest",
  "/logo-kisaantic.jpg",
  "/placeholder-logo.png",
  "/placeholder-logo.svg",
  "/placeholder-user.jpg",
  "/icons/icon-192.jpg",
  "/icons/icon-512.jpg",
]

// Install - cache only static assets
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(STATIC_CACHE)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  )
})

// Activate - clean old caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== STATIC_CACHE)
          .map((key) => caches.delete(key))
      )
    )
  )
  self.clients.claim()
})

// Fetch strategy
self.addEventListener("fetch", (event) => {
  const { request } = event
  const url = new URL(request.url)

  // NEVER cache API calls
  if (url.href.startsWith(API_BASE) || url.pathname.startsWith("/api")) {
    event.respondWith(fetch(request))
    return
  }

  // NEVER cache auth-related data
  if (request.method !== "GET" || url.search.includes("token")) {
    event.respondWith(fetch(request))
    return
  }

  // Cache-first for static assets only
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached
      
      return fetch(request).then((response) => {
        // Only cache successful responses for static assets
        if (response.ok && STATIC_ASSETS.some(asset => url.pathname.includes(asset))) {
          const clone = response.clone()
          caches.open(STATIC_CACHE).then((cache) => cache.put(request, clone))
        }
        return response
      })
    })
  )
})
