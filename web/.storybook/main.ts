import type { StorybookConfig } from '@storybook/sveltekit';
import { createRequire } from 'node:module';
import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const tooling = createRequire(new URL('./dependencies/package.json', import.meta.url));
const packageDirectory = (name: string) => dirname(tooling.resolve(`${name}/package.json`));

const config: StorybookConfig = {
    stories: ['../src/stories/**/*.stories.ts'],
    staticDirs: ['../static'],
    framework: { name: packageDirectory('@storybook/sveltekit'), options: {} },
    core: {
        disableTelemetry: true,
        builder: {
            name: packageDirectory('@storybook/builder-vite'),
            options: { viteConfigPath: fileURLToPath(new URL('./vite.config.ts', import.meta.url)) },
        },
    },
    addons: [],
};

export default config;
