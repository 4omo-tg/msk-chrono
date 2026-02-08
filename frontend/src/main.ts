import { mount } from 'svelte'
import './app.css'
import App from './App.svelte'

// Register Service Worker for PWA
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js', { scope: '/' })
      .then((registration) => {
        console.log('SW registered:', registration.scope);
        
        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // New content available, show update notification
                console.log('New content available, please refresh.');
              }
            });
          }
        });
      })
      .catch((err) => {
        console.log('SW registration failed:', err);
      });
  });
}

// Handle Telegram OAuth redirect - check for auth params in URL
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.has('id') && urlParams.has('hash')) {
  // Telegram OAuth callback - redirect to hash route with params preserved
  const newUrl = window.location.origin + window.location.pathname + '?tg_auth=1&' + urlParams.toString() + '#/telegram-callback';
  window.history.replaceState({}, '', newUrl);
}

const app = mount(App, {
  target: document.getElementById('app')!,
})

export default app
