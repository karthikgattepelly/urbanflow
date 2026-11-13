import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/network': 'http://127.0.0.1:8000',
      '/scenario': 'http://127.0.0.1:8000',
      '/emergencies': 'http://127.0.0.1:8000',
      '/routes': 'http://127.0.0.1:8000',
      '/decisions': 'http://127.0.0.1:8000',
      '/incidents': 'http://127.0.0.1:8000',
      '/recommendations': 'http://127.0.0.1:8000',
      '/events': {
        target: 'ws://127.0.0.1:8000',
        ws: true
      }
    }
  }
});

