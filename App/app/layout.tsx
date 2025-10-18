import type React from "react"
import type { Metadata, Viewport } from "next"
import { GeistSans } from "geist/font/sans"
import { GeistMono } from "geist/font/mono"
import { Analytics } from "@vercel/analytics/next"
import "./globals.css"
import { Suspense } from "react"
import SiteHeader from "@/components/site-header"
import PWAProvider from "@/components/pwa-provider"
import { AuthProvider } from "@/contexts/auth-context"

export const metadata: Metadata = {
  title: "Kisaantic AI - The Farmer's AI Friend",
  description: "Intelligent agentic AI platform helping farmers choose the right crops, secure equipment at the best prices, and sell directly to nearby markets.",
  generator: "v0.app",
  manifest: "/manifest.webmanifest",
  applicationName: "Kisaantic AI",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Kisaantic AI",
  },
  formatDetection: {
    telephone: false,
  },
  icons: {
    icon: [
      { url: "/logo-kisaantic.jpg", sizes: "any", type: "image/jpeg" },
      { url: "/icons/icon-192.jpg", sizes: "192x192", type: "image/jpeg" },
      { url: "/icons/icon-512.jpg", sizes: "512x512", type: "image/jpeg" },
    ],
    shortcut: [{ url: "/logo-kisaantic.jpg", type: "image/jpeg" }],
    apple: [
      { url: "/logo-kisaantic.jpg", sizes: "any", type: "image/jpeg" },
      { url: "/icons/icon-192.jpg", sizes: "192x192", type: "image/jpeg" },
      { url: "/icons/icon-512.jpg", sizes: "512x512", type: "image/jpeg" },
    ],
  },
}

export const viewport: Viewport = {
  themeColor: "#4CAF50",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/logo-kisaantic.jpg" type="image/jpeg" />
        <link rel="shortcut icon" href="/logo-kisaantic.jpg" type="image/jpeg" />
        <link rel="apple-touch-icon" href="/logo-kisaantic.jpg" />
        <link rel="manifest" href="/manifest.webmanifest" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="Kisaantic AI" />
      </head>
      <body className={`font-sans ${GeistSans.variable} ${GeistMono.variable}`}>
        <AuthProvider>
          <SiteHeader />
          <main className="min-h-[calc(100svh-64px)] overflow-hidden">{children}</main>
          <PWAProvider />
        </AuthProvider>
        <Suspense fallback={null}>
          <Analytics />
        </Suspense>
      </body>
    </html>
  )
}
