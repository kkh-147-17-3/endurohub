<script lang="ts">
	import type { CalendarFilters } from '$lib/calendar-filters';
	import { raceSearchHref } from '$lib/calendar-filters';
	import Button from '$lib/components/eh/Button.svelte';

	let { month, filters, regions, onapply }: {
		month: number;
		filters: CalendarFilters;
		regions: string[];
		onapply: (changes: Partial<CalendarFilters>) => void;
	} = $props();

	let nameDraft = $derived(filters.name);
	const active = $derived(!!filters.name || filters.regions.length > 0 || filters.openOnly || filters.sports.length > 0);
</script>

<section class="discovery" aria-label="이 달 대회 검색과 빠른 필터">
	<form class="discovery-search" role="search" aria-label="이 달 대회 검색" onsubmit={(event) => {
		event.preventDefault();
		onapply({ name: nameDraft.trim() });
	}}>
		<label for="calendar-race-search">{month}월 대회 찾기</label>
		<div class="search-field">
			<input id="calendar-race-search" type="search" name="name" placeholder="찾고 싶은 대회명을 입력하세요" bind:value={nameDraft} />
			<Button type="submit" variant="signal">검색</Button>
		</div>
	</form>
	<div class="discovery-options">
		<label class="region-field">
			<span>지역</span>
			<select aria-label="대회 지역" value={filters.regions.length === 1 ? filters.regions[0] : ''} onchange={(event) => onapply({ regions: event.currentTarget.value ? [event.currentTarget.value] : [] })}>
				<option value="">전국</option>
				{#each regions as region}<option value={region}>{region}</option>{/each}
			</select>
		</label>
		<label class="open-filter">
			<input type="checkbox" checked={filters.openOnly} onchange={(event) => onapply({ openOnly: event.currentTarget.checked })} />
			접수 중만 보기
		</label>
		{#if active}<button type="button" class="reset" onclick={() => onapply({ name: '', regions: [], sports: [], openOnly: false })}>조건 초기화</button>{/if}
		<a class="more-search" href={raceSearchHref(filters)}>더 많은 조건으로 찾기 →</a>
	</div>
	{#if filters.regions.length > 1}<p class="region-summary">선택 지역: {filters.regions.join(' · ')}</p>{/if}
</section>

<style>
	.discovery { margin-top: var(--sp-6); padding: var(--sp-5); border: var(--border-hair); background: var(--bg-section); }
	.discovery-search label { display: block; margin-bottom: var(--sp-2); color: var(--text-strong); font-size: var(--text-body-sm); font-weight: var(--w-heading); }
	.search-field { display: flex; gap: var(--sp-2); }
	.search-field input { min-width: 0; flex: 1; padding: 12px 14px; border: 1px solid var(--line); border-radius: var(--r-1); background: var(--surface-card); color: var(--text-strong); font: inherit; font-size: 16px; }
	.search-field input::placeholder { color: var(--text-muted); }
	.discovery-options { display: flex; align-items: center; flex-wrap: wrap; gap: 12px 20px; margin-top: var(--sp-3); font-size: var(--text-caption); }
	.region-field { display: flex; align-items: center; gap: var(--sp-2); color: var(--text-muted); }
	.region-field select { min-height: 40px; min-width: 92px; max-width: 100%; padding: 6px 26px 6px 10px; border: 1px solid var(--line); border-radius: var(--r-1); background: var(--surface-card); color: var(--text-strong); font: inherit; }
	.open-filter { display: flex; align-items: center; gap: var(--sp-2); min-height: 44px; color: var(--text-strong); cursor: pointer; }
	.open-filter input { width: 18px; height: 18px; accent-color: var(--accent-strong); }
	.reset { min-height: 44px; padding: 0; border: 0; background: transparent; color: var(--text-muted); text-decoration: underline; text-underline-offset: 3px; font: inherit; cursor: pointer; }
	.more-search { margin-left: auto; color: var(--text-accent); font-weight: var(--w-strong); text-underline-offset: 3px; }
	.more-search:hover { text-decoration: underline; }
	.region-summary { margin-top: var(--sp-2); color: var(--text-muted); font-size: var(--text-caption); }
	input:focus-visible, select:focus-visible, button:focus-visible, a:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
	@media (max-width: 768px) {
		.discovery { margin-top: var(--sp-4); padding: var(--sp-4); }
		.discovery-options { gap: 4px 14px; }
		.more-search { margin-left: 0; min-height: 36px; display: inline-flex; align-items: center; }
	}
</style>
