<script lang="ts">
    import { enhance } from '$app/forms';

    let { data, form } = $props();

    let user = $derived(data.user);
    let hasPendingSocialLogin = $derived(!!data.hasPendingSocialLogin);
    let email = $state('');
    let code = $state('');
    let emailUpdatesOptIn = $state(false);
    let isSubmitting = $state(false);
    let isSending = $state(false);

    let errors = $derived(flattenErrors(form?.errors));
    let sendErrors = $derived(flattenErrors(form?.sendErrors));
    let sendMessage = $derived(form?.sendMessage || '');

    function flattenErrors(errs: Record<string, string[]> | undefined): Record<string, string> {
        if (!errs) return {};
        const flat: Record<string, string> = {};
        for (const [key, msgs] of Object.entries(errs)) {
            flat[key] = Array.isArray(msgs) ? msgs[0] : msgs;
        }
        return flat;
    }

    /** OTP 붙여넣기 시 공백·구분자 제거, 전각 숫자 → ASCII (pattern [0-9]{6} 통과) */
    function normalizeOtpDigits(raw: string): string {
        const ascii = raw.replace(/[\uFF10-\uFF19]/g, (c) =>
            String.fromCharCode(c.charCodeAt(0) - 0xff10 + 0x30)
        );
        return ascii.replace(/\D/g, '').slice(0, 6);
    }

    $effect(() => {
        if (!email) {
            email = form?.email || data.user?.email || '';
        }

        if (form?.emailUpdatesOptIn !== undefined) {
            emailUpdatesOptIn = !!form.emailUpdatesOptIn;
        } else if (user?.emailUpdatesOptIn !== undefined) {
            emailUpdatesOptIn = !!user.emailUpdatesOptIn;
        }
    });
</script>

<svelte:head>
    <title>이메일 인증 - 엔듀로허브</title>
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="container mx-auto px-4 py-16">
    <div class="max-w-sm mx-auto">
        <div class="text-center mb-8">
            <h1 class="text-2xl font-bold">이메일 인증</h1>
            <p class="mt-2 text-base-content/60">
                {#if hasPendingSocialLogin}
                    소셜 로그인 가입을 완료하려면 이메일 인증이 필요합니다.
                {:else if user?.email}
                    가입한 이메일로 전송된 인증 코드를 입력해주세요.
                {:else}
                    인증 코드를 받을 이메일을 먼저 입력해주세요.
                {/if}
            </p>
        </div>

        <div class="card bg-base-100 shadow-xl">
            <div class="card-body space-y-4">
                <form
                    method="POST"
                    action="?/send"
                    use:enhance={() => {
                        isSending = true;
                        return async ({ update }) => {
                            isSending = false;
                            await update();
                        };
                    }}
                >
                    <div class="form-control w-full">
                        <label class="label" for="email">
                            <span class="label-text font-medium">이메일</span>
                        </label>
                        <input
                            type="email"
                            id="email"
                            name="email"
                            class="input input-bordered w-full"
                            class:input-error={sendErrors.email}
                            placeholder="you@example.com"
                            autocomplete="email"
                            bind:value={email}
                        />
                        {#if sendErrors.email}
                            <div class="label py-1">
                                <span class="label-text-alt text-error">{sendErrors.email}</span>
                            </div>
                        {:else}
                            <div class="label py-1">
                                <span class="label-text-alt text-base-content/50">인증 코드는 이 주소로 발송됩니다.</span>
                            </div>
                        {/if}
                    </div>

                    <label class="flex cursor-pointer items-start gap-3 rounded-lg border border-base-300 px-4 py-3 mb-2">
                        <input
                            type="checkbox"
                            name="email_updates_opt_in"
                            class="checkbox checkbox-sm mt-0.5 shrink-0"
                            bind:checked={emailUpdatesOptIn}
                        />
                        <span class="text-sm leading-6">
                            [선택] 대회 소식, 업데이트, 이벤트 등 이메일 알림 수신에 동의합니다.
                            <span class="block text-xs text-base-content/50 mt-1">
                                계정 관련 중요 안내는 동의 여부와 관계없이 발송됩니다.
                            </span>
                        </span>
                    </label>

                    <div>
                        <button
                            type="submit"
                            class="btn btn-outline btn-block"
                            disabled={isSending || !email.trim()}
                        >
                            {#if isSending}
                                <span class="loading loading-spinner loading-sm"></span>
                            {/if}
                            인증 코드 발송
                        </button>
                        {#if sendMessage}
                            <p class="text-sm text-success mt-2">{sendMessage}</p>
                        {/if}
                    </div>
                </form>

                <div class="divider text-sm text-base-content/50">코드 입력</div>

                <!-- Verify Code -->
                <form
                    method="POST"
                    action="?/verify"
                    use:enhance={() => {
                        isSubmitting = true;
                        return async ({ update }) => {
                            isSubmitting = false;
                            await update();
                        };
                    }}
                >
                    <input type="hidden" name="email" value={email} />
                    <input type="hidden" name="email_updates_opt_in" value={emailUpdatesOptIn ? 'true' : 'false'} />
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
                            inputmode="numeric"
                            autocomplete="one-time-code"
                            required
                            value={code}
                            oninput={(e) => {
                                code = normalizeOtpDigits(e.currentTarget.value);
                            }}
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
                    <a href={hasPendingSocialLogin ? '/auth/login' : '/'} class="text-sm text-base-content/50 hover:text-base-content">
                        {hasPendingSocialLogin ? '로그인 다시 하기' : '나중에 하기'}
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>
