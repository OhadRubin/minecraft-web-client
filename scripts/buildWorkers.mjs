#!/usr/bin/env node

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const projectRoot = path.join(__dirname, '..')
const watch = process.argv.includes('-w')

function buildWorkers() {
  console.log('Building worker files...')

  // Ensure dist directory exists
  const distDir = path.join(projectRoot, 'dist')
  if (!fs.existsSync(distDir)) {
    fs.mkdirSync(distDir, { recursive: true })
  }

  // Create workers directory in dist
  const workersDistDir = path.join(distDir, 'workers')
  if (!fs.existsSync(workersDistDir)) {
    fs.mkdirSync(workersDistDir, { recursive: true })
  }

  // Build screenshot worker
  const workerSrcPath = path.join(projectRoot, 'src', 'workers', 'screenshot-worker.ts')
  const workerDistPath = path.join(workersDistDir, 'screenshot-worker.js')

  if (fs.existsSync(workerSrcPath)) {
    // Read TypeScript worker file
    let workerContent = fs.readFileSync(workerSrcPath, 'utf8')
    
    // Simple TS to JS conversion (remove type annotations)
    workerContent = workerContent
      .replace(/: MessageEvent/g, '')
      .replace(/: string/g, '')
      .replace(/: number/g, '')
      .replace(/: any/g, '')
      .replace(/: OffscreenCanvasRenderingContext2D/g, '')
      .replace(/as string/g, '')
      .replace(/as OffscreenCanvasRenderingContext2D/g, '')
    
    // Write JS worker file
    fs.writeFileSync(workerDistPath, workerContent, 'utf8')
    console.log(`✅ Built screenshot worker: ${workerDistPath}`)
  } else {
    console.log(`❌ Screenshot worker source not found: ${workerSrcPath}`)
    process.exit(1)
  }

  console.log('✅ All workers built successfully!')
}

// Initial build
buildWorkers()

// Watch mode
if (watch) {
  console.log('👀 Watching src/workers for changes...')
  const workersDir = path.join(projectRoot, 'src', 'workers')
  
  if (fs.existsSync(workersDir)) {
    fs.watch(workersDir, { recursive: true }, (eventType, filename) => {
      if (filename && filename.endsWith('.ts')) {
        console.log(`📝 ${filename} changed, rebuilding workers...`)
        try {
          buildWorkers()
        } catch (error) {
          console.error('❌ Build failed:', error.message)
        }
      }
    })
  }
}