import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          charts: ['chart.js', 'react-chartjs-2'],
          ui: ['@headlessui/react', 'framer-motion']
        }
      }
    },
    target: 'es2015',
    cssCodeSplit: true,
    chunkSizeWarningLimit: 1000
  },
  server: {
    port: 3001,
    host: true,
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'https://aurum-solarv3-production.up.railway.app',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/ws': {
        target: process.env.VITE_WS_BASE_URL || 'wss://aurum-solarv3-production.up.railway.app',
        ws: true,
        changeOrigin: true,
        secure: true
      }
    }
  },
  preview: {
    port: 3001,
    host: true,
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'https://aurum-solarv3-production.up.railway.app',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'chart.js',
      'react-chartjs-2',
      'date-fns',
      'clsx',
      'tailwind-merge',
      'lucide-react'
    ]
  }
})
