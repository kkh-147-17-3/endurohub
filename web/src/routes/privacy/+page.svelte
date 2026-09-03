<script lang="ts">
    let { data } = $props();

    const dateStr = '2026.09.03';

    const sections = [
        {
            num: '01',
            title: '개인정보의 처리 목적',
            body: [
                '엔듀로허브(이하 "서비스")는 다음의 목적을 위하여 개인정보를 처리합니다.',
            ],
            list: [
                '회원가입·본인 확인·계정 관리: 이메일 주소, 닉네임, 소셜 로그인 식별자',
                '맞춤형 서비스 제공: 선호 종목·지역, 관심 대회, 참가 계획 및 이용자가 입력한 경기 기록',
                '커뮤니티 운영: 게시물, 리뷰, 신고 및 문의 내용',
                '이벤트 운영: 회원 식별자, 리뷰·기록 참여 내역, 인증된 이메일 주소',
                '선택 알림 제공: 이메일 수신 동의 여부, 관심 종목·지역 및 푸시 토큰',
                '보안·서비스 개선·통계 분석: 접속 기록, IP 주소의 해시값, 세션 식별자, 기기·브라우저 정보 및 이용 기록',
            ],
        },
        {
            num: '02',
            title: '수집하는 개인정보 항목',
            body: ['서비스는 다음과 같은 개인정보를 수집합니다.'],
            list: [
                '필수 수집: 이메일 주소, 닉네임, 소셜 로그인 제공자 및 식별자',
                '이용자가 직접 입력: 선호 종목·지역, 관심·참가 대회, 경기 기록, 게시물·리뷰·문의 내용',
                '선택 수집: 이메일 소식 수신 여부, 모바일 푸시 토큰과 알림 대상 종목·지역',
                '자동 생성·수집: 세션 쿠키(ehub_sid), 접속 일시, 페이지·기능 이용 기록, 리퍼러, 브라우저·기기 정보 및 IP 주소의 해시값',
            ],
        },
        {
            num: '03',
            title: '개인정보의 보유 및 이용 기간',
            body: [
                '회원 계정과 회원이 입력한 정보는 회원 탈퇴 시까지 보유하며, 탈퇴 요청이 처리되면 지체 없이 파기합니다. 이벤트 당첨 및 경품 발송 정보는 이벤트 종료와 발송·문의 처리가 끝난 날부터 3개월간 보관한 후 파기합니다. 이메일 인증 코드는 유효기간 만료 또는 사용 후 파기합니다. 분석용 세션 쿠키는 생성일부터 최대 1년간 유지됩니다. 관계 법령에 별도 보존 의무가 있는 경우에는 해당 정보만 법정 기간 동안 분리 보관합니다.',
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
            title: '개인정보 처리의 위탁 및 국외 이전',
            body: [
                '서비스 운영을 위해 이메일 발송, 오류 분석, 이용 통계 및 소셜 로그인 사업자의 시스템을 이용할 수 있습니다. 현재 이용 통계는 PostHog로 전송될 수 있으며 기본 수신 서버는 미국에 있습니다. 전송 항목에는 회원 식별자, 이메일, 닉네임, 이메일 수신 동의 여부, 세션 식별자와 서비스 이용 기록이 포함될 수 있습니다. 오류 분석을 위해 Sentry가 사용될 수 있습니다. 각 서비스는 목적 달성 또는 계약 종료 시까지 관련 정보를 처리합니다. 실제 운영 위탁사·이전 국가·일시·방법·보유기간이 변경되면 이 방침을 통해 공개합니다.',
            ],
        },
        {
            num: '06',
            title: '개인정보의 파기 절차 및 방법',
            body: ['보유기간이 지나거나 처리 목적이 달성된 정보는 별도 검토 후 지체 없이 파기합니다. 전자파일은 복구 또는 재생되지 않도록 안전한 방법으로 삭제하고, 종이 문서는 분쇄하거나 소각합니다. 법령에 따라 보존하는 정보는 다른 정보와 분리하여 보관합니다.'],
        },
        {
            num: '07',
            title: '이용자의 권리와 행사 방법',
            body: ['이용자는 자신의 개인정보에 대한 열람, 정정, 삭제, 처리정지 및 동의 철회를 요청할 수 있습니다. 프로필과 이메일 수신 설정은 마이페이지에서 변경할 수 있으며, 그 밖의 요청과 회원 탈퇴는 아래 이메일로 접수할 수 있습니다. 법정대리인은 관련 법령에 따라 이용자를 대신하여 권리를 행사할 수 있습니다. 요청자의 본인 여부를 확인한 후 법령이 정한 기간 안에 처리합니다.'],
            contact: 'contact@endurohub.kr',
        },
        {
            num: '08',
            title: '자동 수집 장치와 거부 방법',
            body: ['로그인 유지, 보안 및 이용 통계를 위해 쿠키와 유사한 기술을 사용합니다. 이용자는 브라우저 설정에서 쿠키를 삭제하거나 저장을 거부할 수 있습니다. 필수 쿠키를 거부하면 로그인 등 일부 기능을 이용하기 어려울 수 있습니다. 선택적 이메일 알림은 마이페이지에서 언제든지 해제할 수 있으며, 해제해도 회원가입과 이벤트 참여에는 영향이 없습니다.'],
        },
        { num: '09', title: '개인정보의 안전성 확보조치', body: ['서비스는 접근 권한 관리, 인증정보 보호, 전송구간 암호화, 접속 기록 관리, 보안 업데이트와 백업 등 개인정보의 안전성 확보에 필요한 관리적·기술적 조치를 시행합니다.'] },
        { num: '10', title: '개인정보 보호책임자 및 문의', body: ['개인정보 처리와 권리 행사, 불만 처리 및 피해구제에 관한 문의는 개인정보 보호 담당자에게 접수할 수 있습니다.'], contact: 'contact@endurohub.kr' },
        { num: '11', title: '권익침해 구제 방법', body: ['개인정보 침해에 대한 상담이나 구제가 필요한 경우 개인정보침해 신고센터(국번 없이 118), 개인정보분쟁조정위원회(1833-6972), 경찰청(국번 없이 182) 등 관계 기관에 문의할 수 있습니다.'] },
        {
            num: '12',
            title: '개인정보처리방침의 변경',
            body: ['이 방침은 2026년 9월 3일부터 적용합니다. 내용이 변경되는 경우 원칙적으로 시행 7일 전부터 공지하며, 이용자 권리에 중요한 변경은 시행 30일 전에 알립니다. 이전 방침은 변경 이력과 함께 확인할 수 있도록 보관합니다.'],
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
