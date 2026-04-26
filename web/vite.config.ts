import { sentrySvelteKit } from '@sentry/sveltekit';
import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

const isDocker = process.env.DOCKER === 'true';
const apiTarget = isDocker ? 'http://api:8000' : 'http://localhost:8000';
const port = Number(process.env.VITE_PORT) || 3000;

export default defineConfig({
	plugins: [
		sentrySvelteKit({ autoUploadSourceMaps: false }),
		tailwindcss(),
		sveltekit()
	],
	server: {
		host: '0.0.0.0',
		port,
		strictPort: true,
		allowedHosts: true,
		proxy: {
			'/api/v1': {
				target: apiTarget,
				changeOrigin: true
			},
			'/storage': {
				target: apiTarget,
				changeOrigin: true
			}
		},
		...(isDocker && {
			watch: {
				usePolling: true,
				interval: 1000
			},
			hmr: {
				port: 5173
			}
		})
	}
});
