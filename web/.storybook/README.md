# 디자인 변경 비교

실제 변경 전 컴포넌트와 현재 컴포넌트를 같은 데이터로 비교한다. 기본으로 열리는 **일자별 그룹 목록**은 날짜 그룹핑 직전의 작업 트리 목록을 `src/stories/before-date-groups`에 보존한 비교다. **달력 높이 개선**은 높이 수정 직전의 작업 트리 달력을 `src/stories/before-density`에 보존한다. 나머지 대상의 변경 전 기준은 `src/stories/before/provenance.json`의 Git 커밋으로 고정한다. 변경 후는 현재 서비스 컴포넌트를 직접 import하므로 이후 수정도 반영된다.

## Storybook 실행

`web` 디렉터리에서 실행한다.

```powershell
npm run storybook:install
npm run storybook
```

접속: http://localhost:6006/?path=/story/design-comparison--overview

```powershell
npm run storybook:check
npm run build-storybook
```

개발 도구 의존성은 `.storybook/dependencies/package.json`에서 별도로 관리한다. 최초 설치가 완료되면 해당 디렉터리의 잠금 파일도 함께 커밋한다. 앱의 기존 `package-lock.json`과 `npm ci`는 그대로 사용할 수 있다. Storybook 10.6.4, SvelteKit 2, Svelte 5, Vite 6을 대상으로 한다.

## 비교 방법

`디자인 비교 → 나란히 비교`에서 대상, 화면 너비, 테마를 선택한다. 두 iframe에 동일한 조건을 적용하므로 작은 화면에서도 실제 390px, 768px, 1100px 렌더링을 비교한다. 넓은 화면 두 개는 가로로 스크롤해서 살펴볼 수 있다. `개별 보기`에는 각 버전을 따로 여는 20개 스토리가 있다.

| 대상 | 비교할 내용 |
| --- | --- |
| 일자별 그룹 목록 | 행마다 반복하는 날짜를 그룹 제목으로 한 번 표시하고 대회명·상태·메타정보의 위치를 조정한 월 전체 목록 |
| 달력 높이 개선 | 종목별 집계와 접수 수로 늘어나는 날짜 칸, 고정 높이의 날짜·전체 수 요약 |
| 종목 태그와 접수 상태 | 중복 점과 점 없는 텍스트 표현 |
| 대회 카드 | 같은 제목, 날짜, 지역, 거리, 참가비의 배치 |
| 러닝 대회 목록 | 제목에 이미 명시한 종목의 반복 여부 |
| 홈 후기와 회원 기록 | 작성 정보, 대회명, 코스와 날짜의 위계 |
| 여러 종목의 달력 | 모바일 점 표시와 종목별 대회 수 |
| 러닝 필터 달력 | 단일 종목에서 생략하는 반복 정보 |
| 접수 중 필터 목록 | 일반 상태 반복과 마감 임박·남은 기간의 구분 |
| 지역별 대회 지도 | 색상에만 의존하는 점과 종목명 텍스트 |

예시는 모두 가상의 데이터다. 양쪽 시계는 2026-11-07 12:00 KST로 고정한다. **일자별 그룹 목록**은 달력 전체를 제외하고 5월 전체 목록을 열린 상태로 보여준다. 2027년 5월의 같은 36개 대회와 6개 날짜를 양쪽에 사용한다. 변경 전의 날짜 36회 표시는 변경 후 그룹 제목 6회로 줄어든다. 각 대회 행에서는 날짜를 생략하며, 제목·종목·접수 상태·마감일·지역·거리·참가비는 유지한다. 이미 날짜가 정해진 일자별 모달에는 그룹 제목을 추가하지 않는다. 이 비교에는 현재 공통 컴포넌트·토큰 CSS를 적용한다. 개별 스토리 ID는 `design-preview--date-groups-before`와 `design-preview--date-groups-after`다.

**달력 높이 개선**은 2027년 5월의 6주 모두에 다섯 종목, 6개 대회가 있는 날짜를 배치한다. 기존 대상의 11월 데이터는 바꾸지 않는다. 이 비교의 양쪽에는 현재 공통 컴포넌트·토큰 CSS를 적용하여 달력 배치와 높이 변화에 집중한다. 개별 스토리 ID는 `design-preview--calendar-height-before`와 `design-preview--calendar-height-after`다.

나머지 대상은 각 버전의 전역 컴포넌트 CSS를 해당 iframe 안에서만 주입한다. 공통 CSS에는 최신 컴포넌트 CSS를 섞지 않아 기존 Git 기준 화면이 현재 스타일에 영향을 받지 않게 한다. 실제 API와 분석 이벤트는 프리뷰용 모듈로 대체한다.

Storybook의 달력 URL 상태는 스토리별로 고정한다. 필터 버튼의 탐색은 Storybook 액션으로 기록하며, 필터 결과 비교는 해당 스토리를 선택한다. 날짜별 목록 모달과 지역 선택 등 컴포넌트 내부 동작은 직접 확인할 수 있다.

## 서버 없이 여는 비교 화면

```powershell
npm run design:compare
npm run design:check
```

`design-comparison/index.html`을 브라우저에서 연다. 모든 스크립트와 스타일을 한 HTML에 포함하므로 별도 서버가 필요 없다. Storybook 스토리와 동일한 컴포넌트·예시 데이터를 사용하는 비교 갤러리이며 Storybook 런타임 자체는 포함하지 않는다. 이 갤러리에서는 필터 변경도 로컬 모의 상태에만 반영된다. 외부 요청 없이 열 수 있도록 시스템 대체 폰트를 사용한다. Storybook에서 실행하면 서비스와 같은 웹폰트가 적용된다.

현재 작업 환경에서는 `registry.npmjs.org` DNS 조회가 `ENOTFOUND`로 실패하여 Storybook 패키지 설치와 Storybook 자체 빌드는 검증하지 못했다. 기존에 설치된 Svelte/Vite를 사용하는 별도 비교 갤러리 빌드는 검증한다.
