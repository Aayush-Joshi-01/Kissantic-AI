"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { motion, AnimatePresence } from "framer-motion"

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export function PWAInstallButton() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [isInstallable, setIsInstallable] = useState(false)
  const [isIOS, setIsIOS] = useState(false)
  const [isAndroid, setIsAndroid] = useState(false)
  const [isInstalled, setIsInstalled] = useState(false)
  const [showInstructions, setShowInstructions] = useState(false)

  useEffect(() => {
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setIsInstalled(true)
      return
    }

    // Detect iOS
    const iOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !(window as any).MSStream
    setIsIOS(iOS)

    // Detect Android
    const android = /Android/.test(navigator.userAgent)
    setIsAndroid(android)

    // Listen for beforeinstallprompt event (Android/Chrome)
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
      setIsInstallable(true)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)

    // Listen for appinstalled event
    const handleAppInstalled = () => {
      setIsInstalled(true)
      setIsInstallable(false)
      setDeferredPrompt(null)
    }

    window.addEventListener('appinstalled', handleAppInstalled)

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
      window.removeEventListener('appinstalled', handleAppInstalled)
    }
  }, [])

  const handleInstallClick = async () => {
    if (!deferredPrompt) {
      if (isIOS) {
        setShowInstructions(true)
      }
      return
    }

    // Show the install prompt
    await deferredPrompt.prompt()

    // Wait for the user to respond to the prompt
    const { outcome } = await deferredPrompt.userChoice

    if (outcome === 'accepted') {
      setIsInstallable(false)
      setDeferredPrompt(null)
    }
  }

  const handleIOSInstall = () => {
    setShowInstructions(true)
  }

  // Don't show anything if already installed
  if (isInstalled) {
    return (
      <Card className="border-green-200 bg-green-50 dark:bg-green-950 dark:border-green-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-green-900 dark:text-green-100">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            App Installed
          </CardTitle>
          <CardDescription className="text-green-700 dark:text-green-300">
            Kisaantic AI is already installed on your device
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  // Show install option for iOS
  if (isIOS) {
    return (
      <Card className="border-blue-200 bg-blue-50 dark:bg-blue-950 dark:border-blue-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-900 dark:text-blue-100">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            Install App (iOS)
          </CardTitle>
          <CardDescription className="text-blue-700 dark:text-blue-300">
            Install Kisaantic AI on your iPhone or iPad for quick access
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button 
            onClick={handleIOSInstall} 
            className="w-full transition-all hover:scale-[1.02]"
            variant="default"
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            View Installation Instructions
          </Button>

          <AnimatePresence>
            {showInstructions && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-3 pt-3 border-t border-blue-200 dark:border-blue-800"
              >
                <div className="text-sm space-y-2 text-blue-900 dark:text-blue-100">
                  <p className="font-semibold">To install on iOS:</p>
                  <ol className="list-decimal list-inside space-y-2 ml-2">
                    <li className="flex items-start gap-2">
                      <span className="mt-0.5">1.</span>
                      <span>Tap the <strong>Share</strong> button (square with arrow) at the bottom of Safari</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="mt-0.5">2.</span>
                      <span>Scroll down and tap <strong>"Add to Home Screen"</strong></span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="mt-0.5">3.</span>
                      <span>Tap <strong>"Add"</strong> in the top right corner</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="mt-0.5">4.</span>
                      <span>The Kisaantic AI app will appear on your home screen</span>
                    </li>
                  </ol>
                </div>

                <div className="flex items-center gap-2 p-3 bg-blue-100 dark:bg-blue-900 rounded-lg text-xs text-blue-800 dark:text-blue-200">
                  <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Note: This feature only works in Safari browser on iOS</span>
                </div>

                <Button 
                  onClick={() => setShowInstructions(false)} 
                  variant="outline"
                  className="w-full"
                >
                  Close Instructions
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    )
  }

  // Show install button for Android/Chrome
  if (isInstallable && deferredPrompt) {
    return (
      <Card className="border-blue-200 bg-blue-50 dark:bg-blue-950 dark:border-blue-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-900 dark:text-blue-100">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            Install App
          </CardTitle>
          <CardDescription className="text-blue-700 dark:text-blue-300">
            Install Kisaantic AI for quick access and offline use
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button 
            onClick={handleInstallClick} 
            className="w-full transition-all hover:scale-[1.02]"
            variant="default"
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Install Kisaantic AI
          </Button>
        </CardContent>
      </Card>
    )
  }

  // Show Android manual instructions if not installable via prompt
  if (isAndroid) {
    return (
      <Card className="border-blue-200 bg-blue-50 dark:bg-blue-950 dark:border-blue-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-900 dark:text-blue-100">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            Install App (Android)
          </CardTitle>
          <CardDescription className="text-blue-700 dark:text-blue-300">
            Install Kisaantic AI on your Android device
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button 
            onClick={() => setShowInstructions(!showInstructions)} 
            className="w-full transition-all hover:scale-[1.02]"
            variant="default"
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            View Installation Instructions
          </Button>

          <AnimatePresence>
            {showInstructions && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-3 pt-3 border-t border-blue-200 dark:border-blue-800"
              >
                <div className="text-sm space-y-2 text-blue-900 dark:text-blue-100">
                  <p className="font-semibold">To install on Android:</p>
                  <ol className="list-decimal list-inside space-y-2 ml-2">
                    <li className="flex items-start gap-2">
                      <span className="mt-0.5">1.</span>
                      <span>Tap the <strong>menu</strong> button (three dots) in Chrome</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="mt-0.5">2.</span>
                      <span>Tap <strong>"Add to Home screen"</strong> or <strong>"Install app"</strong></span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="mt-0.5">3.</span>
                      <span>Tap <strong>"Install"</strong> or <strong>"Add"</strong></span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="mt-0.5">4.</span>
                      <span>The Kisaantic AI app will appear on your home screen</span>
                    </li>
                  </ol>
                </div>

                <Button 
                  onClick={() => setShowInstructions(false)} 
                  variant="outline"
                  className="w-full"
                >
                  Close Instructions
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    )
  }

  // Don't show anything if not on mobile or not installable
  return null
}
