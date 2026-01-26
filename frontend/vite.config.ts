import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  server: {
    allowedHosts: ['test-serv.exe.xyz', 'localhost'],
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        followRedirects: true,
      },
      '/admin': {
        target: 'http://backend:8000',
        changeOrigin: true,
        followRedirects: true,
      },
      '/static': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})
