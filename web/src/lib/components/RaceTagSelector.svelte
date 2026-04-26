<script lang="ts">
    interface RaceOption {
        id: number;
        title: string;
        sport: string;
        sportLabel: string;
        raceDate: string;
    }

    let { races, selectedIds = $bindable([]), maxTags = 5 }: {
        races: RaceOption[];
        selectedIds: number[];
        maxTags?: number;
    } = $props();

    let searchQuery = $state('');
    let isOpen = $state(false);

    let filteredRaces = $derived(
        searchQuery.trim() === ''
            ? races.filter((r) => !selectedIds.includes(r.id)).slice(0, 20)
            : races
                  .filter(
                      (r) =>
                          !selectedIds.includes(r.id) &&
                          r.title.toLowerCase().includes(searchQuery.toLowerCase())
                  )
                  .slice(0, 20)
    );

    let selectedRaces = $derived(
        selectedIds.map((id) => races.find((r) => r.id === id)).filter(Boolean) as RaceOption[]
    );

    function addRace(race: RaceOption) {
        if (selectedIds.length < maxTags && !selectedIds.includes(race.id)) {
            selectedIds = [...selectedIds, race.id];
        }
        searchQuery = '';
        isOpen = false;
    }

    function removeRace(raceId: number) {
        selectedIds = selectedIds.filter((id) => id !== raceId);
    }

    function handleInputFocus() {
        if (selectedIds.length < maxTags) isOpen = true;
    }

    function handleInputBlur() {
        setTimeout(() => {
            isOpen = false;
        }, 200);
    }
</script>

<div class="tag-selector">
    <div class="label-row">
        <span class="label">관련 대회 태그</span>
        <span class="hint">최대 {maxTags}개</span>
    </div>

    {#if selectedRaces.length > 0}
        <div class="selected-row">
            {#each selectedRaces as race}
                <span class="active-chip">
                    <span>{race.title.length > 20 ? race.title.slice(0, 20) + '…' : race.title}</span>
                    <button
                        type="button"
                        class="x"
                        aria-label="{race.title} 태그 삭제"
                        onclick={() => removeRace(race.id)}
                    >
                        ×
                    </button>
                </span>
            {/each}
        </div>
    {/if}

    {#if selectedIds.length < maxTags}
        <div class="search-wrap">
            <input
                type="text"
                class="search-input"
                placeholder="대회 이름으로 검색..."
                aria-label="대회 검색"
                bind:value={searchQuery}
                onfocus={handleInputFocus}
                onblur={handleInputBlur}
            />
            {#if isOpen && filteredRaces.length > 0}
                <ul class="dropdown">
                    {#each filteredRaces as race}
                        <li>
                            <button
                                type="button"
                                class="option"
                                onmousedown={() => addRace(race)}
                            >
                                <div class="option-title">{race.title}</div>
                                <div class="option-meta">
                                    <span>{race.sportLabel}</span>
                                    <span class="sep">·</span>
                                    <span>{race.raceDate}</span>
                                </div>
                            </button>
                        </li>
                    {/each}
                </ul>
            {/if}
        </div>
    {:else}
        <p class="full">최대 태그 수에 도달했습니다.</p>
    {/if}
</div>

<style>
    .tag-selector {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .label-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
    }
    .label {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: var(--arena-ink-soft);
    }
    .hint {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        color: var(--arena-ink-mute);
        letter-spacing: 1px;
    }
    .selected-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }
    .active-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: var(--arena-ink);
        color: var(--arena-paper);
        padding: 4px 6px 4px 10px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        line-height: 1.4;
        border: 1px solid var(--arena-ink);
    }
    .x {
        background: transparent;
        border: none;
        color: inherit;
        cursor: pointer;
        font-size: 14px;
        line-height: 1;
        padding: 0;
        opacity: 0.7;
        transform: translateY(-1px);
    }
    .x:hover {
        opacity: 1;
    }
    .search-wrap {
        position: relative;
    }
    .search-input {
        width: 100%;
        border: 1px solid var(--arena-line);
        border-radius: 0;
        background: var(--arena-paper);
        padding: 10px 14px;
        font-family: var(--arena-f-body);
        font-size: 14px;
        color: var(--arena-ink);
        appearance: none;
        -webkit-appearance: none;
    }
    .search-input:focus {
        outline: none;
        border-color: var(--arena-ink);
        background: var(--arena-paper-alt);
    }
    .search-input::placeholder {
        color: var(--arena-ink-mute);
    }
    .dropdown {
        position: absolute;
        z-index: 50;
        top: calc(100% + 2px);
        left: 0;
        right: 0;
        margin: 0;
        padding: 0;
        list-style: none;
        background: var(--arena-paper);
        border: 1px solid var(--arena-ink);
        max-height: 240px;
        overflow-y: auto;
        box-shadow: 4px 4px 0 var(--arena-ink);
    }
    .option {
        display: block;
        width: 100%;
        text-align: left;
        background: transparent;
        border: none;
        border-bottom: 1px solid var(--arena-line-soft);
        padding: 10px 14px;
        cursor: pointer;
    }
    .option:last-child {
        border-bottom: none;
    }
    .option:hover {
        background: var(--arena-paper-alt);
    }
    .option-title {
        font-family: var(--arena-f-body);
        font-size: 13px;
        font-weight: 600;
        color: var(--arena-ink);
        margin-bottom: 2px;
    }
    .option-meta {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        color: var(--arena-ink-soft);
        letter-spacing: 0.5px;
    }
    .sep {
        margin: 0 6px;
        opacity: 0.5;
    }
    .full {
        font-size: 12px;
        color: var(--arena-ink-soft);
        margin: 0;
    }
</style>
