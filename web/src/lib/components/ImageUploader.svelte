<script lang="ts">
    interface ImageFile {
        file?: File;
        preview: string;
        path?: string;
    }

    let {
        images = $bindable<ImageFile[]>([]),
        maxImages = 5,
        maxSizeMB = 5,
    }: {
        images?: ImageFile[];
        maxImages?: number;
        maxSizeMB?: number;
    } = $props();

    let fileInput = $state<HTMLInputElement | null>(null);
    let error = $state('');

    function handleFileSelect(e: Event) {
        const input = e.target as HTMLInputElement;
        if (!input.files) return;

        error = '';
        const files = Array.from(input.files);

        if (images.length + files.length > maxImages) {
            error = `이미지는 최대 ${maxImages}개까지 첨부 가능합니다.`;
            input.value = '';
            return;
        }

        for (const file of files) {
            if (file.size > maxSizeMB * 1024 * 1024) {
                error = `이미지 크기는 최대 ${maxSizeMB}MB까지 가능합니다.`;
                continue;
            }

            if (!['image/jpeg', 'image/png', 'image/gif', 'image/webp'].includes(file.type)) {
                error = '지원되는 이미지 형식: jpeg, png, gif, webp';
                continue;
            }

            const reader = new FileReader();
            reader.onload = (e) => {
                images = [...images, {
                    file,
                    preview: e.target?.result as string,
                }];
            };
            reader.readAsDataURL(file);
        }

        input.value = '';
    }

    function removeImage(index: number) {
        images = images.filter((_, i) => i !== index);
    }

    function openFileDialog() {
        fileInput?.click();
    }
</script>

<div class="form-control w-full">
    <div class="label">
        <span class="label-text font-medium">이미지 첨부</span>
        <span class="label-text-alt">{images.length}/{maxImages}</span>
    </div>

    {#if images.length > 0}
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-3">
            {#each images as image, index}
                <div class="relative group">
                    <img
                        src={image.preview}
                        alt="미리보기 {index + 1}"
                        class="w-full h-24 object-cover rounded-lg border border-base-300"
                    />
                    <button
                        type="button"
                        onclick={() => removeImage(index)}
                        class="absolute -top-2 -right-2 btn btn-circle btn-xs btn-error opacity-0 group-hover:opacity-100 transition-opacity"
                        aria-label="이미지 삭제"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
            {/each}
        </div>
    {/if}

    {#if images.length < maxImages}
        <input
            type="file"
            accept="image/jpeg,image/png,image/gif,image/webp"
            multiple
            class="hidden"
            bind:this={fileInput}
            onchange={handleFileSelect}
        />
        <button
            type="button"
            onclick={openFileDialog}
            class="btn btn-outline btn-sm gap-2"
        >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            이미지 추가
        </button>
    {/if}

    {#if error}
        <div class="label">
            <span class="label-text-alt text-error">{error}</span>
        </div>
    {/if}

    <div class="mt-2 flex items-start gap-2 text-sm text-base-content/60">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>최대 {maxImages}개, 각 {maxSizeMB}MB 이하 (jpeg, png, gif, webp)</span>
    </div>
</div>
