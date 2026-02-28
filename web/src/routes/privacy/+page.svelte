<script lang="ts">
    const today = new Date();
    const dateStr = `${today.getFullYear()}년 ${String(today.getMonth() + 1).padStart(2, '0')}월 ${String(today.getDate()).padStart(2, '0')}일`;
</script>

<svelte:head>
    <title>개인정보처리방침 - 엔듀로허브</title>
    <meta name="description" content="엔듀로허브의 개인정보처리방침" />
    <meta property="og:title" content="개인정보처리방침 - 엔듀로허브" />
    <meta property="og:description" content="엔듀로허브의 개인정보처리방침" />
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="container mx-auto px-4 py-8">
    <div class="max-w-3xl mx-auto">
        <h1 class="text-3xl font-bold mb-8 text-center">개인정보처리방침</h1>

        <div class="card bg-base-100 shadow-xl">
            <div class="card-body prose max-w-none">
                <p class="text-sm text-base-content/70">시행일: {dateStr}</p>

                <h2>1. 개인정보의 처리 목적</h2>
                <p>엔듀로허브(이하 "서비스")는 다음의 목적을 위하여 개인정보를 처리합니다.</p>
                <ul>
                    <li>서비스 제공 및 운영</li>
                    <li>푸시 알림 서비스 제공</li>
                    <li>서비스 개선 및 통계 분석</li>
                </ul>

                <h2>2. 수집하는 개인정보 항목</h2>
                <p>서비스는 다음과 같은 개인정보를 수집합니다.</p>
                <ul>
                    <li>모바일 앱 이용 시: 기기 식별자(푸시 토큰), 관심 종목 및 지역 설정</li>
                    <li>웹사이트 이용 시: 쿠키, 접속 로그</li>
                </ul>

                <h2>3. 개인정보의 보유 및 이용 기간</h2>
                <p>
                    수집된 개인정보는 수집 목적이 달성된 후에는 지체 없이 파기됩니다.
                    단, 관련 법령에 의해 보존할 필요가 있는 경우 해당 기간 동안 보관됩니다.
                </p>

                <h2>4. 개인정보의 제3자 제공</h2>
                <p>
                    서비스는 원칙적으로 이용자의 개인정보를 제3자에게 제공하지 않습니다.
                    다만, 다음의 경우에는 예외로 합니다.
                </p>
                <ul>
                    <li>이용자가 사전에 동의한 경우</li>
                    <li>법령의 규정에 의거하거나, 수사 목적으로 법령에 정해진 절차와 방법에 따라 수사기관의 요구가 있는 경우</li>
                </ul>

                <h2>5. 개인정보의 파기</h2>
                <p>
                    개인정보 보유기간의 경과, 처리목적 달성 등 개인정보가 불필요하게 되었을 때에는 지체 없이 해당 개인정보를 파기합니다.
                </p>

                <h2>6. 이용자의 권리</h2>
                <p>이용자는 언제든지 다음의 권리를 행사할 수 있습니다.</p>
                <ul>
                    <li>개인정보 열람 요구</li>
                    <li>오류 등이 있을 경우 정정 요구</li>
                    <li>삭제 요구</li>
                    <li>처리정지 요구</li>
                </ul>

                <h2>7. 개인정보 보호책임자</h2>
                <p>
                    개인정보 처리에 관한 업무를 총괄해서 책임지고, 개인정보 처리와 관련한 정보주체의 불만처리 및 피해구제 등을 위하여 아래와 같이 개인정보 보호책임자를 지정하고 있습니다.
                </p>
                <p>
                    이메일: <a href="mailto:privacy@endurohub.kr" class="link link-primary">privacy@endurohub.kr</a>
                </p>

                <h2>8. 개인정보처리방침의 변경</h2>
                <p>
                    이 개인정보처리방침은 시행일로부터 적용되며, 법령 및 방침에 따른 변경내용의 추가, 삭제 및 정정이 있는 경우에는 변경사항의 시행 7일 전부터 공지사항을 통하여 고지할 것입니다.
                </p>
            </div>
        </div>
    </div>
</div>
