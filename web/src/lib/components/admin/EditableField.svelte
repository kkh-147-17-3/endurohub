<script lang="ts">
    type FieldType = 'text' | 'textarea' | 'date' | 'time' | 'number' | 'url';

    let {
        label,
        value,
        field,
        type = 'text',
        placeholder = '',
        save,
        locked = false,
        onUnlock,
    }: {
        label: string;
        value: string | number | null;
        field: string;
        type?: FieldType;
        placeholder?: string;
        save: (field: string, value: string | number | null) => Promise<void>;
        locked?: boolean;
        onUnlock?: (field: string) => Promise<void>;
    } = $props();

    let unlocking = $state(false);

    async function handleUnlock() {
        if (!onUnlock || unlocking) return;
        if (!confirm(`"${label}" 필드의 크롤러 보호를 해제할까요?\n해제하면 다음 크롤링에서 외부 데이터로 덮어쓸 수 있습니다.`)) return;
        unlocking = true;
        try {
            await onUnlock(field);
        } finally {
            unlocking = false;
        }
    }

    let editing = $state(false);
    let draft = $state<string>(value == null ? '' : String(value));
    let saving = $state(false);
    let error = $state('');
    let inputEl = $state<HTMLInputElement | HTMLTextAreaElement | null>(null);

    function startEdit() {
        draft = value == null ? '' : String(value);
        editing = true;
        error = '';
        queueMicrotask(() => inputEl?.focus());
    }

    function cancel() {
        editing = false;
        error = '';
    }

    async function commit() {
        if (saving) return;
        const trimmed = type === 'textarea' ? draft : draft.trim();
        const original = value == null ? '' : String(value);
        if (trimmed === original) {
            editing = false;
            return;
        }
        saving = true;
        error = '';
        try {
            const out: string | number | null = trimmed === ''
                ? null
                : type === 'number'
                    ? Number(trimmed)
                    : trimmed;
            await save(field, out);
            editing = false;
        } catch (e) {
            error = e instanceof Error ? e.message : '저장 실패';
        } finally {
            saving = false;
        }
    }

    function onKey(e: KeyboardEvent) {
        if (e.key === 'Escape') {
            e.preventDefault();
            cancel();
        } else if (e.key === 'Enter' && type !== 'textarea' && !e.shiftKey) {
            e.preventDefault();
            commit();
        } else if (e.key === 'Enter' && type === 'textarea' && (e.metaKey || e.ctrlKey)) {
            e.preventDefault();
            commit();
        }
    }

    let displayValue = $derived(value == null || value === '' ? '—' : String(value));
</script>

<div class="field" class:editing class:locked>
    <div class="label">
        <span>{label}</span>
        {#if locked}
            <button
                type="button"
                class="lock-badge"
                title={onUnlock ? '클릭하여 크롤러 보호 해제' : '크롤러 자동 갱신에서 보호 중'}
                disabled={!onUnlock || unlocking}
                onclick={handleUnlock}
            >
                {unlocking ? '…' : '🔒 보호'}
            </button>
        {/if}
    </div>
    {#if editing}
        {#if type === 'textarea'}
            <textarea
                bind:this={inputEl as any}
                bind:value={draft}
                onkeydown={onKey}
                onblur={commit}
                {placeholder}
                rows="4"
                disabled={saving}
            ></textarea>
        {:else}
            <input
                bind:this={inputEl as any}
                {type}
                bind:value={draft}
                onkeydown={onKey}
                onblur={commit}
                {placeholder}
                disabled={saving}
            />
        {/if}
        {#if saving}<div class="hint">저장중…</div>{/if}
        {#if error}<div class="error">{error}</div>{/if}
    {:else}
        <button class="display" type="button" onclick={startEdit}>
            <span class:empty={value == null || value === ''}>{displayValue}</span>
            <span class="edit-hint">편집</span>
        </button>
    {/if}
</div>

<style>
    .field {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 10px 12px;
        background: #fff;
        border: 1px solid var(--arena-line, #ddd);
    }
    .field.editing {
        border-color: var(--arena-accent, #22c55e);
    }
    .field.locked {
        background: #fffaf0;
        border-color: #fbbf24;
    }
    .label {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        font-family: var(--arena-f-mono, ui-monospace);
        font-size: 10px;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: var(--arena-ink-mute, #888);
    }
    .lock-badge {
        all: unset;
        cursor: pointer;
        font-family: var(--arena-f-mono, ui-monospace);
        font-size: 9px;
        letter-spacing: 0.5px;
        padding: 1px 6px;
        border: 1px solid #fbbf24;
        background: #fef3c7;
        color: #92400e;
        border-radius: 2px;
    }
    .lock-badge:hover:not(:disabled) {
        background: #fde68a;
    }
    .lock-badge:disabled {
        cursor: default;
        opacity: 0.6;
    }
    .display {
        all: unset;
        cursor: text;
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 12px;
        font-size: 14px;
        line-height: 1.4;
        color: var(--arena-ink, #111);
        white-space: pre-wrap;
        word-break: break-word;
        min-height: 20px;
    }
    .display .empty { color: var(--arena-ink-mute, #888); font-style: italic; }
    .edit-hint {
        font-family: var(--arena-f-mono, ui-monospace);
        font-size: 9px;
        color: var(--arena-ink-mute, #ccc);
        letter-spacing: 0.5px;
        flex-shrink: 0;
    }
    .display:hover .edit-hint { color: var(--arena-accent-deep, #16a34a); }
    input, textarea {
        width: 100%;
        padding: 4px 6px;
        border: 1px solid var(--arena-line, #ddd);
        background: #fff;
        font-size: 14px;
        font-family: inherit;
        line-height: 1.4;
        resize: vertical;
    }
    input:focus, textarea:focus {
        outline: none;
        border-color: var(--arena-ink, #111);
    }
    .hint { font-size: 10px; color: var(--arena-ink-mute, #888); }
    .error { font-size: 11px; color: #dc2626; }
</style>
