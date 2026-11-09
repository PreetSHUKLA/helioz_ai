/**
 * Helioz AI - API Service Layer
 * Coordinates all network interactions with the backend.
 */

import { store } from './store.js';

class ApiService {
  /**
   * Helper to get active authorization header
   */
  getAuthHeaders() {
    const state = store.getState();
    const token = state.userToken || (state.user ? state.user.uid : "local-developer");
    return {
      'Authorization': `Bearer ${token}`
    };
  }

  /**
   * Fetches backend telemetry & API configuration status
   */
  async getSystemStatus() {
    try {
      const res = await fetch('/api/status');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn("[API] Status check failed:", err.message);
      return {
        status: "offline",
        meta_api_configured: false,
        rapidapi_configured: false,
        youtube_api_configured: false,
        firebase_enabled: false,
        storage_mode: "Local Workspace"
      };
    }
  }

  /**
   * Retrieves all notebooks saved for the current user
   */
  async getNotebooks() {
    try {
      const res = await fetch('/api/notebooks', {
        headers: this.getAuthHeaders()
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || `Failed to fetch notebooks (HTTP ${res.status})`);
      }
      return await res.json();
    } catch (err) {
      console.error("[API] getNotebooks error:", err);
      throw err;
    }
  }

  /**
   * Triggers the course generation pipeline
   */
  async generateCourse({ syllabusText, imageFile }) {
    const formData = new FormData();
    if (syllabusText && syllabusText.trim()) {
      formData.append('syllabus_text', syllabusText.trim());
    }
    if (imageFile) {
      formData.append('image', imageFile);
    }

    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: formData
    });

    const data = await res.json();
    if (!res.ok || data.error) {
      throw new Error(data.error || `Compilation failed with status ${res.status}`);
    }

    return data;
  }

  /**
   * Deletes a saved notebook by ID
   */
  async deleteNotebook(notebookId) {
    const res = await fetch(`/api/notebooks/${notebookId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });

    const data = await res.json();
    if (!res.ok || data.error) {
      throw new Error(data.error || "Failed to delete notebook.");
    }

    return data;
  }
}

export const api = new ApiService();
