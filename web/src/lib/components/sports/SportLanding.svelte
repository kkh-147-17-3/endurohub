<script lang="ts">
	import RaceResultList from '$lib/components/eh/RaceResultList.svelte';
	import { withYear, type SportLandingContent } from '$lib/seo/sport-landing';
	import type { Race } from '$lib/types';

	let {
		content,
		races,
		total,
		openTotal,
		appUrl,
		year,
	}: {
		content: SportLandingContent;
		races: Race[];
		total: number;
		openTotal: number | null;
		appUrl: string;
		year: number;
	} = $props();

	let pageUrl = $derived(`${appUrl}${content.path}`);
	let title = $derived(withYear(content.metaTitle, year));
	let description = $derived(withYear(content.metaDescription, year));
	let ogImage = $derived(`${appUrl}${content.ogImage}`);

	// ── JSON-LD ───────────────────────────────────────────────────────────────
	// 목록 페이지이므로 CollectionPage + ItemList 로 표현한다. 개별 대회의
	// SportsEvent 마크업은 각 상세 페이지가 이미 들고 있으므로 여기서는 링크만 건다.
	let collectionSchema = $derived({
		'@context': 'https://schema.org',
		'@type': 'CollectionPage',
		name: title,
		description,
		url: pageUrl,
		inLanguage: 'ko-KR',
		mainEntity: {
			'@type': 'ItemList',
			numberOfItems: races.length,
			itemListElement: races.map((race, i) => ({
				'@type': 'ListItem',
				position: i + 1,
				name: race.title,
				url: `${appUrl}/races/${encodeURIComponent(race.slug)}`,
			})),
		},
	});

	let breadcrumbSchema = $derived({
		'@context': 'https://schema.org',
		'@type': 'BreadcrumbList',
		itemListElement: [
			{ '@type': 'ListItem', position: 1, name: '홈', item: appUrl },
			{ '@type': 'ListItem', position: 2, name: '대회', item: `${appUrl}/races` },
			{ '@type': 'ListItem', position: 3, name: content.label, item: pageUrl },
		],
	});

	let faqSchema = $derived({
		'@context': 'https://schema.org',
		'@type': 'FAQPage',
		mainEntity: content.faqs.map((f) => ({
			'@type': 'Question',
			name: f.q,
			acceptedAnswer: { '@type': 'Answer', text: f.a },
		})),
	});
</script>

<svelte:head>
	<title>{title} - 엔듀로허브</title>
	<meta name="description" content={description} />
	<meta property="og:type" content="website" />
	<meta property="og:title" content="{title} - 엔듀로허브" />
	<meta property="og:description" content={description} />
	<meta property="og:image" content={ogImage} />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta name="twitter:image" content={ogImage} />
	{@html `<script type="application/ld+json">${JSON.stringify(collectionSchema)}</script>`}
	{@html `<script type="application/ld+json">${JSON.stringify(breadcrumbSchema)}</script>`}
	{@html `<script type="application/ld+json">${JSON.stringify(faqSchema)}</script>`}
</svelte:head>

