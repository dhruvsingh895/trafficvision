import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Allow large file uploads through proxy
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq, req) => {
            // Forward content-length for large files
            const contentLength = req.headers['content-length'];
            if (contentLength) {
              proxyReq.setHeader('Content-Length', contentLength);
            }
          });
        },
      },
    },
  },
});
