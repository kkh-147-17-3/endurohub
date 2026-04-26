<script lang="ts">
    let { active = false }: { active?: boolean } = $props();
</script>

{#if active}
    <div class="progress" aria-hidden="true">
        <div class="progress-bar"></div>
    </div>
{/if}

<style>
    .progress {
        position: fixed;
        top: 56px;
        left: 0;
        right: 0;
        height: 2px;
        background: var(--arena-paper-alt);
        z-index: 50;
        pointer-events: none;
        overflow: hidden;
    }
    .progress-bar {
        height: 100%;
        width: 0;
        background: var(--arena-accent);
        animation: progress-grow 2s ease-out forwards;
    }
    @keyframes progress-grow {
        0% { width: 0; }
        100% { width: 90%; }
    }
</style>
