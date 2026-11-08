import { fileURLToPath } from 'node:url';

/** Shared foundation only; each isolated version supplies its own component CSS. */
export function versionedStyles() {
    const appCss = fileURLToPath(new URL('../src/app.css', import.meta.url)).replaceAll('\\', '/');
    return {
        name: 'comparison-versioned-component-styles',
        enforce: 'pre',
        transform(source, id) {
            if (id.split('?')[0].replaceAll('\\', '/') !== appCss) return;
            return source.replace(/^@import\s+['"]\.\/lib\/styles\/eh-components\.css['"];\s*$/m, '');
        },
    };
}
