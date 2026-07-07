"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import type { ReactNode } from "react";
import { FileTextIcon, GearIcon, HomeIcon, MenuIcon, TraceIcon, XIcon } from "./icons";

const navItems = [
  { href: "/overview", label: "Overview", icon: HomeIcon },
  { href: "/audits", label: "Audits", icon: TraceIcon },
  { href: "/reports", label: "Reports", icon: FileTextIcon },
  { href: "/settings", label: "Settings", icon: GearIcon },
];

function SidebarContent({
  pathname,
  onClose,
}: {
  pathname: string;
  onClose?: () => void;
}) {
  return (
    <div className="flex h-full flex-col">
      {/* Logo */}
      <div className="flex items-center justify-between border-b border-rose-950/10 px-5 py-5 dark:border-white/10">
        <Link href="/" className="flex items-center gap-3" onClick={onClose}>
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-rose-700 font-display text-sm font-semibold text-white shadow-sm">
            V
          </span>
          <div>
            <p className="font-display text-sm font-semibold tracking-[0.2em] text-rose-800 dark:text-rose-300">
              VERDANT
            </p>
            <p className="text-[10px] text-slate-400 dark:text-slate-500">Dashboard</p>
          </div>
        </Link>
        {onClose && (
          <button
            onClick={onClose}
            className="rounded p-1 text-slate-400 hover:text-slate-700 dark:hover:text-white lg:hidden"
            aria-label="Close menu"
          >
            <XIcon className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav aria-label="Dashboard navigation" className="flex-1 px-3 py-4">
        <ul className="space-y-0.5">
          {navItems.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <li key={href}>
                <Link
                  href={href}
                  onClick={onClose}
                  aria-current={active ? "page" : undefined}
                  className={[
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors duration-200",
                    active
                      ? "bg-rose-700 text-white shadow-sm"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/10 dark:hover:text-white",
                  ].join(" ")}
                >
                  <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                  {label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Docs link */}
      <div className="px-3 pb-2">
        <Link
          href="/docs"
          onClick={onClose}
          className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:text-slate-500 dark:hover:bg-white/10 dark:hover:text-white"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-4 w-4 shrink-0" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
          Documentation
        </Link>
      </div>

      {/* Footer */}
      <div className="border-t border-rose-950/10 px-5 py-4 dark:border-white/10">
        <p className="mb-2 text-xs text-slate-400 dark:text-slate-500">VERDANT v0.1.0-beta</p>
        <Link
          href="/"
          className="text-xs font-medium text-slate-500 transition-colors hover:text-rose-700 dark:text-slate-400 dark:hover:text-rose-400"
        >
          ← Back to site
        </Link>
      </div>
    </div>
  );
}

export function DashboardShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex min-h-dvh bg-slate-50 text-slate-950 dark:bg-[#100a0b] dark:text-slate-50">
      {/* Desktop sidebar */}
      <aside className="hidden w-60 shrink-0 border-r border-rose-950/10 bg-white dark:border-white/10 dark:bg-white/[0.02] lg:block">
        <div className="sticky top-0 h-dvh overflow-y-auto">
          <SidebarContent pathname={pathname} />
        </div>
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-slate-950/50 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
          <aside className="absolute inset-y-0 left-0 w-60 border-r border-rose-950/10 bg-white shadow-xl dark:border-white/10 dark:bg-[#100a0b]">
            <SidebarContent pathname={pathname} onClose={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      {/* Content area */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Mobile topbar */}
        <header className="flex items-center justify-between border-b border-rose-950/10 bg-white px-5 py-4 dark:border-white/10 dark:bg-white/[0.02] lg:hidden">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-700 font-display text-sm font-semibold text-white">
              V
            </span>
            <span className="font-display text-sm font-semibold tracking-[0.2em] text-rose-800 dark:text-rose-300">
              VERDANT
            </span>
          </Link>
          <button
            id="mobile-menu-trigger"
            onClick={() => setMobileOpen(true)}
            className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/10"
            aria-label="Open navigation"
          >
            <MenuIcon className="h-5 w-5" />
          </button>
        </header>

        <main className="flex-1 px-6 py-8 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
