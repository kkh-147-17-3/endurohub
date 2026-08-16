<script lang="ts">
	import SportLanding from '$lib/components/sports/SportLanding.svelte';

	let { data } = $props();
</script>

<SportLanding
	content={data.content}
	races={data.races}
	total={data.total}
	openTotal={data.openTotal}
	appUrl={data.appUrl}
	year={data.currentYear}
/>
