/**
 * Helioz AI - Reactive State Store
 * Centralized state container with subscriber notification.
 */

class StateStore {
  constructor() {
    this.state = {
      user: null,                  // { uid, email, isGuest }
      userToken: null,             // Firebase Bearer token or local token
      userNotebooks: [],           // Array of user saved courses
      featuredCourses: [],         // Curated courses
      activeCourse: null,          // Current open course { course_title, modules, ... }
      currentModuleIndex: 0,       // Current active module index
      isCinemaMode: false,         // Cinema expansion state
      systemStatus: {              // Live backend telemetry
        status: "checking",
        llm_provider: "Meta Llama API",
        meta_api_configured: false,
        rapidapi_configured: false,
        youtube_api_configured: false,
        firebase_enabled: false,
        storage_mode: "Checking..."
      },
      currentView: "studio",       // "studio" | "theater"
      activeGalleryTab: "academy", // "academy" | "notebooks"
      isCompiling: false           // Generation in progress
    };

    this.listeners = new Set();
  }

  getState() {
    return this.state;
  }

  setState(partialState) {
    this.state = { ...this.state, ...partialState };
    this.notify();
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notify() {
    for (const listener of this.listeners) {
      try {
        listener(this.state);
      } catch (err) {
        console.error("[Store] Listener error:", err);
      }
    }
  }
}

export const store = new StateStore();
