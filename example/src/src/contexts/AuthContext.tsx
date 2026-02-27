"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  useMemo,
} from "react";
import { User, onAuthStateChanged } from "firebase/auth";
import { auth } from "@/lib/firebase";
import { UserProfile } from "@/types/user";
import { getUserProfile } from "@/services/users";
import {
  signUp as authSignUp,
  logIn as authLogIn,
  logOut as authLogOut,
} from "@/services/auth";

/** Duration (in milliseconds) after which a session is considered expired: 24 hours. */
const SESSION_EXPIRY_MS = 24 * 60 * 60 * 1000;

/** localStorage key used to persist the session start timestamp. */
const SESSION_TIMESTAMP_KEY = "auth_session_timestamp";

interface AuthContextValue {
  /** The currently authenticated Firebase Auth user, or null if signed out. */
  currentUser: User | null;
  /** The Firestore user profile for the current user, or null if not loaded / signed out. */
  userProfile: UserProfile | null;
  /** True while the initial auth state is being determined. */
  loading: boolean;
  /** Create a new account, store the profile in Firestore, and start a session. */
  signUp: (name: string, email: string, password: string) => Promise<void>;
  /** Sign in with email and password and start a session. */
  logIn: (email: string, password: string) => Promise<void>;
  /** Sign out and clear the session. */
  logOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Hook that returns the current authentication context value.
 * Must be used within an <AuthProvider>.
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

/**
 * Stores the current timestamp in localStorage so we can enforce a
 * 24-hour session expiry window on subsequent page loads.
 */
function setSessionTimestamp(): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(SESSION_TIMESTAMP_KEY, Date.now().toString());
  }
}

/**
 * Returns true if the stored session timestamp is older than 24 hours
 * (or if no timestamp exists, which means the session is invalid).
 */
function isSessionExpired(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  const stored = localStorage.getItem(SESSION_TIMESTAMP_KEY);
  if (!stored) {
    return true;
  }
  const elapsed = Date.now() - parseInt(stored, 10);
  return elapsed >= SESSION_EXPIRY_MS;
}

/**
 * Removes the session timestamp from localStorage.
 */
function clearSessionTimestamp(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(SESSION_TIMESTAMP_KEY);
  }
}

interface AuthProviderProps {
  children: React.ReactNode;
}

/**
 * Provider component that wraps the app and supplies authentication state
 * to all descendants via the useAuth() hook.
 *
 * - Listens to Firebase `onAuthStateChanged` for real-time auth state.
 * - Fetches the matching Firestore user profile whenever a user is detected.
 * - Enforces a 24-hour session expiry: if the stored session timestamp
 *   exceeds 24 hours the user is automatically signed out.
 * - Firebase Auth persistence is set to `browserLocalPersistence` in
 *   `src/lib/firebase.ts`, so sessions survive page refreshes within the
 *   24-hour window.
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (user) {
        // Check whether the 24-hour session window has elapsed.
        if (isSessionExpired()) {
          // Session expired – sign the user out silently.
          await authLogOut();
          clearSessionTimestamp();
          setCurrentUser(null);
          setUserProfile(null);
          setLoading(false);
          return;
        }

        setCurrentUser(user);

        try {
          const profile = await getUserProfile(user.uid);
          setUserProfile(profile);
        } catch {
          // If fetching the profile fails, leave it as null.
          setUserProfile(null);
        }
      } else {
        setCurrentUser(null);
        setUserProfile(null);
        clearSessionTimestamp();
      }

      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const signUp = useCallback(
    async (name: string, email: string, password: string): Promise<void> => {
      const credential = await authSignUp(name, email, password);
      setSessionTimestamp();

      // Eagerly set the profile so downstream consumers don't need to wait
      // for the onAuthStateChanged callback.
      setUserProfile({
        uid: credential.user.uid,
        name,
        email,
      });
    },
    []
  );

  const logIn = useCallback(
    async (email: string, password: string): Promise<void> => {
      await authLogIn(email, password);
      setSessionTimestamp();
    },
    []
  );

  const logOut = useCallback(async (): Promise<void> => {
    await authLogOut();
    clearSessionTimestamp();
    setCurrentUser(null);
    setUserProfile(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      currentUser,
      userProfile,
      loading,
      signUp,
      logIn,
      logOut,
    }),
    [currentUser, userProfile, loading, signUp, logIn, logOut]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export default AuthContext;
