import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  root: './',
  base: './',
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        deck_builder: resolve(__dirname, 'deck_builder.html'),
        deck_converter: resolve(__dirname, 'deck_converter.html'),
        deck_viewer: resolve(__dirname, 'deck_viewer.html'),
        interactive_deck_viewer: resolve(__dirname, 'interactive_deck_viewer.html'),
      },
    },
  },
  server: {
    port: 3000,
    open: true,
  },
});
