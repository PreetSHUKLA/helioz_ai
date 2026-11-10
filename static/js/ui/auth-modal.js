/**
 * Helioz AI - Authentication Modal Controller
 * Provides Firebase Authentication alongside instant Developer Guest mode.
 */

import { store } from '../store.js';
import { firebaseConfig, isFirebaseConfigured } from '../config.js';
import { toast } from './toast.js';

export class AuthModal {
  constructor() {
    this.modal = document.getElementById('auth-modal');
    this.emailInput = document.getElementById('auth-email');
    this.passwordInput = document.getElementById('auth-password');
    this.authTitle = document.getElementById('auth-modal-title');
    this.authSubtitle = document.getElementById('auth-modal-subtitle');
    this.actionBtn = document.getElementById('auth-submit-btn');
    this.toggleModeBtn = document.getElementById('auth-toggle-mode');
    this.guestBtn = document.getElementById('auth-guest-btn');
    this.closeBtn = document.getElementById('auth-modal-close');
    this.googleBtn = document.getElementById('auth-google-btn');

    this.isLoginMode = true;
    this.firebaseAuth = null;

    this.initFirebase();
    this.bindEvents();
  }

  async initFirebase() {
    if (isFirebaseConfigured()) {
      try {
        const { initializeApp } = await import('https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js');
        const { getAuth, onAuthStateChanged } = await import('https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js');

        const app = initializeApp(firebaseConfig);
        this.firebaseAuth = getAuth(app);

        onAuthStateChanged(this.firebaseAuth, async (user) => {
          if (user) {
            const token = await user.getIdToken();
            store.setState({
              user: { uid: user.uid, email: user.email, isGuest: false },
              userToken: token
            });
            this.hide();
          } else {
            // If user logged out of Firebase
            if (!store.getState().user || !store.getState().user.isGuest) {
              store.setState({ user: null, userToken: null });
            }
          }
        });
      } catch (err) {
        console.warn("[Auth] Firebase web client initialization skipped:", err);
      }
    } else {
      // Default to guest/developer session for instant zero-config experience
      this.loginAsGuest();
    }
  }

  bindEvents() {
    window.addEventListener('open-auth-modal', () => this.show());

    window.addEventListener('execute-logout', async () => {
      if (this.firebaseAuth) {
        const { signOut } = await import('https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js');
        await signOut(this.firebaseAuth);
      }
      store.setState({ user: null, userToken: null, userNotebooks: [] });
      toast.info("Logged out successfully.");
    });

    if (this.closeBtn) {
      this.closeBtn.addEventListener('click', () => this.hide());
    }
    if (this.googleBtn) {
      this.googleBtn.addEventListener('click', () => this.handleGoogleAuth());
    }

    if (this.toggleModeBtn) {
      this.toggleModeBtn.addEventListener('click', () => {
        this.isLoginMode = !this.isLoginMode;
        this.authTitle.textContent = this.isLoginMode ? "Welcome Back" : "Create Account";
        this.authSubtitle.textContent = this.isLoginMode ? "Sign in to access your course notebooks." : "Sign up to compile custom courses.";
        this.actionBtn.textContent = this.isLoginMode ? "Sign In" : "Create Account";
        this.toggleModeBtn.textContent = this.isLoginMode ? "Don't have an account? Sign Up" : "Already have an account? Sign In";
      });
    }

    if (this.actionBtn) {
      this.actionBtn.addEventListener('click', () => this.handleAuth());
    }

    if (this.guestBtn) {
      this.guestBtn.addEventListener('click', () => this.loginAsGuest());
    }

    if (this.googleBtn) {
      this.googleBtn.addEventListener('click', () => this.handleGoogleAuth());
    }
  }

  show() {
    if (this.modal) this.modal.style.display = 'flex';
  }

  hide() {
    if (this.modal) this.modal.style.display = 'none';
  }

  loginAsGuest() {
    store.setState({
      user: { uid: "guest-user-1", email: "Guest Studio", isGuest: true },
      userToken: "demo-token"
    });
    this.hide();
  }
  async handleGoogleAuth() {
    if (!this.firebaseAuth) {
      toast.error("Firebase is not configured yet in config.js");
      return;
    }

    try {
      const { GoogleAuthProvider, signInWithPopup } = await import('https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js');
      const provider = new GoogleAuthProvider();
      await signInWithPopup(this.firebaseAuth, provider);
      toast.success("Signed in with Google successfully!");
      this.hide();
    } catch (err) {
      console.error("Google Auth Error:", err);
      toast.error(err.message || "Google sign-in failed.");
    }
  }

  async handleAuth() {
    const email = this.emailInput ? this.emailInput.value.trim() : '';
    const password = this.passwordInput ? this.passwordInput.value.trim() : '';

    if (!email || !password) {
      toast.error("Please enter email and password.");
      return;
    }

    if (!this.firebaseAuth) {
      toast.info("Firebase is in local development mode. Signed in as developer.");
      store.setState({
        user: { uid: email.split('@')[0], email, isGuest: false },
        userToken: email.split('@')[0]
      });
      this.hide();
      return;
    }

    try {
      if (this.isLoginMode) {
        const { signInWithEmailAndPassword } = await import('https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js');
        await signInWithEmailAndPassword(this.firebaseAuth, email, password);
        toast.success("Welcome back!");
      } else {
        const { createUserWithEmailAndPassword } = await import('https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js');
        await createUserWithEmailAndPassword(this.firebaseAuth, email, password);
        toast.success("Account created successfully!");
      }
      this.hide();
    } catch (err) {
      toast.error(err.message || "Authentication failed.");
    }
  }
}
