<script lang="ts">
    import { onMount } from 'svelte';
    import { get } from 'svelte/store';
    import { page } from '$app/stores';
    import { goto } from '$app/navigation';
    import { Button } from '$lib/components/eh';

    let status = $derived($page.status);
    let message = $derived($page.error?.message || '');

    // Client-only timestamp (KST) — set after mount to avoid an SSR/CSR
    // hydration mismatch on the minute field.
    let stamp = $state('');

    // Live "RESUMES IN" countdown (maintenance only). KST is a fixed UTC+9
    // offset (no DST), so we count seconds to the next 06:00 KST boundary —
    // the end of the 02:00–06:00 maintenance window shown alongside.
    let resumesIn = $state('');

    function resumeCountdown(): string {
        const kstSecOfDay = Math.floor((Date.now() / 1000 + 9 * 3600) % 86400);
        let rem = 6 * 3600 - kstSecOfDay;
        if (rem <= 0) rem += 86400;
        const hh = String(Math.floor(rem / 3600)).padStart(2, '0');
        const mm = String(Math.floor((rem % 3600) / 60)).padStart(2, '0');
        const ss = String(rem % 60).padStart(2, '0');
        return `${hh}:${mm}:${ss}`;
    }

    onMount(() => {
        stamp =
            new Intl.DateTimeFormat('sv-SE', {
                timeZone: 'Asia/Seoul',
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            }).format(new Date()) + ' KST';

        resumesIn = resumeCountdown();
        const timer = setInterval(() => (resumesIn = resumeCountdown()), 1000);

        const p = get(page);
        if (
            p.status === 403 &&
            p.url.pathname.startsWith('/admin') &&
            p.url.pathname !== '/admin/login' &&
            !p.url.pathname.startsWith('/admin/login/')
        ) {
            const next = p.url.pathname + p.url.search;
            goto(`/admin/login?redirect=${encodeURIComponent(next)}`, { replaceState: true });
        }

        return () => clearInterval(timer);
    });

    type Kind = '404' | '403' | '500' | 'maint';

    const kind: Kind = $derived(
        status === 404 ? '404' : status === 403 ? '403' : status === 503 ? 'maint' : '500'
    );

    type Copy = { label: string; title: string; sub: string };

    const COPY: Record<Kind, Copy> = {
        '404': {
            label: 'PAGE NOT FOUND',
            title: '페이지를 찾을 수 없습니다',
            sub: '주소가 바뀌었거나 삭제된 페이지입니다. 입력하신 주소를 다시 확인해 주세요.'
        },
        '403': {
            label: 'FORBIDDEN',
            title: '접근 권한이 없습니다',
            sub: '이 페이지를 볼 수 있는 권한이 없습니다. 로그인이 필요한 페이지일 수 있습니다.'
        },
        '500': {
            label: 'SERVER ERROR',
            title: '일시적인 오류가 발생했습니다',
            sub: '서버에서 요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요. 문제가 계속되면 공지를 확인해 주세요.'
        },
        maint: {
            label: 'MAINTENANCE',
            title: '서비스 점검 중입니다',
            sub: '더 나은 서비스를 위해 시스템 점검을 진행하고 있습니다. 점검 중에는 접속이 제한됩니다.'
        }
    };

    let c = $derived(COPY[kind]);

    // Requested URL (404 only) — built from the real request, uppercased
    // editorial-style to match the design's data treatment.
    let requestedUrl = $derived(
        ($page.url.host + $page.url.pathname).toUpperCase()
    );

    const links = [
        { l: '대회 캘린더', m: 'HOME', href: '/' },
        { l: '대회 검색', m: 'SEARCH', href: '/races' },
        { l: '공지사항', m: 'NOTICE', href: '/notice' }
    ];
</script>

<svelte:head>
    <title>{status} · {c.title} · endurohub</title>
    <meta name="robots" content="noindex" />
</svelte:head>

