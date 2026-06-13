<script lang="ts">
    // ENDUROHUB v2 — page-load progress bar.
    // A thin indeterminate accent rule pinned to the bottom edge of the sticky
    // nav header, shown while a client navigation is in flight. Driven by the
    // `active` prop (the layout passes `!!$navigating`).
    let { active = false }: { active?: boolean } = $props();

    // ms — keep the bar up at least this long so a fast nav doesn't flash a
    // single frame and read as a glitch.
    const MIN_SHOW = 300;

    const now = () => (typeof performance !== 'undefined' ? performance.now() : Date.now());

    let visible = $state(false);
    let shownAt = 0;
    let hideTimer: ReturnType<typeof setTimeout> | undefined;

    $effect(() => {
        if (active) {
            if (hideTimer) {
                clearTimeout(hideTimer);
                hideTimer = undefined;
            }
            if (!visible) {
                visible = true;
                shownAt = now();
            }
        } else if (visible) {
            const wait = Math.max(0, MIN_SHOW - (now() - shownAt));
            if (hideTimer) clearTimeout(hideTimer);
            hideTimer = setTimeout(() => {
                visible = false;
                hideTimer = undefined;
            }, wait);
        }
    });

    $effect(() => () => {
        if (hideTimer) clearTimeout(hideTimer);
    });
</script>

<div class="eh-loadbar" class:on={visible} aria-hidden="true">
    <span class="eh-loadbar__run"></span>
</div>

<style>
    .eh-loadbar {
        position: fixed;
        left: 0;
        right: 0;
        top: 64px; /* sits on the sticky nav's bottom border (.eh-nav height) */
        height: 2px;
        z-index: 60; /* above the nav (z-50) */
        overflow: hidden;
        pointer-events: none;
        background: transparent;
        opacity: 0;
        transition: opacity 160ms cubic-bezier(0.2, 0.8, 0.2, 1);
    }

    .eh-loadbar.on {
        opacity: 1;
    }

    .eh-loadbar__run {
        position: absolute;
        top: 0;
        left: 0;
        height: 100%;
        width: 28%;
        background: var(--accent, #43a564);
        animation: eh-loadbar-run 1.1s cubic-bezier(0.2, 0.8, 0.2, 1) infinite;
        animation-play-state: paused;
    }

    .eh-loadbar.on .eh-loadbar__run {
        animation-play-state: running;
    }

    @keyframes eh-loadbar-run {
        from {
            transform: translateX(-110%);
        }
        to {
            transform: translateX(470%);
        }
    }

    @media (max-width: 768px) {
        .eh-loadbar {
            top: 52px; /* mobile .eh-nav height */
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .eh-loadbar__run {
            animation: none;
            width: 100%;
            opacity: 0.7;
        }
    }
</style>
