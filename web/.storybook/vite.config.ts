import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';
import { fileURLToPath } from 'node:url';
import { versionedStyles } from './versioned-styles.mjs';

export default defineConfig({
    envDir: false,
    plugins: [versionedStyles(), tailwindcss()],
    resolve: {
        alias: [
            { find: '$lib/analytics', replacement: fileURLToPath(new URL('./mocks/analytics.ts', import.meta.url)) },
            { find: '$lib/api.client', replacement: fileURLToPath(new URL('./mocks/api.client.ts', import.meta.url)) },
            { find: '$before', replacement: fileURLToPath(new URL('../src/stories/before', import.meta.url)) },
        ],
    },
});
