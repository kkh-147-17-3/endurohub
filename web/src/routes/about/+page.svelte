<script lang="ts">
    const sports = [
        { code: '01', label: '마라톤', desc: '도로 · 5K~풀코스' },
        { code: '02', label: '트레일러닝', desc: '산악 · 오프로드' },
        { code: '03', label: '자전거', desc: '도로 · 그래블' },
        { code: '04', label: '수영', desc: '오픈워터 · 수영장' },
        { code: '05', label: '철인3종', desc: '수영 · 자전거 · 달리기' },
    ];

    const features = [
        {
            kicker: '01',
            title: '대회 검색',
            body: '종목 · 지역 · 기간 · 거리로 원하는 대회를 좁혀 찾을 수 있습니다.',
        },
        {
            kicker: '02',
            title: '캘린더 뷰',
            body: '월별 대회 일정을 한 화면에서 확인하고 일정을 비교합니다.',
        },
        {
            kicker: '03',
            title: '마감 임박 알림',
            body: '접수 마감이 다가오는 대회를 D-day로 한눈에 확인합니다.',
        },
        {
            kicker: '04',
            title: '상세 정보',
            body: '대회 일시, 장소, 참가비, 거리별 종목까지 정리해 드립니다.',
        },
    ];
</script>

<svelte:head>
    <title>소개 - 엔듀로허브</title>
    <meta
        name="description"
        content="엔듀로허브는 국내 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 정보를 제공하는 플랫폼입니다."
    />
    <meta property="og:title" content="소개 - 엔듀로허브" />
    <meta
        property="og:description"
        content="엔듀로허브는 국내 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 정보를 제공하는 플랫폼입니다."
    />
</svelte:head>

