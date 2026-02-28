import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

const isDocker = process.env.DOCKER === 'true';
const apiTarget = isDocker ? 'http://api:8000' : 'http://localhost:8000';

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit()
	],
	server: {
		host: '0.0.0.0',
		port: 3000,
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
