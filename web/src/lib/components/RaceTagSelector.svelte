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
            ? races.filter(r => !selectedIds.includes(r.id)).slice(0, 20)
            : races
                .filter(r => !selectedIds.includes(r.id) && r.title.toLowerCase().includes(searchQuery.toLowerCase()))
                .slice(0, 20)
    );

    let selectedRaces = $derived(
        selectedIds.map(id => races.find(r => r.id === id)).filter(Boolean) as RaceOption[]
    );

    function addRace(race: RaceOption) {
        if (selectedIds.length < maxTags && !selectedIds.includes(race.id)) {
            selectedIds = [...selectedIds, race.id];
        }
        searchQuery = '';
        isOpen = false;
    }

    function removeRace(raceId: number) {
        selectedIds = selectedIds.filter(id => id !== raceId);
    }

    function handleInputFocus() {
        if (selectedIds.length < maxTags) {
            isOpen = true;
        }
    }

    function handleInputBlur() {
        setTimeout(() => {
            isOpen = false;
        }, 200);
    }
</script>

<div class="space-y-2">
    <div class="label">
        <span class="label-text font-medium">관련 대회 태그</span>
        <span class="label-text-alt">최대 {maxTags}개</span>
    </div>

    {#if selectedRaces.length > 0}
        <div class="flex flex-wrap gap-2 mb-2">
            {#each selectedRaces as race}
                <span class="badge badge-primary gap-1">
                    {race.title.length > 20 ? race.title.slice(0, 20) + '...' : race.title}
                    <button
                        type="button"
                        class="btn btn-xs btn-ghost btn-circle cursor-pointer"
                        aria-label="{race.title} 태그 삭제"
                        onclick={() => removeRace(race.id)}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </span>
            {/each}
        </div>
    {/if}

    {#if selectedIds.length < maxTags}
        <div class="relative">
            <input
                type="text"
                class="input input-bordered w-full"
                placeholder="대회 이름으로 검색..."
                aria-label="대회 검색"
                bind:value={searchQuery}
                onfocus={handleInputFocus}
                onblur={handleInputBlur}
            />

            {#if isOpen && filteredRaces.length > 0}
                <ul class="absolute z-50 w-full mt-1 bg-base-100 border border-base-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {#each filteredRaces as race}
                        <li>
                            <button
                                type="button"
                                class="w-full text-left px-4 py-2 hover:bg-base-200 transition-colors cursor-pointer"
                                onmousedown={() => addRace(race)}
                            >
                                <div class="font-medium text-sm">{race.title}</div>
                                <div class="text-xs text-base-content/60">
                                    {race.sportLabel} | {race.raceDate}
                                </div>
                            </button>
                        </li>
                    {/each}
                </ul>
            {/if}
        </div>
    {:else}
        <p class="text-sm text-base-content/60">최대 태그 수에 도달했습니다.</p>
    {/if}
</div>
