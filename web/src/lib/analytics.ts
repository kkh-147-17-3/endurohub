/**
 * 프론트엔드 이벤트 트래킹 — GA4 커스텀 이벤트 + 자체 API 동시 전송
 */

type EventProperties = Record<string, string | number | boolean | null | undefined>;

function sendToGA(eventType: string, properties: EventProperties) {
	if (typeof gtag === 'function') {
		gtag('event', eventType, properties);
	}
}

interface QueueItem {
	eventType: string;
	properties: EventProperties;
	retries: number;
}

const MAX_RETRIES = 2;
const queue: QueueItem[] = [];
let flushTimer: ReturnType<typeof setTimeout> | null = null;

function sendToAPI(eventType: string, properties: EventProperties) {
	queue.push({ eventType, properties, retries: 0 });

	if (flushTimer) return;
	flushTimer = setTimeout(flushQueue, 2000);
}

function requeueBatch(batch: QueueItem[]) {
	const retryable = batch.filter((e) => e.retries < MAX_RETRIES);
	if (retryable.length === 0) return;

	for (const item of retryable) {
		item.retries++;
		queue.push(item);
	}
	if (!flushTimer) {
		flushTimer = setTimeout(flushQueue, 5000);
	}
}

function flushQueue() {
	flushTimer = null;
	if (queue.length === 0) return;

	const batch = queue.splice(0, 10);
	const payload = JSON.stringify(
		batch.map((e) => ({ event_type: e.eventType, properties: e.properties }))
	);

	if (navigator.sendBeacon) {
		const sent = navigator.sendBeacon('/api/v1/events/', new Blob([payload], { type: 'application/json' }));
		if (!sent) {
			requeueBatch(batch);
		}
	} else {
		fetch('/api/v1/events/', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: payload,
			keepalive: true
		}).catch(() => {
			requeueBatch(batch);
		});
	}
}

export function track(eventType: string, properties: EventProperties = {}) {
	sendToGA(eventType, properties);
	sendToAPI(eventType, properties);
}

/**
 * 외부 링크 클릭 추적
 */
export function trackOutboundClick(url: string, label?: string) {
	track('outbound_click', { url, label: label || '' });
}

/**
 * 페이지 이탈 시 큐에 남은 이벤트를 즉시 전송
 */
if (typeof window !== 'undefined') {
	document.addEventListener('visibilitychange', () => {
		if (document.visibilityState === 'hidden') {
			flushQueue();
		}
	});
}
