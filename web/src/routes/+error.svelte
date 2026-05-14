<script lang="ts">
    import { onMount } from 'svelte';
    import { get } from 'svelte/store';
    import { page } from '$app/stores';
    import { goto } from '$app/navigation';

    let status = $derived($page.status);
    let message = $derived($page.error?.message || '');

    onMount(() => {
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
    });

    type ErrorMeta = { kicker: string; title: string; sub: string };

    const meta: ErrorMeta = $derived.by(() => {
        switch (status) {
            case 404:
                return {
                    kicker: '페이지 없음',
                    title: '페이지를 찾을 수 없습니다',
                    sub: '요청하신 페이지가 존재하지 않거나 이동되었을 수 있습니다.',
                };
            case 403:
                return {
                    kicker: '접근 거부',
                    title: '접근 권한이 없습니다',
                    sub: '이 페이지를 볼 수 있는 권한이 없습니다.',
                };
            case 500:
                return {
                    kicker: '서버 오류',
                    title: '서버 오류가 발생했습니다',
                    sub: '잠시 후 다시 시도해주세요. 문제가 계속되면 운영팀에 문의해 주세요.',
                };
            default:
                return {
                    kicker: '오류',
                    title: '오류가 발생했습니다',
                    sub: message || '잠시 후 다시 시도해주세요.',
                };
        }
    });

    function goBack() {
        if (typeof window !== 'undefined') {
            if (window.history.length > 1) {
                window.history.back();
            } else {
                goto('/');
            }
        }
    }
</script>

<svelte:head>
    <title>{status} · {meta.title} · endurohub</title>
    <meta name="robots" content="noindex" />
</svelte:head>

<main class="error-wrap">
    <div class="frame">
        <div class="frame-head">
            <span class="dot"></span>
            <span class="kicker">{meta.kicker} · {status}</span>
        </div>

        <div class="frame-body">
            <div class="status-num">{status}</div>
            <div class="rule"></div>
            <h1 class="title">{meta.title}</h1>
            <p class="sub">{meta.sub}</p>
            <div class="actions">
                <a href="/" class="arena-btn arena-btn-primary">
                    홈으로 <span class="arrow">↗</span>
                </a>
                <button type="button" class="arena-btn arena-btn-ghost" onclick={goBack}>
                    뒤로가기
                </button>
            </div>
        </div>

        <div class="frame-foot">
            <span>endurohub</span>
            <span class="mono">{new Date().toISOString().slice(0, 10).replace(/-/g, '.')}</span>
        </div>
    </div>
</main>

<style>
    .error-wrap {
        min-height: 70vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 56px 24px 80px;
        background: var(--arena-paper);
    }

    .frame {
        width: 100%;
        max-width: 560px;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
    }

    .frame-head {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 18px;
        border-bottom: 1px solid var(--arena-line);
        background: var(--arena-paper-alt);
    }
    .dot {
        width: 8px;
        height: 8px;
        background: var(--arena-urgent);
        display: inline-block;
    }
    .kicker {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 2px;
        color: var(--arena-ink);
    }

    .frame-body {
        padding: 56px 32px 48px;
        text-align: center;
    }
    .status-num {
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: clamp(120px, 22vw, 200px);
        line-height: 0.85;
        letter-spacing: -7px;
        color: var(--arena-ink);
        margin: 0;
    }
    .rule {
        width: 56px;
        height: 1px;
        background: var(--arena-ink);
        margin: 36px auto 24px;
    }
    .title {
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 22px;
        letter-spacing: -0.4px;
        color: var(--arena-ink);
        margin: 0 0 12px;
    }
    .sub {
        font-family: var(--arena-f-body);
        font-size: 14px;
        line-height: 1.7;
        color: var(--arena-ink-soft);
        margin: 0 0 32px;
        max-width: 380px;
        margin-left: auto;
        margin-right: auto;
    }
    .actions {
        display: inline-flex;
        gap: 10px;
        flex-wrap: wrap;
        justify-content: center;
    }
    .arrow {
        font-family: var(--arena-f-mono);
        margin-left: 2px;
    }

    .frame-foot {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 18px;
        border-top: 1px solid var(--arena-line);
        background: var(--arena-paper-alt);
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
    }
    .mono {
        font-family: var(--arena-f-mono);
    }

    @media (max-width: 600px) {
        .frame-body { padding: 44px 20px 36px; }
        .status-num { letter-spacing: -5px; }
        .title { font-size: 19px; }
        .sub { font-size: 13px; margin-bottom: 28px; }
        .rule { margin: 28px auto 20px; }
    }
</style>
