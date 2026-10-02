import { defineConfig } from 'vite';
import { fileURLToPath } from 'node:url';

// Two pages: the Phase 1 massing viewer and the Phase 3 IFC model viewer.
export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        massing: fileURLToPath(new URL('./index.html', import.meta.url)),
        model: fileURLToPath(new URL('./model.html', import.meta.url)),
      },
    },
  },
});
