<script lang="ts">
	import { page } from '$app/stores';
	import ToolsShell from '$lib/components/arena/ToolsShell.svelte';

	const tools = [
		{
			slug: 'pace-calculator',
			title: '페이스 계산기',
			desc: '거리와 목표 완주 시간을 선택하면 km당 페이스, 평균 속도와 주요 구간의 누적 통과 시간을 계산합니다.',
			tags: ['거리·목표 시간', '구간 통과 시간', '평균 속도'],
		},
		{
			slug: 'training-plan',
			title: '훈련 플랜',
			desc: '가상의 목표를 사용한 16주 공개 예시와 BASE·BUILD·PEAK·TAPER 구성을 살펴봅니다. 로그인 후 관심 대회 일정으로 참고 구성을 볼 수 있습니다.',
			tags: ['공개 예시', '주차별 구성', '4단계 참고 플랜'],
		},
		{
			slug: 'vo2max',
			title: 'VDOT 계산기',
			desc: '러닝 거리와 기록으로 VDOT 근사값과 같은 지수의 거리별 동등 기록을 비교합니다. 실제 VO₂max 측정과 구분해 확인하세요.',
			tags: ['VDOT 근사값', '기록 기반 계산', '동등 기록 비교'],
		},
		{
			slug: 'race-predictor',
			title: '대회 기록 예측',
			desc: '최근 기록을 바탕으로 5K · 10K · 하프 · 풀코스의 예상 완주 시간과 평균 페이스를 비교합니다 (Riegel 모델, k = 1.06).',
			tags: ['Riegel 모델', '거리별 예상', '평균 페이스'],
		},
	];
</script>

<svelte:head>
	<title>러닝 도구실 — endurohub</title>
	<meta
		name="description"
		content="페이스 계산기, 훈련 플랜 공개 예시, VDOT와 동등 기록, 대회 기록 예측 — 러너를 위한 도구"
	/>
</svelte:head>

<ToolsShell currentPath={$page.url.pathname}>
	<div class="hub v-container">
		<!-- intro -->
		<div class="intro">
			<h2 class="eh-h2">달리기를 위한 도구</h2>
			<p class="intro-desc">
				4가지 도구를 한 곳에서. 로그인 시 최근 기록이 자동으로 채워집니다.
			</p>
		</div>

		<!-- tool cards -->
		<div class="cards">
			{#each tools as t (t.slug)}
				<a class="tool-card" href="/tools/{t.slug}">
					<div class="card-title">{t.title}</div>
					<p class="card-desc">{t.desc}</p>
					<div class="card-tags">
						{#each t.tags as tg}
							<span class="card-tag">{tg}</span>
						{/each}
					</div>
					<div class="card-foot">
						<span class="card-go">열기 →</span>
					</div>
				</a>
			{/each}
		</div>

		<!-- sidebar -->
		<aside class="aside">
			<a href="/running-terms" class="aux-link">
				<div class="aux-title">러닝 용어 사전</div>
				<p class="aux-desc">페이스 · LSD · 인터벌 · VO₂max … 러닝 용어 120개+</p>
			</a>
			<div class="note">
				<div class="eh-micro" style="margin-bottom:var(--sp-2);color:var(--text-muted)">계산 방식</div>
				<ul class="note-list">
					<li>Daniels &amp; Gilbert VDOT 근사식</li>
					<li>Riegel 피로 지수 모델 (k = 1.06)</li>
					<li>4단계 주기화 (Base / Build / Peak / Taper)</li>
				</ul>
			</div>
		</aside>
	</div>
</ToolsShell>

<style>
	.hub {
		padding-top: var(--sp-8);
		padding-bottom: var(--sp-20);
		display: grid;
		grid-template-columns: 1fr;
		gap: var(--sp-8);
	}
	@media (min-width: 1024px) {
		.hub {
			grid-template-columns: 1fr 280px;
			gap: var(--sp-10);
			align-items: start;
		}
		.cards { grid-column: 1; }
		.aside { grid-column: 2; grid-row: 2 / 4; }
	}

	.intro { grid-column: 1 / -1; }
	.intro-desc {
		margin: var(--sp-2) 0 0;
		font-size: var(--text-body-sm);
		color: var(--text-muted);
		line-height: var(--leading-body);
		max-width: 58ch;
	}

	/* ── cards ── */
	.cards {
		display: grid;
		grid-template-columns: 1fr;
		gap: var(--sp-4);
	}
	@media (min-width: 680px) {
		.cards { grid-template-columns: 1fr 1fr; }
	}
	.tool-card {
		display: flex;
		flex-direction: column;
		gap: var(--sp-3);
		padding: var(--sp-5) var(--sp-6);
		border: var(--border-hair);
		background: var(--paper-0);
		text-decoration: none;
		color: var(--text-strong);
		transition: border-color var(--dur-base) var(--ease-out),
		            transform var(--dur-base) var(--ease-out),
		            box-shadow var(--dur-base) var(--ease-out);
	}
	.tool-card:hover {
		border-color: var(--ink-900);
		transform: translateY(-2px);
		box-shadow: var(--shadow-card-hover);
	}
	.card-title {
		font-size: var(--text-h3);
		font-weight: var(--w-heading);
		letter-spacing: var(--track-heading);
		line-height: var(--leading-tight);
		color: var(--text-strong);
	}
	.card-desc {
		font-size: var(--text-body-sm);
		color: var(--text-muted);
		line-height: var(--leading-body);
		margin: 0;
		flex: 1;
	}
	.card-tags {
		display: flex;
		gap: var(--sp-2);
		flex-wrap: wrap;
	}
	.card-tag {
		font-family: var(--font-mono);
		font-size: 10px;
		letter-spacing: 0.04em;
		padding: 2px var(--sp-2);
		border: var(--border-hair);
		color: var(--text-muted);
	}
	.card-foot {
		margin-top: var(--sp-1);
		padding-top: var(--sp-3);
		border-top: var(--border-hair);
		display: flex;
		justify-content: flex-end;
	}
	.card-go {
		font-family: var(--font-mono);
		font-size: 11px;
		letter-spacing: 0.06em;
		color: var(--text-strong);
	}

	/* ── aside ── */
	.aside {
		display: flex;
		flex-direction: column;
		gap: var(--sp-5);
	}
	.aux-link {
		display: block;
		padding: var(--sp-4) var(--sp-5);
		border: var(--border-hair);
		border-style: dashed;
		background: var(--paper-50);
		text-decoration: none;
		color: var(--text-strong);
		transition: border-style var(--dur-fast);
	}
	.aux-link:hover { border-style: solid; }
	.aux-title {
		font-size: 15px;
		font-weight: var(--w-strong);
		letter-spacing: var(--track-heading);
		margin-bottom: var(--sp-1);
	}
	.aux-desc {
		margin: 0;
		font-size: 12px;
		color: var(--text-muted);
		line-height: var(--leading-body);
	}
	.note {
		padding: var(--sp-4);
		border-top: var(--border-rule);
		background: var(--paper-50);
	}
	.note-list {
		margin: 0;
		padding-left: var(--sp-4);
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--text-muted);
		line-height: 1.8;
		list-style: disc;
	}
</style>
