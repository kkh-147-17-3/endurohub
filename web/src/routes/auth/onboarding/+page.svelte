<script lang="ts">
    import { enhance } from '$app/forms';
    import type { Sport } from '$lib/types';

    let { data, form } = $props();

    let selectedSports = $state<string[]>([]);
    let selectedRegions = $state<string[]>([]);
    let isSubmitting = $state(false);

    const sports: { value: Sport; label: string; emoji: string; color: string; colorSelected: string }[] = [
        { value: 'running', label: '마라톤', emoji: '🏃', color: 'border-base-300 hover:border-primary/40', colorSelected: 'border-primary bg-primary/8 ring-2 ring-primary/20' },
        { value: 'trail_running', label: '트레일러닝', emoji: '⛰️', color: 'border-base-300 hover:border-success/40', colorSelected: 'border-success bg-success/8 ring-2 ring-success/20' },
        { value: 'cycling', label: '자전거', emoji: '🚴', color: 'border-base-300 hover:border-warning/40', colorSelected: 'border-warning bg-warning/8 ring-2 ring-warning/20' },
        { value: 'swimming', label: '수영', emoji: '🏊', color: 'border-base-300 hover:border-info/40', colorSelected: 'border-info bg-info/8 ring-2 ring-info/20' },
        { value: 'triathlon', label: '철인3종', emoji: '🏅', color: 'border-base-300 hover:border-secondary/40', colorSelected: 'border-secondary bg-secondary/8 ring-2 ring-secondary/20' },
    ];

    const regions = [
        '서울', '경기', '인천', '부산', '대구', '광주', '대전', '울산', '세종',
        '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주',
    ];

    function toggleSport(sport: string) {
        if (selectedSports.includes(sport)) {
            selectedSports = selectedSports.filter((s) => s !== sport);
        } else {
            selectedSports = [...selectedSports, sport];
        }
    }

    function toggleRegion(region: string) {
        if (selectedRegions.includes(region)) {
            selectedRegions = selectedRegions.filter((r) => r !== region);
        } else {
            selectedRegions = [...selectedRegions, region];
        }
    }

    let step = $state(1);
    let totalSteps = 2;

    function nextStep() {
        if (step < totalSteps) step++;
    }

    function prevStep() {
        if (step > 1) step--;
    }
</script>

<svelte:head>
    <title>관심사 설정 - 엔듀로허브</title>
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
    <div class="w-full max-w-lg">

        <!-- Progress -->
        <div class="flex items-center gap-2 mb-8 px-2">
            <div class="flex-1 h-1.5 rounded-full overflow-hidden bg-base-200">
                <div
                    class="h-full bg-primary rounded-full transition-all duration-500 ease-out"
                    style="width: {(step / totalSteps) * 100}%"
                ></div>
            </div>
            <span class="text-xs text-base-content/40 tabular-nums shrink-0">{step}/{totalSteps}</span>
        </div>

        <form
            method="POST"
            use:enhance={() => {
                isSubmitting = true;
                return async ({ update }) => {
                    isSubmitting = false;
                    await update();
                };
            }}
        >
            <input type="hidden" name="preferred_sports" value={selectedSports.join(',')} />
            <input type="hidden" name="preferred_regions" value={selectedRegions.join(',')} />

            <!-- Step 1: Sport Selection -->
            {#if step === 1}
                <div class="text-center mb-8" style="animation: fadeSlideUp 0.4s ease-out">
                    <h1 class="text-2xl font-bold tracking-tight">어떤 종목에 관심 있으세요?</h1>
                    <p class="mt-2 text-base-content/50 text-sm">관심 종목을 선택하면 맞춤 대회 정보를 받을 수 있어요</p>
                </div>

                <div class="grid grid-cols-1 gap-3" style="animation: fadeSlideUp 0.4s ease-out 0.05s both">
                    {#each sports as sport}
                        {@const isSelected = selectedSports.includes(sport.value)}
                        <button
                            type="button"
                            class="flex items-center gap-4 px-5 py-4 rounded-xl border-2 transition-all duration-200 cursor-pointer
                                {isSelected ? sport.colorSelected : sport.color}"
                            onclick={() => toggleSport(sport.value)}
                        >
                            <span class="text-3xl w-10 text-center select-none">{sport.emoji}</span>
                            <span class="font-semibold text-base flex-1 text-left">{sport.label}</span>
                            {#if isSelected}
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary" viewBox="0 0 20 20" fill="currentColor">
                                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                                </svg>
                            {:else}
                                <div class="w-5 h-5 rounded-full border-2 border-base-300"></div>
                            {/if}
                        </button>
                    {/each}
                </div>

                <div class="mt-8 flex gap-3">
                    <button
                        type="button"
                        class="btn btn-primary btn-block"
                        onclick={nextStep}
                    >
                        {selectedSports.length > 0 ? '다음' : '건너뛰기'}
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                        </svg>
                    </button>
                </div>
            {/if}

            <!-- Step 2: Region Selection -->
            {#if step === 2}
                <div class="text-center mb-8" style="animation: fadeSlideUp 0.4s ease-out">
                    <h1 class="text-2xl font-bold tracking-tight">주로 어디서 뛰세요?</h1>
                    <p class="mt-2 text-base-content/50 text-sm">관심 지역의 대회를 우선 추천해드릴게요</p>
                </div>

                <div class="flex flex-wrap gap-2 justify-center" style="animation: fadeSlideUp 0.4s ease-out 0.05s both">
                    {#each regions as region}
                        {@const isSelected = selectedRegions.includes(region)}
                        <button
                            type="button"
                            class="px-4 py-2.5 rounded-full border-2 text-sm font-medium transition-all duration-200 cursor-pointer
                                {isSelected
                                    ? 'border-primary bg-primary text-primary-content shadow-sm'
                                    : 'border-base-300 hover:border-primary/30 text-base-content/70 hover:text-base-content'}"
                            onclick={() => toggleRegion(region)}
                        >
                            {region}
                        </button>
                    {/each}
                </div>

                {#if selectedRegions.length > 0}
                    <div class="mt-4 text-center" style="animation: fadeSlideUp 0.3s ease-out">
                        <span class="text-xs text-base-content/40">
                            {selectedRegions.join(', ')} 선택됨
                        </span>
                    </div>
                {/if}

                <div class="mt-8 flex gap-3">
                    <button
                        type="button"
                        class="btn btn-ghost flex-none"
                        onclick={prevStep}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
                        </svg>
                        이전
                    </button>
                    <button
                        type="submit"
                        class="btn btn-primary flex-1"
                        disabled={isSubmitting}
                    >
                        {#if isSubmitting}
                            <span class="loading loading-spinner loading-sm"></span>
                        {/if}
                        시작하기
                    </button>
                </div>
            {/if}
        </form>

        <!-- Skip link -->
        <div class="text-center mt-6">
            <form
                method="POST"
                use:enhance={() => {
                    isSubmitting = true;
                    return async ({ update }) => {
                        isSubmitting = false;
                        await update();
                    };
                }}
            >
                <input type="hidden" name="preferred_sports" value="" />
                <input type="hidden" name="preferred_regions" value="" />
                <button
                    type="submit"
                    class="text-sm text-base-content/40 hover:text-base-content/60 transition-colors cursor-pointer"
                    disabled={isSubmitting}
                >
                    나중에 설정할게요
                </button>
            </form>
        </div>
    </div>
</div>

<style>
    @keyframes fadeSlideUp {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
</style>
