import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import fs from 'fs'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    // Serve ../reports/ at /reports/ during dev
    {
      name: 'serve-reports',
      configureServer(server) {
        server.middlewares.use('/reports', (req, res, next) => {
          const filePath = path.resolve(__dirname, '..', 'reports', req.url!.replace(/^\//, ''))
          if (fs.existsSync(filePath)) {
            res.setHeader('Content-Type', 'application/json')
            fs.createReadStream(filePath).pipe(res)
          } else {
            next()
          }
        })
        // Serve the manifest
        server.middlewares.use('/report-manifest.json', (_req, res) => {
          const reportsDir = path.resolve(__dirname, '..', 'reports')
          const files = fs.readdirSync(reportsDir).filter(f => /^\d{4}-\d{2}-\d{2}\.json$/.test(f)).sort()
          const manifest = files.map(f => ({ date: f.replace('.json', ''), file: f }))
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify(manifest))
        })
      },
    },
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
