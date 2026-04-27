<script lang="ts">
    let { data } = $props();

    const today = new Date();
    const dateStr = `${today.getFullYear()}.${String(today.getMonth() + 1).padStart(2, '0')}.${String(today.getDate()).padStart(2, '0')}`;

    const sections = [
        {
            num: '01',
            title: '개인정보의 처리 목적',
            body: [
                '엔듀로허브(이하 "서비스")는 다음의 목적을 위하여 개인정보를 처리합니다.',
            ],
            list: ['서비스 제공 및 운영', '푸시 알림 서비스 제공', '서비스 개선 및 통계 분석'],
        },
        {
            num: '02',
            title: '수집하는 개인정보 항목',
            body: ['서비스는 다음과 같은 개인정보를 수집합니다.'],
            list: [
                '모바일 앱 이용 시: 기기 식별자(푸시 토큰), 관심 종목 및 지역 설정',
                '웹사이트 이용 시: 쿠키, 접속 로그',
            ],
        },
        {
            num: '03',
            title: '개인정보의 보유 및 이용 기간',
            body: [
                '수집된 개인정보는 수집 목적이 달성된 후에는 지체 없이 파기됩니다. 단, 관련 법령에 의해 보존할 필요가 있는 경우 해당 기간 동안 보관됩니다.',
            ],
        },
        {
            num: '04',
            title: '개인정보의 제3자 제공',
            body: [
                '서비스는 원칙적으로 이용자의 개인정보를 제3자에게 제공하지 않습니다. 다만, 다음의 경우에는 예외로 합니다.',
            ],
            list: [
                '이용자가 사전에 동의한 경우',
                '법령의 규정에 의거하거나, 수사 목적으로 법령에 정해진 절차와 방법에 따라 수사기관의 요구가 있는 경우',
            ],
        },
        {
            num: '05',
            title: '개인정보의 파기',
            body: [
                '개인정보 보유기간의 경과, 처리목적 달성 등 개인정보가 불필요하게 되었을 때에는 지체 없이 해당 개인정보를 파기합니다.',
            ],
        },
        {
            num: '06',
            title: '이용자의 권리',
            body: ['이용자는 언제든지 다음의 권리를 행사할 수 있습니다.'],
            list: ['개인정보 열람 요구', '오류 등이 있을 경우 정정 요구', '삭제 요구', '처리정지 요구'],
        },
        {
            num: '07',
            title: '개인정보 보호책임자',
            body: [
                '개인정보 처리에 관한 업무를 총괄해서 책임지고, 개인정보 처리와 관련한 정보주체의 불만처리 및 피해구제 등을 위하여 아래와 같이 개인정보 보호책임자를 지정하고 있습니다.',
            ],
            contact: 'contact@endurohub.kr',
        },
        {
            num: '08',
            title: '개인정보처리방침의 변경',
            body: [
                '이 개인정보처리방침은 시행일로부터 적용되며, 법령 및 방침에 따른 변경내용의 추가, 삭제 및 정정이 있는 경우에는 변경사항의 시행 7일 전부터 공지사항을 통하여 고지할 것입니다.',
            ],
        },
    ];
</script>

