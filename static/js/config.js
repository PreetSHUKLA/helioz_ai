/**
 * Helioz AI - Application Configuration
 * Contains Firebase web client config and app defaults.
 */

// REPLACE WITH YOUR FIREBASE WEB APP CONFIGURATION IF USING FIREBASE AUTH
// (Obtain from Firebase Console -> Project Settings -> General -> Your apps -> Web app)
export const firebaseConfig = {
  apiKey: "AIzaSy_YOUR_FIREBASE_WEB_API_KEY",
  authDomain: "your-project-id.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project-id.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abcdef1234567890"
};

// Check if Firebase credentials have been configured by the user
export function isFirebaseConfigured() {
  return (
    firebaseConfig.apiKey &&
    !firebaseConfig.apiKey.includes("YOUR_FIREBASE") &&
    firebaseConfig.projectId !== "your-project-id"
  );
}

export const APP_CONFIG = {
  MAX_NOTEBOOKS_QUOTA: 3,
  DEFAULT_COMPILATION_TOPICS: 3,
  API_TIMEOUT_MS: 120000,
};