{#if kind === '404'}
    <!-- Full-bleed photo hero with all content overlaid -->
    <section class="err-hero err-hero--photo">
        <img src="/images/error-404.jpg" alt="안개 낀 산길을 달리는 러너" />
        <div class="err-hero-overlay">
            <span class="hero-micro eh-micro"><span class="acc">{c.label}</span></span>
            <div class="hero-code eh-data">{status}</div>
            <h1 class="hero-title">{c.title}</h1>
            <p class="hero-sub">{c.sub}</p>

            <div class="hero-url">
                <span class="k">REQUESTED URL</span>
                <span class="v eh-data">{requestedUrl}</span>
            </div>

            <div class="hero-actions">
                <a class="hero-btn hero-btn--primary" href="/">홈으로 가기</a>
                <a class="hero-btn hero-btn--ghost" href="/races">대회 검색</a>
            </div>

            <nav class="hero-links">
                {#each links as it (it.m)}
                    <a class="hero-link" href={it.href}>
                        <span>{it.l}<span class="micro">{it.m}</span></span>
                        <span class="arrow">→</span>
                    </a>
                {/each}
            </nav>

            <div class="hero-cap eh-micro eh-data">ENDUROHUB · {stamp}</div>
        </div>
    </section>
{:else}
    <div class="err-page">
        <div class="err-code-wrap">
            <div class="err-code eh-data">
                {#if kind === 'maint'}<span><span class="dim">··</span>·</span>{:else}{status}{/if}
            </div>
        </div>

        <div class="err-label-row">
            <span class="eh-micro"><span class="acc">{c.label}</span></span>
            <span class="eh-micro eh-data" style="color: var(--text-faint);">{stamp}</span>
        </div>

        <h1 class="err-title">{c.title}</h1>
        <p class="err-sub">{c.sub}</p>

        {#if kind === 'maint'}
            <div class="maint-window">
                <div class="maint-cell">
                    <div class="k">MAINTENANCE WINDOW</div>
                    <div class="v eh-data">02:00 — 06:00 KST</div>
                </div>
                <div class="maint-cell">
                    <div class="k">RESUMES IN</div>
                    <div class="v eh-data" style="color: var(--text-accent);">{resumesIn || '—'}</div>
                </div>
            </div>
        {/if}

        <div class="err-actions">
            {#if kind === '500'}
                <Button variant="primary" size="lg" onclick={() => location.reload()}>새로고침</Button>
                <Button variant="secondary" size="lg" href="/notice">공지 확인</Button>
            {:else}
                <Button variant="primary" size="lg" href="/">홈으로 가기</Button>
            {/if}
        </div>

        {#if kind !== 'maint'}
            <div class="err-links">
                {#each links as it (it.m)}
                    <a class="err-link" href={it.href}>
                        <span>{it.l}<span class="micro">{it.m}</span></span>
                        <span class="arrow">→</span>
                    </a>
                {/each}
            </div>
        {/if}
    </div>
{/if}

<style>
    .err-page {
        max-width: 720px;
        margin: 0 auto;
        padding: 72px var(--container-pad-mobile) 100px;
    }

    .err-code-wrap {
        border-top: 2px solid var(--ink-900);
        border-bottom: 2px solid var(--ink-900);
        padding: 8px 0 16px;
    }
    .err-code {
        font-size: clamp(110px, 22vw, 200px);
        font-weight: var(--w-display);
        letter-spacing: var(--track-display);
        line-height: 0.95;
        color: var(--text-strong);
    }
    .err-code .dim {
        color: var(--text-faint);
    }

    .err-label-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        padding: 12px 2px 0;
        gap: 12px;
    }

    .err-title {
        font-size: clamp(26px, 4vw, 34px);
        font-weight: var(--w-display);
        letter-spacing: var(--track-display);
        line-height: 1.1;
        margin-top: 40px;
        color: var(--text-strong);
    }
    .err-sub {
        color: var(--text-muted);
        font-size: 15px;
        line-height: var(--leading-body);
        margin-top: 14px;
        max-width: 480px;
        text-wrap: pretty;
    }

    .maint-window {
        margin-top: 26px;
        border: var(--border-hair);
        display: grid;
        grid-template-columns: 1fr 1fr;
    }
    .maint-cell {
        padding: 16px 18px;
    }
    .maint-cell + .maint-cell {
        border-left: var(--border-hair);
    }
    .maint-cell .k {
        font-size: 10.5px;
        font-weight: 600;
        letter-spacing: 0.09em;
        color: var(--text-faint);
    }
    .maint-cell .v {
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-top: 6px;
        color: var(--text-strong);
    }

    .err-actions {
        display: flex;
        gap: 10px;
        margin-top: 36px;
        flex-wrap: wrap;
    }

    .err-links {
        margin-top: 56px;
        border-top: var(--border-hair);
    }
    .err-link {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        padding: 15px 2px;
        border: 0;
        border-bottom: var(--border-hair);
        background: none;
        cursor: pointer;
        font-size: 14.5px;
        font-weight: 600;
        color: var(--text-strong);
        text-align: left;
        text-decoration: none;
        transition: background var(--dur-fast) var(--ease-out);
    }
    .err-link:hover {
        background: var(--paper-50);
    }
    .err-link .arrow {
        color: var(--text-faint);
    }
    .err-link:hover .arrow {
        color: var(--accent-strong);
    }
    .err-link .micro {
        font-size: 10.5px;
        font-weight: 600;
        letter-spacing: 0.09em;
        color: var(--text-faint);
        margin-left: 12px;
    }

    /* ── 404 full-bleed photo hero with everything overlaid ── */
    .err-hero {
        position: relative;
        width: 100%;
        min-height: clamp(640px, calc(100vh - 60px), 940px);
        display: flex;
        align-items: center;
        overflow: hidden;
        border-bottom: var(--border-rule);
    }
    .err-hero img {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: 60% 50%;
    }
    .err-hero-overlay {
        position: relative;
        z-index: 2;
        width: 100%;
        max-width: 880px;
        margin: 0 auto;
        padding: 56px var(--container-pad-mobile);
        box-sizing: border-box;
        color: #fff;
    }
    /* No tint panel behind the text — only the dark text itself carries a soft
       shadow so it stays legible directly on the photo. */
    .hero-micro,
    .hero-code,
    .hero-title,
    .hero-sub,
    .hero-link,
    .hero-cap {
        text-shadow: 0 1px 20px rgba(0, 0, 0, 0.55);
    }
    .hero-micro {
        display: block;
        margin-bottom: 14px;
    }
    .hero-micro .acc {
        color: var(--signal-200);
    }
    .hero-code {
        font-size: clamp(72px, 12vw, 156px);
        font-weight: var(--w-display);
        letter-spacing: var(--track-display);
        line-height: 0.86;
    }
    .hero-title {
        font-size: clamp(24px, 3vw, 36px);
        font-weight: var(--w-display);
        letter-spacing: var(--track-display);
        line-height: 1.05;
        margin-top: 22px;
        max-width: 18ch;
    }
    .hero-sub {
        font-size: clamp(14px, 1.3vw, 16px);
        line-height: var(--leading-body);
        margin-top: 14px;
        max-width: 42ch;
        color: rgba(255, 255, 255, 0.78);
        text-wrap: pretty;
    }

    /* Requested URL — overlaid, light-on-dark */
    .hero-url {
        margin-top: 28px;
        max-width: 480px;
        border: 1px solid rgba(255, 255, 255, 0.24);
        display: grid;
        grid-template-columns: auto 1fr;
        align-items: center;
    }
    .hero-url .k {
        padding: 11px 16px;
        border-right: 1px solid rgba(255, 255, 255, 0.24);
        font-size: 10.5px;
        font-weight: 600;
        letter-spacing: 0.09em;
        color: rgba(255, 255, 255, 0.55);
        white-space: nowrap;
    }
    .hero-url .v {
        padding: 11px 16px;
        font-size: 13px;
        font-weight: 600;
        color: #fff;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
    }

    /* Actions — custom buttons tuned for the dark overlay */
    .hero-actions {
        display: flex;
        gap: 10px;
        margin-top: 28px;
        flex-wrap: wrap;
    }
    .hero-btn {
        display: inline-flex;
        align-items: center;
        height: 50px;
        padding: 0 26px;
        font-family: var(--font-sans);
        font-size: 15px;
        font-weight: 600;
        border: 1px solid transparent;
        border-radius: var(--r-1);
        text-decoration: none;
        cursor: pointer;
        transition: background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
    }
    .hero-btn:active { transform: translateY(1px); }
    .hero-btn--primary {
        background: #fff;
        color: var(--ink-900);
    }
    .hero-btn--primary:hover {
        background: rgba(255, 255, 255, 0.86);
    }
    .hero-btn--ghost {
        background: transparent;
        color: #fff;
        border-color: rgba(255, 255, 255, 0.4);
    }
    .hero-btn--ghost:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(255, 255, 255, 0.7);
    }

    /* Quick links — overlaid, light-on-dark */
    .hero-links {
        display: block;
        margin-top: 40px;
        max-width: 520px;
        border-top: 1px solid rgba(255, 255, 255, 0.22);
    }
    .hero-link {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        padding: 14px 2px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.14);
        font-size: 14.5px;
        font-weight: 600;
        color: #fff;
        text-decoration: none;
        transition: background var(--dur-fast) var(--ease-out);
    }
    .hero-link:hover {
        background: rgba(255, 255, 255, 0.06);
    }
    .hero-link .arrow {
        color: rgba(255, 255, 255, 0.5);
    }
    .hero-link:hover .arrow {
        color: var(--signal-200);
    }
    .hero-link .micro {
        font-size: 10.5px;
        font-weight: 600;
        letter-spacing: 0.09em;
        color: rgba(255, 255, 255, 0.45);
        margin-left: 12px;
    }

    .hero-cap {
        margin-top: 28px;
        color: rgba(255, 255, 255, 0.45);
    }

    @media (min-width: 768px) {
        .err-page {
            padding-left: var(--container-pad);
            padding-right: var(--container-pad);
        }
    }
</style>
