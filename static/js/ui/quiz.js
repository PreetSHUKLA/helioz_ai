/**
 * Helioz AI - Active Recall Quiz Engine
 * Interactive comprehension checkpoints, question scoring, and progression.
 */

import { store } from '../store.js';
import { toast } from './toast.js';

export class QuizEngine {
  constructor() {
    this.quizContainer = document.getElementById('quiz-section');
    this.bindEvents();
    store.subscribe((state) => this.render(state));
  }

  bindEvents() {
    window.addEventListener('video-ended', () => {
      if (this.quizContainer) {
        this.quizContainer.scrollIntoView({ behavior: 'smooth' });
        toast.info("Lecture completed. Test your comprehension with the module quiz!");
      }
    });
  }

  render(state) {
    if (state.currentView !== 'theater' || !state.activeCourse || !this.quizContainer) return;

    const module = (state.activeCourse.modules || [])[state.currentModuleIndex];
    if (!module) return;

    const quizData = module.quiz || [];

    if (quizData.length === 0) {
      this.quizContainer.innerHTML = `
        <div class="empty-deck" style="max-width: 600px; margin: 2rem auto;">
          <p style="color: var(--text-muted); font-size: 0.9375rem;">No active-recall quiz generated for this introductory module.</p>
          <button class="btn-primary" id="btn-skip-next-module" style="margin-top: 1rem;">
            Continue to Next Module &rarr;
          </button>
        </div>
      `;
      const skipBtn = document.getElementById('btn-skip-next-module');
      if (skipBtn) {
        skipBtn.addEventListener('click', () => this.proceedToNextModule());
      }
      return;
    }

    let formHTML = `
      <div class="quiz-chassis fade-in">
        <div class="quiz-header-banner">
          <span class="card-badge gold font-mono">Knowledge Checkpoint</span>
          <h2 style="font-size: 1.75rem; margin-top: 0.5rem;">Active Recall Assessment</h2>
          <p style="color: var(--text-secondary); font-size: 0.875rem; margin-top: 0.25rem;">
            Test conceptual retention before progressing to the next micro-topic.
          </p>
        </div>

        <form id="active-quiz-form">
    `;

    quizData.forEach((q, qIndex) => {
      formHTML += `
        <div class="quiz-question-card" data-question-index="${qIndex}">
          <p class="quiz-question-text">
            <span style="color: var(--solar-400); font-family: var(--font-mono); margin-right: 0.5rem;">${qIndex + 1}.</span>
            ${q.question}
          </p>
          <div class="quiz-options-group">
      `;

      q.options.forEach((opt) => {
        formHTML += `
          <label class="quiz-option-label" data-value="${opt}">
            <input type="radio" name="question_${qIndex}" value="${opt}" style="accent-color: var(--solar-500); width: 16px; height: 16px;">
            <span style="font-size: 0.875rem; font-weight: 500;">${opt}</span>
          </label>
        `;
      });

      formHTML += `
          </div>
        </div>
      `;
    });

    formHTML += `
        </form>

        <div style="display: flex; justify-content: flex-end; margin-top: 1.5rem;">
          <button class="btn-primary" id="btn-submit-quiz" style="padding: 0.75rem 2rem; font-size: 1rem;">
            Verify Answers
          </button>
        </div>
      </div>
    `;

    this.quizContainer.innerHTML = formHTML;

    // Attach option click highlighting
    this.quizContainer.querySelectorAll('.quiz-option-label').forEach(label => {
      label.addEventListener('click', () => {
        const parent = label.closest('.quiz-options-group');
        parent.querySelectorAll('.quiz-option-label').forEach(l => l.classList.remove('selected'));
        label.classList.add('selected');
      });
    });

    const submitBtn = document.getElementById('btn-submit-quiz');
    if (submitBtn) {
      submitBtn.addEventListener('click', () => this.evaluateQuiz(quizData));
    }
  }

  evaluateQuiz(quizData) {
    let allAnswered = true;
    let score = 0;

    quizData.forEach((q, qIndex) => {
      const selected = document.querySelector(`input[name="question_${qIndex}"]:checked`);
      const card = document.querySelector(`.quiz-question-card[data-question-index="${qIndex}"]`);

      if (!selected) {
        allAnswered = false;
      } else {
        const answer = selected.value;
        const isCorrect = answer === q.correct_answer;
        if (isCorrect) score++;

        // Highlight options in UI
        if (card) {
          card.querySelectorAll('.quiz-option-label').forEach(lbl => {
            const val = lbl.getAttribute('data-value');
            if (val === q.correct_answer) {
              lbl.classList.add('correct');
            } else if (val === answer && !isCorrect) {
              lbl.classList.add('incorrect');
            }
          });
        }
      }
    });

    if (!allAnswered) {
      toast.error("Please answer all questions before submitting.");
      return;
    }

    const state = store.getState();
    const isPerfect = score === quizData.length;
    const hasNextModule = state.currentModuleIndex + 1 < (state.activeCourse.modules || []).length;

    // Trigger celebration if perfect score
    if (isPerfect && window.confetti) {
      window.confetti({
        particleCount: 120,
        spread: 70,
        origin: { y: 0.7 },
        colors: ['#f59e0b', '#fbbf24', '#10b981', '#f8fafc']
      });
    }

    // Render Milestone Result Box
    const resultBox = document.createElement('div');
    resultBox.className = 'empty-deck fade-in';
    resultBox.style.marginTop = '2rem';
    resultBox.style.border = isPerfect ? '1px solid var(--accent-emerald)' : '1px solid var(--border-medium)';
    resultBox.innerHTML = `
      <span class="card-badge ${isPerfect ? 'gold' : ''}" style="font-size: 0.8125rem;">
        ${isPerfect ? 'Mastery Achieved' : 'Review Recommended'}
      </span>
      <h3 style="font-size: 2rem; margin-top: 0.25rem;">
        Score: <span style="color: ${isPerfect ? 'var(--accent-emerald)' : 'var(--solar-400)'};">${score}</span> / ${quizData.length}
      </h3>
      <p style="color: var(--text-secondary); max-width: 400px; font-size: 0.875rem;">
        ${isPerfect ? 'Outstanding comprehension! All concepts from this lecture retained.' : 'Good effort! Review the highlighted correct solutions above.'}
      </p>
      <div style="display: flex; gap: 1rem; margin-top: 0.5rem;">
        <button class="btn-primary" id="btn-next-module-action">
          ${hasNextModule ? 'Advance to Next Module →' : 'Complete Course & Return to Studio'}
        </button>
      </div>
    `;

    this.quizContainer.querySelector('.quiz-chassis').appendChild(resultBox);
    resultBox.scrollIntoView({ behavior: 'smooth' });

    // Disable re-submits
    const submitBtn = document.getElementById('btn-submit-quiz');
    if (submitBtn) submitBtn.style.display = 'none';

    const nextBtn = document.getElementById('btn-next-module-action');
    if (nextBtn) {
      nextBtn.addEventListener('click', () => this.proceedToNextModule());
    }
  }

  proceedToNextModule() {
    const state = store.getState();
    const nextIdx = state.currentModuleIndex + 1;
    if (nextIdx < (state.activeCourse.modules || []).length) {
      store.setState({ currentModuleIndex: nextIdx });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      toast.success("Congratulations! You completed the full curriculum.");
      store.setState({ currentView: 'studio' });
    }
  }
}
