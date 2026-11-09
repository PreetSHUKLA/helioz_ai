/**
 * Helioz AI - Theater & YouTube Player Controller
 * Coordinates YouTube IFrame API, curriculum milestone tracking, and video playback.
 */

import { store } from '../store.js';

export class Player {
  constructor() {
    this.railList = document.getElementById('curriculum-rail-list');
    this.courseTitleHeader = document.getElementById('theater-course-title');
    this.moduleTitleHeader = document.getElementById('theater-module-title');
    this.exitBtn = document.getElementById('theater-exit-btn');
    this.cinemaBtn = document.getElementById('theater-cinema-btn');
    this.theaterLayout = document.getElementById('theater-view');
    this.takeQuizBtn = document.getElementById('theater-take-quiz-btn');

    this.ytPlayer = null;
    this.isYTReady = false;

    this.bindEvents();
    this.initYouTubeAPI();
    store.subscribe((state) => this.render(state));
  }

  bindEvents() {
    if (this.exitBtn) {
      this.exitBtn.addEventListener('click', () => {
        if (this.ytPlayer && this.ytPlayer.stopVideo) {
          this.ytPlayer.stopVideo();
        }
        store.setState({ currentView: 'studio' });
      });
    }

    if (this.cinemaBtn) {
      this.cinemaBtn.addEventListener('click', () => {
        const state = store.getState();
        const nextCinema = !state.isCinemaMode;
        store.setState({ isCinemaMode: nextCinema });
      });
    }

    if (this.takeQuizBtn) {
      this.takeQuizBtn.addEventListener('click', () => {
        const quizContainer = document.getElementById('quiz-section');
        if (quizContainer) {
          quizContainer.scrollIntoView({ behavior: 'smooth' });
        }
      });
    }
  }

  initYouTubeAPI() {
    if (window.YT && window.YT.Player) {
      this.createPlayer();
    } else {
      window.onYouTubeIframeAPIReady = () => {
        this.createPlayer();
      };
    }
  }

  createPlayer() {
    try {
      this.ytPlayer = new YT.Player('yt-player-target', {
        height: '100%',
        width: '100%',
        videoId: '',
        playerVars: {
          autoplay: 1,
          controls: 1,
          rel: 0,
          modestbranding: 1
        },
        events: {
          onReady: () => {
            this.isYTReady = true;
            this.loadActiveModule();
          },
          onStateChange: (event) => {
            if (event.data === YT.PlayerState.ENDED) {
              window.dispatchEvent(new CustomEvent('video-ended'));
            }
          }
        }
      });
    } catch (err) {
      console.warn("[Player] YouTube initialization delayed:", err);
    }
  }

  render(state) {
    if (state.currentView !== 'theater' || !state.activeCourse) return;

    // 1. Update Header Titles
    if (this.courseTitleHeader) {
      this.courseTitleHeader.textContent = state.activeCourse.course_title;
    }

    const currentMod = (state.activeCourse.modules || [])[state.currentModuleIndex];
    if (this.moduleTitleHeader && currentMod) {
      this.moduleTitleHeader.textContent = currentMod.topic;
    }

    // 2. Cinema Mode toggle
    if (this.theaterLayout) {
      const rail = document.getElementById('curriculum-rail');
      if (rail) {
        rail.style.display = state.isCinemaMode ? 'none' : 'flex';
      }
      this.theaterLayout.style.gridTemplateColumns = state.isCinemaMode ? '1fr' : '360px 1fr';
    }

    // 3. Render Curriculum Rail Milestones
    this.renderRail(state.activeCourse, state.currentModuleIndex);

    // 4. Load video for current module
    this.loadActiveModule();
  }

  renderRail(course, currentIndex) {
    if (!this.railList || !course || !course.modules) return;

    this.railList.innerHTML = course.modules.map((mod, idx) => {
      const isActive = idx === currentIndex;
      const isPast = idx < currentIndex;

      return `
        <div class="module-milestone-card ${isActive ? 'active' : ''}" data-module-index="${idx}">
          <div class="module-index-badge">
            ${isPast ? '✓' : idx + 1}
          </div>
          <div style="flex: 1; min-width: 0;">
            <p class="truncate-2" style="font-size: 0.875rem; font-weight: 600; color: ${isActive ? 'var(--solar-400)' : 'var(--text-primary)'};">
              ${mod.topic}
            </p>
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.35rem;">
              <span class="card-badge" style="font-size: 0.625rem; padding: 0.1rem 0.35rem;">
                ${isActive ? 'Active Lecture' : isPast ? 'Mastered' : 'Up Next'}
              </span>
              <span style="font-size: 0.6875rem; color: var(--text-muted); font-family: var(--font-mono);">
                ${(mod.quiz || []).length} Checkpoints
              </span>
            </div>
          </div>
        </div>
      `;
    }).join('');

    // Attach listeners
    this.railList.querySelectorAll('.module-milestone-card').forEach(card => {
      card.addEventListener('click', () => {
        const idx = parseInt(card.getAttribute('data-module-index'), 10);
        store.setState({ currentModuleIndex: idx });
      });
    });
  }

  loadActiveModule() {
    const state = store.getState();
    if (!state.activeCourse || !state.activeCourse.modules) return;

    const currentMod = state.activeCourse.modules[state.currentModuleIndex];
    if (!currentMod) return;

    let videoId = currentMod.video_url;
    if (videoId && videoId.includes('v=')) {
      videoId = videoId.split('v=')[1].split('&')[0];
    }

    if (this.ytPlayer && this.ytPlayer.loadVideoById && videoId) {
      try {
        this.ytPlayer.loadVideoById(videoId);
      } catch (e) {
        console.warn("[Player] Error loading video ID:", e);
      }
    }
  }
}
