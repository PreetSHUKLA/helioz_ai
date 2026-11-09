/**
 * Helioz AI - Dashboard & Gallery Controller
 * Manages Curated Academy courses, Custom User Notebooks, and deletion actions.
 */

import { store } from '../store.js';
import { api } from '../api.js';
import { toast } from './toast.js';

export class Dashboard {
  constructor() {
    this.tabAcademyBtn = document.getElementById('tab-academy-btn');
    this.tabNotebooksBtn = document.getElementById('tab-notebooks-btn');
    this.notebookCountBadge = document.getElementById('notebooks-count-badge');
    this.cardsGrid = document.getElementById('cards-grid');

    this.bindEvents();
    store.subscribe((state) => this.render(state));
  }

  bindEvents() {
    if (this.tabAcademyBtn) {
      this.tabAcademyBtn.addEventListener('click', () => {
        store.setState({ activeGalleryTab: 'academy' });
      });
    }

    if (this.tabNotebooksBtn) {
      this.tabNotebooksBtn.addEventListener('click', () => {
        store.setState({ activeGalleryTab: 'notebooks' });
      });
    }
  }

  render(state) {
    // 1. Update tab active states
    const isAcademy = state.activeGalleryTab === 'academy';
    if (this.tabAcademyBtn) {
      this.tabAcademyBtn.classList.toggle('active', isAcademy);
    }
    if (this.tabNotebooksBtn) {
      this.tabNotebooksBtn.classList.toggle('active', !isAcademy);
    }
    if (this.notebookCountBadge) {
      this.notebookCountBadge.textContent = state.userNotebooks.length;
    }

    // 2. Render Cards Grid
    if (!this.cardsGrid) return;

    if (isAcademy) {
      this.renderAcademyCourses(state.featuredCourses);
    } else {
      this.renderUserNotebooks(state.userNotebooks);
    }
  }

  renderAcademyCourses(courses) {
    if (!courses || courses.length === 0) {
      this.cardsGrid.innerHTML = `
        <div class="empty-deck">
          <p style="color: var(--text-muted); font-weight: 600;">No featured academy courses loaded.</p>
        </div>
      `;
      return;
    }

    this.cardsGrid.innerHTML = courses.map((course) => {
      const topicsHtml = (course.modules || [])
        .slice(0, 3)
        .map(m => `
          <div class="card-topic-item">
            <span class="card-topic-dot"></span>
            <span class="truncate-1">${m.topic}</span>
          </div>
        `).join('');

      return `
        <div class="notebook-card featured" data-course-id="${course.id}">
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
              <span class="card-badge gold">Curated Studio</span>
              <span class="card-badge font-mono">${(course.modules || []).length} Modules</span>
            </div>
            <h3 class="card-title">${course.course_title}</h3>
            <p style="font-size: 0.8125rem; color: var(--text-secondary); margin: 0.5rem 0 0.875rem 0; line-height: 1.4;">
              ${course.description || 'Deconstructed micro-curriculum with vetted video lectures and active-recall quizzes.'}
            </p>
            <div class="card-topics-list">
              ${topicsHtml}
            </div>
          </div>

          <div class="card-actions">
            <span style="font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono);">INSTANT LAUNCH</span>
            <button class="btn-primary" style="padding: 0.4rem 0.875rem; font-size: 0.8125rem;" data-action="open-academy" data-id="${course.id}">
              Study Now &rarr;
            </button>
          </div>
        </div>
      `;
    }).join('');

    // Attach click listeners
    this.cardsGrid.querySelectorAll('[data-action="open-academy"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const id = btn.getAttribute('data-id');
        this.openCourse(id, true);
      });
    });

    this.cardsGrid.querySelectorAll('.notebook-card').forEach(card => {
      card.addEventListener('click', () => {
        const id = card.getAttribute('data-course-id');
        this.openCourse(id, true);
      });
    });
  }

  renderUserNotebooks(notebooks) {
    if (!notebooks || notebooks.length === 0) {
      this.cardsGrid.innerHTML = `
        <div class="empty-deck">
          <div style="width: 48px; height: 48px; border-radius: var(--radius-md); background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); display: flex; align-items: center; justify-content: center; color: var(--solar-400); font-size: 1.5rem;">
            📓
          </div>
          <h4 style="font-size: 1.125rem; margin-top: 0.25rem;">No Custom Notebooks Yet</h4>
          <p style="font-size: 0.875rem; color: var(--text-secondary); max-width: 320px;">
            Synthesize a course using the left pane to extract granular micro-topics and vetted video lectures.
          </p>
          <button class="btn-primary" id="btn-focus-synthesizer" style="margin-top: 0.5rem;">
            Synthesize First Notebook
          </button>
        </div>
      `;

      const focusBtn = document.getElementById('btn-focus-synthesizer');
      if (focusBtn) {
        focusBtn.addEventListener('click', () => {
          const textarea = document.getElementById('syllabus-input');
          if (textarea) textarea.focus();
        });
      }
      return;
    }

    this.cardsGrid.innerHTML = notebooks.map((nb) => {
      const topicsHtml = (nb.modules || [])
        .slice(0, 3)
        .map(m => `
          <div class="card-topic-item">
            <span class="card-topic-dot"></span>
            <span class="truncate-1">${m.topic}</span>
          </div>
        `).join('');

      return `
        <div class="notebook-card" data-notebook-id="${nb.id}">
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
              <span class="card-badge">Custom Compiled</span>
              <span class="card-badge font-mono">${(nb.modules || []).length} Modules</span>
            </div>
            <h3 class="card-title">${nb.course_title || 'Untitled Curriculum'}</h3>
            <div class="card-topics-list" style="margin-top: 0.875rem;">
              ${topicsHtml}
            </div>
          </div>

          <div class="card-actions">
            <button class="card-delete-btn" data-action="delete" data-id="${nb.id}" title="Delete notebook from quota">
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
            <button class="btn-primary" style="padding: 0.4rem 0.875rem; font-size: 0.8125rem;" data-action="open-user" data-id="${nb.id}">
              Open Study &rarr;
            </button>
          </div>
        </div>
      `;
    }).join('');

    // Attach listeners
    this.cardsGrid.querySelectorAll('[data-action="open-user"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const id = btn.getAttribute('data-id');
        this.openCourse(id, false);
      });
    });

    this.cardsGrid.querySelectorAll('[data-action="delete"]').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const id = btn.getAttribute('data-id');
        await this.handleDelete(id);
      });
    });

    this.cardsGrid.querySelectorAll('.notebook-card').forEach(card => {
      card.addEventListener('click', () => {
        const id = card.getAttribute('data-notebook-id');
        this.openCourse(id, false);
      });
    });
  }

  async handleDelete(notebookId) {
    if (!confirm("Are you sure you want to delete this custom notebook? This will free up your quota.")) {
      return;
    }

    try {
      await api.deleteNotebook(notebookId);
      toast.success("Notebook removed successfully.");
      const updatedNotebooks = await api.getNotebooks();
      store.setState({ userNotebooks: updatedNotebooks });
    } catch (err) {
      toast.error(err.message || "Failed to delete notebook.");
    }
  }

  openCourse(courseId, isFeatured = false) {
    const state = store.getState();
    const source = isFeatured ? state.featuredCourses : state.userNotebooks;
    const course = source.find(c => c.id === courseId);

    if (course) {
      store.setState({
        activeCourse: course,
        currentModuleIndex: 0,
        currentView: 'theater'
      });
    } else {
      toast.error("Course not found.");
    }
  }
}
