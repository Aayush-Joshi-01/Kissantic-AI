"use client"

import type React from "react"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useAuth } from "@/contexts/auth-context"

export default function SiteHeader() {
  const pathname = usePathname()
  const { isAuthenticated, logout } = useAuth()

  return (
    <nav className="border-b bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3 md:gap-6">
          <Link href="/" className="flex items-center gap-2 group hover:bg-background/90 p-2 rounded-md">
            <img
              src="/logo-kisaantic.jpg"
              alt="Kisaantic logo"
              className="h-7 w-7 rounded-md ring-1 ring-border transition-transform duration-200 group-hover:scale-105"
            />
            <div className="leading-tight">
              <div className="font-semibold tracking-tight">
                <span className="text-primary">Kisaantic</span> <span className="opacity-80">AI</span>
              </div>
              <div className="text-[11px] text-muted-foreground hidden sm:block">The Farmer&apos;s AI Friend</div>
            </div>
          </Link>
          <div className="hidden md:flex items-center gap-4 text-sm">
            <HeaderLink href="/" current={pathname === "/"}>
              Home
            </HeaderLink>
            <HeaderLink href="/chat" current={pathname?.startsWith("/chat")}>
              Chat
            </HeaderLink>
            <HeaderLink href="/bookings-orders" current={pathname?.startsWith("/bookings-orders")}>
              Bookings & Orders
            </HeaderLink>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!isAuthenticated ? (
            <>
              <Button asChild size="sm">
                <Link href="/login">Login</Link>
              </Button>
              <Button asChild size="sm" variant="secondary">
                <Link href="/signup">Sign up</Link>
              </Button>
            </>
          ) : (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button aria-label="Open profile menu">
                  <Avatar className="h-8 w-8 ring-1 ring-border">
                    <AvatarImage src="/logo-kisaantic.jpg" alt="Profile" />
                    <AvatarFallback>KA</AvatarFallback>
                  </Avatar>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link href="/profile">Profile</Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link href="/bookings-orders">Bookings & Orders</Link>
                </DropdownMenuItem>
                <DropdownMenuItem onClick={logout}>Logout</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
    </nav>
  )
}

function HeaderLink({ href, current, children }: { href: string; current?: boolean; children: React.ReactNode }) {
  return (
    <Link href={href} className={cn("hover:underline", current && "font-medium")}>
      {children}
    </Link>
  )
}
