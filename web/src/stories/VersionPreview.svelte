<script lang="ts">
	import BeforeBadge from '$before/lib/components/eh/Badge.svelte';
	import BeforeSportTag from '$before/lib/components/eh/SportTag.svelte';
	import BeforeFilterChip from '$before/lib/components/eh/FilterChip.svelte';
	import BeforeEventCard from '$before/lib/components/eh/EventCard.svelte';
	import BeforeRaceResultList from '$before/lib/components/eh/RaceResultList.svelte';
	import BeforeHomeCommunity from '$before/lib/components/home/HomeCommunityHighlights.svelte';
	import BeforeCalendarBoard from '$before/lib/components/calendar/CalendarBoard.svelte';
	import BeforeDensityCalendar from './before-density/CalendarBoard.svelte';
	import BeforeDateGroupList from './before-date-groups/CalendarRaceList.svelte';
	import oldComponents from '$before/lib/styles/eh-components.css.txt?raw';
	import oldTokens from '$before/lib/styles/eh-tokens.css.txt?raw';
	import currentComponents from '$lib/styles/eh-components.css?raw';
	import currentTokens from '$lib/styles/eh-tokens.css?raw';
	import AfterBadge from '$lib/components/eh/Badge.svelte';
	import AfterSportTag from '$lib/components/eh/SportTag.svelte';
	import AfterFilterChip from '$lib/components/eh/FilterChip.svelte';
	import AfterEventCard from '$lib/components/eh/EventCard.svelte';
	import AfterRaceResultList from '$lib/components/eh/RaceResultList.svelte';
	import AfterHomeCommunity from '$lib/components/home/HomeCommunityHighlights.svelte';
	import AfterCalendarBoard from '$lib/components/calendar/CalendarBoard.svelte';
	import AfterCalendarRaceList from '$lib/components/calendar/CalendarRaceList.svelte';
	import { raceToEventCard } from '$lib/components/eh/race';
	import { SPORT_META, type DsBadgeStatus, type DsSport } from '$lib/components/eh/meta';
	import { calendarProps, denseCalendarProps, denseCalendarRaces, races, records, reviews, runningRaces } from './fixtures';
	import type { ComparisonVersion, Scenario } from './scenarios';

	let { version = 'after', scenario = 'primitives' }: { version?: ComparisonVersion; scenario?: Scenario } = $props();
	let chosenSport = $state<DsSport>('run');
	const Badge = $derived(version === 'before' ? BeforeBadge : AfterBadge);
	const SportTag = $derived(version === 'before' ? BeforeSportTag : AfterSportTag);
	const EventCard = $derived(version === 'before' ? BeforeEventCard : AfterEventCard);
	const HomeCommunity = $derived(version === 'before' ? BeforeHomeCommunity : AfterHomeCommunity);
	const CalendarBoard = $derived(version === 'before' ? (scenario === 'calendar-height' ? BeforeDensityCalendar : BeforeCalendarBoard) : AfterCalendarBoard);
	const CalendarRaceList = $derived(version === 'before' ? BeforeDateGroupList : AfterCalendarRaceList);
	const sportKeys: DsSport[] = ['run', 'trail', 'ride', 'swim', 'tri'];
	const statuses: DsBadgeStatus[] = ['open', 'closing', 'upcoming', 'closed', 'cancelled', 'live'];

	function keepLinksInPreview(event: MouseEvent) {
		const target = event.target;
		if (target instanceof Element && target.closest('a[href^="/"]')) event.preventDefault();
	}
</script>

<svelte:window onclick={keepLinksInPreview} />

{#if version === 'before' && scenario !== 'calendar-height' && scenario !== 'date-groups'}
	<!-- Only mounted in the historical story's independent iframe. -->
	{@html `<style data-comparison-baseline>${oldTokens}\n${oldComponents}</style>`}
{:else}
	{@html `<style data-comparison-current>${currentTokens}\n${currentComponents}</style>`}
{/if}

{#if scenario === 'primitives'}
	<main class="component-samples">
		<section aria-labelledby="sample-sports">
			<h2 id="sample-sports">종목</h2>
			<div class="sample-row">
				{#each sportKeys as sport}<SportTag {sport}>{SPORT_META[sport].ko}</SportTag>{/each}
			</div>
		</section>
		<section aria-labelledby="sample-statuses">
			<h2 id="sample-statuses">접수 상태</h2>
			<div class="sample-row">
				{#each statuses as status}<Badge {status} />{/each}
			</div>
		</section>
		<section aria-labelledby="sample-filters">
			<h2 id="sample-filters">종목 선택</h2>
			<div class="sample-row">
				{#each sportKeys as sport, index}
					{#if version === 'before'}
						<BeforeFilterChip selected={chosenSport === sport} dotColor={SPORT_META[sport].color} count={[5, 2, 1, 1, 1][index]} onclick={() => chosenSport = sport}>{SPORT_META[sport].ko}</BeforeFilterChip>
					{:else}
						<AfterFilterChip selected={chosenSport === sport} count={[5, 2, 1, 1, 1][index]} onclick={() => chosenSport = sport}>{SPORT_META[sport].ko}</AfterFilterChip>
					{/if}
				{/each}
			</div>
		</section>
	</main>
{:else if scenario === 'cards'}
	<main class="component-samples">
		<h1>다가오는 대회</h1>
		<div class="event-grid">
			{#each races.slice(0, 4) as race}
				<EventCard {...raceToEventCard(race)} />
			{/each}
		</div>
	</main>
{:else if scenario === 'single-sport'}
	<main class="component-samples">
		<h1>러닝 대회</h1>
		{#if version === 'before'}<BeforeRaceResultList races={runningRaces} />
		{:else}<AfterRaceResultList races={runningRaces} showSport={false} />{/if}
	</main>
{:else if scenario === 'home'}
	<HomeCommunity {reviews} {records} />
{:else if scenario === 'date-groups'}
	<main class="month-list-preview">
		<details class="month-list" open>
			<summary>5월 전체 대회 목록 <span class="eh-data">{denseCalendarRaces.length}개</span></summary>
			<CalendarRaceList rows={denseCalendarRaces} />
		</details>
	</main>
{:else}
	<CalendarBoard {...(scenario === 'calendar-height' ? denseCalendarProps : calendarProps)} initialView={scenario === 'map' ? 'map' : scenario === 'calendar-open' ? 'list' : 'cal'} />
{/if}

<style>
	.component-samples { padding: 28px; max-width: 1320px; margin: 0 auto; }
	.component-samples section + section { margin-top: 40px; }
	.component-samples h1 { margin: 0 0 24px; font-size: 28px; font-weight: 800; letter-spacing: -0.03em; color: var(--text-strong); }
	.component-samples h2 { margin: 0 0 14px; font-size: 18px; font-weight: 700; color: var(--text-strong); }
	.sample-row { display: flex; flex-wrap: wrap; align-items: center; gap: 12px 20px; }
	.event-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; }
	.month-list-preview { padding: 20px 16px; max-width: 1320px; margin: 0 auto; }
	.month-list { border: 1px solid var(--line); background: var(--paper-0); }
	.month-list summary { padding: 14px 16px; font-size: 13px; font-weight: 600; cursor: pointer; }
	.month-list summary span { margin-left: 8px; color: var(--text-muted); }
	@media (max-width: 600px) { .component-samples { padding: 20px; } .event-grid { grid-template-columns: 1fr; } }
</style>
