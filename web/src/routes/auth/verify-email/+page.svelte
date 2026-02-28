<script lang="ts">
    import { enhance } from '$app/forms';
    import { clientApiFetch } from '$lib/api.client';
    import type { EmailSendResponse } from '$lib/types';

    let { data, form } = $props();

    let code = $state('');
    let isSubmitting = $state(false);
    let isSending = $state(false);
    let sendMessage = $state('');
    let sendError = $state('');

    let errors = $derived(flattenErrors(form?.errors));

    function flattenErrors(errs: Record<string, string[]> | undefined): Record<string, string> {
        if (!errs) return {};
        const flat: Record<string, string> = {};
        for (const [key, msgs] of Object.entries(errs)) {
            flat[key] = Array.isArray(msgs) ? msgs[0] : msgs;
        }
        return flat;
    }

    async function sendCode() {
        if (isSending) return;
        isSending = true;
        sendMessage = '';
        sendError = '';

        try {
            const result = await clientApiFetch<EmailSendResponse | { error: string }>(
                '/auth/email/send/',
                { method: 'POST' }
            );

            if ('error' in result) {
                sendError = (result as { error: string }).error;
            } else {
                sendMessage = (result as EmailSendResponse).message;
            }
        } catch {
            sendError = '이메일 발송에 실패했습니다.';
        } finally {
            isSending = false;
        }
    }
</script>

<svelte:head>
    <title>이메일 인증 - 엔듀로허브</title>
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="container mx-auto px-4 py-16">
    <div class="max-w-sm mx-auto">
        <div class="text-center mb-8">
            <h1 class="text-2xl font-bold">이메일 인증</h1>
            <p class="mt-2 text-base-content/60">가입한 이메일로 전송된 인증 코드를 입력해주세요.</p>
        </div>

        <div class="card bg-base-100 shadow-xl">
            <div class="card-body space-y-4">
                <!-- Send Code -->
                <div>
                    <button
                        class="btn btn-outline btn-block"
                        onclick={sendCode}
                        disabled={isSending}
                    >
                        {#if isSending}
                            <span class="loading loading-spinner loading-sm"></span>
                        {/if}
                        인증 코드 발송
                    </button>
                    {#if sendMessage}
                        <p class="text-sm text-success mt-2">{sendMessage}</p>
                    {/if}
                    {#if sendError}
                        <p class="text-sm text-error mt-2">{sendError}</p>
                    {/if}
                </div>

                <div class="divider text-sm text-base-content/50">코드 입력</div>

                <!-- Verify Code -->
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
                        <label class="label" for="code">
                            <span class="label-text font-medium">인증 코드 (6자리)</span>
                        </label>
                        <input
                            type="text"
                            id="code"
                            name="code"
                            class="input input-bordered w-full text-center text-2xl tracking-[0.5em] font-mono"
                            class:input-error={errors.code}
                            placeholder="000000"
                            maxlength="6"
                            pattern="[0-9]{6}"
                            inputmode="numeric"
                            autocomplete="one-time-code"
                            required
                            bind:value={code}
                        />
                        {#if errors.code}
                            <div class="label py-1">
                                <span class="label-text-alt text-error">{errors.code}</span>
                            </div>
                        {/if}
                    </div>

                    <button type="submit" class="btn btn-primary btn-block mt-4" disabled={isSubmitting || code.length !== 6}>
                        {#if isSubmitting}
                            <span class="loading loading-spinner loading-sm"></span>
                        {/if}
                        인증 확인
                    </button>
                </form>

                <div class="text-center">
                    <a href="/" class="text-sm text-base-content/50 hover:text-base-content">나중에 하기</a>
                </div>
            </div>
        </div>
    </div>
</div>
