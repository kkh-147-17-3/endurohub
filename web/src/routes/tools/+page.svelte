<script lang="ts">
    import { page } from '$app/stores';
    import ToolsShell from '$lib/components/arena/ToolsShell.svelte';

    const tools = [
        {
            slug: 'pace-calculator',
            kicker: '01 · 페이스',
            title: '페이스 계산기',
            desc: '거리 · 시간 · 페이스 — 셋 중 둘을 입력하면 나머지를 계산합니다. 1km 구간 스플릿과 페이스 변환 표 포함.',
            tags: ['거리/시간/페이스', '구간 스플릿', '페이스 변환'],
        },
        {
            slug: 'training-plan',
            kicker: '02 · 훈련',
            title: '훈련 플랜',
            desc: '8 · 12 · 16주 주기화 (베이스 → 빌드 → 피크 → 테이퍼). VDOT 기반 강도, 주간 캘린더, 포커스 주차 상세.',
            tags: ['주기화', '주간 캘린더', '강도 단계'],
        },
        {
            slug: 'vo2max',
            kicker: '03 · VDOT',
            title: 'VO₂max 계산기',
            desc: '최근 레이스 기록으로 VDOT(Daniels)을 추정하고, 트레이닝 페이스(E/M/T/I/R)를 자동으로 산출합니다.',
            tags: ['Daniels VDOT', '체력 등급', '트레이닝 페이스'],
        },
        {
            slug: 'race-predictor',
            kicker: '04 · 예측',
            title: '대회 기록 예측',
            desc: '최근 기록을 바탕으로 5K · 10K · 하프 · 풀 · 50K 예상 완주 시간을 산출합니다 (Riegel 모델).',
            tags: ['Riegel 모델', '거리별 예상', '평균 페이스'],
        },
    ];
</script>

<svelte:head>
    <title>러닝 도구실 — endurohub</title>
    <meta
        name="description"
        content="페이스 계산기, 훈련 플랜, VO₂max, 대회 기록 예측 — 러너를 위한 도구"
    />
</svelte:head>

<ToolsShell currentPath={$page.url.pathname}>
    <div class="hub">
        <div class="intro">
            <div class="arena-kicker">개요</div>
            <h2 class="intro-h">달리기를 위한 도구</h2>
            <p class="intro-p">
                4가지 도구를 한 곳에서. 입력은 자동 저장되며, 결과는 내 시즌의 대회 목표로 바로
                옮길 수 있습니다.
            </p>
        </div>

        <div class="cards">
            {#each tools as t (t.slug)}
                <a class="tool-card" href={`/tools/${t.slug}`}>
                    <div class="card-kicker">{t.kicker}</div>
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

        <div class="sidebar">
            <div class="arena-kicker">함께 보기</div>
            <a href="/running-terms" class="aux-link">
                <div class="aux-title">러닝 용어 사전</div>
                <p class="aux-desc">페이스 · LSD · 인터벌 · VO₂max … 러닝 용어 120개+</p>
            </a>
        </div>
    </div>
</ToolsShell>

<style>
    .hub {
        max-width: 1100px;
        margin: 0 auto;
        padding: 32px 24px 60px;
        display: grid;
        grid-template-columns: 1fr;
        gap: 28px;
    }
    @media (min-width: 1024px) {
        .hub {
            padding: 40px 32px 80px;
            grid-template-columns: 1fr 320px;
            gap: 40px;
        }
    }
    .intro {
        grid-column: 1 / -1;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .intro-h {
        font-family: var(--arena-f-display);
        font-size: clamp(24px, 3vw, 32px);
        font-weight: 700;
        letter-spacing: -0.8px;
        margin: 4px 0 0;
        color: var(--arena-ink);
    }
    .intro-p {
        margin: 0;
        font-size: 14px;
        color: var(--arena-ink-soft);
        line-height: 1.6;
        max-width: 60ch;
    }

    .cards {
        display: grid;
        grid-template-columns: 1fr;
        gap: 16px;
    }
    @media (min-width: 768px) {
        .cards {
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
    }

    .tool-card {
        display: flex;
        flex-direction: column;
        gap: 10px;
        padding: 22px;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
        text-decoration: none;
        color: var(--arena-ink);
        transition: transform 0.15s, box-shadow 0.15s;
    }
    .tool-card:hover {
        transform: translate(-2px, -2px);
        box-shadow: 4px 4px 0 var(--arena-ink);
    }
    .card-kicker {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1.5px;
        color: var(--arena-accent-deep);
    }
    .card-title {
        font-family: var(--arena-f-display);
        font-size: 22px;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .card-desc {
        font-size: 13px;
        color: var(--arena-ink-soft);
        line-height: 1.6;
        margin: 0;
        flex: 1;
    }
    .card-tags {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
    }
    .card-tag {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 0.5px;
        padding: 2px 8px;
        border: 1px solid var(--arena-line-soft);
        color: var(--arena-ink-soft);
    }
    .card-foot {
        margin-top: 4px;
        padding-top: 12px;
        border-top: 1px solid var(--arena-line-soft);
        display: flex;
        justify-content: flex-end;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1px;
    }
    .card-go {
        color: var(--arena-ink);
    }

    .sidebar {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .aux-link {
        display: block;
        padding: 18px;
        border: 1px dashed var(--arena-line);
        background: var(--arena-paper-alt);
        text-decoration: none;
        color: var(--arena-ink);
    }
    .aux-link:hover {
        border-style: solid;
    }
    .aux-title {
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 16px;
        letter-spacing: -0.3px;
        margin-bottom: 6px;
    }
    .aux-desc {
        margin: 0;
        font-size: 12px;
        color: var(--arena-ink-soft);
        line-height: 1.5;
    }
</style>
