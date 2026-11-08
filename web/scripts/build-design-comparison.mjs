import { build } from 'vite';
import { svelte, vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import tailwindcss from '@tailwindcss/vite';
import { readFile, mkdir, writeFile, readdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';
import { versionedStyles } from '../.storybook/versioned-styles.mjs';

const webRoot = fileURLToPath(new URL('../', import.meta.url));
const tooling = join(webRoot, '.storybook');
const generated = join(tooling, 'generated');
const output = join(webRoot, 'design-comparison');
const mock = (name) => join(tooling, 'mocks', name);
const alias = [
    { find: '$lib/analytics', replacement: mock('analytics.ts') },
    { find: '$lib/api.client', replacement: mock('api.client.ts') },
    { find: '$app/state', replacement: mock('app-state.svelte.ts') },
    { find: '$app/navigation', replacement: mock('navigation.ts') },
    { find: '$app/environment', replacement: mock('environment.ts') },
    { find: '$env/dynamic/public', replacement: mock('public-env.ts') },
    { find: '$before', replacement: join(webRoot, 'src/stories/before') },
    { find: '$lib', replacement: join(webRoot, 'src/lib') },
];

async function bundle(name, entry) {
    const outDir = join(generated, name);
    await build({
        configFile: false,
        root: webRoot,
        envDir: false,
        publicDir: false,
        plugins: [versionedStyles(), svelte({ configFile: false, preprocess: vitePreprocess() }), tailwindcss()],
        resolve: { alias },
        logLevel: 'warn',
        build: {
            outDir, emptyOutDir: true, target: 'es2022', cssCodeSplit: false,
            lib: { entry: join(tooling, 'standalone', entry), name: 'DesignComparison', formats: ['iife'], fileName: () => `${name}.js` },
            rollupOptions: { output: { inlineDynamicImports: true } },
        },
    });
    const files = await readdir(outDir);
    const css = (await Promise.all(files.filter((file) => file.endsWith('.css')).map((file) => readFile(join(outDir, file), 'utf8')))).join('\n');
    const js = await readFile(join(outDir, `${name}.js`), 'utf8');
    return { css, js };
}

const safeScript = (source) => source.replace(/<\/script/gi, '<\\/script');
function document(title, css, js, setup = '') {
    return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title}</title><style>${css}</style></head><body class="arena"><div id="app"></div><script>${safeScript(setup + '\n' + js)}</script></body></html>`;
}

const preview = await bundle('preview', 'preview.ts');
const previewDocument = document('컴포넌트 비교', preview.css, preview.js, '/*__COMPARISON_CONFIG__*/');
const gallery = await bundle('gallery', 'main.ts');
const html = document('엔듀로허브 디자인 전후 비교', gallery.css, gallery.js,
    `window.__DESIGN_PREVIEW_DOCUMENT__=${JSON.stringify(previewDocument)};`);
await mkdir(output, { recursive: true });
await writeFile(join(output, 'index.html'), html);
console.log(`Self-contained comparison: ${join(output, 'index.html')}`);
console.log('This gallery uses the same Svelte components and fixtures as the Storybook stories; it does not replace the Storybook runtime.');
