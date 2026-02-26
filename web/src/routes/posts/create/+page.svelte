<script lang="ts">
    import { enhance } from '$app/forms';
    import RaceTagSelector from '$lib/components/RaceTagSelector.svelte';
    import ImageUploader from '$lib/components/ImageUploader.svelte';

    interface ImageFile {
        file?: File;
        preview: string;
        path?: string;
    }

    let { data, form } = $props();

    let nickname = $state('');
    let title = $state('');
    let content = $state('');
    let password = $state('');
    let selectedRaceIds = $state<number[]>([]);
    let images = $state<ImageFile[]>([]);

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

    // Restore nickname and password from localStorage
    $effect(() => {
        const savedNickname = localStorage.getItem('nickname');
        const savedPassword = localStorage.getItem('postPassword');
        if (savedNickname) nickname = savedNickname;
        if (savedPassword) password = savedPassword;
    });

    function handleEnhance({ formData, cancel }: { formData: FormData; cancel: () => void }) {
        isSubmitting = true;

        // Save to localStorage
        if (nickname) localStorage.setItem('nickname', nickname);
        if (password) localStorage.setItem('postPassword', password);

        // Append image files from component state
        images.forEach((img, index) => {
            if (img.file) {
                formData.append('images', img.file);
            }
        });

        return async ({ update }: { update: () => Promise<void> }) => {
            isSubmitting = false;
            await update();
        };
    }
</script>

<svelte:head>
    <title>글쓰기 - EnduroHub</title>
    <meta name="description" content="자유게시판에 글을 작성합니다." />
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="container mx-auto px-4 py-8">
    <div class="max-w-2xl mx-auto pb-24">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
            <a href="/posts" class="btn btn-ghost btn-sm btn-circle">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
            </a>
            <div>
                <h1 class="text-2xl font-bold">글쓰기</h1>
            </div>
        </div>

        <form
            id="post-form"
            method="POST"
            enctype="multipart/form-data"
            use:enhance={handleEnhance}
            class="space-y-6"
        >
            <!-- Nickname + Password -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="form-control w-full">
                    <label class="label" for="nickname">
                        <span class="label-text font-medium">닉네임</span>
                        <span class="label-text-alt text-base-content/50">선택</span>
                    </label>
                    <input
                        type="text"
                        id="nickname"
                        name="nickname"
                        class="input input-bordered w-full"
                        placeholder="익명"
                        maxlength="50"
                        bind:value={nickname}
                    />
                </div>

                <div class="form-control w-full">
                    <label class="label" for="password">
                        <span class="label-text font-medium">비밀번호 <span class="text-error">*</span></span>
                    </label>
                    <input
                        type="password"
                        id="password"
                        name="password"
                        class="input input-bordered w-full"
                        class:input-error={errors.password}
                        placeholder="수정/삭제 시 필요"
                        minlength="4"
                        maxlength="50"
                        required
                        bind:value={password}
                    />
                    {#if errors.password}
                        <label class="label py-1" role="alert">
                            <span class="label-text-alt text-error">{errors.password}</span>
                        </label>
                    {/if}
                </div>
            </div>

            <!-- Title -->
            <div class="form-control w-full">
                <label class="label" for="title">
                    <span class="label-text font-medium">제목 <span class="text-error">*</span></span>
                    <span class="label-text-alt text-base-content/50">{title.length}/100</span>
                </label>
                <input
                    type="text"
                    id="title"
                    name="title"
                    class="input input-bordered w-full"
                    class:input-error={errors.title}
                    placeholder="제목을 입력하세요"
                    maxlength="100"
                    required
                    bind:value={title}
                />
                {#if errors.title}
                    <label class="label py-1" role="alert">
                        <span class="label-text-alt text-error">{errors.title}</span>
                    </label>
                {/if}
            </div>

            <!-- Content -->
            <div class="form-control w-full">
                <label class="label" for="content">
                    <span class="label-text font-medium">내용 <span class="text-error">*</span></span>
                    <span class="label-text-alt text-base-content/50">{content.length}/10000</span>
                </label>
                <textarea
                    id="content"
                    name="content"
                    class="textarea textarea-bordered w-full min-h-[240px]"
                    class:textarea-error={errors.content}
                    placeholder="내용을 입력하세요"
                    maxlength="10000"
                    required
                    bind:value={content}
                ></textarea>
                {#if errors.content}
                    <label class="label py-1" role="alert">
                        <span class="label-text-alt text-error">{errors.content}</span>
                    </label>
                {/if}
            </div>

            <!-- Race Tags -->
            <div class="form-control w-full">
                <RaceTagSelector races={data.races} bind:selectedIds={selectedRaceIds} />
                {#if errors.race_ids}
                    <p class="text-sm text-error mt-1" role="alert">{errors.race_ids}</p>
                {/if}
            </div>

            <!-- Hidden race_ids inputs for form submission -->
            {#each selectedRaceIds as raceId}
                <input type="hidden" name="race_ids" value={raceId} />
            {/each}

            <!-- Image Uploader -->
            <ImageUploader bind:images />
            {#if errors.images}
                <p class="text-sm text-error mt-1" role="alert">{errors.images}</p>
            {/if}

            <!-- Error message -->
            {#if errors.post}
                <div class="alert alert-error" role="alert">
                    <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>{errors.post}</span>
                </div>
            {/if}
        </form>
    </div>

    <!-- Sticky bottom button -->
    <div class="fixed bottom-0 left-0 right-0 bg-base-100 border-t border-base-300 p-4 z-40">
        <div class="max-w-2xl mx-auto flex gap-3 justify-end">
            <a href="/posts" class="btn btn-ghost">취소</a>
            <button type="submit" form="post-form" class="btn btn-primary" disabled={isSubmitting}>
                {#if isSubmitting}
                    <span class="loading loading-spinner loading-sm"></span>
                {/if}
                등록하기
            </button>
        </div>
    </div>
</div>
