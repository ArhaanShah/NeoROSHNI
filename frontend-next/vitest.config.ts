import path from 'path'
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '.'),
    },
  },
  test: {
    globals: true,
    // auth-actions tests run in node (server-side); component tests use jsdom.
    // Per-file environment is declared with the @vitest-environment docblock.
    environment: 'node',
    setupFiles: [],
  },
})
