<script lang="ts">
    let {
        current = '',
    }: {
        current?: string;
    } = $props();

    const tools = [
        { name: '페이스 계산기', href: '/tools/pace-calculator', key: 'pace-calculator', icon: 'clock' },
        { name: '훈련 플랜', href: '/tools/training-plan', key: 'training-plan', icon: 'clipboard' },
        { name: 'VO2max 계산기', href: '/tools/vo2max', key: 'vo2max', icon: 'heart' },
        { name: '대회 기록 예측기', href: '/tools/race-predictor', key: 'race-predictor', icon: 'chart' },
        { name: '러닝 용어 사전', href: '/running-terms', key: 'glossary', icon: 'book' },
    ];

    let otherTools = $derived(tools.filter(t => t.key !== current));
</script>

<div class="card bg-slate-900 text-white">
    <div class="card-body">
        <h2 class="font-semibold text-sm uppercase tracking-wide text-white/50 mb-3">다른 도구</h2>
        <ul class="space-y-1">
            {#each otherTools as tool (tool.key)}
                <li>
                    <a
                        href={tool.href}
                        class="flex items-center gap-3 px-3 py-2 rounded-lg text-white/70 hover:text-white hover:bg-white/10 text-sm cursor-pointer transition-all duration-200"
                    >
                        {#if tool.icon === 'clock'}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 shrink-0 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        {:else if tool.icon === 'clipboard'}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 shrink-0 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" /></svg>
                        {:else if tool.icon === 'heart'}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 shrink-0 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>
                        {:else if tool.icon === 'chart'}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 shrink-0 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                        {:else if tool.icon === 'book'}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 shrink-0 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
                        {/if}
                        {tool.name}
                    </a>
                </li>
            {/each}
        </ul>
    </div>
</div>
