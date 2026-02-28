<script lang="ts">
    import { browser } from '$app/environment';
    import { clientApiFetch } from '$lib/api.client';

    let {
        content = $bindable(''),
        textLength = $bindable(0),
        maxLength = 10000,
        placeholder = '내용을 입력하세요',
        error = false,
    }: {
        content: string;
        textLength: number;
        maxLength?: number;
        placeholder?: string;
        error?: boolean;
    } = $props();

    let editorElement: HTMLDivElement | undefined = $state();
    let editor: any = $state(null);
    let isUploading = $state(false);

    // Color palette presets
    const textColors = [
        { label: '기본', value: '' },
        { label: '빨강', value: '#dc2626' },
        { label: '주황', value: '#ea580c' },
        { label: '노랑', value: '#ca8a04' },
        { label: '초록', value: '#16a34a' },
        { label: '파랑', value: '#2563eb' },
        { label: '남색', value: '#4f46e5' },
        { label: '보라', value: '#9333ea' },
        { label: '회색', value: '#6b7280' },
    ];

    const highlightColors = [
        { label: '제거', value: '' },
        { label: '노랑', value: '#fef08a' },
        { label: '초록', value: '#bbf7d0' },
        { label: '파랑', value: '#bfdbfe' },
        { label: '분홍', value: '#fbcfe8' },
        { label: '보라', value: '#e9d5ff' },
    ];

    let showColorPicker = $state(false);
    let showHighlightPicker = $state(false);
    let showLinkInput = $state(false);
    let linkUrl = $state('');

    // Close dropdowns on outside click
    function handleClickOutside(e: MouseEvent) {
        const target = e.target as HTMLElement;
        if (!target.closest('.color-picker-wrapper')) {
            showColorPicker = false;
        }
        if (!target.closest('.highlight-picker-wrapper')) {
            showHighlightPicker = false;
        }
        if (!target.closest('.link-input-wrapper')) {
            showLinkInput = false;
        }
    }

    $effect(() => {
        if (!browser || !editorElement) return;

        let destroyed = false;

        (async () => {
            const { Editor } = await import('@tiptap/core');
            const { default: StarterKit } = await import('@tiptap/starter-kit');
            const { default: Underline } = await import('@tiptap/extension-underline');
            const { default: Link } = await import('@tiptap/extension-link');
            const { default: Placeholder } = await import('@tiptap/extension-placeholder');
            const { default: CharacterCount } = await import('@tiptap/extension-character-count');
            const { TextStyle } = await import('@tiptap/extension-text-style');
            const { Color } = await import('@tiptap/extension-color');
            const { default: Highlight } = await import('@tiptap/extension-highlight');
            const { default: Image } = await import('@tiptap/extension-image');

            if (destroyed) return;

            const instance = new Editor({
                element: editorElement,
                extensions: [
                    StarterKit.configure({
                        heading: { levels: [2, 3] },
                    }),
                    Underline,
                    Link.configure({
                        openOnClick: false,
                        HTMLAttributes: {
                            rel: 'nofollow noopener noreferrer',
                            target: '_blank',
                        },
                    }),
                    Placeholder.configure({ placeholder }),
                    CharacterCount,
                    TextStyle,
                    Color,
                    Highlight.configure({ multicolor: true }),
                    Image.configure({
                        HTMLAttributes: {
                            style: 'max-width: 100%; height: auto;',
                        },
                    }),
                ],
                content: content || '',
                onUpdate: ({ editor: e }) => {
                    content = e.getHTML();
                    textLength = e.storage.characterCount.characters();
                },
                onCreate: ({ editor: e }) => {
                    textLength = e.storage.characterCount.characters();
                },
            });

            if (destroyed) {
                instance.destroy();
                return;
            }
            editor = instance;
        })();

        return () => {
            destroyed = true;
            if (editor) {
                editor.destroy();
                editor = null;
            }
        };
    });

    // Toolbar action helpers
    function toggleBold() { editor?.chain().focus().toggleBold().run(); }
    function toggleItalic() { editor?.chain().focus().toggleItalic().run(); }
    function toggleUnderline() { editor?.chain().focus().toggleUnderline().run(); }
    function toggleStrike() { editor?.chain().focus().toggleStrike().run(); }
    function toggleH2() { editor?.chain().focus().toggleHeading({ level: 2 }).run(); }
    function toggleH3() { editor?.chain().focus().toggleHeading({ level: 3 }).run(); }
    function toggleBulletList() { editor?.chain().focus().toggleBulletList().run(); }
    function toggleOrderedList() { editor?.chain().focus().toggleOrderedList().run(); }
    function toggleBlockquote() { editor?.chain().focus().toggleBlockquote().run(); }
    function toggleCodeBlock() { editor?.chain().focus().toggleCodeBlock().run(); }
    function undo() { editor?.chain().focus().undo().run(); }
    function redo() { editor?.chain().focus().redo().run(); }

    function setTextColor(color: string) {
        if (!editor) return;
        if (color) {
            editor.chain().focus().setColor(color).run();
        } else {
            editor.chain().focus().unsetColor().run();
        }
        showColorPicker = false;
    }

    function setHighlight(color: string) {
        if (!editor) return;
        if (color) {
            editor.chain().focus().toggleHighlight({ color }).run();
        } else {
            editor.chain().focus().unsetHighlight().run();
        }
        showHighlightPicker = false;
    }

    function openLinkInput() {
        if (!editor) return;
        const prev = editor.getAttributes('link').href || '';
        linkUrl = prev;
        showLinkInput = true;
    }

    function applyLink() {
        if (!editor) return;
        if (linkUrl) {
            let url = linkUrl.trim();
            if (!/^https?:\/\//i.test(url) && !url.startsWith('mailto:')) {
                url = 'https://' + url;
            }
            editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
        } else {
            editor.chain().focus().extendMarkRange('link').unsetLink().run();
        }
        showLinkInput = false;
        linkUrl = '';
    }

    function removeLink() {
        if (!editor) return;
        editor.chain().focus().extendMarkRange('link').unsetLink().run();
        showLinkInput = false;
        linkUrl = '';
    }

    let fileInput: HTMLInputElement | undefined = $state();

    function triggerImageUpload() {
        fileInput?.click();
    }

    async function handleImageUpload(e: Event) {
        const input = e.target as HTMLInputElement;
        const file = input.files?.[0];
        if (!file || !editor) return;

        isUploading = true;
        try {
            const formData = new FormData();
            formData.append('image', file);
            const result = await clientApiFetch<{ url: string }>('/posts/upload-image/', {
                method: 'POST',
                body: formData,
            });
            if (result.url) {
                editor.chain().focus().setImage({ src: result.url }).run();
            }
        } catch (err) {
            console.error('Image upload failed:', err);
        } finally {
            isUploading = false;
            input.value = '';
        }
    }

    function isActive(name: string, attrs?: Record<string, any>): boolean {
        return editor?.isActive(name, attrs) ?? false;
    }

    // Reactive active states
    let isBold = $derived(editor ? isActive('bold') : false);
    let isItalicActive = $derived(editor ? isActive('italic') : false);
    let isUnderlineActive = $derived(editor ? isActive('underline') : false);
    let isStrikeActive = $derived(editor ? isActive('strike') : false);
    let isH2 = $derived(editor ? isActive('heading', { level: 2 }) : false);
    let isH3 = $derived(editor ? isActive('heading', { level: 3 }) : false);
    let isBulletListActive = $derived(editor ? isActive('bulletList') : false);
    let isOrderedListActive = $derived(editor ? isActive('orderedList') : false);
    let isBlockquoteActive = $derived(editor ? isActive('blockquote') : false);
    let isCodeBlockActive = $derived(editor ? isActive('codeBlock') : false);
    let isLinkActive = $derived(editor ? isActive('link') : false);

    // Force reactivity on editor transactions
    let transactionCounter = $state(0);
    $effect(() => {
        if (!editor) return;
        const handler = () => { transactionCounter++; };
        editor.on('transaction', handler);
        return () => { editor?.off('transaction', handler); };
    });

    // Re-derive active states when transactionCounter changes
    $effect(() => {
        // Touch transactionCounter to trigger re-derivation
        void transactionCounter;
        isBold = editor?.isActive('bold') ?? false;
        isItalicActive = editor?.isActive('italic') ?? false;
        isUnderlineActive = editor?.isActive('underline') ?? false;
        isStrikeActive = editor?.isActive('strike') ?? false;
        isH2 = editor?.isActive('heading', { level: 2 }) ?? false;
        isH3 = editor?.isActive('heading', { level: 3 }) ?? false;
        isBulletListActive = editor?.isActive('bulletList') ?? false;
        isOrderedListActive = editor?.isActive('orderedList') ?? false;
        isBlockquoteActive = editor?.isActive('blockquote') ?? false;
        isCodeBlockActive = editor?.isActive('codeBlock') ?? false;
        isLinkActive = editor?.isActive('link') ?? false;
    });