<svelte:head>
    <title>개인정보처리방침 - 엔듀로허브</title>
    <meta name="description" content="엔듀로허브의 개인정보처리방침" />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="개인정보처리방침 - 엔듀로허브" />
    <meta property="og:description" content="엔듀로허브의 개인정보처리방침" />
    <meta property="og:image" content="{data.appUrl}/images/og-image.png" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta name="twitter:image" content="{data.appUrl}/images/og-image.png" />
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="page-wrap">
    <article class="page-shell">
        <header class="page-head">
            <div class="head-row">
                <div class="arena-kicker">개인정보 · 처리방침</div>
                <div class="head-meta">
                    <span class="meta-key">시행</span>
                    <span class="meta-val">{dateStr}</span>
                </div>
            </div>
            <h1 class="page-title">개인정보<br />처리방침</h1>
            <p class="page-lead">
                엔듀로허브가 어떤 정보를 수집하고, 어떻게 보관하며, 누구에게 제공하는지 정리했습니다.
            </p>
        </header>

        <div class="toc">
            <div class="arena-kicker">목차 · {sections.length}</div>
            <ol class="toc-list">
                {#each sections as s}
                    <li>
                        <a href={`#sec-${s.num}`} class="toc-link">
                            <span class="toc-num">{s.num}</span>
                            <span class="toc-title">{s.title}</span>
                        </a>
                    </li>
                {/each}
            </ol>
        </div>

        <div class="sections">
            {#each sections as s}
                <section id={`sec-${s.num}`} class="policy-section">
                    <div class="sec-head">
                        <span class="sec-num">{s.num}</span>
                        <h2 class="sec-title">{s.title}</h2>
                    </div>
                    <div class="sec-body">
                        {#each s.body as p}
                            <p class="sec-paragraph">{p}</p>
                        {/each}
                        {#if s.list}
                            <ul class="sec-list">
                                {#each s.list as item}
                                    <li>{item}</li>
                                {/each}
                            </ul>
                        {/if}
                        {#if s.contact}
                            <div class="sec-contact">
                                <span class="contact-key">이메일</span>
                                <a href={`mailto:${s.contact}`} class="contact-val">{s.contact}</a>
                            </div>
                        {/if}
                    </div>
                </section>
            {/each}
        </div>
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
        gap: 40px;
    }

    /* Header */
    .page-head {
        display: flex;
        flex-direction: column;
        gap: 14px;
        padding-bottom: 32px;
        border-bottom: 1px solid var(--arena-line);
    }
    .head-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
    }
    .head-meta {
        display: inline-flex;
        align-items: baseline;
        gap: 8px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1px;
    }
    .meta-key {
        color: var(--arena-ink-mute);
        text-transform: uppercase;
    }
    .meta-val {
        color: var(--arena-ink);
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .page-title {
        font-family: var(--arena-f-display);
        font-size: 52px;
        font-weight: 700;
        letter-spacing: -2px;
        line-height: 1;
        margin: 0;
        color: var(--arena-ink);
    }
    .page-lead {
        font-family: var(--arena-f-body);
        font-size: 15px;
        line-height: 1.6;
        color: var(--arena-ink-soft);
        margin: 0;
        max-width: 56ch;
        word-break: keep-all;
    }

    /* Table of contents */
    .toc {
        display: flex;
        flex-direction: column;
        gap: 14px;
        padding: 22px 20px;
        background: var(--arena-paper-alt);
        border: 1px solid var(--arena-line);
    }
    .toc-list {
        display: grid;
        grid-template-columns: 1fr;
        gap: 0;
        margin: 0;
        padding: 0;
        list-style: none;
    }
    @media (min-width: 720px) {
        .toc-list {
            grid-template-columns: 1fr 1fr;
        }
    }
    .toc-link {
        display: flex;
        align-items: baseline;
        gap: 12px;
        padding: 8px 0;
        text-decoration: none;
        color: var(--arena-ink);
        border-top: 1px dashed transparent;
    }
    .toc-link:hover {
        color: var(--arena-accent-deep);
    }
    .toc-num {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: var(--arena-ink-mute);
        flex-shrink: 0;
        min-width: 26px;
    }
    .toc-link:hover .toc-num {
        color: var(--arena-accent-deep);
    }
    .toc-title {
        font-family: var(--arena-f-body);
        font-size: 13px;
        line-height: 1.4;
        word-break: keep-all;
    }

    /* Sections */
    .sections {
        display: flex;
        flex-direction: column;
        gap: 0;
        border-top: 1px solid var(--arena-line);
    }
    .policy-section {
        padding: 28px 0;
        border-bottom: 1px solid var(--arena-line-soft);
        scroll-margin-top: 80px;
    }
    .policy-section:last-child {
        border-bottom: none;
    }
    .sec-head {
        display: flex;
        align-items: baseline;
        gap: 12px;
        margin-bottom: 14px;
    }
    .sec-num {
        font-family: var(--arena-f-mono);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: var(--arena-accent-deep);
        flex-shrink: 0;
    }
    .sec-title {
        font-family: var(--arena-f-display);
        font-size: 20px;
        font-weight: 700;
        letter-spacing: -0.4px;
        color: var(--arena-ink);
        margin: 0;
    }
    .sec-body {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding-left: 38px;
    }
    @media (max-width: 540px) {
        .sec-body {
            padding-left: 0;
        }
    }
    .sec-paragraph {
        font-family: var(--arena-f-body);
        font-size: 14px;
        line-height: 1.75;
        color: var(--arena-ink);
        margin: 0;
        word-break: keep-all;
    }
    .sec-list {
        margin: 0;
        padding: 0 0 0 20px;
        list-style: disc;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .sec-list li {
        font-family: var(--arena-f-body);
        font-size: 14px;
        line-height: 1.6;
        color: var(--arena-ink);
        word-break: keep-all;
    }
    .sec-list li::marker {
        color: var(--arena-ink-soft);
    }

    .sec-contact {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        padding: 10px 14px;
        background: var(--arena-paper-alt);
        border: 1px solid var(--arena-line);
        align-self: flex-start;
    }
    .contact-key {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
    }
    .contact-val {
        font-family: var(--arena-f-mono);
        font-size: 13px;
        color: var(--arena-ink);
        text-decoration: none;
        font-weight: 600;
    }
    .contact-val:hover {
        color: var(--arena-accent-deep);
    }

    @media (max-width: 719px) {
        .page-title {
            font-size: 40px;
            letter-spacing: -1.5px;
        }
        .head-row {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
        }
    }
</style>
