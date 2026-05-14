<script lang="ts">
    /** load()에서 항상 리다이렉트되므로 이 화면은 거의 보이지 않습니다. */
</script>

<svelte:head>
    <title>관리자 로그인 · Admin</title>
</svelte:head>

<p class="fallback">Django 관리자 로그인으로 이동 중입니다…</p>

<style>
    .fallback {
        font-family: var(--arena-f-body, system-ui);
        font-size: 14px;
        color: var(--arena-ink-mute, #888);
        padding: 24px;
        text-align: center;
    }
</style>
