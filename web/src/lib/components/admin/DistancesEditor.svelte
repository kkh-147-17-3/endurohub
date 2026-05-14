<script lang="ts">
    interface Distance {
        name: string;
        distance_meter?: number | null;
        fee?: number | null;
        cutoff?: string | null;
        start_time?: string | null;
    }

    let {
        value,
        save,
    }: {
        value: Distance[] | null;
        save: (field: string, val: Distance[]) => Promise<void>;
    } = $props();

    function cloneRows(src: Distance[] | null): Distance[] {
        return (src ?? []).map((d) => ({ ...d }));
    }

    let rows = $state<Distance[]>(cloneRows(value));
    let saving = $state(false);
    let error = $state('');
    let dirty = $state(false);

    function addRow() {
        rows = [...rows, { name: '', fee: null, cutoff: null }];
        dirty = true;
    }

    function removeRow(i: number) {
        rows = rows.filter((_, idx) => idx !== i);
        dirty = true;
    }

    function update(i: number, key: keyof Distance, raw: string) {
        const next = [...rows];
        const trimmed = raw.trim();
        if (key === 'fee' || key === 'distance_meter') {
            next[i] = { ...next[i], [key]: trimmed === '' ? null : Number(trimmed) };
        } else {
            next[i] = { ...next[i], [key]: trimmed === '' ? null : trimmed };
        }
        rows = next;
        dirty = true;
    }

    async function commit() {
        if (saving) return;
        saving = true;
        error = '';
        try {
            // Strip empty rows (no name) before saving.
            const clean = rows
                .filter((r) => r.name && r.name.trim())
                .map((r) => ({
                    name: r.name.trim(),
                    distance_meter: r.distance_meter ?? null,
                    fee: r.fee ?? null,
                    cutoff: r.cutoff ?? null,
                    start_time: r.start_time ?? null,
                }));
            await save('distances', clean);
            rows = cloneRows(clean);
            dirty = false;
        } catch (e) {
            error = e instanceof Error ? e.message : '저장 실패';
        } finally {
            saving = false;
        }
    }

    function reset() {
        rows = cloneRows(value);
        dirty = false;
        error = '';
    }
</script>

<div class="editor">
    <div class="header">
        <span class="label">거리 / 참가비</span>
        <span class="hint">각 종목별 이름·미터·참가비·컷오프</span>
    </div>

    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>이름</th>
                    <th class="num">거리(m)</th>
                    <th class="num">참가비</th>
                    <th>컷오프</th>
                    <th class="time">출발 시간</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                {#each rows as row, i (i)}
                    <tr>
                        <td>
                            <input
                                value={row.name}
                                placeholder="예: 10km"
                                oninput={(e) => update(i, 'name', (e.target as HTMLInputElement).value)}
                            />
                        </td>
                        <td class="num">
                            <input
                                type="number"
                                value={row.distance_meter ?? ''}
                                placeholder="자동"
                                oninput={(e) => update(i, 'distance_meter', (e.target as HTMLInputElement).value)}
                            />
                        </td>
                        <td class="num">
                            <input
                                type="number"
                                value={row.fee ?? ''}
                                placeholder="원"
                                oninput={(e) => update(i, 'fee', (e.target as HTMLInputElement).value)}
                            />
                        </td>
                        <td>
                            <input
                                value={row.cutoff ?? ''}
                                placeholder="예: 1시간 20분"
                                oninput={(e) => update(i, 'cutoff', (e.target as HTMLInputElement).value)}
                            />
                        </td>
                        <td class="time">
                            <input
                                value={row.start_time ?? ''}
                                placeholder="HH:MM"
                                oninput={(e) => update(i, 'start_time', (e.target as HTMLInputElement).value)}
                            />
                        </td>
                        <td class="del-col">
                            <button
                                type="button"
                                class="del"
                                onclick={() => removeRow(i)}
                                aria-label="행 삭제"
                            >×</button>
                        </td>
                    </tr>
                {/each}
                {#if rows.length === 0}
                    <tr><td colspan="6" class="empty">아직 종목이 없습니다.</td></tr>
                {/if}
            </tbody>
        </table>
    </div>

    <div class="actions">
        <button type="button" class="add" onclick={addRow}>+ 행 추가</button>
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
    .hint {
        font-size: 11px;
        color: var(--arena-ink-mute, #aaa);
    }
    .table-wrap {
        overflow-x: auto;
        border: 1px solid var(--arena-line-soft, #eee);
    }
    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }
    th {
        padding: 8px;
        text-align: left;
        background: var(--arena-paper-alt, #f4f4f0);
        border-bottom: 1px solid var(--arena-line, #ddd);
        font-family: var(--arena-f-mono, ui-monospace);
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--arena-ink-soft, #555);
        font-weight: 600;
    }
    td {
        padding: 4px;
        border-bottom: 1px solid var(--arena-line-soft, #f3f3f3);
    }
    .num { text-align: right; width: 100px; }
    .time { width: 80px; }
    .del-col { width: 32px; }
    input {
        width: 100%;
        padding: 4px 6px;
        border: 1px solid transparent;
        background: transparent;
        font-size: 13px;
        font-family: inherit;
    }
    input:hover { border-color: var(--arena-line-soft, #eee); }
    input:focus { outline: none; border-color: var(--arena-ink, #111); background: #fff; }
    .num input { text-align: right; }
    .del {
        width: 22px; height: 22px;
        border-radius: 50%;
        background: transparent;
        border: 0;
        color: var(--arena-ink-mute, #ccc);
        font-size: 16px;
        cursor: pointer;
        line-height: 1;
    }
    tr:hover .del { color: #ef4444; }
    .empty { text-align: center; color: var(--arena-ink-mute, #888); padding: 16px; }
    .actions {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 8px;
    }
    .spacer { flex: 1; }
    .add {
        padding: 6px 10px;
        background: transparent;
        border: 1px dashed var(--arena-line, #ddd);
        cursor: pointer;
        font-size: 11px;
        font-family: var(--arena-f-mono, ui-monospace);
        color: var(--arena-ink-soft, #555);
    }
    .add:hover { border-color: var(--arena-ink, #111); color: var(--arena-ink, #111); }
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
