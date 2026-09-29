import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_PROXY_TARGET || 'https://vakil-vision.fastapicloud.dev'

  return {
    plugins: [react()],
    server: {
      proxy: {
        '/contracts': { target: apiTarget, changeOrigin: true, secure: true },
        '/analysis': { target: apiTarget, changeOrigin: true, secure: true },
      },
    },
  }
})
