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

    let nickname = $state(data.post.nickname === '익명' ? '' : data.post.nickname);
    let title = $state(data.post.title);
    let content = $state(data.post.content);
    let selectedRaceIds = $state<number[]>(data.post.taggedRaces?.map(r => r.id) || []);

    // Convert existing images to ImageFile format
    let images = $state<ImageFile[]>(
        (data.post.images || []).map((path: string, index: number) => ({
            preview: data.post.imageSrcs?.[index] || '',
            path: path,
        }))
    );

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

    function handleEnhance({ formData, cancel }: { formData: FormData; cancel: () => void }) {
        isSubmitting = true;

        // Save nickname to localStorage
        if (nickname) localStorage.setItem('nickname', nickname);

        // Append existing image paths and new image files from component state
        images.forEach((img) => {
            if (img.path) {
                formData.append('existing_images', img.path);
            } else if (img.file) {
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
    <title>글 수정 - EnduroHub</title>
    <meta name="description" content="자유게시판 글을 수정합니다." />
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="container mx-auto px-4 py-8">
    <div class="breadcrumbs text-sm mb-6">
        <ul>
            <li><a href="/">홈</a></li>
            <li><a href="/posts">자유게시판</a></li>
            <li><a href="/posts/{data.post.id}">{data.post.title}</a></li>
            <li>수정</li>
        </ul>
    </div>

    <div class="max-w-2xl mx-auto">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
            <div>
                <h1 class="text-3xl font-bold">글 수정</h1>
                <p class="text-base-content/60 mt-1">게시글을 수정합니다.</p>
            </div>
            <div class="flex gap-2">
                <a href="/posts/{data.post.id}" class="btn btn-ghost">취소</a>
                <button type="submit" form="edit-form" class="btn btn-primary" disabled={isSubmitting}>
                    {#if isSubmitting}
                        <span class="loading loading-spinner loading-sm"></span>
                    {/if}
                    수정하기
                </button>
            </div>
        </div>

        <form
            id="edit-form"
            method="POST"
            enctype="multipart/form-data"
            use:enhance={handleEnhance}
            class="space-y-6"
        >
            <input type="hidden" name="edit_token" value={data.editToken} />

            <!-- Basic Info Card -->
            <div class="card bg-base-100 shadow-xl">
                <div class="card-body">
                    <h2 class="card-title text-lg mb-4">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                        기본 정보
                    </h2>

                    <div class="space-y-5">
                        <!-- Nickname -->
                        <div class="form-control w-full">
                            <label class="label" for="nickname">
                                <span class="label-text font-medium">닉네임</span>
                                <span class="label-text-alt">선택사항</span>
                            </label>
                            <input
                                type="text"
                                id="nickname"
                                name="nickname"
                                class="input input-bordered w-full"
                                placeholder="미입력 시 익명으로 표시됩니다"
                                maxlength="50"
                                bind:value={nickname}
                            />
                        </div>

                        <!-- Title -->
                        <div class="form-control w-full">
                            <label class="label" for="title">
                                <span class="label-text font-medium">제목 <span class="text-error">*</span></span>
                                <span class="label-text-alt">{title.length}/100</span>
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
                                <label class="label" role="alert">
                                    <span class="label-text-alt text-error">{errors.title}</span>
                                </label>
                            {/if}
                        </div>

                        <!-- Content -->
                        <div class="form-control w-full">
                            <label class="label" for="content">
                                <span class="label-text font-medium">내용 <span class="text-error">*</span></span>
                                <span class="label-text-alt">{content.length}/10000</span>
                            </label>
                            <textarea
                                id="content"
                                name="content"
                                class="textarea textarea-bordered w-full min-h-[200px]"
                                class:textarea-error={errors.content}
                                placeholder="내용을 입력하세요"
                                maxlength="10000"
                                required
                                bind:value={content}
                            ></textarea>
                            {#if errors.content}
                                <label class="label" role="alert">
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

                        <!-- Hidden race_ids for form submission -->
                        {#each selectedRaceIds as raceId}
                            <input type="hidden" name="race_ids" value={raceId} />
                        {/each}

                        <!-- Image Uploader -->
                        <ImageUploader bind:images />
                        {#if errors.images}
                            <p class="text-sm text-error mt-1" role="alert">{errors.images}</p>
                        {/if}
                    </div>
                </div>
            </div>

            <!-- Error message -->
            {#if errors.password}
                <div class="alert alert-error" role="alert">
                    <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>{errors.password}</span>
                </div>
            {/if}

            <!-- Mobile bottom button -->
            <div class="flex gap-4 justify-end lg:hidden">
                <a href="/posts/{data.post.id}" class="btn btn-ghost">취소</a>
                <button type="submit" class="btn btn-primary" disabled={isSubmitting}>
                    {#if isSubmitting}
                        <span class="loading loading-spinner loading-sm"></span>
                    {/if}
                    수정하기
                </button>
            </div>
        </form>
    </div>
</div>
