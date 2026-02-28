<script lang="ts">
    import { enhance } from '$app/forms';

    let { form } = $props();

    let nickname = $state('');
    let isSubmitting = $state(false);

    let errors = $derived(flattenErrors(form?.errors));

    function flattenErrors(errs: Record<string, string[]> | undefined): Record<string, string> {
        if (!errs) return {};
        const flat: Record<string, string> = {};
        for (const [key, msgs] of Object.entries(errs)) {
            flat[key] = Array.isArray(msgs) ? msgs[0] : msgs;
        }
        return flat;
    }
</script>

<svelte:head>
    <title>닉네임 설정 - 엔듀로허브</title>
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="container mx-auto px-4 py-16">
    <div class="max-w-sm mx-auto">
        <div class="text-center mb-8">
            <h1 class="text-2xl font-bold">닉네임 설정</h1>
            <p class="mt-2 text-base-content/60">커뮤니티에서 사용할 닉네임을 설정해주세요.</p>
        </div>

        <div class="card bg-base-100 shadow-xl">
            <div class="card-body">
                <form
                    method="POST"
                    use:enhance={() => {
                        isSubmitting = true;
                        return async ({ update }) => {
                            isSubmitting = false;
                            await update();
                        };
                    }}
                >
                    <div class="form-control w-full">
                        <label class="label" for="nickname">
                            <span class="label-text font-medium">닉네임 <span class="text-error">*</span></span>
                        </label>
                        <input
                            type="text"
                            id="nickname"
                            name="nickname"
                            class="input input-bordered w-full"
                            class:input-error={errors.nickname}
                            placeholder="2~50자, 한글/영문/숫자"
                            minlength="2"
                            maxlength="50"
                            required
                            bind:value={nickname}
                        />
                        {#if errors.nickname}
                            <div class="label py-1">
                                <span class="label-text-alt text-error">{errors.nickname}</span>
                            </div>
                        {/if}
                        <div class="label py-1">
                            <span class="label-text-alt text-base-content/50">한글, 영문, 숫자, 밑줄, 하이픈 사용 가능</span>
                        </div>
                    </div>

                    <button type="submit" class="btn btn-primary btn-block mt-4" disabled={isSubmitting || !nickname.trim()}>
                        {#if isSubmitting}
                            <span class="loading loading-spinner loading-sm"></span>
                        {/if}
                        설정 완료
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>
