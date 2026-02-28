<script lang="ts">
    const tools = [
        {
            name: '페이스 계산기',
            description: '목표 시간에 맞는 km당 페이스를 계산하고 구간별 스플릿 테이블을 확인하세요.',
            href: '/tools/pace-calculator',
            iconBg: 'bg-primary/10 group-hover:bg-primary/20',
            iconColor: 'text-primary',
            hoverText: 'group-hover:text-primary',
            hoverBorder: 'hover:border-primary/40',
            ctaColor: 'text-primary',
            icon: 'clock',
        },
        {
            name: '훈련 플랜',
            description: '목표 대회에 맞는 12주/16주 맞춤 훈련 계획을 무료로 만들어 보세요.',
            href: '/tools/training-plan',
            iconBg: 'bg-secondary/10 group-hover:bg-secondary/20',
            iconColor: 'text-secondary',
            hoverText: 'group-hover:text-secondary',
            hoverBorder: 'hover:border-secondary/40',
            ctaColor: 'text-secondary',
            icon: 'clipboard',
        },
        {
            name: 'VO2max 계산기',
            description: '대회 기록으로 최대산소섭취량을 추정하고 체력 등급을 확인하세요.',
            href: '/tools/vo2max',
            iconBg: 'bg-error/10 group-hover:bg-error/20',
            iconColor: 'text-error',
            hoverText: 'group-hover:text-error',
            hoverBorder: 'hover:border-error/40',
            ctaColor: 'text-error',
            icon: 'heart',
        },
        {
            name: '대회 기록 예측기',
            description: '현재 기록으로 다른 거리의 예상 완주 시간을 예측하세요.',
            href: '/tools/race-predictor',
            iconBg: 'bg-info/10 group-hover:bg-info/20',
            iconColor: 'text-info',
            hoverText: 'group-hover:text-info',
            hoverBorder: 'hover:border-info/40',
            ctaColor: 'text-info',
            icon: 'chart',
        },
        {
            name: '러닝 용어 사전',
            description: '마라톤과 러닝에서 자주 사용되는 용어를 쉽게 알아보세요.',
            href: '/running-terms',
            iconBg: 'bg-warning/10 group-hover:bg-warning/20',
            iconColor: 'text-warning',
            hoverText: 'group-hover:text-warning',
            hoverBorder: 'hover:border-warning/40',
            ctaColor: 'text-warning',
            icon: 'book',
        },
    ];
</script>

<svelte:head>
    <title>러닝 도구 모음 - 엔듀로허브</title>
    <meta name="description" content="마라톤 페이스 계산기, 훈련 플랜 생성기, VO2max 계산기, 대회 기록 예측기, 러닝 용어 사전 등 러너를 위한 무료 도구 모음." />
    <meta property="og:title" content="러닝 도구 모음 - 엔듀로허브" />
    <meta property="og:description" content="마라톤 페이스 계산기, 훈련 플랜 생성기, VO2max 계산기, 대회 기록 예측기, 러닝 용어 사전 등 러너를 위한 무료 도구 모음." />
    {@html `<script type="application/ld+json">${JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'CollectionPage',
        'name': '러닝 도구 모음 - 엔듀로허브',
        'description': '마라톤 페이스 계산기, 훈련 플랜, VO2max 계산기, 대회 기록 예측기 등 러너를 위한 무료 도구 모음.',
    })}</script>`}
</svelte:head>

<div class="container mx-auto px-4 py-8">
    <div class="breadcrumbs text-sm mb-6">
        <ul>
            <li><a href="/">홈</a></li>
            <li>도구</li>
        </ul>
    </div>

    <div class="mb-10">
        <h1 class="text-2xl md:text-3xl font-bold">러닝 도구 모음</h1>
        <p class="text-base-content/60 mt-2 max-w-2xl">훈련과 대회 준비에 도움이 되는 무료 도구들을 활용해 보세요.</p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {#each tools as tool (tool.href)}
            <a
                href={tool.href}
                class="card bg-base-100 border border-base-300 {tool.hoverBorder} hover:shadow-lg transition-all duration-200 cursor-pointer group"
            >
                <div class="card-body">
                    <div class="flex items-start gap-4">
                        <div class="w-11 h-11 rounded-xl {tool.iconBg} flex items-center justify-center shrink-0 transition-colors duration-200">
                            {#if tool.icon === 'clock'}
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 {tool.iconColor}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                            {:else if tool.icon === 'clipboard'}
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 {tool.iconColor}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" /></svg>
                            {:else if tool.icon === 'heart'}
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 {tool.iconColor}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>
                            {:else if tool.icon === 'chart'}
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 {tool.iconColor}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                            {:else if tool.icon === 'book'}
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 {tool.iconColor}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
                            {/if}
                        </div>
                        <div class="flex-1 min-w-0">
                            <h2 class="font-semibold text-base {tool.hoverText} transition-colors duration-200">{tool.name}</h2>
                            <p class="text-sm text-base-content/60 mt-1 leading-relaxed">{tool.description}</p>
                        </div>
                    </div>
                    <div class="flex justify-end mt-3">
                        <span class="{tool.ctaColor} text-sm font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                            사용하기
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg>
                        </span>
                    </div>
                </div>
            </a>
        {/each}
    </div>
</div>
