import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		adapter: adapter({
			out: 'build',
			precompress: true
		}),
		alias: {
			$components: 'src/lib/components'
		},
		version: {
			// Poll for new deployments. When a stale tab (loaded before a deploy)
			// detects a new version, the beforeNavigate guard in +layout.svelte
			// forces a full page load — otherwise client-side navigation hangs
			// trying to import route chunks whose hashed filenames no longer exist.
			pollInterval: 60_000
		}
	}
};

export default config;