<div class="page-wrap">
    <article class="page-shell">
        <header class="page-head">
            <div class="arena-kicker">소개 · 0001</div>
            <h1 class="page-title">엔듀로허브<br />소개</h1>
            <p class="page-lead">
                국내에서 열리는 지구력 대회를 한곳에서 찾고, 비교하고, 놓치지 않게 합니다.
            </p>
        </header>

        <section class="page-section">
            <div class="arena-kicker">우리가 하는 일</div>
            <p class="section-body">
                엔듀로허브는 마라톤 · 수영 · 자전거 · 철인3종 · 트레일러닝 대회 정보를 큐레이션하는 플랫폼입니다.
                흩어져 있는 공식 페이지의 일정과 모집 정보를 한 곳에 모아, 지구력 종목을 즐기는 분들이 다음 시즌을 더
                쉽게 계획할 수 있도록 돕습니다.
            </p>
        </section>

        <section class="page-section">
            <div class="arena-kicker">기능 · 04</div>
            <div class="feature-grid">
                {#each features as f}
                    <div class="feature-card">
                        <div class="feature-kicker">{f.kicker}</div>
                        <div class="feature-title">{f.title}</div>
                        <p class="feature-body">{f.body}</p>
                    </div>
                {/each}
            </div>
        </section>

        <section class="page-section">
            <div class="arena-kicker">종목 · 05</div>
            <div class="sport-grid">
                {#each sports as s}
                    <div class="sport-tile">
                        <span class="sport-code">{s.code}</span>
                        <span class="sport-label">{s.label}</span>
                        <span class="sport-desc">{s.desc}</span>
                    </div>
                {/each}
            </div>
        </section>

        <section class="page-section">
            <div class="arena-kicker">문의</div>
            <div class="contact-row">
                <div class="contact-meta">서비스 이용 중 문의사항이 있으시면 메일로 연락 주세요.</div>
                <a class="contact-link" href="mailto:contact@endurohub.kr">
                    contact@endurohub.kr
                    <span class="contact-arrow">→</span>
                </a>
            </div>
        </section>
    </article>
</div>

<style>
    .page-wrap {
        background: var(--arena-paper);
        padding: 56px 24px 80px;
    }
    .page-shell {
        max-width: 760px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        gap: 48px;
    }

    .page-head {
        display: flex;
        flex-direction: column;
        gap: 14px;
        padding-bottom: 32px;
        border-bottom: 1px solid var(--arena-line);
    }
    .page-title {
        font-family: var(--arena-f-display);
        font-size: 56px;
        font-weight: 700;
        letter-spacing: -2px;
        line-height: 1;
        margin: 0;
        color: var(--arena-ink);
    }
    .page-lead {
        font-family: var(--arena-f-body);
        font-size: 16px;
        line-height: 1.6;
        color: var(--arena-ink-soft);
        margin: 0;
        max-width: 56ch;
        word-break: keep-all;
    }

    .page-section {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }
    .section-body {
        font-family: var(--arena-f-body);
        font-size: 15px;
        line-height: 1.75;
        color: var(--arena-ink);
        margin: 0;
        max-width: 60ch;
        word-break: keep-all;
    }

    /* Feature grid */
    .feature-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 0;
        border: 1px solid var(--arena-line);
    }
    @media (min-width: 720px) {
        .feature-grid {
            grid-template-columns: 1fr 1fr;
        }
    }
    .feature-card {
        padding: 22px 20px;
        background: var(--arena-paper);
        border-bottom: 1px solid var(--arena-line-soft);
        border-right: 1px solid var(--arena-line-soft);
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    @media (min-width: 720px) {
        .feature-card:nth-child(2n) {
            border-right: none;
        }
        .feature-card:nth-last-child(-n + 2) {
            border-bottom: none;
        }
    }
    @media (max-width: 719px) {
        .feature-card {
            border-right: none;
        }
        .feature-card:last-child {
            border-bottom: none;
        }
    }
    .feature-kicker {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1.5px;
        color: var(--arena-accent-deep);
        font-weight: 700;
    }
    .feature-title {
        font-family: var(--arena-f-display);
        font-size: 18px;
        font-weight: 600;
        letter-spacing: -0.4px;
        color: var(--arena-ink);
    }
    .feature-body {
        font-family: var(--arena-f-body);
        font-size: 14px;
        line-height: 1.6;
        color: var(--arena-ink-soft);
        margin: 0;
        word-break: keep-all;
    }

    /* Sport grid */
    .sport-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px;
    }
    @media (min-width: 720px) {
        .sport-grid {
            grid-template-columns: repeat(5, 1fr);
        }
    }
    .sport-tile {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 14px 14px 16px;
        background: var(--arena-paper);
        border: 1px solid var(--arena-line-soft);
    }
    .sport-code {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
    }
    .sport-label {
        font-family: var(--arena-f-display);
        font-size: 17px;
        font-weight: 600;
        letter-spacing: -0.3px;
        color: var(--arena-ink);
    }
    .sport-desc {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 0.5px;
        color: var(--arena-ink-mute);
    }

    /* Contact */
    .contact-row {
        display: flex;
        flex-direction: column;
        gap: 14px;
        padding: 22px 20px;
        background: var(--arena-paper-alt);
        border: 1px solid var(--arena-line);
    }
    @media (min-width: 720px) {
        .contact-row {
            flex-direction: row;
            align-items: center;
            justify-content: space-between;
        }
    }
    .contact-meta {
        font-family: var(--arena-f-body);
        font-size: 14px;
        line-height: 1.6;
        color: var(--arena-ink);
        word-break: keep-all;
    }
    .contact-link {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
        background: var(--arena-ink);
        color: var(--arena-paper);
        font-family: var(--arena-f-display);
        font-weight: 600;
        font-size: 14px;
        letter-spacing: -0.2px;
        text-decoration: none;
        border: 1px solid var(--arena-ink);
        flex-shrink: 0;
    }
    .contact-arrow {
        font-family: var(--arena-f-mono);
        color: var(--arena-accent);
    }

    @media (max-width: 719px) {
        .page-title {
            font-size: 40px;
            letter-spacing: -1.5px;
        }
        .page-lead {
            font-size: 15px;
        }
    }
</style>
