<script lang="ts">
    import { page } from '$app/stores';
    import type { Snippet } from 'svelte';

    let {
        children,
        currentPath,
        maxWidth = '1100px',
    }: {
        children: Snippet;
        currentPath: string;
        maxWidth?: string;
    } = $props();

    const tabs = [
        { k: 'hub', label: '개요', href: '/tools' },
        { k: 'pace', label: '페이스 계산기', href: '/tools/pace-calculator' },
        { k: 'plan', label: '훈련 플랜', href: '/tools/training-plan' },
        { k: 'vo2', label: 'VO₂max', href: '/tools/vo2max' },
        { k: 'predict', label: '기록 예측', href: '/tools/race-predictor' },
    ];

    const user = $derived($page.data.user);
    const userLabel = $derived(
        user ? user.nickname?.trim() || user.email.split('@')[0] || '계정' : null,
    );

    function isActive(href: string): boolean {
        if (href === '/tools') return currentPath === '/tools';
        return currentPath === href;
    }
</script>

<div class="tools-frame" style="--tools-max-w: {maxWidth}">
    <header class="tools-head">
        <div class="head-inner">
            <div class="head-row">
                <div>
                    <div class="arena-kicker tools-kicker">endurohub · /tools</div>
                    <h1 class="tools-title">러닝 도구실</h1>
                </div>
                <div class="tools-meta">
                    {#if userLabel}
                        로그인: <span class="meta-name">{userLabel}</span> · 최근 기록 자동 채움
                    {:else}
                        <a href="/auth/login?next={currentPath}">로그인</a>해서 최근 기록 자동 채움
                    {/if}
                </div>
            </div>
            <div class="tabs" role="tablist">
                {#each tabs as t (t.k)}
                    <a
                        class="tab"
                        class:active={isActive(t.href)}
                        href={t.href}
                        role="tab"
                        aria-selected={isActive(t.href)}
                    >
                        {t.label}
                    </a>
                {/each}
            </div>
        </div>
    </header>

    <div class="tools-body">
        {@render children()}
    </div>
</div>

<style>
    .tools-frame {
        background: var(--arena-paper);
        min-height: 100vh;
        display: flex;
        flex-direction: column;
    }
    .tools-head {
        border-bottom: 1px solid var(--arena-line);
        background: var(--arena-paper);
    }
    .head-inner {
        max-width: var(--tools-max-w, 1100px);
        margin: 0 auto;
        padding: 20px 24px 0;
    }
    @media (min-width: 1024px) {
        .head-inner {
            padding: 20px 32px 0;
        }
    }
    .head-row {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        margin-bottom: 16px;
        gap: 16px;
        flex-wrap: wrap;
    }
    .tools-kicker {
        margin-bottom: 6px;
    }
    .tools-title {
        font-family: var(--arena-f-display);
        font-size: clamp(28px, 4vw, 40px);
        font-weight: 700;
        letter-spacing: -1.2px;
        margin: 0;
        color: var(--arena-ink);
    }
    .tools-meta {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
    }
    .tools-meta a {
        color: var(--arena-accent-deep);
        text-decoration: underline;
    }
    .meta-name {
        color: var(--arena-ink);
        font-weight: 600;
    }
    .tabs {
        display: flex;
        gap: 0;
        overflow-x: auto;
        scrollbar-width: none;
        -ms-overflow-style: none;
    }
    .tabs::-webkit-scrollbar {
        display: none;
    }
    .tab {
        padding: 10px 18px;
        border-bottom: 2px solid transparent;
        font-family: var(--arena-f-display);
        font-weight: 500;
        font-size: 14px;
        color: var(--arena-ink-soft);
        cursor: pointer;
        text-decoration: none;
        white-space: nowrap;
        transition: color 0.1s;
    }
    .tab:hover {
        color: var(--arena-ink);
    }
    .tab.active {
        border-bottom-color: var(--arena-ink);
        font-weight: 700;
        color: var(--arena-ink);
    }
    .tools-body {
        flex: 1;
    }
</style>
