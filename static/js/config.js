/**
 * Helioz AI - Application Configuration
 * Contains Firebase web client config and app defaults.
 */

// REPLACE WITH YOUR FIREBASE WEB APP CONFIGURATION IF USING FIREBASE AUTH
// (Obtain from Firebase Console -> Project Settings -> General -> Your apps -> Web app)
export const firebaseConfig = {
  apiKey: "AIzaSyAa3ESZpGZ_hoY3-sMvPiLDFpCkcTqBxwc",
  authDomain: "helioz-e8c32.firebaseapp.com",
  projectId: "helioz-e8c32",
  storageBucket: "helioz-e8c32.firebasestorage.app",
  messagingSenderId: "960866423324",
  appId: "1:960866423324:web:0972c9b2bf8c27924385d9",
  measurementId: "G-26XWN4N2FC"
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
