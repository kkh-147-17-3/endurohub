<script lang="ts">
	import type { ToolPage } from '$lib/seo/tool-pages';
	let { tool }: { tool: ToolPage } = $props();
</script>

<section class="guide v-container" aria-labelledby={`${tool.slug}-guide`}>
	<div class="v-sechead"><h2 id={`${tool.slug}-guide`}>사용 방법과 계산 기준</h2></div>
	<div class="guide-grid">
		<div>
			<h3>이럴 때 활용하세요</h3>
			<ul>{#each tool.useCases as item}<li>{item}</li>{/each}</ul>
			<h3>사용 순서</h3>
			<ol>{#each tool.steps as item}<li>{item}</li>{/each}</ol>
		</div>
		<div>
			<h3>계산 방식</h3>
			<p>{tool.method.explanation}</p>
			<div class="formulas">{#each tool.method.formulas as formula}<code>{formula}</code>{/each}</div>
			<h3>결과를 읽을 때</h3>
			<ul>{#each tool.assumptions as item}<li>{item}</li>{/each}</ul>
		</div>
	</div>
	<div class="faq">
		<h2>자주 묻는 질문</h2>
		{#each tool.faqs as faq}
			<details><summary>{faq.question}</summary><p>{faq.answer}</p></details>
		{/each}
	</div>
	<nav class="related" aria-label="함께 사용할 도구와 대회 정보">
		<h2>함께 보면 좋은 정보</h2>
		<div class="related-grid">
			{#each tool.related as link}
				<a href={link.href}><strong>{link.label} →</strong><span>{link.description}</span></a>
			{/each}
		</div>
	</nav>
</section>

<style>
	.guide { border-top: var(--border-rule); padding-top: var(--sp-8); padding-bottom: var(--sp-20); }
	h2 { margin: 0; font-size: var(--text-h3); font-weight: var(--w-heading); line-height: var(--leading-heading); }
	h3 { margin: var(--sp-5) 0 var(--sp-2); font-size: var(--text-body); font-weight: var(--w-heading); }
	p, li { font-size: var(--text-body-sm); line-height: var(--leading-body); color: var(--text-muted); }
	p { margin: var(--sp-2) 0; }
	ul, ol { margin: var(--sp-2) 0 0; padding-left: var(--sp-5); }
	li + li { margin-top: var(--sp-2); }
	.guide-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--sp-10); }
	.formulas { display: grid; gap: var(--sp-2); padding: var(--sp-4); margin-top: var(--sp-3); background: var(--paper-50); border: var(--border-hair); }
	code { font-size: var(--text-micro); color: var(--text-body); white-space: normal; overflow-wrap: anywhere; line-height: var(--leading-body); }
	.faq, .related { margin-top: var(--sp-10); }
	.faq h2, .related h2 { margin-bottom: var(--sp-4); }
	details { border-top: var(--border-hair); }
	details:last-child { border-bottom: var(--border-hair); }
	summary { padding: var(--sp-4) 0; font-size: var(--text-body-sm); font-weight: var(--w-heading); cursor: pointer; }
	details p { padding: 0 var(--sp-4) var(--sp-4); margin: 0; }
	.related-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--sp-3); }
	.related a { display: flex; flex-direction: column; gap: var(--sp-2); border: var(--border-hair); padding: var(--sp-4); color: var(--text-strong); text-decoration: none; }
	.related a:hover { border-color: var(--ink-900); }
	.related strong { font-size: var(--text-body-sm); }
	.related span { color: var(--text-muted); font-size: var(--text-micro); line-height: var(--leading-body); }
	summary:focus-visible, a:focus-visible { outline: 2px solid var(--ink-900); outline-offset: 3px; }
	@media (max-width: 768px) { .guide-grid, .related-grid { grid-template-columns: 1fr; gap: var(--sp-4); } }
</style>
