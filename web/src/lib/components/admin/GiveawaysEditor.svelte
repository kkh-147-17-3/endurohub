<script lang="ts">
    let {
        value,
        save,
    }: {
        value: string[] | null;
        save: (field: string, val: string[]) => Promise<void>;
    } = $props();

    function clone(src: string[] | null): string[] {
        return (src ?? []).map((s) => String(s));
    }

    let tags = $state<string[]>(clone(value));
    let draft = $state('');
    let saving = $state(false);
    let error = $state('');
    let inputEl = $state<HTMLInputElement | null>(null);

    let dirty = $derived(JSON.stringify(tags) !== JSON.stringify(value ?? []));

    function parseList(text: string): string[] {
        const trimmed = text.trim();
        if (!trimmed) return [];
        let parts: string[];
        if (/[,，]/.test(trimmed)) {
            parts = trimmed.split(/[,，]/);
        } else if (/\n/.test(trimmed)) {
            parts = trimmed.split(/\n+/);
        } else if (/\t/.test(trimmed)) {
            parts = trimmed.split(/\t+/);
        } else {
            // Avoid splitting two-word names like "기념 티셔츠";
            // only split on whitespace when there are 3+ tokens.
            const tokens = trimmed.split(/\s+/);
            parts = tokens.length >= 3 ? tokens : [trimmed];
        }
        return parts.map((s) => s.trim()).filter(Boolean);
    }

    function addMany(newOnes: string[]) {
        if (newOnes.length === 0) return;
        const seen = new Set(tags);
        const merged = [...tags];
        for (const t of newOnes) {
            if (!seen.has(t)) {
                merged.push(t);
                seen.add(t);
            }
        }
        tags = merged;
    }

    function commitDraft() {
        const items = parseList(draft);
        if (items.length > 0) {
            addMany(items);
        }
        draft = '';
    }

    function removeAt(i: number) {
        tags = tags.filter((_, idx) => idx !== i);
    }

    function onKey(e: KeyboardEvent) {
        if (e.key === 'Enter' || e.key === ',' || e.key === 'Tab') {
            // Tab: only intercept if there's a draft to commit.
            if (e.key === 'Tab' && !draft.trim()) return;
            e.preventDefault();
            commitDraft();
        } else if (e.key === 'Backspace' && draft === '' && tags.length > 0) {
            e.preventDefault();
            tags = tags.slice(0, -1);
        }
    }

    function onPaste(e: ClipboardEvent) {
        const text = e.clipboardData?.getData('text');
        if (!text) return;
        const items = parseList(text);
        // Only intercept if it looks like a list — otherwise let normal paste happen.
        if (items.length > 1) {
            e.preventDefault();
            addMany(items);
            draft = '';
        }
    }

    async function commit() {
        if (saving) return;
        // Flush any in-progress draft first.
        if (draft.trim()) commitDraft();
        saving = true;
        error = '';
        try {
            await save('giveaways', tags.slice());
        } catch (e) {
            error = e instanceof Error ? e.message : '저장 실패';
        } finally {
            saving = false;
        }
    }

    function reset() {
        tags = clone(value);
        draft = '';
        error = '';
    }
</script>

<div class="editor">
    <div class="header">
        <span class="label">기념품</span>
        <span class="hint">쉼표·줄바꿈·탭으로 여러 개 한 번에 붙여넣기 가능</span>
    </div>

    <button
        type="button"
        class="chips"
        onclick={() => inputEl?.focus()}
        aria-label="기념품 입력 영역"
    >
        {#each tags as tag, i (i)}
            <span class="chip">
                <span class="chip-text">{tag}</span>
                <button
                    type="button"
                    class="chip-x"
                    onclick={(e) => { e.stopPropagation(); removeAt(i); }}
                    aria-label={`${tag} 삭제`}
                >×</button>
            </span>
        {/each}
        <input
            bind:this={inputEl}
            bind:value={draft}
            placeholder={tags.length === 0 ? '예: 기념 티셔츠, 메달, 완주증' : '추가…'}
            onkeydown={onKey}
            onpaste={onPaste}
            onblur={() => draft.trim() && commitDraft()}
        />
    </button>

    <div class="actions">
        <span class="count">{tags.length}개</span>
        <div class="spacer"></div>
        {#if dirty}
            <span class="dirty-tag">미저장 변경</span>
            <button type="button" class="reset" onclick={reset} disabled={saving}>되돌리기</button>
            <button type="button" class="commit" onclick={commit} disabled={saving}>
                {saving ? '저장중…' : '저장'}
            </button>
        {/if}
    </div>

    {#if error}<div class="error">{error}</div>{/if}
</div>

<style>
    .editor {
        background: #fff;
        border: 1px solid var(--arena-line, #ddd);
        padding: 12px;
    }
    .header {
        display: flex;
        align-items: baseline;
        gap: 8px;
        margin-bottom: 8px;
    }
    .label {
        font-family: var(--arena-f-mono, ui-monospace);
        font-size: 10px;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: var(--arena-ink-mute, #888);
    }
    .hint { font-size: 11px; color: var(--arena-ink-mute, #aaa); }
    .chips {
        all: unset;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;
        padding: 6px 8px;
        min-height: 36px;
        border: 1px solid var(--arena-line, #ddd);
        background: #fff;
        cursor: text;
        width: 100%;
        box-sizing: border-box;
    }
    .chips:focus-within { border-color: var(--arena-ink, #111); }
    .chip {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 4px 3px 10px;
        background: var(--arena-paper-alt, #f4f4f0);
        border: 1px solid var(--arena-line-soft, #e5e5e5);
        border-radius: 14px;
        font-size: 12px;
        line-height: 1.2;
        max-width: 100%;
    }
    .chip-text {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 200px;
    }
    .chip-x {
        all: unset;
        cursor: pointer;
        width: 18px;
        height: 18px;
        line-height: 16px;
        text-align: center;
        border-radius: 50%;
        color: var(--arena-ink-mute, #888);
        font-size: 14px;
    }
    .chip-x:hover { background: #ef4444; color: #fff; }
    input {
        flex: 1;
        min-width: 120px;
        border: 0;
        outline: none;
        padding: 4px 0;
        font-size: 13px;
        font-family: inherit;
        background: transparent;
    }
    .actions {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 8px;
    }
    .count {
        font-family: var(--arena-f-mono, ui-monospace);
        font-size: 11px;
        color: var(--arena-ink-mute, #888);
    }
    .spacer { flex: 1; }
    .dirty-tag {
        font-size: 11px;
        font-family: var(--arena-f-mono, ui-monospace);
        color: #d97706;
    }
    .reset, .commit {
        padding: 6px 12px;
        cursor: pointer;
        font-size: 11px;
        font-family: var(--arena-f-mono, ui-monospace);
        letter-spacing: 0.5px;
        border: 1px solid var(--arena-line, #ddd);
    }
    .reset { background: #fff; }
    .commit {
        background: var(--arena-ink, #111);
        color: #fff;
        border-color: var(--arena-ink, #111);
    }
    .reset:disabled, .commit:disabled { opacity: 0.5; cursor: not-allowed; }
    .error {
        margin-top: 8px;
        padding: 6px 8px;
        background: #fef2f2;
        border: 1px solid #fecaca;
        color: #b91c1c;
        font-size: 12px;
    }
</style>
