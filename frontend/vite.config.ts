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
        // Backend is running with your command on port 8001:
        // python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
})
