import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

const projectRoot = fileURLToPath(new URL('.', import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // The project path contains characters (spaces/colons) that break Vite's
    // default fs allow-list, so we explicitly allow serving from the project root.
    fs: {
      strict: false,
      allow: [projectRoot],
    },
    proxy: {
      '/api': {
        // Local backend if running; otherwise production for design preview.
        target: process.env.VITE_API_PROXY || 'https://alblingo-backend.onrender.com',
        changeOrigin: true,
        secure: true,
      },
    },
  },
})
