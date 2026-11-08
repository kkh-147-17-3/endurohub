import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';

const webRoot = fileURLToPath(new URL('../', import.meta.url));
const tooling = createRequire(new URL('../.storybook/dependencies/package.json', import.meta.url));
let packagePath;
try {
    packagePath = tooling.resolve('storybook/package.json');
} catch {
    console.error('Storybook dependencies are missing. Run npm run storybook:install first.');
    process.exit(1);
}

const pkg = JSON.parse(await readFile(packagePath, 'utf8'));
const bin = typeof pkg.bin === 'string' ? pkg.bin : pkg.bin.storybook;
const child = spawn(process.execPath, [resolve(dirname(packagePath), bin), ...process.argv.slice(2)], {
    cwd: webRoot,
    stdio: 'inherit',
    windowsHide: true,
    env: { ...process.env, STORYBOOK_DISABLE_TELEMETRY: '1' },
});
child.on('error', (error) => { console.error(error.message); process.exitCode = 1; });
child.on('exit', (code) => { process.exitCode = code ?? 1; });
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill(signal));
