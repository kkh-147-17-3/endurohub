<script lang="ts">
	import { previewStoryId, scenarios, viewports, type ComparisonVersion, type PreviewViewport, type Scenario } from './scenarios';

	let {
		scenario = 'date-groups',
		viewport = 'mobile',
		theme = 'light',
		standalone = false,
		previewDocument = ''
	}: { scenario?: Scenario; viewport?: PreviewViewport; theme?: 'light' | 'dark'; standalone?: boolean; previewDocument?: string } = $props();

	const scenarioKeys = Object.keys(scenarios) as Scenario[];
	const viewportKeys = Object.keys(viewports) as PreviewViewport[];
	const versions: ComparisonVersion[] = ['before', 'after'];
	const viewportWidth = $derived(viewports[viewport].width);

	function previewUrl(version: ComparisonVersion): string {
		if (standalone) {
			return `./preview.html?scenario=${scenario}&version=${version}&theme=${theme}`;
		}
		return `./iframe.html?id=${previewStoryId(scenario, version)}&viewMode=story&globals=theme:${theme}`;
	}

	function previewSource(version: ComparisonVersion): string | undefined {
		return previewDocument ? previewDocument.replace('/*__COMPARISON_CONFIG__*/', `window.__DESIGN_COMPARISON__=${JSON.stringify({ scenario, version, theme })};`) : undefined;
	}
</script>

<main class="comparison">
	<header class="comparison__header">
		<h1>디자인 변경 비교</h1>
		<p>같은 예시 데이터와 화면 너비로 변경 전후의 실제 컴포넌트를 비교합니다.</p>
		{#if standalone}<p class="comparison__mode">로컬 비교 갤러리</p>{/if}
	</header>

	<div class="comparison__controls">
		<label>
			<span>비교 대상</span>
			<select bind:value={scenario}>
				{#each scenarioKeys as key}<option value={key}>{scenarios[key].label}</option>{/each}
			</select>
		</label>
		<label>
			<span>화면 너비</span>
			<select bind:value={viewport}>
				{#each viewportKeys as key}<option value={key}>{viewports[key].label}</option>{/each}
			</select>
		</label>
		<label>
			<span>테마</span>
			<select bind:value={theme}>
				<option value="light">라이트</option>
				<option value="dark">다크</option>
			</select>
		</label>
	</div>

	<p class="comparison__note" aria-live="polite">{scenarios[scenario].note}</p>
	<!-- svelte-ignore a11y_no_noninteractive_tabindex (The scroll region must be reachable for keyboard scrolling.) -->
	<div class="comparison__scroll" tabindex="0" role="region" aria-label="변경 전후 비교 화면">
		<div class="comparison__panes" style:--preview-width={`${viewportWidth}px`}>
			{#each versions as version}
				<section class="comparison__pane" aria-labelledby={`comparison-${version}`}>
					<div class="comparison__pane-head">
						<h2 id={`comparison-${version}`}>변경 {version === 'before' ? '전' : '후'}</h2>
						{#if !previewDocument}<a href={previewUrl(version)} target="_blank" rel="noreferrer">별도 화면으로 열기</a>{/if}
					</div>
					{#key `${scenario}-${theme}`}
						<iframe src={previewDocument ? undefined : previewUrl(version)} srcdoc={previewSource(version)} title={`${scenarios[scenario].label} 변경 ${version === 'before' ? '전' : '후'}`} width={viewportWidth} height="1120"></iframe>
					{/key}
				</section>
			{/each}
		</div>
	</div>
</main>

<style>
	.comparison { margin: 0 auto; padding: 28px; color: var(--text-strong, #18201e); font-family: var(--font-sans, sans-serif); }
	.comparison__header h1 { margin: 0 0 10px; font-size: 28px; font-weight: 800; letter-spacing: -0.04em; }
	.comparison__header p { margin: 0; color: var(--text-body, #4b5752); font-size: 14px; line-height: 1.7; }
	.comparison__header .comparison__mode { margin-top: 4px; font-size: 12px; color: var(--text-muted, #66736d); }
	.comparison__controls { display: flex; flex-wrap: wrap; gap: 16px 24px; margin-top: 28px; }
	.comparison__controls label { display: grid; gap: 7px; min-width: 148px; font-size: 12px; font-weight: 650; }
	.comparison__controls select { width: 100%; min-height: 42px; padding: 8px 36px 8px 12px; border: 1px solid var(--line, #d6ded9); border-radius: 6px; background: var(--surface, #fff); color: var(--text-strong, #18201e); font: inherit; font-size: 14px; }
	.comparison__note { margin: 20px 0 24px; max-width: 900px; font-size: 13px; line-height: 1.8; color: var(--text-body, #4b5752); }
	.comparison__scroll { overflow-x: auto; padding-bottom: 16px; }
	.comparison__panes { display: grid; grid-template-columns: repeat(2, calc(var(--preview-width) + 2px)); gap: 24px; width: max-content; }
	.comparison__pane-head { min-height: 40px; display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
	.comparison__pane-head h2 { margin: 0; font-size: 18px; font-weight: 750; letter-spacing: -0.025em; }
	.comparison__pane-head a { font-size: 12px; color: var(--text-muted, #66736d); text-underline-offset: 3px; }
	.comparison__pane iframe { display: block; box-sizing: content-box; width: var(--preview-width); border: 1px solid var(--line, #d6ded9); border-radius: 8px; background: var(--surface, #fff); }
	.comparison__scroll:focus-visible, .comparison__controls select:focus-visible { outline: 2px solid var(--accent, #208467); outline-offset: 4px; }
	@media (max-width: 600px) { .comparison { padding: 20px 16px; } .comparison__header h1 { font-size: 24px; } .comparison__controls { gap: 14px; } .comparison__controls label:first-child { flex-basis: 100%; } }
</style>
