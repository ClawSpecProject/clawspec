"use client";

import { useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

/**
 * Top navigation bar component.
 *
 * - Displays the app name/logo linking to /tasks.
 * - Shows the current user's name from AuthContext.
 * - Provides a Log Out button that signs the user out and redirects to /login.
 * - Only rendered for authenticated users (intended to be placed inside an
 *   AuthGuard-protected layout).
 */
export default function Navbar() {
  const { userProfile, logOut } = useAuth();
  const router = useRouter();

  const handleLogOut = useCallback(async () => {
    try {
      await logOut();
      router.replace("/login");
    } catch {
      // Even if logout fails unexpectedly, redirect to login
      router.replace("/login");
    }
  }, [logOut, router]);

  // Don't render the navbar if there is no authenticated user profile
  if (!userProfile) {
    return null;
  }

  return (
    <nav className="sticky top-0 z-30 border-b border-gray-200 bg-white">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* App name / logo */}
        <Link
          href="/tasks"
          className="text-lg font-bold text-primary-600 transition-colors hover:text-primary-700"
        >
          Task Manager
        </Link>

        {/* Right side: user name + log out */}
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-gray-700">
            {userProfile.name}
          </span>
          <button
            type="button"
            onClick={handleLogOut}
            className="btn-secondary text-sm"
          >
            Log Out
          </button>
        </div>
      </div>
    </nav>
  );
}
