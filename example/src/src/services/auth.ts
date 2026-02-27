import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  UserCredential,
} from "firebase/auth";
import { doc, setDoc } from "firebase/firestore";
import { auth, db } from "@/lib/firebase";
import { UserProfile } from "@/types/user";

/**
 * Maps Firebase Auth error codes to user-friendly error messages.
 */
function mapFirebaseError(errorCode: string): string {
  switch (errorCode) {
    case "auth/email-already-in-use":
      return "Email already in use";
    case "auth/invalid-email":
      return "Invalid email address";
    case "auth/operation-not-allowed":
      return "Email/password accounts are not enabled";
    case "auth/weak-password":
      return "Password is too weak";
    case "auth/user-disabled":
      return "This account has been disabled";
    case "auth/user-not-found":
      return "Invalid email or password";
    case "auth/wrong-password":
      return "Invalid email or password";
    case "auth/invalid-credential":
      return "Invalid email or password";
    case "auth/too-many-requests":
      return "Too many failed attempts. Please try again later";
    case "auth/network-request-failed":
      return "Network error. Please check your connection";
    default:
      return "An unexpected error occurred. Please try again";
  }
}

/**
 * Creates a new Firebase Auth user, then writes a profile document
 * to the Firestore `users` collection with uid, name, and email.
 */
export async function signUp(
  name: string,
  email: string,
  password: string
): Promise<UserCredential> {
  try {
    const credential = await createUserWithEmailAndPassword(
      auth,
      email,
      password
    );

    const userProfile: UserProfile = {
      uid: credential.user.uid,
      name,
      email,
    };

    await setDoc(doc(db, "users", credential.user.uid), userProfile);

    return credential;
  } catch (error: unknown) {
    if (
      error !== null &&
      typeof error === "object" &&
      "code" in error &&
      typeof (error as { code: unknown }).code === "string"
    ) {
      throw new Error(mapFirebaseError((error as { code: string }).code));
    }
    throw new Error("An unexpected error occurred. Please try again");
  }
}

/**
 * Signs in an existing user with email and password.
 */
export async function logIn(
  email: string,
  password: string
): Promise<UserCredential> {
  try {
    const credential = await signInWithEmailAndPassword(auth, email, password);
    return credential;
  } catch (error: unknown) {
    if (
      error !== null &&
      typeof error === "object" &&
      "code" in error &&
      typeof (error as { code: unknown }).code === "string"
    ) {
      throw new Error(mapFirebaseError((error as { code: string }).code));
    }
    throw new Error("Invalid email or password");
  }
}

/**
 * Signs out the currently authenticated user.
 */
export async function logOut(): Promise<void> {
  try {
    await signOut(auth);
  } catch (error: unknown) {
    if (
      error !== null &&
      typeof error === "object" &&
      "code" in error &&
      typeof (error as { code: unknown }).code === "string"
    ) {
      throw new Error(mapFirebaseError((error as { code: string }).code));
    }
    throw new Error("An unexpected error occurred. Please try again");
  }
}