<main class="sl v-container">
	<!-- ── 헤더 ────────────────────────────────────────────────────────────── -->
	<header class="sl-head">
		<nav class="sl-crumb eh-micro" aria-label="breadcrumb">
			<a href="/">홈</a><span class="sl-crumb__sep">/</span>
			<a href="/races">대회</a><span class="sl-crumb__sep">/</span>
			<span class="sl-crumb__cur">{content.label}</span>
		</nav>

		<h1 class="sl-h1">{content.h1}</h1>
		<p class="sl-lede">{content.lede}</p>

		<dl class="sl-stats">
			<div class="sl-stat">
				<dt class="eh-micro">예정 대회</dt>
				<dd class="eh-data">{total.toLocaleString()}<small>개</small></dd>
			</div>
			{#if openTotal !== null}
				<div class="sl-stat">
					<dt class="eh-micro">접수 중</dt>
					<dd class="eh-data">{openTotal.toLocaleString()}<small>개</small></dd>
				</div>
			{/if}
			<div class="sl-stat sl-stat--wide">
				<dt class="eh-micro">시즌</dt>
				<dd class="sl-stat__text">{content.season}</dd>
			</div>
		</dl>
	</header>

	<!-- ── 다가오는 대회 ───────────────────────────────────────────────────── -->
	<section class="sl-sec" aria-labelledby="upcoming">
		<div class="v-sechead">
			<h2 id="upcoming" class="sl-h2">
				<span class="eh-micro eh-data sl-n">01</span> 다가오는 {content.label} 대회
			</h2>
			<a class="sl-more eh-micro" href="/races?sport={content.sport}">전체 {total.toLocaleString()}개 보기 →</a>
		</div>

		{#if races.length === 0}
			<p class="sl-empty">현재 등록된 예정 대회가 없습니다. 새 일정이 확인되는 대로 갱신됩니다.</p>
		{:else}
			<RaceResultList {races} />
		{/if}
	</section>

	<!-- ── 거리 가이드 ─────────────────────────────────────────────────────── -->
	<section class="sl-sec" aria-labelledby="distances">
		<div class="v-sechead">
			<h2 id="distances" class="sl-h2">
				<span class="eh-micro eh-data sl-n">02</span> {content.label} 거리 · 종목 가이드
			</h2>
		</div>
		<ul class="sl-dists">
			{#each content.distances as d (d.label)}
				<li class="sl-dist">
					<span class="sl-dist__label">{d.label}</span>
					<span class="sl-dist__spec eh-data">{d.spec}</span>
					<span class="sl-dist__note">{d.note}</span>
				</li>
			{/each}
		</ul>
	</section>

	<!-- ── 요강 체크리스트 ─────────────────────────────────────────────────── -->
	<section class="sl-sec" aria-labelledby="checklist">
		<div class="v-sechead">
			<h2 id="checklist" class="sl-h2">
				<span class="eh-micro eh-data sl-n">03</span> 신청 전 확인할 것
			</h2>
		</div>
		<ul class="sl-check">
			{#each content.checklist as item, i (item)}
				<li class="sl-check__item">
					<span class="eh-micro eh-data sl-check__n">{String(i + 1).padStart(2, '0')}</span>
					<span>{item}</span>
				</li>
			{/each}
		</ul>
	</section>

	<!-- ── FAQ ─────────────────────────────────────────────────────────────── -->
	<section class="sl-sec" aria-labelledby="faq">
		<div class="v-sechead">
			<h2 id="faq" class="sl-h2">
				<span class="eh-micro eh-data sl-n">04</span> 자주 묻는 질문
			</h2>
		</div>
		<div class="sl-faqs">
			{#each content.faqs as f (f.q)}
				<details class="sl-faq">
					<summary class="sl-faq__q">{f.q}</summary>
					<p class="sl-faq__a">{f.a}</p>
				</details>
			{/each}
		</div>
	</section>

	<!-- ── 관련 ────────────────────────────────────────────────────────────── -->
	<section class="sl-sec" aria-labelledby="related">
		<div class="v-sechead">
			<h2 id="related" class="sl-h2">
				<span class="eh-micro eh-data sl-n">05</span> 함께 보면 좋은 것
			</h2>
		</div>
		<div class="sl-related">
			{#each content.related as r (r.href)}
				<a class="sl-rel" href={r.href}>
					<span class="sl-rel__label">{r.label}</span>
					<span class="sl-rel__desc">{r.desc}</span>
				</a>
			{/each}
		</div>
	</section>
</main>

<style>
	.sl {
		padding-top: var(--sp-8);
		padding-bottom: var(--sp-20);
	}

	/* ── header ── */
	.sl-crumb {
		display: flex;
		align-items: center;
		gap: var(--sp-2);
		color: var(--text-muted);
	}
	.sl-crumb a {
		color: var(--text-muted);
		text-decoration: none;
	}
	.sl-crumb a:hover {
		color: var(--text-accent);
	}
	.sl-crumb__sep {
		color: var(--text-faint);
	}
	.sl-crumb__cur {
		color: var(--text-strong);
	}

	.sl-h1 {
		margin: var(--sp-4) 0 0;
		font-size: var(--text-h1);
		font-weight: var(--w-display);
		line-height: var(--leading-display);
		letter-spacing: var(--track-display);
		color: var(--text-strong);
	}
	.sl-lede {
		margin: var(--sp-4) 0 0;
		max-width: 68ch;
		font-size: var(--text-body);
		line-height: var(--leading-body);
		color: var(--text-muted);
	}

	.sl-stats {
		margin: var(--sp-6) 0 0;
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: var(--sp-4);
		border-top: var(--border-rule);
		padding-top: var(--sp-4);
	}
	@media (min-width: 720px) {
		.sl-stats {
			grid-template-columns: auto auto 1fr;
			gap: var(--sp-8);
		}
	}
	.sl-stat dt {
		color: var(--text-muted);
	}
	.sl-stat dd {
		margin: var(--sp-1) 0 0;
		font-size: var(--text-h3);
		font-weight: var(--w-heading);
		color: var(--text-strong);
	}
	.sl-stat dd small {
		font-size: var(--text-body-sm);
		font-weight: var(--w-body);
		color: var(--text-muted);
		margin-left: 2px;
	}
	.sl-stat--wide {
		grid-column: 1 / -1;
	}
	@media (min-width: 720px) {
		.sl-stat--wide {
			grid-column: auto;
		}
	}
	.sl-stat__text {
		font-size: var(--text-body-sm);
		font-weight: var(--w-body);
		line-height: var(--leading-body);
		color: var(--text-muted);
		max-width: 46ch;
	}

	/* ── sections ── */
	.sl-sec {
		margin-top: var(--sp-12);
	}
	.sl-h2 {
		margin: 0;
		font-size: var(--text-h3);
		font-weight: var(--w-heading);
		letter-spacing: var(--track-heading);
		color: var(--text-strong);
		display: flex;
		align-items: baseline;
		gap: var(--sp-3);
	}
	.sl-n {
		color: var(--text-accent);
	}
	.sl-more {
		color: var(--text-muted);
		text-decoration: none;
		white-space: nowrap;
	}
	.sl-more:hover {
		color: var(--text-accent);
	}
	.sl-sec > :global(*:nth-child(2)) {
		margin-top: var(--sp-5);
	}
	.sl-empty {
		font-size: var(--text-body-sm);
		color: var(--text-muted);
	}

	/* ── distances ── */
	.sl-dists {
		list-style: none;
		margin: 0;
		padding: 0;
		border: var(--border-hair);
		background: var(--surface-card);
	}
	.sl-dist {
		display: grid;
		grid-template-columns: 1fr auto;
		gap: var(--sp-1) var(--sp-4);
		padding: var(--sp-4) var(--sp-5);
		border-bottom: var(--border-hair);
	}
	.sl-dist:last-child {
		border-bottom: 0;
	}
	@media (min-width: 720px) {
		.sl-dist {
			grid-template-columns: 140px minmax(0, 260px) 1fr;
			align-items: baseline;
		}
	}
	.sl-dist__label {
		font-weight: var(--w-strong);
		color: var(--text-strong);
		font-size: var(--text-body-sm);
	}
	.sl-dist__spec {
		font-size: var(--text-body-sm);
		color: var(--text-accent);
		text-align: right;
	}
	@media (min-width: 720px) {
		.sl-dist__spec {
			text-align: left;
		}
	}
	.sl-dist__note {
		grid-column: 1 / -1;
		font-size: var(--text-body-sm);
		color: var(--text-muted);
		line-height: var(--leading-body);
	}
	@media (min-width: 720px) {
		.sl-dist__note {
			grid-column: auto;
		}
	}

	/* ── checklist ── */
	.sl-check {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: var(--sp-3);
	}
	@media (min-width: 720px) {
		.sl-check {
			grid-template-columns: 1fr 1fr;
			gap: var(--sp-3) var(--sp-8);
		}
	}
	.sl-check__item {
		display: flex;
		align-items: baseline;
		gap: var(--sp-3);
		padding-bottom: var(--sp-3);
		border-bottom: var(--border-hair);
		font-size: var(--text-body-sm);
		color: var(--text-body);
		line-height: var(--leading-body);
	}
	.sl-check__n {
		color: var(--text-faint);
		flex: none;
	}

	/* ── faq ── */
	.sl-faqs {
		border-top: var(--border-hair);
	}
	.sl-faq {
		border-bottom: var(--border-hair);
	}
	.sl-faq__q {
		cursor: pointer;
		list-style: none;
		padding: var(--sp-4) 0;
		font-size: var(--text-body-sm);
		font-weight: var(--w-strong);
		color: var(--text-strong);
		display: flex;
		justify-content: space-between;
		gap: var(--sp-4);
	}
	.sl-faq__q::-webkit-details-marker {
		display: none;
	}
	.sl-faq__q::after {
		content: '+';
		color: var(--text-muted);
		flex: none;
	}
	.sl-faq[open] .sl-faq__q::after {
		content: '−';
	}
	.sl-faq__a {
		margin: 0;
		padding: 0 0 var(--sp-5);
		max-width: 68ch;
		font-size: var(--text-body-sm);
		line-height: var(--leading-body);
		color: var(--text-muted);
	}

	/* ── related ── */
	.sl-related {
		display: grid;
		gap: var(--sp-3);
	}
	@media (min-width: 720px) {
		.sl-related {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}
	.sl-rel {
		display: flex;
		flex-direction: column;
		gap: var(--sp-1);
		padding: var(--sp-4) var(--sp-5);
		border: var(--border-hair);
		background: var(--surface-card);
		text-decoration: none;
		transition: border-color var(--dur-base) var(--ease-out);
	}
	.sl-rel:hover {
		border-color: var(--ink-900);
	}
	.sl-rel__label {
		font-size: var(--text-body-sm);
		font-weight: var(--w-strong);
		color: var(--text-strong);
	}
	.sl-rel__desc {
		font-size: var(--text-caption);
		color: var(--text-muted);
		line-height: var(--leading-body);
	}
</style>