</script>

<svelte:document onclick={handleClickOutside} />

<input
    type="file"
    accept="image/jpeg,image/png,image/gif,image/webp"
    class="hidden"
    bind:this={fileInput}
    onchange={handleImageUpload}
/>

<div class="rich-editor" class:rich-editor-error={error}>
    <!-- Toolbar -->
    {#if editor}
        <div class="toolbar">
            <!-- Text formatting -->
            <div class="toolbar-group">
                <button type="button" class="toolbar-btn" class:active={isBold} onclick={toggleBold} title="굵게">
                    <strong>B</strong>
                </button>
                <button type="button" class="toolbar-btn" class:active={isItalicActive} onclick={toggleItalic} title="기울임">
                    <em>I</em>
                </button>
                <button type="button" class="toolbar-btn" class:active={isUnderlineActive} onclick={toggleUnderline} title="밑줄">
                    <u>U</u>
                </button>
                <button type="button" class="toolbar-btn" class:active={isStrikeActive} onclick={toggleStrike} title="취소선">
                    <s>S</s>
                </button>
            </div>

            <div class="toolbar-divider"></div>

            <!-- Headings -->
            <div class="toolbar-group">
                <button type="button" class="toolbar-btn text-xs font-bold" class:active={isH2} onclick={toggleH2} title="제목 2">
                    H2
                </button>
                <button type="button" class="toolbar-btn text-xs font-bold" class:active={isH3} onclick={toggleH3} title="제목 3">
                    H3
                </button>
            </div>

            <div class="toolbar-divider"></div>

            <!-- Lists & Block -->
            <div class="toolbar-group">
                <button type="button" class="toolbar-btn" class:active={isBulletListActive} onclick={toggleBulletList} title="목록">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" /></svg>
                </button>
                <button type="button" class="toolbar-btn" class:active={isOrderedListActive} onclick={toggleOrderedList} title="번호 목록">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><text x="1" y="7" font-size="6" font-weight="bold">1.</text><line x1="8" y1="5" x2="19" y2="5" stroke="currentColor" stroke-width="1.5"/><text x="1" y="13" font-size="6" font-weight="bold">2.</text><line x1="8" y1="11" x2="19" y2="11" stroke="currentColor" stroke-width="1.5"/><text x="1" y="19" font-size="6" font-weight="bold">3.</text><line x1="8" y1="17" x2="19" y2="17" stroke="currentColor" stroke-width="1.5"/></svg>
                </button>
                <button type="button" class="toolbar-btn" class:active={isBlockquoteActive} onclick={toggleBlockquote} title="인용">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 13V5a2 2 0 00-2-2H4a2 2 0 00-2 2v8a2 2 0 002 2h3l3 3 3-3h3a2 2 0 002-2zM5 7a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1zm1 3a1 1 0 100 2h3a1 1 0 100-2H6z" clip-rule="evenodd" /></svg>
                </button>
            </div>

            <div class="toolbar-divider"></div>

            <!-- Link & Code -->
            <div class="toolbar-group">
                <div class="link-input-wrapper relative">
                    <button type="button" class="toolbar-btn" class:active={isLinkActive} onclick={openLinkInput} title="링크">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
                    </button>
                    {#if showLinkInput}
                        <div class="dropdown-panel link-panel">
                            <input
                                type="url"
                                class="input input-bordered input-sm w-full"
                                placeholder="https://example.com"
                                bind:value={linkUrl}
                                onkeydown={(e) => e.key === 'Enter' && applyLink()}
                            />
                            <div class="flex gap-1 mt-1">
                                <button type="button" class="btn btn-primary btn-xs flex-1" onclick={applyLink}>적용</button>
                                {#if isLinkActive}
                                    <button type="button" class="btn btn-error btn-xs" onclick={removeLink}>제거</button>
                                {/if}
                            </div>
                        </div>
                    {/if}
                </div>
                <button type="button" class="toolbar-btn" class:active={isCodeBlockActive} onclick={toggleCodeBlock} title="코드 블록">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
                </button>
            </div>

            <div class="toolbar-divider"></div>

            <!-- Color & Highlight -->
            <div class="toolbar-group">
                <div class="color-picker-wrapper relative">
                    <button type="button" class="toolbar-btn" onclick={() => { showColorPicker = !showColorPicker; showHighlightPicker = false; }} title="텍스트 색상">
                        <span class="flex flex-col items-center leading-none">
                            <span class="text-xs font-bold">A</span>
                            <span class="w-4 h-1 rounded-sm mt-0.5" style="background: linear-gradient(90deg, #dc2626, #2563eb, #16a34a)"></span>
                        </span>
                    </button>
                    {#if showColorPicker}
                        <div class="dropdown-panel color-panel">
                            <div class="grid grid-cols-5 gap-1">
                                {#each textColors as color}
                                    <button
                                        type="button"
                                        class="color-swatch"
                                        class:color-swatch-default={!color.value}
                                        style={color.value ? `background-color: ${color.value}` : ''}
                                        title={color.label}
                                        onclick={() => setTextColor(color.value)}
                                    >
                                        {#if !color.value}
                                            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" /></svg>
                                        {/if}
                                    </button>
                                {/each}
                            </div>
                        </div>
                    {/if}
                </div>

                <div class="highlight-picker-wrapper relative">
                    <button type="button" class="toolbar-btn" onclick={() => { showHighlightPicker = !showHighlightPicker; showColorPicker = false; }} title="하이라이트">
                        <span class="flex flex-col items-center leading-none">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                        </span>
                    </button>
                    {#if showHighlightPicker}
                        <div class="dropdown-panel color-panel">
                            <div class="grid grid-cols-3 gap-1">
                                {#each highlightColors as color}
                                    <button
                                        type="button"
                                        class="color-swatch"
                                        class:color-swatch-default={!color.value}
                                        style={color.value ? `background-color: ${color.value}` : ''}
                                        title={color.label}
                                        onclick={() => setHighlight(color.value)}
                                    >
                                        {#if !color.value}
                                            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" /></svg>
                                        {/if}
                                    </button>
                                {/each}
                            </div>
                        </div>
                    {/if}
                </div>
            </div>

            <div class="toolbar-divider"></div>

            <!-- Image -->
            <div class="toolbar-group">
                <button type="button" class="toolbar-btn" onclick={triggerImageUpload} title="이미지 삽입" disabled={isUploading}>
                    {#if isUploading}
                        <span class="loading loading-spinner loading-xs"></span>
                    {:else}
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                    {/if}
                </button>
            </div>

            <div class="toolbar-divider"></div>

            <!-- Undo/Redo -->
            <div class="toolbar-group">
                <button type="button" class="toolbar-btn" onclick={undo} title="되돌리기">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a4 4 0 010 8H9" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 6L3 10l4 4" /></svg>
                </button>
                <button type="button" class="toolbar-btn" onclick={redo} title="다시 실행">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 10H11a4 4 0 100 8h4" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 6l4 4-4 4" /></svg>
                </button>
            </div>
        </div>
    {/if}

    <!-- Editor area -->
    <div class="editor-content" bind:this={editorElement}></div>

    <!-- Character count -->
    <div class="editor-footer">
        <span class="text-xs text-base-content/50" class:text-error={textLength > maxLength}>
            {textLength.toLocaleString()} / {maxLength.toLocaleString()}
        </span>
    </div>
</div>

<style>
    .rich-editor {
        border: 1px solid oklch(var(--bc) / 0.2);
        border-radius: var(--rounded-btn, 0.5rem);
        overflow: hidden;
        background: oklch(var(--b1));
        transition: border-color 0.2s;
    }
    .rich-editor:focus-within {
        border-color: oklch(var(--p));
        outline: 2px solid oklch(var(--p) / 0.2);
        outline-offset: 0;
    }
    .rich-editor-error {
        border-color: oklch(var(--er));
    }

    .toolbar {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 2px;
        padding: 6px 8px;
        border-bottom: 1px solid oklch(var(--bc) / 0.1);
        background: oklch(var(--b2));
    }

    .toolbar-group {
        display: flex;
        align-items: center;
        gap: 1px;
    }

    .toolbar-divider {
        width: 1px;
        height: 20px;
        background: oklch(var(--bc) / 0.15);
        margin: 0 4px;
    }

    .toolbar-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: 4px;
        border: none;
        background: transparent;
        color: oklch(var(--bc));
        cursor: pointer;
        transition: all 0.15s;
        font-size: 14px;
    }
    .toolbar-btn:hover {
        background: oklch(var(--bc) / 0.1);
    }
    .toolbar-btn.active {
        background: oklch(var(--p) / 0.15);
        color: oklch(var(--p));
    }
    .toolbar-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }

    .dropdown-panel {
        position: absolute;
        top: 100%;
        left: 0;
        z-index: 50;
        background: oklch(var(--b1));
        border: 1px solid oklch(var(--bc) / 0.2);
        border-radius: 8px;
        box-shadow: 0 4px 12px oklch(var(--bc) / 0.1);
        padding: 8px;
        margin-top: 4px;
    }
    .link-panel {
        min-width: 240px;
    }
    .color-panel {
        min-width: 140px;
    }

    .color-swatch {
        width: 24px;
        height: 24px;
        border-radius: 4px;
        border: 1px solid oklch(var(--bc) / 0.2);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.1s;
    }
    .color-swatch:hover {
        transform: scale(1.15);
    }
    .color-swatch-default {
        background: oklch(var(--b1));
    }

    .editor-content {
        min-height: 240px;
        padding: 12px 16px;
    }

    /* Tiptap ProseMirror styles */
    .editor-content :global(.ProseMirror) {
        outline: none;
        min-height: 220px;
    }
    .editor-content :global(.ProseMirror p.is-editor-empty:first-child::before) {
        content: attr(data-placeholder);
        float: left;
        color: oklch(var(--bc) / 0.35);
        pointer-events: none;
        height: 0;
    }
    .editor-content :global(.ProseMirror h2) {
        font-size: 1.5em;
        font-weight: 700;
        margin: 0.75em 0 0.5em;
    }
    .editor-content :global(.ProseMirror h3) {
        font-size: 1.25em;
        font-weight: 600;
        margin: 0.75em 0 0.5em;
    }
    .editor-content :global(.ProseMirror p) {
        margin: 0.5em 0;
    }
    .editor-content :global(.ProseMirror ul),
    .editor-content :global(.ProseMirror ol) {
        padding-left: 1.5em;
        margin: 0.5em 0;
    }
    .editor-content :global(.ProseMirror ul) {
        list-style: disc;
    }
    .editor-content :global(.ProseMirror ol) {
        list-style: decimal;
    }
    .editor-content :global(.ProseMirror blockquote) {
        border-left: 3px solid oklch(var(--bc) / 0.2);
        padding-left: 1em;
        margin: 0.75em 0;
        color: oklch(var(--bc) / 0.7);
    }
    .editor-content :global(.ProseMirror pre) {
        background: oklch(var(--bc) / 0.05);
        border-radius: 6px;
        padding: 0.75em 1em;
        font-family: monospace;
        font-size: 0.9em;
        overflow-x: auto;
        margin: 0.75em 0;
    }
    .editor-content :global(.ProseMirror code) {
        background: oklch(var(--bc) / 0.05);
        border-radius: 3px;
        padding: 0.15em 0.3em;
        font-family: monospace;
        font-size: 0.9em;
    }
    .editor-content :global(.ProseMirror pre code) {
        background: none;
        padding: 0;
    }
    .editor-content :global(.ProseMirror a) {
        color: oklch(var(--p));
        text-decoration: underline;
        cursor: pointer;
    }
    .editor-content :global(.ProseMirror img) {
        max-width: 100%;
        height: auto;
        border-radius: 6px;
        margin: 0.5em 0;
    }
    .editor-content :global(.ProseMirror mark) {
        border-radius: 2px;
        padding: 0.1em 0;
    }

    .editor-footer {
        display: flex;
        justify-content: flex-end;
        padding: 4px 12px 6px;
        border-top: 1px solid oklch(var(--bc) / 0.05);
    }

    @media (max-width: 640px) {
        .toolbar {
            gap: 1px;
            padding: 4px 6px;
        }
        .toolbar-divider {
            margin: 0 2px;
            height: 16px;
        }
    }
</style>
