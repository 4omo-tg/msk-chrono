import { mount } from 'svelte'
import './app.css'
import App from './App.svelte'

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
