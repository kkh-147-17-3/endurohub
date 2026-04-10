<script lang="ts">
    import { enhance } from '$app/forms';

    let { data, form } = $props();

    let user = $derived(form?.user || data.user);
    let emailUpdatesOptIn = $state(false);
    let isSubmitting = $state(false);
    let errors = $derived(flattenErrors(form?.errors));
    let successMessage = $derived(form?.successMessage || '');

    let initials = $derived(
        (user.nickname || user.email || '?').slice(0, 1).toUpperCase()
    );

    function flattenErrors(errs: Record<string, string[]> | undefined): Record<string, string> {
        if (!errs) return {};
        const flat: Record<string, string> = {};
        for (const [key, msgs] of Object.entries(errs)) {
            flat[key] = Array.isArray(msgs) ? msgs[0] : msgs;
        }
        return flat;
    }

    $effect(() => {
        if (form?.emailUpdatesOptIn !== undefined) {
            emailUpdatesOptIn = !!form.emailUpdatesOptIn;
        } else if (user?.emailUpdatesOptIn !== undefined) {
            emailUpdatesOptIn = !!user.emailUpdatesOptIn;
        }
    });
</script>

<svelte:head>
    <title>마이페이지 - 엔듀로허브</title>
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="container mx-auto px-4 py-10">
    <div class="max-w-lg mx-auto space-y-6">

        <!-- Profile Header -->
        <div class="flex items-center gap-4">
            {#if user.profileImage}
                <img
                    src={user.profileImage}
                    alt={user.nickname || '프로필'}
                    class="w-16 h-16 rounded-full object-cover ring-2 ring-base-300"
                />
            {:else}
                <div class="w-16 h-16 rounded-full bg-primary text-primary-content flex items-center justify-center text-2xl font-bold ring-2 ring-primary/20">
                    {initials}
                </div>
            {/if}
            <div class="min-w-0">
                <h1 class="text-xl font-bold truncate">{user.nickname || '닉네임 미설정'}</h1>
                <p class="text-sm text-base-content/50 truncate">{user.email || '이메일 미등록'}</p>
            </div>
        </div>

        <!-- Account Info -->
        <section class="card bg-base-100 shadow">
            <div class="card-body p-5 space-y-0 divide-y divide-base-200">
                <div class="flex items-center justify-between py-3 first:pt-0">
                    <div class="text-sm text-base-content/60">닉네임</div>
                    <div class="font-medium">{user.nickname || '미설정'}</div>
                </div>
                <div class="flex items-center justify-between py-3">
                    <div class="text-sm text-base-content/60">이메일</div>
                    <div class="flex items-center gap-2">
                        <span class="font-medium truncate max-w-[200px]">{user.email || '미등록'}</span>
                        {#if user.emailVerified}
                            <span class="badge badge-success badge-sm gap-1">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" /></svg>
                                인증됨
                            </span>
                        {:else if user.email}
                            <span class="badge badge-warning badge-sm">미인증</span>
                        {/if}
                    </div>
                </div>
            </div>
        </section>

        <!-- Email Verification CTA -->
        {#if !user.emailVerified}
            <div class="rounded-xl border border-warning/30 bg-warning/5 px-5 py-4">
                <div class="flex items-start gap-3">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-warning shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" /></svg>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium">이메일 인증이 필요합니다</p>
                        <p class="text-xs text-base-content/50 mt-1">인증을 완료하면 계정 관련 안내와 알림을 받을 수 있습니다.</p>
                    </div>
                    <a href="/auth/verify-email" class="btn btn-warning btn-sm shrink-0">인증하기</a>
                </div>
            </div>
        {/if}

        <!-- Email Notification Settings -->
        <section class="card bg-base-100 shadow">
            <div class="card-body p-5">
                <h2 class="text-sm font-semibold text-base-content/70 uppercase tracking-wide">알림 설정</h2>

                <form
                    method="POST"
                    class="mt-3 space-y-4"
                    use:enhance={() => {
                        isSubmitting = true;
                        return async ({ update }) => {
                            isSubmitting = false;
                            await update();
                        };
                    }}
                >
                    <label class="flex cursor-pointer items-center justify-between gap-3 rounded-lg border border-base-300 px-4 py-3 transition-colors hover:bg-base-200/50">
                        <div>
                            <div class="text-sm font-medium">이메일 알림 수신</div>
                            <div class="text-xs text-base-content/50 mt-0.5">대회 소식, 일정 업데이트, 이벤트 안내</div>
                        </div>
                        <input
                            type="checkbox"
                            name="email_updates_opt_in"
                            class="toggle toggle-primary toggle-sm"
                            bind:checked={emailUpdatesOptIn}
                        />
                    </label>

                    <p class="text-xs text-base-content/50">
                        계정 보안, 인증 등 필수 안내는 동의 여부와 관계없이 발송됩니다.
                    </p>

                    {#if successMessage}
                        <div class="flex items-center gap-2 text-sm text-success">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" /></svg>
                            {successMessage}
                        </div>
                    {/if}

                    {#if errors.profile || errors.email_updates_opt_in}
                        <div class="flex items-center gap-2 text-sm text-error">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
                            {errors.profile || errors.email_updates_opt_in}
                        </div>
                    {/if}

                    <button type="submit" class="btn btn-primary btn-sm btn-block" disabled={isSubmitting}>
                        {#if isSubmitting}
                            <span class="loading loading-spinner loading-xs"></span>
                        {/if}
                        저장
                    </button>
                </form>
            </div>
        </section>

        <!-- Logout -->
        <form method="POST" action="/auth/logout">
            <button type="submit" class="btn btn-ghost btn-sm btn-block text-base-content/50 hover:text-error cursor-pointer">
                로그아웃
            </button>
        </form>

    </div>
</div>
