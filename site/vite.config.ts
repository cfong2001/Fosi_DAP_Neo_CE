import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'

// One fixed-name bundle in docs/stage/ (stage.js + stage.css), so the Pages
// site needs no build step and CI can rebuild and diff it.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    target: 'es2022',
    outDir: fileURLToPath(new URL('../docs/stage', import.meta.url)),
    emptyOutDir: true,
    cssCodeSplit: false,
    sourcemap: false,
    reportCompressedSize: false,
    rollupOptions: {
      input: fileURLToPath(new URL('./src/main.tsx', import.meta.url)),
      output: {
        format: 'es',
        entryFileNames: 'stage.js',
        chunkFileNames: 'stage-[name].js',
        assetFileNames: 'stage.[ext]',
        inlineDynamicImports: true,
      },
    },
  },
  resolve: { dedupe: ['react', 'react-dom'] },
})
