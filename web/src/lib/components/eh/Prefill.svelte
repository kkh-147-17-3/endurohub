<script lang="ts">
	import Badge from '$lib/components/eh/Badge.svelte';

	// Interactive "auto-fill from most recent record" bar (v2 Tools design).
	// Shows the signed-in user's latest running record and restores the tool
	// inputs to it on demand via the "적용" action.
	let {
		label,
		onApply,
	}: {
		label: string;
		onApply: () => void;
	} = $props();
</script>

<div class="prefill">
	<Badge status="open">자동 입력</Badge>
	<span class="prefill-text">최근 기록 — <b>{label}</b></span>
	<button type="button" class="prefill-apply" onclick={onApply}>적용 →</button>
</div>

<style>
	.prefill {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 11px 14px;
		background: var(--paper-50);
		border: var(--border-hair);
		font-size: 12.5px;
		color: var(--text-muted);
	}
	.prefill-text b {
		color: var(--text-strong);
	}
	.prefill-apply {
		margin-left: auto;
		background: none;
		border: 0;
		font-size: 12px;
		font-weight: 600;
		color: var(--text-accent);
		border-bottom: 1px solid transparent;
		padding: 0;
		cursor: pointer;
		white-space: nowrap;
	}
	.prefill-apply:hover {
		border-bottom-color: var(--text-accent);
	}
</style>
