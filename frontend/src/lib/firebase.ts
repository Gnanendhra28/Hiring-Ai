import { initializeApp, getApps, getApp } from "firebase/app";
import {
  getAuth,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut as fbSignOut,
  sendPasswordResetEmail as fbSendPasswordResetEmail,
  onAuthStateChanged,
  setPersistence,
  browserSessionPersistence,
  User as FirebaseUser,
} from "firebase/auth";

// Firebase public browser key for project hiring-ai-4ae76
const DEFAULT_FB_KEY = process.env.NEXT_PUBLIC_FIREBASE_API_KEY || (typeof atob !== "undefined" ? atob("QUl6YVN5RHdzS1lYVU9POG95dWF1UEY5YnJZc1QwaGZOMnRjSG1B") : "");

export const firebaseConfig = {
  apiKey: DEFAULT_FB_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "hiring-ai-4ae76.firebaseapp.com",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "hiring-ai-4ae76",
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || "hiring-ai-4ae76.firebasestorage.app",
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || "19275497748",
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || "1:19275497748:web:d106cbd003ff2814d3c201",
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID || "G-6036PTV4FY",
};

// Initialize Firebase App singleton
export const firebaseApp = !getApps().length ? initializeApp(firebaseConfig) : getApp();
export const firebaseAuth = getAuth(firebaseApp);

if (typeof window !== "undefined") {
  setPersistence(firebaseAuth, browserSessionPersistence).catch(() => {});
}

export {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  fbSignOut,
  fbSendPasswordResetEmail,
  onAuthStateChanged,
};
export type { FirebaseUser };

/**
 * Retrieves the live Firebase ID Token for API requests.
 */
export async function getClientAuthToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  const user = firebaseAuth.currentUser;
  if (user) {
    try {
      const token = await user.getIdToken();
      localStorage.setItem("auth_token", token);
      localStorage.setItem("firebase_id_token", token);
      return token;
    } catch {
      // fallback to stored token
    }
  }
  return localStorage.getItem("auth_token") || localStorage.getItem("firebase_id_token");
}
