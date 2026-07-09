const DAY_NAMES = ['일', '월', '화', '수', '목', '금', '토'];

/**
 * Today's date in KST as "YYYY-MM-DD", regardless of the runtime timezone
 * (SSR containers run UTC). KST is a fixed UTC+9 offset with no DST, so
 * shifting the epoch by 9h before taking the ISO date is exact.
 */
export function kstTodayStr(): string {
    return new Date(Date.now() + 9 * 3600_000).toISOString().split('T')[0];
}

function parse(date: string): Date {
    return new Date(date + 'T00:00:00');
}

/** "2025년 03월 15일" */
export function formatDateFull(date: string): string {
    const d = parse(date);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}년 ${m}월 ${day}일`;
}

/** "토" */
export function formatDateDay(date: string): string {
    return DAY_NAMES[parse(date).getDay()];
}

/** "2025.03.15" */
export function formatDate(date: string): string {
    const d = parse(date);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}.${m}.${day}`;
}

/** "03.15" */
export function formatDateShort(date: string): string {
    const d = parse(date);
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${m}.${day}`;
}

/** "03/15" */
export function formatDateSlash(date: string): string {
    const d = parse(date);
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${m}/${day}`;
}

export function formatDistanceToNow(dateStr: string): string {
    const d = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (minutes < 1) return '방금 전';
    if (minutes < 60) return `${minutes}분 전`;
    if (hours < 24) return `${hours}시간 전`;
    if (days < 7) return `${days}일 전`;
    return formatDate(dateStr.split('T')[0]);
}
