<script lang="ts">
    import { page } from '$app/stores';

    let { children } = $props();

    let path = $derived($page.url.pathname);
    let showShell = $derived(path !== '/admin/login');
</script>

<div class="admin-shell">
    {#if showShell}
    <header class="admin-header">
        <a href="/admin/races" class="admin-brand">
            <span class="brand-dot"></span>
            EnduroHub <span class="brand-mute">/ admin</span>
        </a>
        <nav class="admin-nav">
            <a href="/admin/races" class:active={path.startsWith('/admin/races')}>대회</a>
            <a href="/dj-admin/" target="_blank" rel="noopener" class="ext">Django Admin ↗</a>
            <a href="/" class="ext">사이트로 ↗</a>
        </nav>
    </header>
    {/if}
    <main class="admin-main" class:login-main={!showShell}>
        {@render children()}
    </main>
</div>

<style>
    .admin-shell {
        min-height: 100vh;
        background: var(--arena-paper-alt, #f4f4f0);
        font-family: var(--arena-f-body, system-ui);
    }
    .admin-header {
        position: sticky;
        top: 0;
        z-index: 50;
        display: flex;
        align-items: center;
        gap: 24px;
        padding: 12px 24px;
        background: var(--arena-paper, #fff);
        border-bottom: 1px solid var(--arena-line, #ddd);
    }
    .admin-brand {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-family: var(--arena-f-display, system-ui);
        font-weight: 700;
        font-size: 14px;
        letter-spacing: -0.3px;
        color: var(--arena-ink, #111);
        text-decoration: none;
    }
    .brand-dot {
        display: inline-block;
        width: 7px;
        height: 7px;
        background: var(--arena-accent, #22c55e);
    }
    .brand-mute {
        color: var(--arena-ink-mute, #888);
        font-weight: 500;
    }
    .admin-nav {
        display: flex;
        gap: 4px;
    }
    .admin-nav a {
        padding: 6px 12px;
        font-size: 12px;
        color: var(--arena-ink-soft, #555);
        text-decoration: none;
        font-family: var(--arena-f-mono, ui-monospace);
        letter-spacing: 0.3px;
    }
    .admin-nav a:hover {
        color: var(--arena-ink, #111);
        background: var(--arena-paper-alt, #f4f4f0);
    }
    .admin-nav a.active {
        color: var(--arena-ink, #111);
        background: var(--arena-paper-alt, #f4f4f0);
        box-shadow: inset 0 -2px 0 var(--arena-ink, #111);
    }
    .admin-nav a.ext {
        color: var(--arena-ink-mute, #888);
    }
    .admin-main {
        max-width: 1280px;
        margin: 0 auto;
        padding: 24px;
    }
    .admin-main.login-main {
        max-width: none;
        padding: 0;
    }
</style>
