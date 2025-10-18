"use client"

import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"

const loadingMessages = [
  "Analyzing request",
  "Processing soil data",
  "Checking weather patterns",
  "Generating recommendations",
  "Invoking agents",
  "Retrieving information",
  "Calculating optimal solutions",
  "Preparing response",
  "Kissantic AI Thinking"
]

export function LoadingIndicator() {
  const [messageIndex, setMessageIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % loadingMessages.length)
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      className="bg-muted rounded-lg p-6 max-w-[85%] flex items-center gap-4"
    >
      <div className="relative w-12 h-12">
        <motion.div
          className="absolute inset-0 border-4 border-primary/20 rounded-full"
          initial={{ scale: 1, opacity: 1 }}
          animate={{ scale: 1.5, opacity: 0 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeOut" }}
        />
        <motion.div
          className="absolute inset-0 border-4 border-primary rounded-full border-t-transparent"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <svg className="w-6 h-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
      </div>
      
      <div className="flex-1 min-w-0">
        <AnimatePresence mode="wait">
          <motion.div
            key={messageIndex}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="text-sm font-medium text-foreground"
          >
            {loadingMessages[messageIndex]}
            <motion.span
              animate={{ opacity: [0, 1, 0] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              ...
            </motion.span>
          </motion.div>
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
