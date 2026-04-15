<script lang="ts">
    import { page } from '$app/stores';

    let status = $derived($page.status);
    let message = $derived($page.error?.message || '');
</script>

<svelte:head>
    <title>{status} - 엔듀로허브</title>
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="min-h-[60vh] flex items-center justify-center px-4">
    <div class="text-center max-w-md">
        <div class="text-8xl font-black tracking-tighter text-base-content/10 select-none leading-none">
            {status}
        </div>

        <h1 class="text-xl font-bold mt-4 text-base-content">
            {#if status === 404}
                페이지를 찾을 수 없습니다
            {:else if status === 500}
                서버 오류가 발생했습니다
            {:else if status === 403}
                접근 권한이 없습니다
            {:else}
                오류가 발생했습니다
            {/if}
        </h1>

        <p class="text-base-content/50 text-sm mt-2">
            {#if status === 404}
                요청하신 페이지가 존재하지 않거나 이동되었을 수 있습니다.
            {:else if message}
                {message}
            {:else}
                잠시 후 다시 시도해주세요.
            {/if}
        </p>

        <div class="flex justify-center gap-3 mt-8">
            <a href="/" class="btn btn-primary btn-sm">홈으로</a>
            <button class="btn btn-ghost btn-sm" onclick={() => history.back()}>뒤로가기</button>
        </div>
    </div>
</div>
