import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { fileURLToPath } from 'node:url';

const webRoot = fileURLToPath(new URL('../../', import.meta.url));
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/** Isolated API fixtures: no real account, cookies or production services. */
export async function startToolsServer() {
    const requests = [];
    const targetDate = new Date(Date.now() + 112 * 86400000).toISOString().slice(0, 10);
    const api = createServer((req, res) => {
        const path = new URL(req.url, 'http://fixture.local').pathname;
        const token = req.headers.authorization?.replace('Bearer ', '') ?? '';
        requests.push({ path, token });
        res.setHeader('Content-Type', 'application/json');
        if (token === 'failed' && path !== '/api/v1/popups/active/') {
            res.writeHead(503).end('unavailable');
            return;
        }
        let body = {};
        if (path === '/api/v1/popups/active/') body = { popup: null };
        else if (path === '/api/v1/auth/me/') body = { user: {
            id: 1, nickname: '도구 테스트', email: 'test@example.invalid', profileImage: '',
            emailVerified: true, onboardingCompleted: true,
        } };
        else if (path === '/api/v1/me/records/') body = { records: token === 'personal' || token === 'slow' ? [
            token === 'slow' ? { sport: 'running', distance: '5K', durationSeconds: 36000, time: '10:00:00' }
                : { sport: 'running', distance: '10K', durationSeconds: 3000, time: '50:00' },
        ] : [] };
        else if (path === '/api/v1/me/favorites/races/') {
            const race = { slug: 'my-real-goal', title: '내 관심 풀코스 테스트 대회', raceDate: targetDate,
                sport: 'running', status: 'upcoming', daysUntilRace: 112, distances: [{ distanceMeter: 42195 }] };
            body = { count: 4, results: token === 'personal' || token === 'slow' ? [race,
                { ...race, slug: 'cancelled', title: '취소 후보', status: 'cancelled' },
                { ...race, slug: 'cycling', title: '자전거 후보', sport: 'cycling' },
                { ...race, slug: 'half', title: '하프 후보', distances: [{ distanceMeter: 21097.5 }] },
            ] : [] };
        } else {
            res.writeHead(404).end(JSON.stringify({ detail: 'Unknown fixture endpoint' }));
            return;
        }
        res.end(JSON.stringify(body));
    });
    api.listen(0, '127.0.0.1');
    await once(api, 'listening');
    // Reserve an ephemeral app port, then let adapter-node bind it.
    const reservation = createServer();
    reservation.listen(0, '127.0.0.1');
    await once(reservation, 'listening');
    const port = reservation.address().port;
    await new Promise((resolve) => reservation.close(resolve));
    const baseUrl = `http://127.0.0.1:${port}`;
    let logs = '';
    const app = spawn(process.execPath, ['build/index.js'], {
        cwd: webRoot,
        env: { ...process.env, HOST: '127.0.0.1', PORT: String(port), ORIGIN: baseUrl,
            API_URL_INTERNAL: `http://127.0.0.1:${api.address().port}`,
            PUBLIC_APP_URL: 'https://www.endurohub.kr', PUBLIC_GOOGLE_ANALYTICS_ID: '',
            PUBLIC_POSTHOG_KEY: '', SENTRY_DSN: '', ADMIN_SECRET: '',
        },
        stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true,
    });
    for (const stream of [app.stdout, app.stderr]) stream.on('data', (data) => { logs = (logs + data).slice(-12000); });
    const close = async () => {
        if (app.exitCode === null) { app.kill(); await once(app, 'exit'); }
        api.closeAllConnections();
        await new Promise((resolve) => api.close(resolve));
    };
    try {
        let ready = false;
        for (let i = 0; i < 100; i++) {
            if (app.exitCode !== null) throw new Error(`SSR server exited: ${logs}`);
            try { if ((await fetch(`${baseUrl}/tools/pace-calculator`)).ok) { ready = true; break; } } catch {}
            await wait(100);
        }
        if (!ready) throw new Error(`SSR server did not start: ${logs}`);
        requests.length = 0;
        return { baseUrl, requests, close, getLogs: () => logs };
    } catch (error) { await close(); throw error; }
}

if (process.argv.includes('--review')) {
    const server = await startToolsServer();
    console.log(`Tools review: ${server.baseUrl}`);
    process.on('SIGINT', async () => { await server.close(); process.exit(0); });
    process.on('SIGTERM', async () => { await server.close(); process.exit(0); });
}
