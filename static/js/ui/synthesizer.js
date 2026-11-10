/**
 * Helioz AI - Synthesizer Dock Controller
 * Handles syllabus input, file dropzone, modifiers, and compilation telemetry.
 */

import { store } from '../store.js';
import { api } from '../api.js';
import { toast } from './toast.js';

export class Synthesizer {
  constructor() {
    this.textarea = document.getElementById('syllabus-input');
    this.fileInput = document.getElementById('syllabus-file-input');
    this.dropzone = document.getElementById('syllabus-dropzone');
    this.filePill = document.getElementById('dropzone-file-pill');
    this.fileNameSpan = document.getElementById('dropzone-file-name');
    this.fileRemoveBtn = document.getElementById('dropzone-file-remove');
    this.compileBtn = document.getElementById('btn-compile-course');
    this.compilerModal = document.getElementById('compiler-modal');
    this.compilerLog = document.getElementById('compiler-terminal-log');

    this.selectedFile = null;
    this.activeModifiers = new Set();

    this.bindEvents();
    store.subscribe((state) => this.render(state));
  }

  bindEvents() {
    // 1. Prompt Sample Injectors
    document.querySelectorAll('[data-prompt-preset]').forEach(btn => {
      btn.addEventListener('click', () => {
        const text = btn.getAttribute('data-prompt-preset');
        if (this.textarea) {
          this.textarea.value = text;
          this.textarea.focus();
        }
      });
    });

    // 2. Modifier Pills
    document.querySelectorAll('.modifier-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        const mod = pill.getAttribute('data-modifier');
        if (this.activeModifiers.has(mod)) {
          this.activeModifiers.delete(mod);
          pill.classList.remove('active');
        } else {
          this.activeModifiers.add(mod);
          pill.classList.add('active');
        }
      });
    });

    // 3. Dropzone & File Input
    if (this.dropzone && this.fileInput) {
      this.dropzone.addEventListener('click', (e) => {
        if (e.target !== this.fileRemoveBtn) {
          this.fileInput.click();
        }
      });

      this.fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
          this.setFile(e.target.files[0]);
        }
      });

      this.dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        this.dropzone.style.borderColor = 'var(--solar-400)';
      });

      this.dropzone.addEventListener('dragleave', () => {
        this.dropzone.style.borderColor = 'var(--border-medium)';
      });

      this.dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        this.dropzone.style.borderColor = 'var(--border-medium)';
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
          this.setFile(e.dataTransfer.files[0]);
        }
      });
    }

    if (this.fileRemoveBtn) {
      this.fileRemoveBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.clearFile();
      });
    }

    // 4. Compile Action
    if (this.compileBtn) {
      this.compileBtn.addEventListener('click', () => this.handleCompile());
    }
  }

  setFile(file) {
    this.selectedFile = file;
    if (this.fileNameSpan) {
      this.fileNameSpan.textContent = file.name;
    }
    if (this.filePill) {
      this.filePill.style.display = 'inline-flex';
    }
    const dropzoneDefault = document.getElementById('dropzone-default-content');
    if (dropzoneDefault) {
      dropzoneDefault.style.display = 'none';
    }
  }

  clearFile() {
    this.selectedFile = null;
    if (this.fileInput) this.fileInput.value = '';
    if (this.filePill) this.filePill.style.display = 'none';
    const dropzoneDefault = document.getElementById('dropzone-default-content');
    if (dropzoneDefault) dropzoneDefault.style.display = 'flex';
  }

  render(state) {
    if (this.compileBtn) {
      // 1. If not logged in, prompt sign in
      if (!state.user || state.user.isGuest) {
        this.compileBtn.disabled = false;
        this.compileBtn.title = 'Sign in to compile notebooks';
        this.compileBtn.innerHTML = `
          <span>Sign In to Compile</span>
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        `;
        return;
      }

      // 2. Existing quota check for logged-in users
      const isQuotaFull = state.userNotebooks.length >= 3;
      if (isQuotaFull) {
        this.compileBtn.disabled = true;
        this.compileBtn.title = 'Quota full (Max 3 notebooks). Delete one to proceed.';
        this.compileBtn.innerHTML = `<span>Quota Full (3/3 Used)</span>`;
      } else {
        this.compileBtn.disabled = false;
        this.compileBtn.title = '';
        this.compileBtn.innerHTML = `
          <span>Compile Curriculum</span>
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        `;
      }
    }
  }

  async handleCompile() {
    const state = store.getState();
    if (!state.user || state.user.isGuest) {
      toast.info("Please sign in with your account to compile notebooks.");
      window.dispatchEvent(new CustomEvent('open-auth-modal'));
      return;
    }
    const text = this.textarea ? this.textarea.value.trim() : '';
    const file = this.selectedFile;

    if (!text && !file) {
      toast.error("Please enter syllabus topics or attach a syllabus image.");
      if (this.textarea) this.textarea.focus();
      return;
    }

    // Append modifiers to syllabus text
    let fullSyllabus = text;
    if (this.activeModifiers.size > 0) {
      const modList = Array.from(this.activeModifiers).join(', ');
      fullSyllabus += `\n[Special Instructions / Pedagogical Modifiers: ${modList}]`;
    }

    // Show compiler terminal modal
    this.showCompilerTerminal();

    try {
      this.logTerminal("Initiating curriculum compilation pipeline...");
      await this.sleep(400);

      this.logTerminal("Connecting to Meta Llama model API...");
      this.logTerminal("Deconstructing input into granular sequential micro-topics...");

      const newCourse = await api.generateCourse({
        syllabusText: fullSyllabus,
        imageFile: file
      });

      this.logTerminal(`[Success] Synthesized course: "${newCourse.course_title}"`, 'done');
      this.logTerminal(`Retrieved and ranked ${newCourse.modules.length} candidate lectures with quizzes.`);
      await this.sleep(600);

      toast.success("Course compiled successfully!");
      this.hideCompilerTerminal();

      // Reset form
      if (this.textarea) this.textarea.value = '';
      this.clearFile();

      // Refresh notebooks list in store
      const updatedNotebooks = await api.getNotebooks();
      store.setState({
        userNotebooks: updatedNotebooks,
        activeCourse: newCourse,
        currentModuleIndex: 0,
        currentView: 'theater'
      });

    } catch (err) {
      console.error("[Synthesizer] Compilation error:", err);
      this.logTerminal(`[Error] ${err.message}`, 'error');
      toast.error(err.message || "Compilation failed. Check API keys in .env.");
      setTimeout(() => this.hideCompilerTerminal(), 3500);
    }
  }

  showCompilerTerminal() {
    if (this.compilerModal) {
      this.compilerModal.style.display = 'flex';
      if (this.compilerLog) {
        this.compilerLog.innerHTML = '';
      }
    }
  }

  hideCompilerTerminal() {
    if (this.compilerModal) {
      this.compilerModal.style.display = 'none';
    }
  }

  logTerminal(message, type = 'normal') {
    if (!this.compilerLog) return;
    const line = document.createElement('div');
    if (type === 'done') {
      line.className = 'compiler-line-done';
    } else if (type === 'error') {
      line.style.color = 'var(--accent-rose)';
    } else {
      line.className = 'compiler-line-active';
    }
    line.textContent = `> ${message}`;
    this.compilerLog.appendChild(line);
    this.compilerLog.scrollTop = this.compilerLog.scrollHeight;
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
