/**
 * Helioz AI - Command Bar Controller
 * Handles top telemetry indicators, quota meter, and identity controls.
 */

import { store } from '../store.js';

export class CommandBar {
  constructor() {
    this.quotaElement = document.getElementById('telemetry-quota');
    this.llmElement = document.getElementById('telemetry-llm');
    this.storageElement = document.getElementById('telemetry-storage');
    this.authButton = document.getElementById('header-auth-btn');
    this.userPill = document.getElementById('header-user-pill');
    this.userEmailText = document.getElementById('header-user-email');

    this.bindEvents();
    store.subscribe((state) => this.render(state));
  }

  bindEvents() {
    const brandElement = document.getElementById('brand-mark');
    if (brandElement) {
      brandElement.addEventListener('click', () => {
        store.setState({ currentView: 'studio' });
      });
    }

    if (this.authButton) {
      this.authButton.addEventListener('click', () => {
        window.dispatchEvent(new CustomEvent('open-auth-modal'));
      });
    }

    const logoutBtn = document.getElementById('header-logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => {
        window.dispatchEvent(new CustomEvent('execute-logout'));
      });
    }
  }

  render(state) {
    // 1. Quota Meter
    if (this.quotaElement) {
      const used = state.userNotebooks.length;
      this.quotaElement.innerHTML = `
        <span class="telemetry-dot ${used >= 3 ? 'warning' : ''}"></span>
        <span>QUOTA: ${used}/3 NOTEBOOKS</span>
      `;
    }

    // 2. LLM Engine Telemetry
    if (this.llmElement) {
      const isMetaReady = state.systemStatus.meta_api_configured;
      this.llmElement.innerHTML = `
        <span class="telemetry-dot ${isMetaReady ? '' : 'warning'}"></span>
        <span>LLM: ${isMetaReady ? 'META LLAMA (READY)' : 'META API (UNSET)'}</span>
      `;
    }

    // 3. Storage Mode
    if (this.storageElement) {
      const isFirestore = state.systemStatus.firebase_enabled;
      this.storageElement.innerHTML = `
        <span>STORE: ${isFirestore ? 'FIRESTORE' : 'LOCAL WORKSPACE'}</span>
      `;
    }

    // 4. User Identity Capsule
    if (state.user) {
      if (this.authButton) this.authButton.style.display = 'none';
      if (this.userPill) this.userPill.style.display = 'flex';
      if (this.userEmailText) {
        this.userEmailText.textContent = state.user.email || (state.user.isGuest ? 'Guest Studio' : 'Developer');
      }
    } else {
      if (this.authButton) this.authButton.style.display = 'inline-flex';
      if (this.userPill) this.userPill.style.display = 'none';
    }
  }
}
