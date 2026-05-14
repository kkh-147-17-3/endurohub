<script lang="ts">
    import { dndzone } from 'svelte-dnd-action';
    import { flip } from 'svelte/animate';

    type Kind = 'course' | 'giveaway';
    interface Item { id: string; path: string; url: string; }

    let {
        slug,
        kind,
        title,
        initialPaths,
        initialUrls,
    }: {
        slug: string;
        kind: Kind;
        title: string;
        initialPaths: string[];
        initialUrls: string[];
    } = $props();

    function toItems(paths: string[], urls: string[]): Item[] {
        return paths.map((p, i) => ({ id: p, path: p, url: urls[i] || '' }));
    }

    let items = $state<Item[]>(toItems(initialPaths, initialUrls));
    let uploading = $state(false);
    let error = $state('');
    let fileInput = $state<HTMLInputElement | null>(null);
    let dragging = $state(false);
    let pasteFocused = $state(false);

    async function uploadFiles(files: File[]) {
        if (files.length === 0) return;
        const fd = new FormData();
        fd.append('kind', kind);
        for (const f of files) fd.append('images', f);

        error = '';
        uploading = true;
        try {
            const res = await fetch(`/admin/api/races/${slug}/images`, {
                method: 'POST',
                body: fd,
            });
            const data = await res.json();
            if (!res.ok) {
                error = data?.errors?.images?.[0] || data?.detail || '업로드 실패';
                return;
            }
            items = (data.images as { path: string; url: string }[]).map(
                (x) => ({ id: x.path, ...x })
            );
        } finally {
            uploading = false;
        }
    }

    async function handleUpload(e: Event) {
        const input = e.target as HTMLInputElement;
        const files = input.files ? Array.from(input.files) : [];
        try {
            await uploadFiles(files);
        } finally {
            input.value = '';
        }
    }

    /** Clipboard often lists the same image in both `items` and `files` with different File refs. */
    function imageFilesFromClipboard(cd: DataTransfer): File[] {
        const seen = new Set<string>();
        const out: File[] = [];
        const push = (f: File | null) => {
            if (!f || !f.type.startsWith('image/')) return;
            const key = `${f.size}\0${f.lastModified}\0${f.type}`;
            if (seen.has(key)) return;
            seen.add(key);
            out.push(f);
        };
        for (const item of Array.from(cd.items)) {
            if (item.kind === 'file' && item.type.startsWith('image/')) {
                push(item.getAsFile());
            }
        }
        // Only use `files` when `items` yielded nothing (avoid duplicate paths of the same blob).
        if (out.length === 0) {
            for (const f of Array.from(cd.files)) {
                push(f);
            }
        }
        return out;
    }

    async function handlePaste(e: ClipboardEvent) {
        if (uploading) return;
        const cd = e.clipboardData;
        if (!cd) return;
        const files = imageFilesFromClipboard(cd);
        if (files.length === 0) return;
        e.preventDefault();
        await uploadFiles(files);
    }

    async function deleteImage(path: string) {
        if (!confirm('이 이미지를 삭제할까요?')) return;
        const url = `/admin/api/races/${slug}/images?kind=${kind}&path=${encodeURIComponent(path)}`;
        const res = await fetch(url, { method: 'DELETE' });
        const data = await res.json();
        if (!res.ok) {
            error = data?.detail || '삭제 실패';
            return;
        }
        items = (data.images as { path: string; url: string }[]).map(
            (x) => ({ id: x.path, ...x })
        );
    }

    async function persistOrder(orderedPaths: string[]) {
        const res = await fetch(`/admin/api/races/${slug}/images`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ kind, paths: orderedPaths }),
        });
        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            error = data?.errors?.paths?.[0] || data?.detail || '순서 저장 실패';
        }
    }

    function onConsider(e: CustomEvent<{ items: Item[] }>) {
        items = e.detail.items;
        dragging = true;
    }

    function onFinalize(e: CustomEvent<{ items: Item[] }>) {
        items = e.detail.items;
        dragging = false;
        persistOrder(items.map((x) => x.path));
    }
</script>

<section
    class="gallery"
    class:paste-focused={pasteFocused}
    tabindex="0"
    role="region"
    aria-label="{title} 갤러리 (Ctrl+V로 붙여넣기 가능)"
    onpaste={handlePaste}
    onfocus={() => (pasteFocused = true)}
    onblur={() => (pasteFocused = false)}
