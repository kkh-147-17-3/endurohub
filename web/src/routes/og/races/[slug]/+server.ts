import type { RequestHandler } from './$types';
import satori from 'satori';
import { Resvg } from '@resvg/resvg-js';
import { html as toReactNode } from 'satori-html';
import { error } from '@sveltejs/kit';
import { read } from '$app/server';
import { apiFetch } from '$lib/api';
import type { RaceDetailResponse, Sport } from '$lib/types';
import PretendardRegular from '$lib/og/fonts/Pretendard-Regular.otf';
import PretendardBold from '$lib/og/fonts/Pretendard-Bold.otf';

// Arena tokens (oklch → hex approximations for satori compat)
const ARENA = {
	paper: '#f4f3eb',
	paperAlt: '#ebe9dd',
	ink: '#283228',
	inkSoft: '#5d685f',
	inkMute: '#9ea7a0',
	line: '#283228',
	lineSoft: '#c1c0b1',
	accent: '#6b9462',
	urgent: '#d35a3f'
};

const SPORT_ACCENT: Record<Sport, string> = {
	running: '#5a3f93',
	swimming: '#3866a2',
	cycling: '#a06c2a',
	triathlon: '#8c3978',
	trail_running: '#3d5e44'
};

const SPORT_LABEL: Record<Sport, string> = {
	running: '마라톤',
	swimming: '수영',
	cycling: '사이클',
	triathlon: '철인3종',
	trail_running: '트레일러닝'
};

const DAY_NAMES = ['일', '월', '화', '수', '목', '금', '토'];

let cachedFontReg: ArrayBuffer | null = null;
let cachedFontBold: ArrayBuffer | null = null;

async function loadFonts() {
	if (!cachedFontReg) {
		cachedFontReg = await read(PretendardRegular).arrayBuffer();
	}
	if (!cachedFontBold) {
		cachedFontBold = await read(PretendardBold).arrayBuffer();
	}
	return { reg: cachedFontReg, bold: cachedFontBold };
}

function formatRaceDate(d: string | null): string {
	if (!d) return '—';
	const [y, m, day] = d.split('-');
	if (!y || !m || !day) return '—';
	const dow = DAY_NAMES[new Date(`${d}T00:00:00`).getDay()] ?? '';
	return `${m}.${day}${dow ? ` (${dow})` : ''}`;
}

