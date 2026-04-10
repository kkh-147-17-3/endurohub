<script lang="ts">
    let { data } = $props();
</script>

<svelte:head>
    <title>로그인 중... - 엔듀로허브</title>
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="container mx-auto px-4 py-16">
    <div class="max-w-sm mx-auto text-center">
        {#if data.error}
            <div class="card bg-base-100 border border-base-300">
                <div class="card-body">
                    <h2 class="card-title justify-center text-error">로그인 실패</h2>
                    <p class="text-base-content/70">{data.error}</p>
                    <div class="card-actions justify-center mt-4">
                        <a href="/auth/login" class="btn btn-primary">다시 시도</a>
                    </div>
                </div>
            </div>
        {:else}
            <span class="loading loading-spinner loading-lg text-primary"></span>
            <p class="mt-4 text-base-content/60">로그인 처리 중...</p>
        {/if}
    </div>
</div>