>
    <header>
        <h3>{title}</h3>
        <span class="count">{items.length}장</span>
        {#if pasteFocused}
            <span class="paste-hint">Ctrl+V 붙여넣기 가능</span>
        {/if}
        <div class="spacer"></div>
        <button
            type="button"
            class="upload-btn"
            onclick={() => fileInput?.click()}
            disabled={uploading}
        >
            {uploading ? '업로드중…' : '+ 이미지 추가'}
        </button>
        <input
            bind:this={fileInput}
            type="file"
            accept="image/*"
            multiple
            hidden
            onchange={handleUpload}
        />
    </header>

    {#if error}
        <div class="error">{error}</div>
    {/if}

    {#if items.length === 0}
        <div class="empty">
            아직 이미지가 없습니다. 버튼으로 추가하거나 여기를 클릭한 뒤 <kbd>Ctrl</kbd>+<kbd>V</kbd>로 붙여넣어 보세요.
        </div>
    {:else}
        <div
            class="grid"
            class:dragging
            use:dndzone={{ items, flipDurationMs: 180, dropTargetStyle: {} }}
            onconsider={onConsider as any}
            onfinalize={onFinalize as any}
        >
            {#each items as item, i (item.id)}
                <div class="thumb" animate:flip={{ duration: 180 }}>
                    <img src={item.url} alt="" />
                    <span class="ord">{i + 1}</span>
                    <button
                        type="button"
                        class="del"
                        onclick={() => deleteImage(item.path)}
                        aria-label="삭제"
                    >×</button>
                </div>
            {/each}
        </div>
        <div class="hint">드래그해서 순서를 바꿀 수 있어요. 갤러리 클릭 후 <kbd>Ctrl</kbd>+<kbd>V</kbd>로 이미지 붙여넣기도 가능.</div>
    {/if}
</section>

<style>
    .gallery {
        background: #fff;
        border: 1px solid var(--arena-line, #ddd);
        padding: 16px;
        outline: none;
        transition: border-color 0.12s, box-shadow 0.12s;
    }
    .gallery.paste-focused {
        border-color: var(--arena-accent, #22c55e);
        box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.15);
    }
    .paste-hint {
        font-family: var(--arena-f-mono, ui-monospace);
        font-size: 10px;
        letter-spacing: 0.5px;
        color: var(--arena-accent-deep, #16a34a);
    }
    kbd {
        display: inline-block;
        padding: 1px 5px;
        background: var(--arena-paper-alt, #f4f4f0);
        border: 1px solid var(--arena-line, #ddd);
        border-radius: 3px;
        font-family: var(--arena-f-mono, ui-monospace);
        font-size: 10px;
        color: var(--arena-ink, #111);
    }
    header {
        display: flex;
        align-items: baseline;
        gap: 12px;
        margin-bottom: 12px;
    }
    h3 {
        font-family: var(--arena-f-display, system-ui);
        font-size: 14px;
        font-weight: 700;
        margin: 0;
    }
    .count {
        font-family: var(--arena-f-mono, ui-monospace);
        font-size: 11px;
        color: var(--arena-ink-mute, #888);
    }
    .spacer { flex: 1; }
    .upload-btn {
        padding: 6px 12px;
        background: var(--arena-ink, #111);
        color: #fff;
        border: 0;
        cursor: pointer;
        font-size: 11px;
        font-family: var(--arena-f-mono, ui-monospace);
        letter-spacing: 0.5px;
    }
    .upload-btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .error {
        padding: 8px;
        margin-bottom: 8px;
        background: #fef2f2;
        border: 1px solid #fecaca;
        color: #b91c1c;
        font-size: 12px;
    }
    .empty {
        padding: 32px;
        text-align: center;
        color: var(--arena-ink-mute, #888);
        font-size: 13px;
        background: var(--arena-paper-alt, #f4f4f0);
    }
    .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 8px;
        min-height: 100px;
    }
    .thumb {
        position: relative;
        aspect-ratio: 1;
        background: var(--arena-paper-alt, #f4f4f0);
        cursor: grab;
        overflow: hidden;
        border: 1px solid var(--arena-line-soft, #eee);
    }
    .thumb:active { cursor: grabbing; }
    .thumb img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }
    .ord {
        position: absolute;
        top: 4px;
        left: 4px;
        background: rgba(0, 0, 0, 0.7);
        color: #fff;
        font-family: var(--arena-f-mono, ui-monospace);
        font-size: 10px;
        padding: 2px 6px;
        border-radius: 2px;
    }
    .del {
        position: absolute;
        top: 4px;
        right: 4px;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: #ef4444;
        color: #fff;
        border: 0;
        font-size: 14px;
        line-height: 1;
        cursor: pointer;
        opacity: 0;
        transition: opacity 0.12s;
    }
    .thumb:hover .del { opacity: 1; }
    .hint {
        margin-top: 8px;
        font-size: 11px;
        color: var(--arena-ink-mute, #888);
        font-family: var(--arena-f-mono, ui-monospace);
    }
</style>
