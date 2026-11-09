/**
 * Helioz AI - Main Application Bootstrapper
 * Orchestrates modules, routes views, and hydrates initial state.
 */

import { store } from './store.js';
import { api } from './api.js';
import { CURATED_COURSES } from './courses-data.js';
import { CommandBar } from './ui/command-bar.js';
import { Dashboard } from './ui/dashboard.js';
import { Synthesizer } from './ui/synthesizer.js';
import { Player } from './ui/player.js';
import { QuizEngine } from './ui/quiz.js';
import { AuthModal } from './ui/auth-modal.js';
import { toast } from './ui/toast.js';

class App {
  constructor() {
    this.studioView = document.getElementById('studio-view');
    this.theaterView = document.getElementById('theater-view');
  }

  async init() {
    console.log("⚡ [Helioz AI] Initializing modular course studio...");

    // 1. Populate curated courses in state store
    store.setState({ featuredCourses: CURATED_COURSES });

    // 2. Initialize UI components
    new CommandBar();
    new Dashboard();
    new Synthesizer();
    new Player();
    new QuizEngine();
    new AuthModal();

    // 3. Subscribe to view changes
    store.subscribe((state) => this.handleViewChange(state.currentView));

    // 4. Check backend status & load initial notebooks
    await this.hydrateTelemetry();
    await this.hydrateNotebooks();
  }

  handleViewChange(viewName) {
    if (viewName === 'theater') {
      if (this.studioView) this.studioView.style.display = 'none';
      if (this.theaterView) this.theaterView.style.display = 'grid';
    } else {
      if (this.studioView) this.studioView.style.display = 'grid';
      if (this.theaterView) this.theaterView.style.display = 'none';
    }
  }

  async hydrateTelemetry() {
    try {
      const status = await api.getSystemStatus();
      store.setState({ systemStatus: status });
      if (!status.meta_api_configured) {
        console.warn("[Helioz] META_API_KEY is not yet populated in .env.");
      }
    } catch (e) {
      console.warn("[Helioz] Could not reach backend status endpoint:", e);
    }
  }

  async hydrateNotebooks() {
    try {
      const notebooks = await api.getNotebooks();
      store.setState({ userNotebooks: notebooks || [] });
    } catch (e) {
      console.log("[Helioz] Default notebooks fetch notice:", e.message);
    }
  }
}

// Boot application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const app = new App();
  app.init();
});
