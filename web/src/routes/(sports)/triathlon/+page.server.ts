import type { PageServerLoad } from './$types';
import { loadSportLanding } from '$lib/server/sport-landing';

// 이 경로는 예전에 /races?sport=… 로 301 리다이렉트했다. 그 착지점은 canonical 이
// /races 라서 종목 키워드가 전부 /races 로 흡수됐고, facet URL 자체는 색인되지
// 않은 채 크롤 예산만 먹었다. 이제 self-canonical 랜딩 페이지로 직접 응답한다.
export const load: PageServerLoad = async ({ locals }) => loadSportLanding('/triathlon', locals);