function escapeHtml(s: string): string {
	return s.replace(
		/[&<>"']/g,
		(c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!
	);
}

function truncate(s: string, max: number): string {
	return s.length > max ? `${s.slice(0, max - 1)}…` : s;
}

export const GET: RequestHandler = async ({ params, locals, setHeaders }) => {
	const data = await apiFetch<RaceDetailResponse>(`/races/${params.slug}/`, {
		clientIp: locals.clientIp
	});
	const race = data.race;
	if (!race) error(404, 'Race not found');

	const sport = race.sport as Sport;
	const accent = SPORT_ACCENT[sport] ?? ARENA.accent;
	const sportLabel = race.sportLabel || SPORT_LABEL[sport] || sport;

	const dDay = race.daysUntilRegistrationEnd;
	const ddayValue =
		dDay === null || dDay === undefined
			? '—'
			: dDay < 0
				? '마감'
				: dDay === 0
					? '오늘'
					: `D-${String(dDay).padStart(2, '0')}`;
	const ddayUrgent = dDay !== null && dDay !== undefined && dDay >= 0 && dDay <= 3;

	const distanceCount = race.distances?.length ?? 0;
	const courseValue = distanceCount > 0 ? `${distanceCount}개 종목` : '—';

	const dateValue = formatRaceDate(race.raceDate);
	const locationValue = race.location ? truncate(race.location, 14) : '—';
	const region = race.region || '';

	const distances = (race.distances || [])
		.slice(0, 4)
		.map((d) => (typeof d === 'string' ? d : d.name))
		.filter(Boolean);
	const moreCount = Math.max(0, distanceCount - distances.length);

	const distanceChips = distances
		.map(
			(chip) =>
				`<div style="display:flex;padding:8px 14px;border:1px solid ${ARENA.line};font-size:18px;color:${ARENA.ink};">${escapeHtml(chip)}</div>`
		)
		.join('');
	const moreChip =
		moreCount > 0
			? `<div style="display:flex;padding:8px 14px;border:1px solid ${ARENA.lineSoft};font-size:18px;color:${ARENA.inkSoft};">+${moreCount}</div>`
			: '';

	const isOpen = race.status === 'registration_open';
	const statusChip = isOpen
		? `<div style="display:flex;padding:4px 10px;background:${ARENA.ink};color:${ARENA.paper};font-size:14px;font-weight:700;letter-spacing:1px;">접수중</div>`
		: '';

	const cells: Array<{ label: string; value: string; urgent?: boolean }> = [
		{ label: '일자', value: dateValue },
		{ label: '장소', value: locationValue },
		{ label: '종목', value: courseValue },
		{ label: '접수마감', value: ddayValue, urgent: ddayUrgent }
	];
	const metaGrid = cells
		.map(
			(cell, i) => `
			<div style="display:flex;flex-direction:column;flex:1;padding:20px 22px;${i < cells.length - 1 ? `border-right:1px solid ${ARENA.line};` : ''}">
				<div style="display:flex;font-size:13px;letter-spacing:2px;color:${ARENA.inkSoft};margin-bottom:8px;">${cell.label}</div>
				<div style="display:flex;font-size:30px;font-weight:700;color:${cell.urgent ? ARENA.urgent : ARENA.ink};letter-spacing:-0.5px;">${escapeHtml(cell.value)}</div>
			</div>`
		)
		.join('');

	const markup = `
		<div style="display:flex;width:100%;height:100%;background:${ARENA.paper};font-family:'Pretendard';">
			<div style="display:flex;width:14px;height:100%;background:${accent};"></div>
			<div style="display:flex;flex-direction:column;flex:1;padding:64px 64px 56px;justify-content:space-between;">
				<div style="display:flex;flex-direction:column;">
					<div style="display:flex;align-items:center;gap:16px;font-size:16px;letter-spacing:2.5px;color:${ARENA.inkSoft};margin-bottom:32px;">
						<div style="display:flex;width:8px;height:8px;background:${accent};"></div>
						<div style="display:flex;color:${ARENA.ink};font-weight:700;">${escapeHtml(sportLabel)}</div>
						${region ? `<div style="display:flex;color:${ARENA.lineSoft};">/</div><div style="display:flex;">${escapeHtml(region)}</div>` : ''}
						${statusChip ? `<div style="display:flex;color:${ARENA.lineSoft};">/</div>${statusChip}` : ''}
					</div>
					<div style="display:flex;font-size:72px;font-weight:700;line-height:1.05;color:${ARENA.ink};letter-spacing:-2.5px;margin-bottom:48px;">${escapeHtml(truncate(race.title, 30))}</div>
					<div style="display:flex;border:1px solid ${ARENA.line};background:${ARENA.paperAlt};">${metaGrid}</div>
					${distanceChips ? `<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:28px;">${distanceChips}${moreChip}</div>` : ''}
				</div>
				<div style="display:flex;align-items:center;justify-content:space-between;border-top:1px solid ${ARENA.lineSoft};padding-top:20px;">
					<div style="display:flex;align-items:center;gap:10px;">
						<div style="display:flex;width:10px;height:10px;background:${ARENA.accent};"></div>
						<div style="display:flex;font-size:22px;font-weight:700;color:${ARENA.ink};letter-spacing:-0.4px;">endurohub</div>
					</div>
					<div style="display:flex;font-size:14px;letter-spacing:2px;color:${ARENA.inkSoft};">엔듀로허브 · 지구력 스포츠 대회 플랫폼</div>
				</div>
			</div>
		</div>
	`;

	const fonts = await loadFonts();
	const node = toReactNode(markup);
	const svg = await satori(node as Parameters<typeof satori>[0], {
		width: 1200,
		height: 630,
		fonts: [
			{ name: 'Pretendard', data: fonts.reg, weight: 400, style: 'normal' },
			{ name: 'Pretendard', data: fonts.bold, weight: 700, style: 'normal' }
		]
	});

	const png = new Resvg(svg, {
		fitTo: { mode: 'width', value: 1200 }
	})
		.render()
		.asPng();

	setHeaders({
		'Content-Type': 'image/png',
		'Cache-Control': 'public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800'
	});

	return new Response(new Uint8Array(png));
};
